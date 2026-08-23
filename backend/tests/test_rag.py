import pytest
from backend.app.rag.embeddings import rag_store
from backend.app.rag.retriever import retrieve_similar_cases, retrieve_relevant_policies

@pytest.mark.asyncio
async def test_rag_vector_store_and_fallback():
    rag_store.initialize()
    
    # Test adding resolved case
    rag_store.add_resolved_case({
        "case_id": "CASE_RAG_TEST_1",
        "event_type": "subscription_dunning",
        "root_cause": "bank_decline",
        "amount": 9999.0,
        "action": "RETRY_PAYMENT",
        "outcome": "recovered",
        "summary": "subscription_dunning caused by bank_decline, amount 9999, action RETRY_PAYMENT, outcome recovered"
    })

    # Test querying similar cases
    results = await retrieve_similar_cases("subscription_dunning", "bank_decline", 9999.0)
    assert len(results) >= 1
    assert any("subscription_dunning" in str(r) for r in results)

@pytest.mark.asyncio
async def test_rag_policy_retrieval():
    rag_store.add_policy_chunk({
        "id": "POL_TEST_1",
        "text": "Maximum retry limit per case is 3 attempts. Cooldown period is 30 minutes.",
        "policy_type": "retry_policy"
    })

    policies = await retrieve_relevant_policies("retry limit cooldown")
    assert len(policies) >= 1
    assert any("retry" in str(p).lower() for p in policies)
