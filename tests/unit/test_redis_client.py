from unittest.mock import AsyncMock

import pytest

from notification_service.infrastructure.adapters.output.cache import redis_client


@pytest.mark.asyncio
async def test_get_redis_reuses_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = AsyncMock()
    created = []

    def fake_from_url(url: str, decode_responses: bool):
        created.append((url, decode_responses))
        return fake_client

    redis_client._redis_client = None
    monkeypatch.setattr(redis_client, "from_url", fake_from_url)

    first = await redis_client.get_redis()
    second = await redis_client.get_redis()

    assert first is fake_client
    assert second is fake_client
    assert len(created) == 1


@pytest.mark.asyncio
async def test_close_redis_closes_and_resets_singleton() -> None:
    fake_client = AsyncMock()
    redis_client._redis_client = fake_client

    await redis_client.close_redis()

    fake_client.close.assert_awaited_once()
    assert redis_client._redis_client is None
