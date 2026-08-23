import logging
from typing import Dict, Any

logger = logging.getLogger("reviveai.tools.messaging")

async def mock_send_message(
    customer_id: str,
    customer_name: str,
    message_type: str,  # email | sms | whatsapp
    template: str,
    content: str = "",
    use_hinglish: bool = False
) -> Dict[str, Any]:
    """
    Simulates notification delivery (SendGrid / Twilio / WhatsApp Business API).
    """
    logger.info(f"[Tool: Messaging] Sending {message_type.upper()} to {customer_name} ({customer_id}) using template '{template}'")

    if not content:
        if use_hinglish:
            content = f"Namaste {customer_name}! Aapka payment update Pending hai for transaction. Kripya niche diye link par click karke complete karein."
        else:
            content = f"Hello {customer_name}, your recent payment could not be processed. Please click the link to update your payment details and restore your account."

    return {
        "status": "delivered",
        "channel": message_type,
        "recipient": customer_id,
        "message_id": f"msg_mock_{message_type[:2]}_1009",
        "delivered_content": content,
        "delivery_timestamp": "2026-08-21T21:00:00Z"
    }
