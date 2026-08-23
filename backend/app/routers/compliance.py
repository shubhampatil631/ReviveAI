import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from backend.app.db.mongo import get_db
from backend.app.mcp.compliance_server import mcp_compliance_server

logger = logging.getLogger("reviveai.routers.compliance")
router = APIRouter(prefix="/compliance", tags=["Compliance MCP Server"])

class CheckRetryRequest(BaseModel):
    case_id: str

class CheckContactRequest(BaseModel):
    customer_id: str
    case_id: Optional[str] = ""

class EvaluateActionRequest(BaseModel):
    case_id: str
    customer_id: str
    action: str

@router.get("/logs")
async def get_compliance_logs(decision: Optional[str] = None):
    """
    Returns full compliance decision audit trail from the MCP Server (4.5.6 Decision Logger).
    """
    db = get_db()
    col = db.get_collection("compliance_decisions")
    query = {}
    if decision and decision != "all":
        query["decision"] = decision.upper()
        
    cursor = col.find(query).sort("timestamp", -1)
    logs = await cursor.to_list()
    for l in logs:
        l.pop("_id", None)
    return {"compliance_logs": logs, "count": len(logs)}

@router.post("/check-retry")
async def check_retry_allowed_tool(payload: CheckRetryRequest):
    """
    Exposed MCP Tool: check_retry_allowed(case_id) -> { allowed: bool, decision: string, reason: string }
    (4.5.1 Retry Limiter & 4.5.2 Cooldown Enforcer)
    """
    allowed, decision, reason = await mcp_compliance_server.check_retry_allowed(payload.case_id)
    return {
        "allowed": allowed,
        "decision": decision,
        "reason": reason,
        "case_id": payload.case_id
    }

@router.post("/check-contact")
async def check_contact_allowed_tool(payload: CheckContactRequest):
    """
    Exposed MCP Tool: check_contact_allowed(customer_id, case_id) -> { allowed: bool, decision: string, reason: string }
    (4.5.3 DND Registry & 4.5.5 Blackout Window Checker)
    """
    allowed, decision, reason = await mcp_compliance_server.check_contact_allowed(payload.customer_id, payload.case_id or "")
    return {
        "allowed": allowed,
        "decision": decision,
        "reason": reason,
        "customer_id": payload.customer_id,
        "case_id": payload.case_id
    }

@router.get("/escalation-tier/{case_id}")
async def check_escalation_tier_tool(case_id: str):
    """
    Exposed MCP Tool: check_escalation_tier(case_id) -> { current_tier: int, max_tier: int, can_escalate: bool }
    (4.5.4 Escalation Tier Manager)
    """
    result = await mcp_compliance_server.check_escalation_tier(case_id)
    result["case_id"] = case_id
    return result

@router.post("/evaluate")
async def evaluate_action_tool(payload: EvaluateActionRequest):
    """
    Primary MCP Tool: evaluate_action(case_id, customer_id, action) -> { allowed: bool, decision: string, rule_fired: string, reason: string }
    Evaluates proposed action against all 5 hard policy guardrails.
    """
    result = await mcp_compliance_server.evaluate_action(
        case_id=payload.case_id,
        customer_id=payload.customer_id,
        action=payload.action
    )
    return result

@router.get("/{case_id}")
async def get_case_compliance_trail(case_id: str):
    """
    Gets compliance decision history for a specific case.
    """
    db = get_db()
    col = db.get_collection("compliance_decisions")
    cursor = col.find({"case_id": case_id}).sort("timestamp", 1)
    logs = await cursor.to_list()
    for l in logs:
        l.pop("_id", None)
    return {"case_id": case_id, "decisions": logs}
