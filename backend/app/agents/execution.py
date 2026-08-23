import logging
from datetime import datetime
from typing import Dict, Any, Tuple
from backend.app.db.mongo import get_db
from backend.app.tools.mock_razorpay import mock_retry_payment
from backend.app.tools.mock_messaging import mock_send_message
from backend.app.tools.mock_link import mock_generate_checkout_link
from backend.app.tools.mock_invoice import mock_send_invoice_reminder
from backend.app.tools.mock_escalation import mock_escalate_human
from backend.app.llm.router import llm_router
from backend.app.agents.prompts import EXECUTION_SYSTEM_PROMPT, EXECUTION_ROLE

logger = logging.getLogger("reviveai.agents.execution")


class IdempotencyGuard:
    """
    4.6.6 Idempotency Guard Submodule:
    Ensures the same action isn't executed twice for the same case_id + attempt_number.
    """
    @classmethod
    async def check_and_lock(cls, case_id: str, attempt_number: int, action: str) -> Tuple[bool, Dict[str, Any]]:
        db = get_db()
        audit_col = db.get_collection("audit_logs")
        existing = await audit_col.find_one({
            "case_id": case_id,
            "agent": "Execution",
            "tool_called": action,
            "result.attempt_number": attempt_number
        })

        if existing:
            logger.warning(f"[IdempotencyGuard] Duplicate execution attempt blocked for case '{case_id}' (Attempt #{attempt_number}, Action: '{action}')")
            return False, existing.get("result", {})

        return True, {}


class ExecutionAgent:
    """
    4.6 Execution Module (Execution Agent orchestrator)
    """
    def __init__(self):
        self.role = EXECUTION_ROLE
        self.system_prompt = EXECUTION_SYSTEM_PROMPT

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs complete 4.6 Execution pipeline across all 6 submodules:
        4.6.1 Payment Retry Tool | 4.6.2 Messaging Tool | 4.6.3 Link Generator Tool
        4.6.4 Invoice Reminder Tool | 4.6.5 Escalation Tool | 4.6.6 Idempotency Guard
        """
        case_id = state.get("case_id", "")
        action = state.get("selected_action", "RETRY_PAYMENT")
        customer_id = state.get("customer_id", "")
        amount = float(state.get("amount", 0.0))
        attempts = int(state.get("attempts", 0)) + 1

        logger.info(f"[{self.role}] Executing action '{action}' for case '{case_id}' (Attempt #{attempts})")

        # 4.6.6 Idempotency Guard Check
        is_fresh, cached_result = await IdempotencyGuard.check_and_lock(case_id, attempts, action)
        if not is_fresh:
            return {
                "case_id": case_id,
                "action": action,
                "result": cached_result.get("status", "already_executed"),
                "amount_recovered": cached_result.get("amount_recovered", 0.0),
                "recovered_amount": cached_result.get("amount_recovered", 0.0),
                "provider_response": cached_result,
                "execution_result": cached_result,
                "attempts": attempts,
                "final_status": "idempotent_duplicate"
            }

        db = get_db()
        cases_col = db.get_collection("recovery_cases")
        
        # Update case attempt counter & timestamp
        await cases_col.update_one(
            {"case_id": case_id},
            {"$set": {
                "attempts": attempts,
                "last_action_at": datetime.utcnow().isoformat(),
                "status": "executing"
            }}
        )

        result_status = "failed"
        amount_recovered = 0.0
        provider_response: Dict[str, Any] = {}

        # 4.6.1 Payment Retry Tool
        if action == "RETRY_PAYMENT":
            p_res = await mock_retry_payment(case_id, amount, customer_id, attempts)
            p_res["attempt_number"] = attempts
            provider_response = p_res
            result_status = p_res.get("status", "failed")
            amount_recovered = float(p_res.get("amount_recovered", 0.0))

        # 4.6.2 Messaging Tool (supports Email/SMS/WhatsApp + LLM Hinglish option)
        elif action in ["SEND_RECOVERY_MESSAGE", "SEND_PAYMENT_METHOD_UPDATE_REQUEST"]:
            cust_col = db.get_collection("customers")
            cust = await cust_col.find_one({"customer_id": customer_id}) or {}
            cust_name = cust.get("name", "Valued Customer")
            
            # Personalize copy using LLM (Gemini Pro -> Groq -> Ollama)
            prompt = (
                f"Generate a polite customer recovery message for WhatsApp/Email:\n"
                f"- Customer Name: {cust_name}\n"
                f"- Amount: INR {amount}\n"
                f"- Action: {action}\n"
                f"Provide concise 2-sentence copy in natural English or Hinglish."
            )
            personalized_copy = await llm_router.route_call("reasoning", prompt, self.system_prompt)
            
            p_res = await mock_send_message(
                customer_id=customer_id,
                customer_name=cust_name,
                message_type="whatsapp" if action == "SEND_RECOVERY_MESSAGE" else "email",
                template=action,
                content=personalized_copy or "",
                use_hinglish=True
            )
            p_res["attempt_number"] = attempts
            provider_response = p_res
            result_status = p_res.get("status", "delivered")
            amount_recovered = 0.0
            
            await cases_col.update_one(
                {"case_id": case_id},
                {"$set": {"last_contact_at": datetime.utcnow().isoformat()}}
            )

        # 4.6.3 Link Generator Tool
        elif action == "GENERATE_CHECKOUT_RECOVERY_LINK":
            p_res = await mock_generate_checkout_link(case_id, amount, customer_id)
            p_res["attempt_number"] = attempts
            provider_response = p_res
            result_status = "delivered" if p_res.get("status") == "success" else p_res.get("status", "delivered")
            amount_recovered = 0.0

        # 4.6.4 Invoice Reminder Tool
        elif action == "SEND_INVOICE_REMINDER":
            p_res = await mock_send_invoice_reminder(case_id, customer_id, amount)
            p_res["attempt_number"] = attempts
            provider_response = p_res
            result_status = p_res.get("status", "delivered")
            amount_recovered = 0.0

        # 4.6.5 Escalation Tool
        elif action == "ESCALATE_TO_HUMAN":
            reason = state.get("guard_result", {}).get("reason", "Manual or policy escalation required")
            p_res = await mock_escalate_human(case_id, customer_id, reason, amount)
            p_res["attempt_number"] = attempts
            provider_response = p_res
            result_status = "escalated"
            amount_recovered = 0.0

        # Close No Action
        elif action == "CLOSE_NO_ACTION":
            provider_response = {
                "status": "closed",
                "attempt_number": attempts,
                "note": "Case closed without action per strategy decision."
            }
            result_status = "closed"
            amount_recovered = 0.0

        # Determine final status for MongoDB
        final_status = "recovered" if result_status == "success" else (
            "delivered" if result_status == "delivered" else (
                "escalated" if action == "ESCALATE_TO_HUMAN" else (
                    "closed" if action == "CLOSE_NO_ACTION" else (
                        "blocked" if state.get("guard_result", {}).get("decision") == "BLOCK" else "executing"
                    )
                )
            )
        )

        await cases_col.update_one(
            {"case_id": case_id},
            {"$set": {
                "status": final_status,
                "recovered_amount": amount_recovered,
                "updated_at": datetime.utcnow().isoformat()
            }}
        )

        # Standard Section 4.6 output contract schema
        return {
            "case_id": case_id,
            "action": action,
            "result": result_status,
            "amount_recovered": amount_recovered,
            "recovered_amount": amount_recovered,
            "provider_response": provider_response,
            "attempts": attempts,
            "execution_result": provider_response,
            "final_status": final_status
        }


execution_agent = ExecutionAgent()
