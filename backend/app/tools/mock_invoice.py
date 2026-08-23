import logging
from typing import Dict, Any

logger = logging.getLogger("reviveai.tools.invoice")

async def mock_send_invoice_reminder(case_id: str, customer_id: str, amount: float) -> Dict[str, Any]:
    """
    Simulates generating and dispatching a B2B Overdue Invoice Reminder Document.
    """
    logger.info(f"[Tool: Invoice Reminder] Issued B2B reminder for case {case_id}, amount ₹{amount}")
    return {
        "status": "delivered",
        "document_type": "b2b_overdue_invoice_notice",
        "document_id": f"DOC_INV_{case_id[-4:]}",
        "recipient": customer_id,
        "amount_due": amount,
        "payment_commitment_link": f"https://reviveai.demo/invoice/pay/{case_id}",
        "sent_timestamp": "2026-08-21T22:00:00Z"
    }
