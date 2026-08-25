import json
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from backend.app.db.mongo import get_db
from backend.app.models.schemas import RecoveryCaseSchema
from backend.app.llm.router import llm_router
from backend.app.agents.prompts import DETECTOR_SYSTEM_PROMPT, DETECTOR_ROLE

logger = logging.getLogger("reviveai.agents.detector")


class EventClassifier:
    """
    4.2.1 Event Classifier Submodule:
    Categorizes raw events into: payment_failure, checkout_abandonment, 
    subscription_dunning, overdue_invoice.
    Uses rule-based pre-filtering + 3-tier hybrid LLM failover (Groq -> Gemini Pro -> Ollama).
    """

    ALLOWED_EVENT_TYPES = [
        "payment_failure",
        "checkout_abandonment",
        "subscription_dunning",
        "overdue_invoice"
    ]

    KEYWORD_MAP = {
        "payment_failure": ["payment.failed", "card_declined", "bank_decline", "insufficient_funds", "gateway_error", "charge.failed"],
        "checkout_abandonment": ["cart_abandoned", "checkout.abandoned", "dropped_checkout", "abandoned_cart"],
        "subscription_dunning": ["subscription.halted", "mandate_expired", "recurring_failed", "subscription_failed", "dunning"],
        "overdue_invoice": ["invoice_overdue", "invoice.payment_failed", "net_terms_breached", "invoice_unpaid"]
    }

    @classmethod
    async def classify_event(cls, event_data: Dict[str, Any], system_prompt: str) -> str:
        given_type = str(event_data.get("event_type", "")).lower()
        if given_type in cls.ALLOWED_EVENT_TYPES:
            return given_type

        raw_reason = str(event_data.get("failure_reason", "")).lower()
        raw_source = str(event_data.get("source", "")).lower()
        raw_text = f"{given_type} {raw_reason} {raw_source} {json.dumps(event_data.get('raw_payload', {}))}".lower()

        # Rule-based pre-filtering
        for event_type, keywords in cls.KEYWORD_MAP.items():
            if any(kw in raw_text for kw in keywords):
                logger.info(f"[EventClassifier] Rule pre-filter matched '{event_type}'")
                return event_type

        # LLM failover call (Groq Llama-70b -> Gemini Pro -> Ollama)
        logger.info("[EventClassifier] Ambiguous event payload. Invoking LLM classification chain...")
        prompt = (
            f"Classify the following raw revenue loss event into strictly ONE category: "
            f"[payment_failure, checkout_abandonment, subscription_dunning, overdue_invoice].\n"
            f"Payload: {json.dumps(event_data)}\n"
            f"Return ONLY the exact category name."
        )
        llm_resp = await llm_router.route_call("classification", prompt, system_prompt)
        if llm_resp:
            cleaned = llm_resp.strip().lower()
            for allowed in cls.ALLOWED_EVENT_TYPES:
                if allowed in cleaned:
                    return allowed

        return "payment_failure"


class RiskScorer:
    """
    4.2.2 Risk Scorer Submodule:
    Computes risk_score (0-1), recovery_probability (0-1), and risk label (LOW, MEDIUM, HIGH)
    using transaction amount, customer history from MongoDB, payment method, and attempt history.
    """

    @classmethod
    async def compute_risk(
        cls,
        event_type: str,
        amount: float,
        customer_id: str,
        payment_method: str = "card"
    ) -> Tuple[float, float, str]:
        db = get_db()
        cust_col = db.get_collection("customers")
        cust = await cust_col.find_one({"customer_id": customer_id}) or {}

        history = cust.get("history", {})
        past_recoveries = int(history.get("past_recoveries", 0))
        past_failures = int(history.get("past_failures", 0))
        lifetime_value = float(history.get("lifetime_value", 0.0))
        opt_out = bool(cust.get("opt_out", False))

        # Base scoring
        risk_score = 0.35
        recovery_prob = 0.85

        # 1. Amount factor
        if amount > 20000:
            risk_score += 0.35
            recovery_prob -= 0.15
        elif amount > 5000:
            risk_score += 0.15
            recovery_prob -= 0.05
        elif amount < 1000:
            risk_score -= 0.10
            recovery_prob += 0.05

        # 2. Customer history factor
        if past_failures > 2:
            risk_score += 0.20
            recovery_prob -= 0.20
        if past_recoveries > 3:
            risk_score -= 0.15
            recovery_prob += 0.15
        if lifetime_value > 50000:
            risk_score -= 0.10
            recovery_prob += 0.10
        if opt_out:
            risk_score += 0.30
            recovery_prob -= 0.40

        # 3. Event type factor
        if event_type == "overdue_invoice":
            risk_score += 0.15
            recovery_prob -= 0.10
        elif event_type == "checkout_abandonment":
            risk_score -= 0.10
            recovery_prob += 0.10
        elif event_type == "subscription_dunning":
            risk_score += 0.05

        # 4. Payment method factor
        pm = payment_method.lower()
        if "mandate" in pm or "upi" in pm:
            recovery_prob += 0.05
        elif "expired" in pm:
            risk_score += 0.10

        # Clamp metrics to [0.05, 0.95]
        risk_score = min(max(round(risk_score, 2), 0.05), 0.95)
        recovery_prob = min(max(round(recovery_prob, 2), 0.05), 0.95)

        # Risk label thresholds
        if risk_score >= 0.70:
            risk_label = "HIGH"
        elif risk_score >= 0.40:
            risk_label = "MEDIUM"
        else:
            risk_label = "LOW"

        return risk_score, recovery_prob, risk_label


class CaseCreator:
    """
    4.2.3 Case Creator Submodule:
    Instantiates a RecoveryCase document in MongoDB with status 'detected'
    and outputs the exact Section 4.2 output contract.
    """

    @classmethod
    async def create_case(
        cls,
        txn_id: str,
        customer_id: str,
        event_type: str,
        amount: float,
        risk_label: str,
        risk_score: float,
        recovery_prob: float,
        reasoning_summary: str,
        raw_event: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        txn_str = str(txn_id or "TXN_INIT")
        case_id = f"CASE_{txn_str.replace('TXN_', '') if 'TXN_' in txn_str else txn_str}"
        raw_evt = raw_event or {}
        raw_pl = raw_evt.get("raw_payload", {}) if isinstance(raw_evt.get("raw_payload"), dict) else {}

        db = get_db()
        cases_col = db.get_collection("recovery_cases")
        existing = await cases_col.find_one({"case_id": case_id})

        cust_col = db.get_collection("customers")
        cust = await cust_col.find_one({"customer_id": customer_id}) or {}
        cust_name = raw_evt.get("customer_name") or raw_pl.get("customer_name") or cust.get("name") or "Valued Customer"
        cust_email = raw_evt.get("customer_email") or raw_pl.get("customer_email") or cust.get("email") or ""
        cust_phone = raw_evt.get("customer_phone") or raw_pl.get("customer_phone") or cust.get("phone") or ""

        if not cust and customer_id:
            cust_doc = {
                "customer_id": customer_id,
                "name": cust_name,
                "email": cust_email,
                "phone": cust_phone,
                "payment_methods": [raw_evt.get("payment_method", "card")],
                "opt_out": bool(raw_evt.get("opt_out", False)),
                "history": {
                    "past_recoveries": 0,
                    "past_failures": 1,
                    "lifetime_value": amount * 2
                }
            }
            await cust_col.insert_one(cust_doc)
        elif cust and cust_name != "Valued Customer" and cust.get("name") != cust_name:
            await cust_col.update_one({"customer_id": customer_id}, {"$set": {"name": cust_name, "email": cust_email, "phone": cust_phone}})

        if not existing:
            new_case = RecoveryCaseSchema(
                case_id=case_id,
                transaction_id=txn_str,
                customer_id=customer_id,
                customer_name=cust_name,
                customer_email=cust_email,
                event_type=event_type,
                amount=amount,
                risk_score=risk_score,
                recovery_probability=recovery_prob,
                reasoning_summary=reasoning_summary,
                status="detected"
            ).model_dump()
            await cases_col.insert_one(new_case)
            logger.info(f"[CaseCreator] Created MongoDB RecoveryCase document: '{case_id}'")
        else:
            if cust_name != "Valued Customer" and existing.get("customer_name") != cust_name:
                await cases_col.update_one({"case_id": case_id}, {"$set": {"customer_name": cust_name, "customer_email": cust_email}})

        # Output contract matching Section 4.2 specification
        return {
            "case_id": case_id,
            "customer_id": customer_id,
            "event_type": event_type,
            "amount": amount,
            "risk": risk_label,
            "risk_score": risk_score,
            "recovery_probability": recovery_prob,
            "reasoning_summary": reasoning_summary,
            "status": "detected"
        }


class DetectorAgent:
    """
    4.2 Detection Module (Detector Agent orchestrator)
    """
    def __init__(self):
        self.role = DETECTOR_ROLE
        self.system_prompt = DETECTOR_SYSTEM_PROMPT

    async def process(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs complete 4.2 Detection pipeline:
        4.2.1 Event Classifier -> 4.2.2 Risk Scorer -> 4.2.3 Case Creator
        """
        logger.info(f"[{self.role}] Processing event '{event_data.get('event_id')}'")

        # 4.2.1 Event Classifier
        event_type = await EventClassifier.classify_event(event_data, self.system_prompt)
        amount = float(event_data.get("amount", 0.0))
        customer_id = event_data.get("customer_id", "")
        txn_id = event_data.get("transaction_id", event_data.get("event_id", ""))
        payment_method = str(event_data.get("payment_method", "card"))

        # 4.2.2 Risk Scorer
        risk_score, recovery_prob, risk_label = await RiskScorer.compute_risk(
            event_type=event_type,
            amount=amount,
            customer_id=customer_id,
            payment_method=payment_method
        )

        # Generate reasoning summary via LLM or template
        prompt = (
            f"Provide a 1-sentence risk summary for the case record:\n"
            f"- Event ID: {event_data.get('event_id')}\n"
            f"- Event Type: {event_type}\n"
            f"- Amount: INR {amount}\n"
            f"- Risk: {risk_label} ({risk_score}), Recovery Prob: {recovery_prob}\n"
        )
        reasoning_summary = await llm_router.route_call("classification", prompt, self.system_prompt)
        if not reasoning_summary:
            reasoning_summary = f"Event classified as {event_type} with risk level {risk_label} ({risk_score}) and {recovery_prob * 100:.0f}% recovery probability."

        # 4.2.3 Case Creator
        result = await CaseCreator.create_case(
            txn_id=txn_id,
            customer_id=customer_id,
            event_type=event_type,
            amount=amount,
            risk_label=risk_label,
            risk_score=risk_score,
            recovery_prob=recovery_prob,
            reasoning_summary=reasoning_summary,
            raw_event=event_data
        )

        return result


detector_agent = DetectorAgent()
