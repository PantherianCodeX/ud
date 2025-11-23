from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

import pytest
from sqlalchemy.exc import SQLAlchemyError

from udocket_api.core import Base, database
from udocket_api.core.database import check_db_health, init_db

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType


pytestmark = pytest.mark.integration


class _FakeConnection:
    """Minimal async context manager that mimics SQLAlchemy engine behavior."""

    def __init__(self, *, raise_on_execute: bool = False) -> None:
        self.raise_on_execute = raise_on_execute
        self.executed_statements: list[str] = []
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
        self.executed_statements.append(str(statement))

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


@pytest.mark.asyncio
async def test_check_db_health_returns_true_when_database_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    """check_db_health should return True when the engine can connect."""
    connection = _FakeConnection()
    monkeypatch.setattr(database, "engine", _FakeEngine(connection))

    assert await check_db_health() is True
    assert connection.executed_statements


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

    assert "CREATE EXTENSION IF NOT EXISTS vector" in " ".join(connection.executed_statements)
    assert tables_created
    assert connection.run_sync_called
