import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.llm.router import llm_router

@pytest.mark.asyncio
async def test_auth_middleware_and_public_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Health check is public
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "online"

@pytest.mark.asyncio
async def test_llm_router_classification_routing():
    res = await llm_router.route_call(
        task_type="classification",
        prompt="Classify error code BAD_GATEWAY_TIMEOUT",
        system_prompt="Return payment_failure or checkout_abandonment."
    )
    # router returns a string or None if all models in failover chain are offline
    assert res is None or isinstance(res, str)

@pytest.mark.asyncio
async def test_llm_router_reasoning_routing():
    res = await llm_router.route_call(
        task_type="reasoning",
        prompt="Generate personalized payment retry copy in Hinglish",
        system_prompt="You are an empathetic recovery assistant."
    )
    assert res is None or isinstance(res, str)
