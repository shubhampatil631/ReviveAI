import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from backend.app.config import settings
from backend.app.db.mongo import get_db
from backend.app.models.schemas import ComplianceDecisionSchema

logger = logging.getLogger("reviveai.mcp_compliance")

class ComplianceGuardServer:
    """
    Model Context Protocol (MCP) Compliance Server
    Deterministic (non-LLM) rule enforcement engine.
    Ensures zero out-of-policy agent executions.
    """

    async def check_retry_allowed(self, case_id: str) -> Tuple[bool, str, str]:
        """
        Checks max retry limit and retry cooldown period.
        Returns: (allowed, decision, reason)
        """
        db = get_db()
        cases_col = db.get_collection("recovery_cases")
        case = await cases_col.find_one({"case_id": case_id})
        
        if not case:
            return True, "ALLOW", "Case not found, defaulting allow for initialization."
            
        attempts = case.get("attempts", 0)
        max_attempts = settings.MAX_RETRY_ATTEMPTS
        
        if attempts >= max_attempts:
            return False, "ESCALATE", f"Max retry limit reached ({attempts}/{max_attempts}). Auto-escalation triggered."

        last_action = case.get("last_action_at")
        if last_action:
            if isinstance(last_action, str):
                last_action = datetime.fromisoformat(last_action)
            cooldown_delta = timedelta(minutes=settings.RETRY_COOLDOWN_MINUTES)
            if datetime.utcnow() - last_action < cooldown_delta:
                mins_left = int((cooldown_delta - (datetime.utcnow() - last_action)).total_seconds() / 60)
                return False, "BLOCK", f"Retry cooldown active ({mins_left} mins remaining)."

        return True, "ALLOW", f"Retry attempt {attempts + 1} allowed (limit: {max_attempts})."

    async def check_contact_allowed(self, customer_id: str, case_id: str = "") -> Tuple[bool, str, str]:
        """
        Checks DND opt-out registry, contact message cooldown, and blackout hours.
        Returns: (allowed, decision, reason)
        """
        db = get_db()
        customers_col = db.get_collection("customers")
        cases_col = db.get_collection("recovery_cases")
        
        customer = await customers_col.find_one({"customer_id": customer_id})
        if customer and customer.get("opt_out"):
            return False, "BLOCK", "Customer has opted out of automated communications (DND Registry Hard Block)."

        # Blackout window check (22:00 to 08:00)
        current_hour = datetime.utcnow().hour
        if current_hour >= 22 or current_hour < 8:
            # Allow override in test/dev mode if configured
            if settings.ENV not in ["development", "test_override"]:
                return False, "BLOCK", "Compliance Blackout Window active (22:00 - 08:00). Contact postponed."

        if case_id:
            case = await cases_col.find_one({"case_id": case_id})
            if case and case.get("last_contact_at"):
                last_contact = case.get("last_contact_at")
                if isinstance(last_contact, str):
                    last_contact = datetime.fromisoformat(last_contact)
                cooldown_delta = timedelta(hours=settings.MESSAGE_COOLDOWN_HOURS)
                if datetime.utcnow() - last_contact < cooldown_delta:
                    hours_left = round((cooldown_delta - (datetime.utcnow() - last_contact)).total_seconds() / 3600, 1)
                    return False, "BLOCK", f"Contact message cooldown active ({hours_left} hours remaining)."

        return True, "ALLOW", "Customer contact permitted."

    async def check_escalation_tier(self, case_id: str) -> Dict[str, Any]:
        """
        Retrieves current escalation tier status.
        """
        db = get_db()
        cases_col = db.get_collection("recovery_cases")
        case = await cases_col.find_one({"case_id": case_id})
        current_tier = case.get("escalation_tier", 1) if case else 1
        return {
            "current_tier": current_tier,
            "max_tier": settings.MAX_ESCALATION_TIER,
            "can_escalate": current_tier < settings.MAX_ESCALATION_TIER
        }

    async def evaluate_action(self, case_id: str, customer_id: str, action: str) -> Dict[str, Any]:
        """
        Primary MCP tool entrypoint. Evaluates whether a proposed action is ALLOW, BLOCK, or ESCALATE.
        """
        rule_fired = "DEFAULT_POLICY"
        allowed = True
        decision = "ALLOW"
        reason = "Action meets all policy criteria."

        if action == "RETRY_PAYMENT":
            allowed, decision, reason = await self.check_retry_allowed(case_id)
            rule_fired = "RETRY_LIMIT_COOLDOWN_RULE"

        elif action in ["SEND_RECOVERY_MESSAGE", "SEND_PAYMENT_METHOD_UPDATE_REQUEST", "SEND_INVOICE_REMINDER"]:
            allowed, decision, reason = await self.check_contact_allowed(customer_id, case_id)
            rule_fired = "DND_OPT_OUT_MESSAGE_COOLDOWN_RULE"

        elif action == "ESCALATE_TO_HUMAN":
            tier_status = await self.check_escalation_tier(case_id)
            if not tier_status["can_escalate"]:
                allowed = False
                decision = "BLOCK"
                reason = f"Max escalation tier ({tier_status['max_tier']}) already reached."
                rule_fired = "MAX_ESCALATION_CAP_RULE"
            else:
                allowed = True
                decision = "ALLOW"
                reason = f"Escalation to Tier {tier_status['current_tier']} approved."
                rule_fired = "ESCALATION_APPROVED_RULE"

        elif action == "CLOSE_NO_ACTION":
            allowed = True
            decision = "ALLOW"
            reason = "Case closure without intervention approved."
            rule_fired = "CLOSE_NO_ACTION_RULE"

        # Log decision to audit system
        await self.log_compliance_decision(
            case_id=case_id,
            customer_id=customer_id,
            action_attempted=action,
            decision=decision,
            rule_fired=rule_fired,
            reason=reason
        )

        return {
            "allowed": allowed,
            "decision": decision,
            "rule_fired": rule_fired,
            "reason": reason
        }

    async def log_compliance_decision(self, case_id: str, customer_id: str, action_attempted: str, decision: str, rule_fired: str, reason: str):
        db = get_db()
        col = db.get_collection("compliance_decisions")
        record = ComplianceDecisionSchema(
            decision_id=f"DEC_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            case_id=case_id,
            customer_id=customer_id,
            action_attempted=action_attempted,
            decision=decision,
            rule_fired=rule_fired,
            reason=reason
        ).model_dump()
        await col.insert_one(record)

mcp_compliance_server = ComplianceGuardServer()
