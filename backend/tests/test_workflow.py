import pytest
from backend.app.graph.workflow import run_recovery_workflow

@pytest.mark.asyncio
async def test_full_recovery_workflow():
    event_payload = {
        "event_id": "TEST_EVT_001",
        "transaction_id": "TXN_TEST_001",
        "customer_id": "CUST_TEST_001",
        "event_type": "subscription_dunning",
        "amount": 4999.0,
        "failure_reason": "bank_decline"
    }

    result = await run_recovery_workflow(event_payload)
    assert result["case_id"] == "CASE_TEST_001"
    assert result["amount"] == 4999.0
    assert result["final_status"] in ["recovered", "escalated", "blocked", "executing"]

@pytest.mark.asyncio
async def test_workflow_blocked_by_guard():
    from backend.app.db.mongo import get_db
    db = get_db()
    cust_col = db.get_collection("customers")
    await cust_col.insert_one({"customer_id": "CUST_OPTED_OUT_001", "opt_out": True})

    event_payload = {
        "event_id": "TEST_EVT_OPT_001",
        "transaction_id": "TXN_OPT_001",
        "customer_id": "CUST_OPTED_OUT_001",
        "event_type": "subscription_dunning",
        "amount": 1999.0,
        "failure_reason": "card_expired"
    }

    result = await run_recovery_workflow(event_payload)
    assert result["final_status"] == "blocked"

    cases_col = db.get_collection("recovery_cases")
    case = await cases_col.find_one({"case_id": result["case_id"]})
    assert case["status"] == "blocked"

