from unittest.mock import AsyncMock

import pytest

from notification_service.infrastructure.adapters.output.persistence import database


class SessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_get_session_commits_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    session = AsyncMock()
    monkeypatch.setattr(database, "async_session_maker", lambda: SessionContext(session))

    generator = database.get_session()
    yielded_session = await anext(generator)
    assert yielded_session is session

    with pytest.raises(StopAsyncIteration):
        await anext(generator)

    session.commit.assert_awaited_once()
    session.rollback.assert_not_called()
    session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_rolls_back_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    session = AsyncMock()
    monkeypatch.setattr(database, "async_session_maker", lambda: SessionContext(session))

    generator = database.get_session()
    _ = await anext(generator)

    with pytest.raises(RuntimeError):
        await generator.athrow(RuntimeError("db error"))

    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_context_commits_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    session = AsyncMock()
    monkeypatch.setattr(database, "async_session_maker", lambda: SessionContext(session))

    async with database.get_session_context() as yielded_session:
        assert yielded_session is session

    session.commit.assert_awaited_once()
    session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_context_rolls_back_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    session = AsyncMock()
    monkeypatch.setattr(database, "async_session_maker", lambda: SessionContext(session))

    with pytest.raises(ValueError):
        async with database.get_session_context():
            raise ValueError("boom")

    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()
