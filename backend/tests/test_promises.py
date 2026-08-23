import pytest
from datetime import datetime, timedelta
from backend.app.db.mongo import get_db
from backend.app.routers.promises import (
    create_promise,
    mark_promise_paid,
    mark_promise_broken,
    deadline_watcher,
    list_promises
)

@pytest.mark.asyncio
async def test_promise_creation_and_listing():
    db = get_db()
    cases_col = db.get_collection("recovery_cases")
    await cases_col.insert_one({
        "case_id": "CASE_PROM_TEST_1",
        "customer_id": "CUST_PROM_1",
        "event_type": "overdue_invoice",
        "amount": 15000.0,
        "status": "detected"
    })

    res = await create_promise({
        "case_id": "CASE_PROM_TEST_1",
        "promised_amount": 15000.0,
        "days_due": 5
    })

    assert res["message"] == "Promise-to-Pay registered"
    p_doc = res["promise"]
    assert p_doc["status"] == "promised"
    assert p_doc["promised_amount"] == 15000.0

    listed = await list_promises("promised")
    assert listed["total"] >= 1
    assert any(p["promise_id"] == p_doc["promise_id"] for p in listed["promises"])

@pytest.mark.asyncio
async def test_mark_promise_paid_transition():
    db = get_db()
    cases_col = db.get_collection("recovery_cases")
    await cases_col.insert_one({
        "case_id": "CASE_PROM_TEST_2",
        "customer_id": "CUST_PROM_2",
        "event_type": "overdue_invoice",
        "amount": 8000.0,
        "status": "promised_to_pay"
    })

    res_create = await create_promise({
        "case_id": "CASE_PROM_TEST_2",
        "promised_amount": 8000.0,
        "days_due": 2
    })
    p_id = res_create["promise"]["promise_id"]

    res_paid = await mark_promise_paid(p_id)
    assert res_paid["status"] == "paid"

    db = get_db()
    cases_col = db.get_collection("recovery_cases")
    case = await cases_col.find_one({"case_id": "CASE_PROM_TEST_2"})
    assert case["status"] == "recovered"
    assert case["recovered_amount"] == 8000.0

@pytest.mark.asyncio
async def test_mark_promise_broken_requeue_transition():
    db = get_db()
    cases_col = db.get_collection("recovery_cases")
    await cases_col.insert_one({
        "case_id": "CASE_PROM_TEST_3",
        "customer_id": "CUST_PROM_3",
        "event_type": "overdue_invoice",
        "amount": 25000.0,
        "status": "promised_to_pay"
    })

    res_create = await create_promise({
        "case_id": "CASE_PROM_TEST_3",
        "promised_amount": 25000.0,
        "days_due": 1
    })
    p_id = res_create["promise"]["promise_id"]

    res_broken = await mark_promise_broken(p_id)
    assert res_broken["status"] == "broken"
    assert "requeue_result" in res_broken

@pytest.mark.asyncio
async def test_deadline_watcher_scan():
    db = get_db()
    promises_col = db.get_collection("promises")
    
    # Insert an overdue promise
    past_due = datetime.utcnow() - timedelta(days=2)
    await promises_col.insert_one({
        "promise_id": "PROM_OVERDUE_99",
        "case_id": "CASE_PROM_TEST_1",
        "promised_amount": 5000.0,
        "due_date": past_due,
        "status": "promised"
    })

    scan_res = await deadline_watcher()
    assert "Handled" in scan_res["message"]
    
    overdue_p = await promises_col.find_one({"promise_id": "PROM_OVERDUE_99"})
    assert overdue_p["status"] == "broken"

@pytest.mark.asyncio
async def test_multiple_promises_same_case():
    db = get_db()
    case_id = "CASE_MULTI_PROM_1"
    
    res1 = await create_promise({
        "case_id": case_id,
        "promised_amount": 5000.0,
        "days_due": 3
    })
    res2 = await create_promise({
        "case_id": case_id,
        "promised_amount": 10000.0,
        "days_due": 5
    })

    p1_id = res1["promise"]["promise_id"]
    p2_id = res2["promise"]["promise_id"]
    assert p1_id != p2_id

    promises_col = db.get_collection("promises")
    p1 = await promises_col.find_one({"promise_id": p1_id})
    p2 = await promises_col.find_one({"promise_id": p2_id})
    
    assert p1 is not None, "First promise should exist"
    assert p2 is not None, "Second promise should exist"
    assert p1["promised_amount"] == 5000.0
    assert p2["promised_amount"] == 10000.0

