import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from backend.app.db.mongo import get_db
from backend.app.graph.workflow import run_recovery_workflow
from backend.app.agents.execution import execution_agent
from backend.app.mcp.compliance_server import mcp_compliance_server
from backend.app.agents.audit import audit_agent, ExportService, CaseTimelineBuilder

logger = logging.getLogger("reviveai.routers.cases")
router = APIRouter(prefix="/cases", tags=["Cases"])

@router.get("")
async def list_cases(
    status: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 50
):
    """
    Lists recovery cases filterable by status or event_type.
    """
    db = get_db()
    col = db.get_collection("recovery_cases")
    
    query = {}
    if status and status != "all":
        query["status"] = status
    if event_type and event_type != "all":
        query["event_type"] = event_type
        
    cursor = col.find(query).sort("created_at", -1).limit(limit)
    cases = await cursor.to_list()
    for c in cases:
        c.pop("_id", None)
    return {"cases": cases, "total": len(cases)}

@router.get("/export/batch/csv")
async def export_batch_cases_csv(status: Optional[str] = "all"):
    """
    4.7.2 Export Service: Generates CSV export for full batch report.
    """
    csv_data = await ExportService.export_batch_csv(status)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=reviveai_batch_report_{status}.csv"}
    )

@router.get("/{case_id}")
async def get_case_detail(case_id: str):
    """
    4.7.3 Case Timeline Builder: Gets full case detail and chronologically sorted audit timeline.
    """
    result = await CaseTimelineBuilder.build_case_timeline(case_id)
    if not result["case"]:
        raise HTTPException(status_code=404, detail="Case not found")
    return result

@router.get("/{case_id}/export/csv")
async def export_case_audit_csv(case_id: str):
    """
    4.7.2 Export Service: Generates CSV export for a specific case's audit trail.
    """
    csv_data = await ExportService.export_case_csv(case_id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=reviveai_audit_{case_id}.csv"}
    )

@router.post("/{case_id}/actions")
async def trigger_manual_action(case_id: str, payload: Dict[str, Any]):
    """
    Manual demo control: trigger an action retry or override for a case.
    Evaluates action through MCP compliance guard before execution.
    """
    action = payload.get("action", "RETRY_PAYMENT")
    db = get_db()
    cases_col = db.get_collection("recovery_cases")
    case = await cases_col.find_one({"case_id": case_id})
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    customer_id = case.get("customer_id", "")
    
    # 1. MCP Compliance Evaluation
    guard_res = await mcp_compliance_server.evaluate_action(
        case_id=case_id,
        customer_id=customer_id,
        action=action
    )
    
    await audit_agent.log_step(
        case_id=case_id,
        agent="ComplianceGuard",
        decision=guard_res["decision"],
        reason=f"Manual trigger rule '{guard_res['rule_fired']}': {guard_res['reason']}"
    )

    if guard_res["decision"] == "BLOCK":
        from datetime import datetime
        await cases_col.update_one(
            {"case_id": case_id},
            {"$set": {"status": "blocked", "updated_at": datetime.utcnow().isoformat()}}
        )
        return {
            "status": "blocked",
            "message": f"Action blocked by Compliance Guard: {guard_res['reason']}",
            "guard_result": guard_res
        }

    # 2. Execution via Execution Agent
    selected_act = action if guard_res["decision"] == "ALLOW" else "ESCALATE_TO_HUMAN"
    state = {
        "case_id": case_id,
        "selected_action": selected_act,
        "customer_id": customer_id,
        "amount": case.get("amount", 0.0),
        "attempts": case.get("attempts", 0),
        "guard_result": guard_res
    }
    
    exec_res = await execution_agent.process(state)
    
    await audit_agent.log_step(
        case_id=case_id,
        agent="Execution",
        decision=exec_res["final_status"].upper(),
        reason=f"Manual action '{exec_res['action']}' executed.",
        tool_called=exec_res["action"],
        result=exec_res["execution_result"]
    )

    msg = f"Action '{action}' executed successfully." if guard_res["decision"] == "ALLOW" else f"Action escalated to human team: {guard_res['reason']}"
    return {
        "status": exec_res.get("final_status"),
        "message": msg,
        "case_id": case_id,
        "guard_result": guard_res,
        "execution_result": exec_res
    }
