import pytest
import asyncio
from backend.app.mcp.compliance_server import mcp_compliance_server
from backend.app.db.mongo import get_db

@pytest.mark.asyncio
async def test_opt_out_dnd_rule():
    db = get_db()
    customers_col = db.get_collection("customers")
    await customers_col.insert_one({
        "customer_id": "TEST_CUST_DND",
        "opt_out": True
    })

    res = await mcp_compliance_server.evaluate_action(
        case_id="TEST_CASE_DND",
        customer_id="TEST_CUST_DND",
        action="SEND_RECOVERY_MESSAGE"
    )

    assert res["allowed"] is False
    assert res["decision"] == "BLOCK"
    assert "DND Registry" in res["reason"]

@pytest.mark.asyncio
async def test_max_retry_limit_rule():
    db = get_db()
    cases_col = db.get_collection("recovery_cases")
    await cases_col.insert_one({
        "case_id": "TEST_CASE_MAX_RETRY",
        "attempts": 3
    })

    res = await mcp_compliance_server.evaluate_action(
        case_id="TEST_CASE_MAX_RETRY",
        customer_id="TEST_CUST_1",
        action="RETRY_PAYMENT"
    )

    assert res["allowed"] is False
    assert res["decision"] == "ESCALATE"
    assert "Max retry limit reached" in res["reason"]

@pytest.mark.asyncio
async def test_check_retry_allowed_tool():
    allowed, decision, reason = await mcp_compliance_server.check_retry_allowed("TEST_CASE_INIT")
    assert allowed is True
    assert decision == "ALLOW"

@pytest.mark.asyncio
async def test_check_escalation_tier_tool():
    res = await mcp_compliance_server.check_escalation_tier("TEST_CASE_INIT")
    assert res["current_tier"] == 1
    assert res["max_tier"] == 3
    assert res["can_escalate"] is True
