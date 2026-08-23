import io
import csv
import logging
from datetime import datetime
from typing import Dict, Any, List
from backend.app.db.mongo import get_db
from backend.app.models.schemas import AuditLogSchema
from backend.app.rag.embeddings import rag_store
from backend.app.agents.prompts import AUDIT_SYSTEM_PROMPT, AUDIT_ROLE

logger = logging.getLogger("reviveai.agents.audit")


class AuditWriter:
    """
    4.7.1 Audit Writer Submodule:
    Writes immutable structured records to audit_logs collection on every state transition.
    """
    @classmethod
    async def log_step(
        cls,
        case_id: str,
        agent: str,
        decision: str,
        reason: str,
        tool_called: str = None,
        result: Dict[str, Any] = None
    ):
        db = get_db()
        logs_col = db.get_collection("audit_logs")
        
        log_id = f"LOG_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        log_entry = AuditLogSchema(
            log_id=log_id,
            case_id=case_id,
            agent=agent,
            decision=decision,
            reason=reason,
            tool_called=tool_called,
            result=result or {}
        ).model_dump()
        
        await logs_col.insert_one(log_entry)
        logger.info(f"[{AUDIT_ROLE}] Case {case_id} | Agent: {agent} | Decision: {decision}")

    @classmethod
    async def log_case_resolution(cls, case_state: Dict[str, Any]):
        case_id = case_state.get("case_id")
        event_type = case_state.get("event_type", "")
        root_cause = case_state.get("root_cause", "")
        amount = case_state.get("amount", 0)
        action = case_state.get("selected_action", "")
        outcome = case_state.get("final_status", "closed")
        
        rag_store.add_resolved_case({
            "case_id": case_id,
            "event_type": event_type,
            "root_cause": root_cause,
            "amount": amount,
            "action": action,
            "outcome": outcome,
            "summary": f"{event_type} caused by {root_cause}, amount {amount}, action taken {action}, outcome {outcome}"
        })


class ExportService:
    """
    4.7.2 Export Service Submodule:
    Generates CSV export of full audit trail per case or per batch.
    """
    @classmethod
    async def export_case_csv(cls, case_id: str) -> str:
        db = get_db()
        audit_col = db.get_collection("audit_logs")
        cursor = audit_col.find({"case_id": case_id}).sort("timestamp", 1)
        logs = await cursor.to_list()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Timestamp", "Case ID", "Agent", "Decision", "Reasoning / Justification", "Tool Called", "Result Payload"])

        for log in logs:
            writer.writerow([
                log.get("timestamp", ""),
                log.get("case_id", ""),
                log.get("agent", ""),
                log.get("decision", ""),
                log.get("reason", ""),
                log.get("tool_called", "") or "None",
                str(log.get("result", {}))
            ])

        return output.getvalue()

    @classmethod
    async def export_batch_csv(cls, status: str = "all") -> str:
        db = get_db()
        cases_col = db.get_collection("recovery_cases")
        query = {}
        if status and status != "all":
            query["status"] = status

        cursor = cases_col.find(query).sort("created_at", -1)
        cases = await cursor.to_list()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Case ID", "Customer ID", "Event Type", "Amount Risk (INR)", "Root Cause", "Selected Action", "Attempts", "Status", "Created At"])

        for c in cases:
            writer.writerow([
                c.get("case_id", ""),
                c.get("customer_id", ""),
                c.get("event_type", ""),
                c.get("amount", 0.0),
                c.get("root_cause", ""),
                c.get("selected_action", ""),
                c.get("attempts", 0),
                c.get("status", ""),
                c.get("created_at", "")
            ])

        return output.getvalue()


class CaseTimelineBuilder:
    """
    4.7.3 Case Timeline Builder Submodule:
    Assembles a human-readable, chronologically ordered timeline view per case for the dashboard drill-down.
    """
    @classmethod
    async def build_case_timeline(cls, case_id: str) -> Dict[str, Any]:
        db = get_db()
        cases_col = db.get_collection("recovery_cases")
        audit_col = db.get_collection("audit_logs")

        case = await cases_col.find_one({"case_id": case_id})
        if not case:
            return {"case": None, "timeline": []}
        case.pop("_id", None)

        cursor = audit_col.find({"case_id": case_id}).sort("timestamp", 1)
        timeline_logs = await cursor.to_list()

        enriched_timeline = []
        for item in timeline_logs:
            enriched_timeline.append({
                "log_id": item.get("log_id"),
                "timestamp": item.get("timestamp"),
                "agent": item.get("agent"),
                "decision": item.get("decision"),
                "reason": item.get("reason"),
                "tool_called": item.get("tool_called"),
                "result": item.get("result", {})
            })

        return {
            "case": case,
            "timeline": enriched_timeline
        }


class AuditAgent:
    """
    4.7 Audit & Logging Module (Audit Agent orchestrator)
    """
    def __init__(self):
        self.role = AUDIT_ROLE
        self.system_prompt = AUDIT_SYSTEM_PROMPT
        self.writer = AuditWriter
        self.export = ExportService
        self.timeline_builder = CaseTimelineBuilder

    async def log_step(self, case_id: str, agent: str, decision: str, reason: str, tool_called: str = None, result: Dict[str, Any] = None):
        await self.writer.log_step(case_id, agent, decision, reason, tool_called, result)

    async def log_case_resolution(self, case_state: Dict[str, Any]):
        await self.writer.log_case_resolution(case_state)


audit_agent = AuditAgent()
