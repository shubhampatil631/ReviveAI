import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Tuple

logger = logging.getLogger("reviveai.ingestion.normalizer")

class EventNormalizer:
    """
    Normalizes incoming revenue loss events from any source (Razorpay, Stripe, 
    Batch CSV, Checkout, Subscription, B2B Invoice, Generic APIs) into 
    the single canonical Event schema.
    """

    EVENT_TYPE_MAPPING = {
        "payment.failed": "payment_failure",
        "payment_intent.payment_failed": "payment_failure",
        "charge.failed": "payment_failure",
        "subscription.halted": "subscription_dunning",
        "invoice.payment_failed": "overdue_invoice",
        "checkout.abandoned": "checkout_abandonment",
        "order.abandoned": "checkout_abandonment",
        "cart_abandoned": "checkout_abandonment",
        "invoice_overdue": "overdue_invoice",
        "subscription_failed": "subscription_dunning"
    }

    REASON_MAPPING = {
        "BAD_REQUEST_ERROR": "insufficient_funds",
        "GATEWAY_ERROR": "gateway_timeout",
        "CARD_EXPIRED": "expired_card",
        "EXPIRED_CARD": "expired_card",
        "INSUFFICIENT_FUNDS": "insufficient_funds",
        "BANK_DECLINE": "bank_decline",
        "MANDATE_EXPIRED": "mandate_lapse",
        "do_not_honor": "bank_decline",
        "stolen_card": "bank_decline",
        "insufficient_funds_stripe": "insufficient_funds"
    }

    @classmethod
    def normalize(cls, raw_payload: Dict[str, Any], source: str = "auto") -> Dict[str, Any]:
        """
        Main entry point to normalize raw event payload.
        """
        source_type = cls._detect_source(raw_payload, source)
        logger.info(f"[Event Normalizer] Normalizing payload from source: '{source_type}'")

        if source_type == "razorpay":
            return cls._normalize_razorpay(raw_payload)
        elif source_type == "stripe":
            return cls._normalize_stripe(raw_payload)
        elif source_type == "batch_csv":
            return cls._normalize_csv_row(raw_payload)
        else:
            return cls._normalize_generic(raw_payload, source_type)

    @classmethod
    def _detect_source(cls, payload: Dict[str, Any], source_hint: str) -> str:
        if source_hint and source_hint != "auto":
            return source_hint.lower()
        if "entity" in payload or "razorpay_event" in payload or "payload" in payload:
            return "razorpay"
        if "object" in payload or ("type" in payload and "." in str(payload.get("type"))):
            return "stripe"
        if "transaction_id" in payload and "event_type" in payload:
            return "generic"
        return "generic"

    @classmethod
    def _normalize_razorpay(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        event_name = payload.get("event", "payment.failed")
        event_type = cls.EVENT_TYPE_MAPPING.get(event_name, "payment_failure")
        
        # Extract payment payload entity
        p_payload = payload.get("payload", {}).get("payment", {}).get("entity", payload)
        
        txn_id = p_payload.get("id", f"PAY_RZP_{uuid.uuid4().hex[:8]}")
        customer_id = p_payload.get("customer_id") or p_payload.get("email") or f"CUST_RZP_{uuid.uuid4().hex[:6]}"
        
        # Razorpay passes amounts in paise (1 INR = 100 paise)
        raw_amount = float(p_payload.get("amount", 0.0))
        amount = raw_amount / 100.0 if raw_amount > 1000 and p_payload.get("currency") == "INR" else raw_amount
        if amount == 0.0:
            amount = float(payload.get("amount", 2499.0))

        raw_reason = p_payload.get("error_code") or p_payload.get("error_description") or "bank_decline"
        failure_reason = cls.REASON_MAPPING.get(raw_reason, raw_reason)

        return {
            "event_id": f"EVT_{txn_id}",
            "transaction_id": txn_id,
            "source": "razorpay",
            "customer_id": customer_id,
            "amount": round(amount, 2),
            "currency": p_payload.get("currency", "INR"),
            "event_type": event_type,
            "failure_reason": failure_reason,
            "raw_payload": payload,
            "received_at": datetime.utcnow().isoformat()
        }

    @classmethod
    def _normalize_stripe(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        event_type_str = payload.get("type", "payment_intent.payment_failed")
        event_type = cls.EVENT_TYPE_MAPPING.get(event_type_str, "payment_failure")
        
        obj = payload.get("data", {}).get("object", payload)
        txn_id = obj.get("id", f"pi_stripe_{uuid.uuid4().hex[:8]}")
        customer_id = obj.get("customer") or obj.get("receipt_email") or f"CUST_STRIPE_{uuid.uuid4().hex[:6]}"
        
        raw_amount = float(obj.get("amount", 0.0))
        amount = raw_amount / 100.0 if raw_amount > 100 else raw_amount
        if amount == 0.0:
            amount = float(payload.get("amount", 3500.0))

        last_error = obj.get("last_payment_error", {})
        raw_reason = last_error.get("code") or last_error.get("decline_code") or "bank_decline"
        failure_reason = cls.REASON_MAPPING.get(raw_reason, raw_reason)

        return {
            "event_id": f"EVT_{txn_id}",
            "transaction_id": txn_id,
            "source": "stripe",
            "customer_id": customer_id,
            "amount": round(amount, 2),
            "currency": obj.get("currency", "INR").upper(),
            "event_type": event_type,
            "failure_reason": failure_reason,
            "raw_payload": payload,
            "received_at": datetime.utcnow().isoformat()
        }

    @classmethod
    def _normalize_csv_row(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        txn_id = row.get("transaction_id") or row.get("txn_id") or f"TXN_CSV_{uuid.uuid4().hex[:8]}"
        customer_id = row.get("customer_id") or row.get("user_id") or f"CUST_{uuid.uuid4().hex[:6]}"
        event_type = row.get("event_type", "payment_failure")
        amount = float(row.get("amount", 0.0))
        currency = row.get("currency", "INR")
        failure_reason = row.get("failure_reason") or row.get("decline_reason") or "bank_decline"

        return {
            "event_id": f"EVT_{txn_id}",
            "transaction_id": txn_id,
            "source": "batch_csv",
            "customer_id": customer_id,
            "amount": round(amount, 2),
            "currency": currency,
            "event_type": event_type,
            "failure_reason": failure_reason,
            "raw_payload": row,
            "received_at": datetime.utcnow().isoformat()
        }

    @classmethod
    def _normalize_generic(cls, payload: Dict[str, Any], source_type: str) -> Dict[str, Any]:
        txn_id = payload.get("transaction_id") or payload.get("event_id") or f"TXN_{uuid.uuid4().hex[:8]}"
        customer_id = payload.get("customer_id") or f"CUST_{uuid.uuid4().hex[:6]}"
        event_type = payload.get("event_type", "payment_failure")
        amount = float(payload.get("amount", 0.0))
        currency = payload.get("currency", "INR")
        failure_reason = payload.get("failure_reason", "bank_decline")

        return {
            "event_id": payload.get("event_id") or f"EVT_{txn_id}",
            "transaction_id": txn_id,
            "source": source_type or payload.get("source", "generic"),
            "customer_id": customer_id,
            "amount": round(amount, 2),
            "currency": currency,
            "event_type": event_type,
            "failure_reason": failure_reason,
            "raw_payload": payload,
            "received_at": datetime.utcnow().isoformat()
        }
