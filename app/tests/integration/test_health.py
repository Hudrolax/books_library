from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
