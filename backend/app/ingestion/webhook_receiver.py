import logging
import hmac
import hashlib
from typing import Dict, Any, Tuple
from backend.app.ingestion.normalizer import EventNormalizer

logger = logging.getLogger("reviveai.ingestion.webhook_receiver")

class WebhookReceiver:
    """
    Webhook Receiver submodule (4.1.1) accepting Razorpay and Stripe-like 
    webhook payloads with HMAC signature verification support.
    """

    @staticmethod
    def verify_razorpay_signature(body_bytes: bytes, signature: str, secret: str) -> bool:
        if not signature or not secret:
            return True  # Sandbox mode / bypass if secret not configured
        try:
            expected = hmac.new(secret.encode('utf-8'), body_bytes, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.warning(f"Razorpay signature check failed: {e}")
            return False

    @staticmethod
    def verify_stripe_signature(body_bytes: bytes, signature_header: str, secret: str) -> bool:
        if not signature_header or not secret:
            return True  # Sandbox mode / bypass if secret not configured
        try:
            # Standard Stripe signature format: t=timestamp,v1=signature
            items = dict(item.split('=', 1) for item in signature_header.split(','))
            timestamp = items.get('t', '')
            v1_sig = items.get('v1', '')
            payload = f"{timestamp}.".encode('utf-8') + body_bytes
            expected = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, v1_sig)
        except Exception as e:
            logger.warning(f"Stripe signature check failed: {e}")
            return False

    @classmethod
    def process_webhook(cls, raw_payload: Dict[str, Any], provider: str = "auto") -> Dict[str, Any]:
        """
        Processes incoming webhook and returns normalized canonical event.
        """
        logger.info(f"[Webhook Receiver] Processing '{provider}' webhook payload...")
        normalized_event = EventNormalizer.normalize(raw_payload, source=provider)
        return normalized_event
