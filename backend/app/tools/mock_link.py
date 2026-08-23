import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger("reviveai.tools.link")

async def mock_generate_checkout_link(case_id: str, amount: float, customer_id: str) -> Dict[str, Any]:
    """
    4.6.3 Link Generator Tool:
    Creates a mock personalized checkout-recovery URL with incentive token.
    """
    logger.info(f"[Tool: Link Generator] Creating checkout recovery link for case {case_id}, amount ₹{amount}")
    
    token = uuid.uuid4().hex[:12]
    expires_at = (datetime.utcnow() + timedelta(hours=48)).isoformat()
    link = f"https://reviveai.demo/checkout/recover/{case_id}?token={token}"

    return {
        "status": "success",
        "recovery_link": link,
        "token": token,
        "expires_at": expires_at,
        "incentive": "5% Instant Recovery Discount Applied",
        "generated_timestamp": datetime.utcnow().isoformat()
    }
