import logging
from typing import Dict, Any, Tuple, Optional
from backend.app.db.mongo import get_db
from backend.app.llm.router import llm_router
from backend.app.agents.prompts import DIAGNOSIS_SYSTEM_PROMPT, DIAGNOSIS_ROLE

logger = logging.getLogger("reviveai.agents.diagnosis")


class CauseTaxonomy:
    """
    4.3.3 Cause Taxonomy Submodule:
    Strictly enforced 9 primary root cause categories.
    """
    ALLOWED_TAXONOMY = [
        "insufficient_funds",
        "expired_card",
        "bank_decline",
        "gateway_timeout",
        "mandate_lapse",
        "cart_abandoned_shipping",
        "cart_abandoned_payment",
        "invoice_terms_breach",
        "customer_churned"
    ]

    @classmethod
    def normalize_cause(cls, cause: str) -> str:
        c = str(cause).strip().lower()
        if c in cls.ALLOWED_TAXONOMY:
            return c
        for allowed in cls.ALLOWED_TAXONOMY:
            if allowed in c:
                return allowed
        return "bank_decline"


class DiagnosisRuleEngine:
    """
    4.3.1 Rule Engine Submodule:
    Deterministic checks first (gateway decline codes, error descriptions) 
    before invoking LLM to save latency and API cost.
    """
    DECLINE_CODE_MAP = {
        "bad_request_error": "insufficient_funds",
        "insufficient_funds": "insufficient_funds",
        "card_expired": "expired_card",
        "expired_card": "expired_card",
        "gateway_error": "gateway_timeout",
        "gateway_timeout": "gateway_timeout",
        "mandate_expired": "mandate_lapse",
        "mandate_lapse": "mandate_lapse",
        "invoice_overdue": "invoice_terms_breach",
        "invoice_terms_breach": "invoice_terms_breach",
        "cart_abandoned_shipping": "cart_abandoned_shipping",
        "cart_abandoned_payment": "cart_abandoned_payment",
        "do_not_honor": "bank_decline",
        "stolen_card": "bank_decline",
        "bank_decline": "bank_decline",
        "customer_churned": "customer_churned"
    }

    @classmethod
    def evaluate_rules(cls, raw_reason: str, event_type: str) -> Tuple[Optional[str], float]:
        clean_reason = str(raw_reason).strip().lower()
        if clean_reason in cls.DECLINE_CODE_MAP:
            cause = cls.DECLINE_CODE_MAP[clean_reason]
            logger.info(f"[DiagnosisRuleEngine] Matched deterministic decline code '{clean_reason}' -> '{cause}'")
            return cause, 0.96

        # Check keyword inclusions
        for key, cause in cls.DECLINE_CODE_MAP.items():
            if key in clean_reason:
                logger.info(f"[DiagnosisRuleEngine] Keyword match '{key}' -> '{cause}'")
                return cause, 0.90

        # Event type fallback rules
        if event_type == "checkout_abandonment":
            return "cart_abandoned_shipping", 0.82
        elif event_type == "overdue_invoice":
            return "invoice_terms_breach", 0.85
        elif event_type == "subscription_dunning":
            return "expired_card", 0.80

        return None, 0.0


class ConfidenceScorer:
    """
    4.3.4 Confidence Scorer Submodule:
    Attaches a confidence value (0.0 to 1.0). Cases with confidence < 0.80 
    are flagged for collaborative reasoning context.
    """
    CONFIDENCE_THRESHOLD = 0.80

    @classmethod
    def score_confidence(cls, base_confidence: float, is_rule_match: bool) -> Tuple[float, bool]:
        conf = min(max(round(base_confidence, 2), 0.50), 0.99)
        requires_collaboration = conf < cls.CONFIDENCE_THRESHOLD
        return conf, requires_collaboration


class LLMReasoner:
    """
    4.3.2 LLM Reasoner Submodule:
    Calls Gemini Pro (with Groq Llama-70b & Ollama failover) for ambiguous payment failures,
    unstructured customer notes, or B2B net-terms nuances.
    """

    @classmethod
    async def reason_cause(
        cls,
        case_id: str,
        event_type: str,
        raw_reason: str,
        tentative_cause: str,
        system_prompt: str
    ) -> Tuple[str, float, str]:
        logger.info(f"[LLMReasoner] Invoking LLM reasoning chain (Gemini Pro -> Groq -> Ollama) for case '{case_id}'")
        
        prompt = (
            f"Analyze transaction failure and determine root cause:\n"
            f"- Case ID: {case_id}\n"
            f"- Event Type: {event_type}\n"
            f"- Raw Reason / Telemetry: {raw_reason}\n"
            f"- Tentative Mapped Cause: {tentative_cause}\n\n"
            f"Allowed Taxonomy: {CauseTaxonomy.ALLOWED_TAXONOMY}\n"
            f"Provide output in format: CAUSE: <one_taxonomy_item> | SUMMARY: <1_sentence_explanation>"
        )

        resp = await llm_router.route_call("reasoning", prompt, system_prompt)
        if resp:
            try:
                if "CAUSE:" in resp and "SUMMARY:" in resp:
                    parts = resp.split("SUMMARY:", 1)
                    cause_part = parts[0].replace("CAUSE:", "").strip().rstrip("|").strip()
                    summary_part = parts[1].strip()
                    matched_cause = CauseTaxonomy.normalize_cause(cause_part)
                    return matched_cause, 0.88, summary_part
                else:
                    matched_cause = CauseTaxonomy.normalize_cause(resp)
                    return matched_cause, 0.82, resp.strip()
            except Exception as e:
                logger.warning(f"[LLMReasoner] Parsing LLM response exception: {e}")

        default_summary = f"Transaction failure diagnosed as '{tentative_cause}' based on gateway error code '{raw_reason}'."
        return tentative_cause, 0.78, default_summary


class DiagnosisAgent:
    """
    4.3 Diagnosis Module (Root-Cause Agent orchestrator)
    """
    def __init__(self):
        self.role = DIAGNOSIS_ROLE
        self.system_prompt = DIAGNOSIS_SYSTEM_PROMPT

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        case_id = state.get("case_id", "")
        event = state.get("event", {})
        raw_reason = event.get("failure_reason", "")
        event_type = event.get("event_type", "payment_failure")

        logger.info(f"[{self.role}] Diagnosing root cause for case '{case_id}'")

        # 4.3.1 Rule Engine
        rule_cause, rule_conf = DiagnosisRuleEngine.evaluate_rules(raw_reason, event_type)

        if rule_cause and rule_conf >= 0.90:
            root_cause = rule_cause
            confidence = rule_conf
            reasoning_summary = f"Transaction failure classified as '{root_cause}' via deterministic gateway decline rule."
        else:
            tentative = rule_cause or "bank_decline"
            # 4.3.2 LLM Reasoner (Gemini Pro -> Groq -> Ollama)
            root_cause, confidence, reasoning_summary = await LLMReasoner.reason_cause(
                case_id=case_id,
                event_type=event_type,
                raw_reason=raw_reason,
                tentative_cause=tentative,
                system_prompt=self.system_prompt
            )

        # 4.3.3 Cause Taxonomy Validation
        root_cause = CauseTaxonomy.normalize_cause(root_cause)

        # 4.3.4 Confidence Scorer
        confidence, requires_collab = ConfidenceScorer.score_confidence(confidence, is_rule_match=bool(rule_cause))

        # Update case document in MongoDB
        db = get_db()
        cases_col = db.get_collection("recovery_cases")
        await cases_col.update_one(
            {"case_id": case_id},
            {"$set": {
                "root_cause": root_cause,
                "confidence": confidence,
                "reasoning_summary": reasoning_summary,
                "status": "diagnosed"
            }}
        )

        # Output contract matching Section 4.3 specification
        return {
            "case_id": case_id,
            "root_cause": root_cause,
            "confidence": confidence,
            "reasoning_summary": reasoning_summary,
            "requires_collaborative_reasoning": requires_collab,
            "status": "diagnosed"
        }


diagnosis_agent = DiagnosisAgent()
