import pytest
from backend.app.agents.detector import EventClassifier, RiskScorer, CaseCreator, detector_agent
from backend.app.agents.diagnosis import DiagnosisRuleEngine, CauseTaxonomy, ConfidenceScorer, diagnosis_agent
from backend.app.agents.strategy import ActionCatalog, DecisionMatrix, StrategyRAGRetriever, DecisionComposer, strategy_agent
from backend.app.agents.execution import IdempotencyGuard, execution_agent
from backend.app.agents.audit import AuditWriter, ExportService, CaseTimelineBuilder, audit_agent
from backend.app.tools.mock_link import mock_generate_checkout_link
from backend.app.agents.prompts import (
    DETECTOR_SYSTEM_PROMPT, 
    DIAGNOSIS_SYSTEM_PROMPT, 
    STRATEGY_SYSTEM_PROMPT, 
    EXECUTION_SYSTEM_PROMPT,
    AUDIT_SYSTEM_PROMPT
)

@pytest.mark.asyncio
async def test_agent_prompts_exist():
    assert "Detector Agent" in DETECTOR_SYSTEM_PROMPT
    assert "Diagnosis Agent" in DIAGNOSIS_SYSTEM_PROMPT
    assert "Strategy Agent" in STRATEGY_SYSTEM_PROMPT
    assert "Execution Agent" in EXECUTION_SYSTEM_PROMPT
    assert "Audit Agent" in AUDIT_SYSTEM_PROMPT

@pytest.mark.asyncio
async def test_event_classifier_submodule():
    evt1 = {"event_type": "subscription_dunning"}
    res1 = await EventClassifier.classify_event(evt1, DETECTOR_SYSTEM_PROMPT)
    assert res1 == "subscription_dunning"

    evt2 = {"failure_reason": "card_declined", "raw_payload": {}}
    res2 = await EventClassifier.classify_event(evt2, DETECTOR_SYSTEM_PROMPT)
    assert res2 == "payment_failure"

@pytest.mark.asyncio
async def test_risk_scorer_submodule():
    score, prob, label = await RiskScorer.compute_risk(
        event_type="overdue_invoice",
        amount=25000.0,
        customer_id="CUST_HIGH_RISK"
    )
    assert label == "HIGH"
    assert score >= 0.70
    assert prob < 0.80

@pytest.mark.asyncio
async def test_case_creator_submodule():
    result = await CaseCreator.create_case(
        txn_id="TXN_TEST_CC_1",
        customer_id="CUST_TEST_1",
        event_type="checkout_abandonment",
        amount=1999.0,
        risk_label="LOW",
        risk_score=0.25,
        recovery_prob=0.90,
        reasoning_summary="Low risk checkout abandonment."
    )
    assert result["case_id"] == "CASE_TEST_CC_1"
    assert result["risk"] == "LOW"
    assert result["amount"] == 1999.0
    assert result["status"] == "detected"

@pytest.mark.asyncio
async def test_diagnosis_rule_engine_submodule():
    cause1, conf1 = DiagnosisRuleEngine.evaluate_rules("bad_request_error", "payment_failure")
    assert cause1 == "insufficient_funds"
    assert conf1 >= 0.90

    cause2, conf2 = DiagnosisRuleEngine.evaluate_rules("card_expired", "payment_failure")
    assert cause2 == "expired_card"
    assert conf2 >= 0.90

@pytest.mark.asyncio
async def test_cause_taxonomy_submodule():
    c1 = CauseTaxonomy.normalize_cause("INSIGHT_INSUFFICIENT_FUNDS_ERR")
    assert c1 == "insufficient_funds"
    assert c1 in CauseTaxonomy.ALLOWED_TAXONOMY

@pytest.mark.asyncio
async def test_confidence_scorer_submodule():
    conf1, collab1 = ConfidenceScorer.score_confidence(0.95, is_rule_match=True)
    assert conf1 == 0.95
    assert collab1 is False

    conf2, collab2 = ConfidenceScorer.score_confidence(0.72, is_rule_match=False)
    assert conf2 == 0.72
    assert collab2 is True

@pytest.mark.asyncio
async def test_diagnosis_agent_full_process():
    state = {
        "case_id": "CASE_TEST_DIAG_1",
        "event": {
            "event_type": "payment_failure",
            "failure_reason": "gateway_error"
        }
    }
    res = await diagnosis_agent.process(state)
    assert res["case_id"] == "CASE_TEST_DIAG_1"
    assert res["root_cause"] == "gateway_timeout"
    assert res["confidence"] >= 0.90
    assert res["status"] == "diagnosed"

@pytest.mark.asyncio
async def test_action_catalog_submodule():
    act1 = ActionCatalog.validate_action("RETRY_PAYMENT")
    assert act1 == "RETRY_PAYMENT"
    act2 = ActionCatalog.validate_action("INVALID_CUSTOM_ACTION")
    assert act2 == "ESCALATE_TO_HUMAN"

@pytest.mark.asyncio
async def test_decision_matrix_submodule():
    act1, rat1 = DecisionMatrix.get_baseline_action("expired_card", attempts=0)
    assert act1 == "SEND_PAYMENT_METHOD_UPDATE_REQUEST"

    act2, rat2 = DecisionMatrix.get_baseline_action("expired_card", attempts=3)
    assert act2 == "ESCALATE_TO_HUMAN"

    act3, rat3 = DecisionMatrix.get_baseline_action("bank_decline", attempts=0, recovery_prob=0.10, amount=200.0)
    assert act3 == "CLOSE_NO_ACTION"

@pytest.mark.asyncio
async def test_strategy_agent_full_process():
    state = {
        "case_id": "CASE_TEST_STRAT",
        "event": {"amount": 5000.0, "event_type": "checkout_abandonment"},
        "diagnosis": {"root_cause": "cart_abandoned_shipping"}
    }
    result = await strategy_agent.process(state)
    assert result["selected_action"] in ActionCatalog.BOUNDED_ACTION_CATALOG
    assert result["selected_action"] == "GENERATE_CHECKOUT_RECOVERY_LINK"
    assert result["status"] == "decided"

@pytest.mark.asyncio
async def test_link_generator_tool():
    res = await mock_generate_checkout_link("CASE_LINK_1", 2499.0, "CUST_LINK_1")
    assert res["status"] == "success"
    assert "https://reviveai.demo/checkout/recover/CASE_LINK_1" in res["recovery_link"]

@pytest.mark.asyncio
async def test_execution_agent_process():
    state = {
        "case_id": "CASE_EXEC_TEST_1",
        "selected_action": "RETRY_PAYMENT",
        "customer_id": "CUST_EXEC_1",
        "amount": 4999.0,
        "attempts": 0
    }
    res = await execution_agent.process(state)
    assert res["case_id"] == "CASE_EXEC_TEST_1"
    assert res["action"] == "RETRY_PAYMENT"
    assert res["result"] in ["success", "failed"]
    assert "provider_response" in res

@pytest.mark.asyncio
async def test_audit_submodules():
    from backend.app.db.mongo import get_db
    db = get_db()
    cases_col = db.get_collection("recovery_cases")
    await cases_col.insert_one({
        "case_id": "CASE_AUDIT_TEST_1",
        "customer_id": "CUST_AUDIT_1",
        "event_type": "payment_failure",
        "amount": 1000.0,
        "status": "detected"
    })

    await AuditWriter.log_step(
        case_id="CASE_AUDIT_TEST_1",
        agent="Detector",
        decision="DETECTED",
        reason="Test detection entry"
    )
    
    csv_single = await ExportService.export_case_csv("CASE_AUDIT_TEST_1")
    assert "Timestamp,Case ID,Agent,Decision" in csv_single
    assert "CASE_AUDIT_TEST_1" in csv_single

    csv_batch = await ExportService.export_batch_csv("all")
    assert "Case ID,Customer ID,Event Type" in csv_batch

    timeline = await CaseTimelineBuilder.build_case_timeline("CASE_AUDIT_TEST_1")
    assert timeline["case"] is not None
    assert len(timeline["timeline"]) >= 1
