import logging
from typing import Dict, Any

logger = logging.getLogger("reviveai.tools.escalation")

async def mock_escalate_human(case_id: str, customer_id: str, reason: str, amount: float) -> Dict[str, Any]:
    """
    Simulates creating a Zendesk / Jira / Internal Support Task for human escalation.
    """
    logger.info(f"[Tool: Escalation] Escalating case {case_id} to human account manager. Reason: {reason}")
    return {
        "status": "escalated",
        "ticket_id": f"TICKET_HUMAN_{case_id[-4:]}",
        "assigned_team": "High-Value Revenue Recovery Ops",
        "priority": "HIGH" if amount > 20000 else "MEDIUM",
        "notes": f"Automated recovery agent halted and escalated. Reason: {reason}"
    }
