import pytest
import asyncio
from backend.app.ingestion.normalizer import EventNormalizer
from backend.app.ingestion.webhook_receiver import WebhookReceiver
from backend.app.ingestion.queue import EventQueue

def test_razorpay_event_normalizer():
    rzp_payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_rzp_123",
                    "amount": 499900,
                    "currency": "INR",
                    "customer_id": "cust_rzp_99",
                    "error_code": "BAD_REQUEST_ERROR"
                }
            }
        }
    }
    normalized = EventNormalizer.normalize(rzp_payload)
    assert normalized["source"] == "razorpay"
    assert normalized["amount"] == 4999.0
    assert normalized["event_type"] == "payment_failure"
    assert normalized["failure_reason"] == "insufficient_funds"
    assert normalized["transaction_id"] == "pay_test_rzp_123"

def test_stripe_event_normalizer():
    stripe_payload = {
        "type": "payment_intent.payment_failed",
        "data": {
            "object": {
                "id": "pi_stripe_test_456",
                "amount": 250000,
                "currency": "inr",
                "customer": "cus_stripe_11",
                "last_payment_error": {
                    "code": "CARD_EXPIRED"
                }
            }
        }
    }
    normalized = EventNormalizer.normalize(stripe_payload)
    assert normalized["source"] == "stripe"
    assert normalized["amount"] == 2500.0
    assert normalized["event_type"] == "payment_failure"
    assert normalized["failure_reason"] == "expired_card"
    assert normalized["transaction_id"] == "pi_stripe_test_456"

def test_csv_row_normalizer():
    csv_row = {
        "transaction_id": "TXN_CSV_789",
        "customer_id": "CUST_CSV_1",
        "event_type": "subscription_dunning",
        "amount": "1499.50",
        "failure_reason": "mandate_lapse"
    }
    normalized = EventNormalizer.normalize(csv_row, source="batch_csv")
    assert normalized["source"] == "batch_csv"
    assert normalized["amount"] == 1499.50
    assert normalized["event_type"] == "subscription_dunning"
    assert normalized["failure_reason"] == "mandate_lapse"

@pytest.mark.asyncio
async def test_event_queue():
    queue = EventQueue(maxsize=10)
    event = {
        "event_id": "EVT_TEST_Q",
        "transaction_id": "TXN_Q_1",
        "amount": 1000.0
    }
    success = await queue.enqueue(event)
    assert success is True
    status = queue.get_status()
    assert status["queue_size"] == 1
