import logging
from datetime import datetime
from typing import Dict, Any, TypedDict, Optional
from langgraph.graph import StateGraph, END
from backend.app.db.mongo import get_db
from backend.app.agents.detector import detector_agent
from backend.app.agents.diagnosis import diagnosis_agent
from backend.app.agents.strategy import strategy_agent
from backend.app.mcp.compliance_server import mcp_compliance_server
from backend.app.agents.execution import execution_agent
from backend.app.agents.audit import audit_agent

logger = logging.getLogger("reviveai.workflow")

class CaseGraphState(TypedDict):
    case_id: str
    customer_id: str
    event: Dict[str, Any]
    diagnosis: Dict[str, Any]
    decision: Dict[str, Any]
    selected_action: str
    guard_result: Dict[str, Any]
    execution_result: Dict[str, Any]
    attempts: int
    amount: float
    event_type: str
    root_cause: str
    final_status: str
    recovered_amount: float
    verification_status: str

# Node definitions
async def detect_node(state: CaseGraphState) -> CaseGraphState:
    res = await detector_agent.process(state["event"])
    await audit_agent.log_step(
        case_id=res["case_id"],
        agent="Detector",
        decision=f"Risk: {res['risk']}",
        reason=f"Event classified. Recovery Probability: {res['recovery_probability']}"
    )
    return {
        **state,
        "case_id": res["case_id"],
        "customer_id": res["customer_id"],
        "amount": res["amount"],
        "event_type": res["event_type"],
        "attempts": 0
    }

async def diagnose_node(state: CaseGraphState) -> CaseGraphState:
    res = await diagnosis_agent.process(state)
    await audit_agent.log_step(
        case_id=state["case_id"],
        agent="Diagnosis",
        decision=res["root_cause"],
        reason=res["reasoning_summary"]
    )
    return {
        **state,
        "diagnosis": res,
        "root_cause": res["root_cause"]
    }

async def decide_node(state: CaseGraphState) -> CaseGraphState:
    res = await strategy_agent.process(state)
    await audit_agent.log_step(
        case_id=state["case_id"],
        agent="Strategy",
        decision=res["selected_action"],
        reason=res["action_rationale"]
    )
    return {
        **state,
        "decision": res,
        "selected_action": res["selected_action"]
    }

async def guard_node(state: CaseGraphState) -> CaseGraphState:
    guard_res = await mcp_compliance_server.evaluate_action(
        case_id=state["case_id"],
        customer_id=state["customer_id"],
        action=state["selected_action"]
    )
    await audit_agent.log_step(
        case_id=state["case_id"],
        agent="ComplianceGuard",
        decision=guard_res["decision"],
        reason=f"Rule '{guard_res['rule_fired']}': {guard_res['reason']}"
    )
    new_state = {**state, "guard_result": guard_res}
    if guard_res["decision"] == "BLOCK":
        new_state["final_status"] = "blocked"
        db = get_db()
        cases_col = db.get_collection("recovery_cases")
        await cases_col.update_one(
            {"case_id": state["case_id"]},
            {"$set": {"status": "blocked", "updated_at": datetime.utcnow().isoformat()}}
        )
    return new_state

async def execute_node(state: CaseGraphState) -> CaseGraphState:
    # If guard escalated, override action to ESCALATE_TO_HUMAN
    if state.get("guard_result", {}).get("decision") == "ESCALATE":
        state["selected_action"] = "ESCALATE_TO_HUMAN"

    exec_res = await execution_agent.process(state)
    await audit_agent.log_step(
        case_id=state["case_id"],
        agent="Execution",
        decision=exec_res["final_status"].upper(),
        reason=f"Action '{exec_res['action']}' executed.",
        tool_called=exec_res["action"],
        result=exec_res["execution_result"]
    )
    return {
        **state,
        "execution_result": exec_res["execution_result"],
        "attempts": exec_res["attempts"],
        "final_status": exec_res["final_status"],
        "recovered_amount": exec_res["recovered_amount"]
    }

async def verify_node(state: CaseGraphState) -> CaseGraphState:
    """
    Section 7 Verify Node:
    Verifies execution outcome (recovered, delivered, escalated, or failed).
    """
    final_st = state.get("final_status", "unknown")
    attempts = state.get("attempts", 1)
    
    if final_st == "recovered":
        ver_st = "VERIFIED_RECOVERED"
        reason = f"Payment verified. Amount ₹{state.get('recovered_amount', 0.0)} recovered."
    elif final_st == "escalated":
        ver_st = "VERIFIED_ESCALATED"
        reason = "Case escalated to human team for manual resolution."
    elif final_st == "delivered":
        ver_st = "VERIFIED_DELIVERED"
        reason = "Communication intervention delivered successfully."
    else:
        ver_st = "VERIFICATION_FAILED"
        reason = f"Intervention attempt #{attempts} failed to recover revenue."

    await audit_agent.log_step(
        case_id=state["case_id"],
        agent="Verification",
        decision=ver_st,
        reason=reason
    )
    return {
        **state,
        "verification_status": ver_st
    }

async def audit_close_node(state: CaseGraphState) -> CaseGraphState:
    if state.get("guard_result", {}).get("decision") == "BLOCK":
        final_status = "blocked"
    else:
        final_status = state.get("final_status") or "closed"

    db = get_db()
    cases_col = db.get_collection("recovery_cases")
    await cases_col.update_one(
        {"case_id": state["case_id"]},
        {"$set": {"status": final_status, "updated_at": datetime.utcnow().isoformat()}}
    )
    await audit_agent.log_case_resolution({**state, "final_status": final_status})
    return {**state, "final_status": final_status}

# Conditional Router Functions
def route_guard_decision(state: CaseGraphState) -> str:
    decision = state.get("guard_result", {}).get("decision")
    if decision in ["ALLOW", "ESCALATE"]:
        return "execute"
    else:  # BLOCK
        return "audit_close"

def route_verify_decision(state: CaseGraphState) -> str:
    """
    Section 7 Conditional Edge:
    - verify fails + attempts < max_retries (3) -> back to decide (retry loop)
    - verify succeeds or max retries reached -> audit_close
    """
    ver_status = state.get("verification_status")
    attempts = state.get("attempts", 1)
    
    if ver_status == "VERIFICATION_FAILED" and attempts < 3:
        logger.info(f"[LangGraph Workflow] Verification failed (attempt #{attempts}). Re-routing to Strategy Agent...")
        return "decide"
    return "audit_close"

# Construct State Graph (Section 7)
workflow = StateGraph(CaseGraphState)
workflow.add_node("detect", detect_node)
workflow.add_node("diagnose", diagnose_node)
workflow.add_node("decide", decide_node)
workflow.add_node("guard", guard_node)
workflow.add_node("execute", execute_node)
workflow.add_node("verify", verify_node)
workflow.add_node("audit_close", audit_close_node)

workflow.set_entry_point("detect")
workflow.add_edge("detect", "diagnose")
workflow.add_edge("diagnose", "decide")
workflow.add_edge("decide", "guard")
workflow.add_conditional_edges(
    "guard",
    route_guard_decision,
    {
        "execute": "execute",
        "audit_close": "audit_close"
    }
)
workflow.add_edge("execute", "verify")
workflow.add_conditional_edges(
    "verify",
    route_verify_decision,
    {
        "decide": "decide",
        "audit_close": "audit_close"
    }
)
workflow.add_edge("audit_close", END)

app_graph = workflow.compile()

async def run_recovery_workflow(event_data: Dict[str, Any]) -> Dict[str, Any]:
    initial_state = {
        "event": event_data,
        "case_id": "",
        "customer_id": event_data.get("customer_id", ""),
        "diagnosis": {},
        "decision": {},
        "selected_action": "",
        "guard_result": {},
        "execution_result": {},
        "attempts": 0,
        "amount": float(event_data.get("amount", 0.0)),
        "event_type": event_data.get("event_type", "payment_failure"),
        "root_cause": "",
        "final_status": "detected",
        "recovered_amount": 0.0,
        "verification_status": "PENDING"
    }
    result = await app_graph.ainvoke(initial_state)
    return result
