from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, cast

import pytest
from sqlalchemy.exc import SQLAlchemyError

from udocket_api.core import Base, database, settings
from udocket_api.core.database import check_db_health, get_db, init_db

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType

pytestmark = pytest.mark.integration


class _FakeConnection:
    """Minimal async context manager that mimics SQLAlchemy engine behavior."""

    def __init__(self, *, raise_on_execute: bool = False) -> None:
        self.raise_on_execute = raise_on_execute
        self.executed_statements: list[Any] = []
        self.run_sync_called = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        return False

    async def execute(self, statement: Any) -> None:  # noqa: ANN401 - symbolic SQLAlchemy API
        if self.raise_on_execute:
            msg = "connect failed"
            raise SQLAlchemyError(msg)
        self.executed_statements.append(statement)

    async def run_sync(self, func: Callable[[Any], Any]) -> None:
        self.run_sync_called = True
        func(self)


class _FakeBegin:
    """Async context manager used to override ``engine.begin``."""

    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    async def __aenter__(self) -> _FakeConnection:
        return self._connection

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        return False


class _FakeEngine:
    """Minimal engine wrapper to support monkeypatching core database engine."""

    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    def connect(self) -> _FakeConnection:
        return self._connection

    def begin(self) -> _FakeBegin:
        return _FakeBegin(self._connection)


class _FakeSession:
    """Trivial async session used to validate get_db behavior."""

    def __init__(self, *, in_transaction: bool = False) -> None:
        self._in_transaction = in_transaction
        self.commit_calls = 0
        self.rollback_calls = 0
        self.close_calls = 0

    async def commit(self) -> None:
        self.commit_calls += 1

    async def rollback(self) -> None:
        self.rollback_calls += 1
        self._in_transaction = False

    async def close(self) -> None:
        self.close_calls += 1

    def in_transaction(self) -> bool:
        return self._in_transaction


class _FakeSessionmaker:
    """AsyncSession factory stub that mimics SQLAlchemy's async_sessionmaker."""

    def __init__(self, session: _FakeSession) -> None:
        self._session = session

    def __call__(self) -> _FakeSessionContext:
        return _FakeSessionContext(self._session)


class _FakeSessionContext:
    """Context manager returned by ``_FakeSessionmaker``."""

    def __init__(self, session: _FakeSession) -> None:
        self._session = session

    async def __aenter__(self) -> _FakeSession:
        return self._session

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        return False


@pytest.mark.asyncio
async def test_check_db_health_returns_true_when_database_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    """check_db_health should return True when the engine can connect."""
    connection = _FakeConnection()
    monkeypatch.setattr(database, "engine", _FakeEngine(connection))

    assert await check_db_health() is True
    assert connection.executed_statements
    statement = connection.executed_statements[0]
    timeout = getattr(statement, "_execution_options", {}).get("timeout")
    assert timeout == settings.database_healthcheck_timeout


@pytest.mark.asyncio
async def test_check_db_health_returns_false_on_sqlalchemy_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """check_db_health should swallow SQLAlchemyError and return False."""
    connection = _FakeConnection(raise_on_execute=True)
    monkeypatch.setattr(database, "engine", _FakeEngine(connection))

    assert await check_db_health() is False


@pytest.mark.asyncio
async def test_init_db_creates_extension_and_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    """init_db should run the pgvector extension creation and metadata initialization."""
    connection = _FakeConnection()
    monkeypatch.setattr(database, "engine", _FakeEngine(connection))

    tables_created = False

    def fake_create_all(_: object) -> None:
        nonlocal tables_created
        tables_created = True

    monkeypatch.setattr(Base.metadata, "create_all", fake_create_all)

    await init_db()

    executed = [str(stmt) for stmt in connection.executed_statements]
    assert any("CREATE EXTENSION IF NOT EXISTS vector" in stmt for stmt in executed)
    assert tables_created
    assert connection.run_sync_called


@pytest.mark.asyncio
async def test_get_db_yields_session_without_committing(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_db should not commit automatically but must close the session."""
    session = _FakeSession(in_transaction=False)
    monkeypatch.setattr(database, "async_session_maker", _FakeSessionmaker(session))

    generator = get_db()
    yielded_session = await anext(generator)

    fake_session = cast("_FakeSession", yielded_session)
    assert fake_session is session
    await generator.aclose()

    assert session.commit_calls == 0
    assert session.rollback_calls == 0
    assert session.close_calls == 1


@pytest.mark.asyncio
async def test_get_db_rolls_back_on_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_db should roll back active transactions when downstream code fails."""
    session = _FakeSession(in_transaction=True)
    monkeypatch.setattr(database, "async_session_maker", _FakeSessionmaker(session))

    generator = get_db()
    await anext(generator)

    with pytest.raises(RuntimeError):
        await generator.athrow(RuntimeError("boom"))

    assert session.rollback_calls == 1
    assert session.close_calls == 1
