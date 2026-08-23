import logging
from typing import Dict, Any, List, Tuple
from backend.app.db.mongo import get_db
from backend.app.rag.retriever import retrieve_similar_cases, retrieve_relevant_policies
from backend.app.llm.router import llm_router
from backend.app.agents.prompts import STRATEGY_SYSTEM_PROMPT, STRATEGY_ROLE

logger = logging.getLogger("reviveai.agents.strategy")


class ActionCatalog:
    """
    4.4.1 Action Catalog & 4.4.2 Bounded Action Set Submodules:
    Fixed, immutable list of 7 allowed recovery interventions.
    """
    BOUNDED_ACTION_CATALOG = [
        "RETRY_PAYMENT",
        "SEND_PAYMENT_METHOD_UPDATE_REQUEST",
        "SEND_RECOVERY_MESSAGE",
        "GENERATE_CHECKOUT_RECOVERY_LINK",
        "SEND_INVOICE_REMINDER",
        "ESCALATE_TO_HUMAN",
        "CLOSE_NO_ACTION"
    ]

    @classmethod
    def validate_action(cls, action: str) -> str:
        act = str(action).strip().upper()
        if act in cls.BOUNDED_ACTION_CATALOG:
            return act
        logger.warning(f"[ActionCatalog] Un-mapped action '{action}' requested. Fallback to 'ESCALATE_TO_HUMAN'.")
        return "ESCALATE_TO_HUMAN"


class DecisionMatrix:
    """
    4.4.2 Baseline Decision Mapping Table:
    Maps root cause -> (Primary Action, Fallback Action).
    Evaluates retry attempt limits and low-probability pruning rules.
    """
    DECISION_TABLE = {
        "bank_decline": ("RETRY_PAYMENT", "SEND_RECOVERY_MESSAGE"),
        "gateway_timeout": ("RETRY_PAYMENT", "SEND_RECOVERY_MESSAGE"),
        "insufficient_funds": ("RETRY_PAYMENT", "SEND_RECOVERY_MESSAGE"),
        "expired_card": ("SEND_PAYMENT_METHOD_UPDATE_REQUEST", "ESCALATE_TO_HUMAN"),
        "mandate_lapse": ("SEND_PAYMENT_METHOD_UPDATE_REQUEST", "ESCALATE_TO_HUMAN"),
        "cart_abandoned_shipping": ("GENERATE_CHECKOUT_RECOVERY_LINK", "CLOSE_NO_ACTION"),
        "cart_abandoned_payment": ("GENERATE_CHECKOUT_RECOVERY_LINK", "CLOSE_NO_ACTION"),
        "invoice_terms_breach": ("SEND_INVOICE_REMINDER", "ESCALATE_TO_HUMAN"),
        "customer_churned": ("CLOSE_NO_ACTION", "ESCALATE_TO_HUMAN")
    }

    DEFAULT_RATIONALES = {
        "RETRY_PAYMENT": "Automated gateway payment retry scheduled.",
        "SEND_PAYMENT_METHOD_UPDATE_REQUEST": "Customer card or mandate expired; requesting payment method update.",
        "SEND_RECOVERY_MESSAGE": "Issuing customer recovery communication via Email/WhatsApp.",
        "GENERATE_CHECKOUT_RECOVERY_LINK": "Instant checkout recovery link generated with recovery incentive.",
        "SEND_INVOICE_REMINDER": "Overdue B2B invoice payment reminder issued.",
        "ESCALATE_TO_HUMAN": "Case escalated to human account manager for review.",
        "CLOSE_NO_ACTION": "Case closed without intervention per recovery policy."
    }

    @classmethod
    def get_baseline_action(
        cls,
        root_cause: str,
        attempts: int = 0,
        recovery_prob: float = 0.5,
        amount: float = 0.0
    ) -> Tuple[str, str]:
        # Low recovery probability + low amount pruning rule
        if recovery_prob < 0.15 and amount < 500:
            return "CLOSE_NO_ACTION", "Closed without action due to low recovery probability (<15%) and low amount."

        primary, fallback = cls.DECISION_TABLE.get(
            root_cause, 
            ("RETRY_PAYMENT", "ESCALATE_TO_HUMAN")
        )

        # High attempt threshold rule: switch to fallback
        if attempts >= 3:
            logger.info(f"[DecisionMatrix] Attempts ({attempts}) >= 3. Switching from primary '{primary}' to fallback '{fallback}'.")
            action = fallback
            rationale = f"Max retry limit reached ({attempts} attempts). Switched to fallback action '{fallback}'."
        else:
            action = primary
            rationale = cls.DEFAULT_RATIONALES.get(primary, f"Baseline intervention for '{root_cause}'.")

        return ActionCatalog.validate_action(action), rationale


class StrategyRAGRetriever:
    """
    4.4.3 RAG Retriever Submodule:
    Queries ChromaDB vector store for top-k similar past cases and relevant policies.
    """
    @classmethod
    async def retrieve_context(cls, event_type: str, root_cause: str, amount: float) -> Tuple[List[Dict[str, Any]], str]:
        try:
            similar_cases = await retrieve_similar_cases(event_type, root_cause, amount)
            policies = await retrieve_relevant_policies("retry_policy communication_policy escalation_policy")
            
            context_str = ""
            if similar_cases:
                past_action = similar_cases[0].get("metadata", {}).get("action", "")
                context_str = f"Found {len(similar_cases)} similar past cases in ChromaDB."
                if past_action:
                    context_str += f" Top historical outcome action: '{past_action}'."
            if policies:
                context_str += f" Retrieved {len(policies)} policy guidelines."
            
            return similar_cases, context_str
        except Exception as e:
            logger.warning(f"[StrategyRAGRetriever] RAG query exception: {e}")
            return [], ""


class DecisionComposer:
    """
    4.4.4 Decision Composer Submodule:
    Combines rule-based matrix + retrieved similar cases -> final bounded action + rationale.
    Uses Gemini Pro (with Groq & Ollama failover) to formulate grounded decision rationale.
    """
    @classmethod
    async def compose_decision(
        cls,
        case_id: str,
        event_type: str,
        root_cause: str,
        amount: float,
        base_action: str,
        base_rationale: str,
        rag_context_str: str,
        system_prompt: str
    ) -> Tuple[str, str]:
        prompt = (
            f"Formulate final intervention decision and 1-sentence rationale:\n"
            f"- Case ID: {case_id}\n"
            f"- Event Type: {event_type}\n"
            f"- Root Cause: {root_cause}\n"
            f"- Amount: INR {amount}\n"
            f"- Baseline Matrix Action: {base_action}\n"
            f"- RAG Context: {rag_context_str or 'None'}\n\n"
            f"Allowed Bounded Actions: {ActionCatalog.BOUNDED_ACTION_CATALOG}\n"
            f"Provide output format: ACTION: <allowed_action> | RATIONALE: <1_sentence_justification>"
        )

        resp = await llm_router.route_call("reasoning", prompt, system_prompt)
        if resp:
            try:
                if "ACTION:" in resp and "RATIONALE:" in resp:
                    parts = resp.split("RATIONALE:", 1)
                    act_part = parts[0].replace("ACTION:", "").strip().rstrip("|").strip()
                    rat_part = parts[1].strip()
                    validated_act = ActionCatalog.validate_action(act_part)
                    full_rationale = f"{rat_part} [RAG Grounded: {rag_context_str}]" if rag_context_str else rat_part
                    return validated_act, full_rationale
                else:
                    full_rationale = f"{resp.strip()} [RAG Grounded: {rag_context_str}]" if rag_context_str else resp.strip()
                    return base_action, full_rationale
            except Exception as e:
                logger.warning(f"[DecisionComposer] LLM response parse exception: {e}")

        final_rationale = f"{base_rationale} [RAG Grounded: {rag_context_str}]" if rag_context_str else base_rationale
        return base_action, final_rationale


class StrategyAgent:
    """
    4.4 Strategy / Decision Module (Strategy Agent orchestrator)
    """
    BOUNDED_ACTION_CATALOG = ActionCatalog.BOUNDED_ACTION_CATALOG

    def __init__(self):
        self.role = STRATEGY_ROLE
        self.system_prompt = STRATEGY_SYSTEM_PROMPT

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs complete 4.4 Strategy pipeline:
        4.4.1 Action Catalog & 4.4.2 Baseline Matrix -> 4.4.3 RAG Retriever -> 4.4.4 Decision Composer
        """
        case_id = state.get("case_id", "")
        event = state.get("event", {})
        diagnosis = state.get("diagnosis", {})
        root_cause = diagnosis.get("root_cause", "bank_decline")
        amount = float(event.get("amount", 0.0))
        event_type = event.get("event_type", "payment_failure")
        attempts = int(state.get("attempts", 0))
        recovery_prob = float(event.get("recovery_probability", 0.5))

        logger.info(f"[{self.role}] Deciding action for case '{case_id}' (Cause: {root_cause}, Attempts: {attempts})")

        # 4.4.1 & 4.4.2 Baseline Decision Matrix
        base_action, base_rationale = DecisionMatrix.get_baseline_action(
            root_cause=root_cause,
            attempts=attempts,
            recovery_prob=recovery_prob,
            amount=amount
        )

        # 4.4.3 RAG Retriever
        similar_cases, rag_context_str = await StrategyRAGRetriever.retrieve_context(event_type, root_cause, amount)

        # 4.4.4 Decision Composer (Gemini Pro -> Groq -> Ollama)
        selected_action, action_rationale = await DecisionComposer.compose_decision(
            case_id=case_id,
            event_type=event_type,
            root_cause=root_cause,
            amount=amount,
            base_action=base_action,
            base_rationale=base_rationale,
            rag_context_str=rag_context_str,
            system_prompt=self.system_prompt
        )

        # Final safety check against Bounded Action Catalog
        selected_action = ActionCatalog.validate_action(selected_action)

        # Update case in MongoDB
        db = get_db()
        cases_col = db.get_collection("recovery_cases")
        await cases_col.update_one(
            {"case_id": case_id},
            {"$set": {
                "selected_action": selected_action,
                "action_rationale": action_rationale,
                "status": "decided"
            }}
        )

        return {
            "case_id": case_id,
            "selected_action": selected_action,
            "action_rationale": action_rationale,
            "status": "decided"
        }


strategy_agent = StrategyAgent()
