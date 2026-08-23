import random
import logging
from typing import Dict, Any

logger = logging.getLogger("reviveai.tools.razorpay")

async def mock_retry_payment(case_id: str, amount: float, customer_id: str, attempt_number: int) -> Dict[str, Any]:
    """
    Simulates Razorpay Payment Retry endpoint.
    Deterministic behavior for test cases:
    - Attempt 1 on normal cards: 80% success
    - High attempts (>2) or known test case TXN_1003: simulated failure to test stopping rule auto-escalation
    """
    logger.info(f"[Tool: Razorpay Retry] Case {case_id}, Attempt {attempt_number}, Amount ₹{amount}")
    
    if "1003" in case_id:
        return {
            "status": "failed",
            "amount_recovered": 0.0,
            "provider_response": {
                "payment_id": f"pay_mock_fail_{attempt_number}",
                "error_code": "BAD_REQUEST_ERROR",
                "error_description": "Insufficient funds in account during retry attempt",
                "gateway_status": "declined"
            }
        }
        
    if random.random() < 0.8:
        return {
            "status": "success",
            "amount_recovered": amount,
            "provider_response": {
                "payment_id": f"pay_mock_success_{attempt_number}",
                "status": "captured",
                "amount": int(amount * 100),
                "currency": "INR",
                "method": "card"
            }
        }
    else:
        return {
            "status": "failed",
            "amount_recovered": 0.0,
            "provider_response": {
                "payment_id": f"pay_mock_decline_{attempt_number}",
                "error_code": "GATEWAY_TIMEOUT",
                "error_description": "Bank payment gateway timeout",
                "gateway_status": "failed"
            }
        }
