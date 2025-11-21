# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from udocket_api.core import Base, get_db
from udocket_api.main import app
from udocket_api.platform.auth.jwt import UserStub, create_access_token
from udocket_api.workflow.analysis.api.router import get_analysis_service
from udocket_api.workflow.intake.api.router import get_intake_service
from udocket_api.workflow.matters.api.router import get_matters_service

# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine]:
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: Any) -> AsyncGenerator[AsyncSession]:  # noqa: ANN401 - pytest fixture type
    """Create test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client(db_session: AsyncSession) -> Generator[TestClient]:
    """Create test client with database override."""

    def override_get_db() -> Generator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_workflow_services() -> Generator[None]:
    """Ensure workflow services start from a clean slate per test."""
    intake_service = get_intake_service()
    matters_service = get_matters_service()
    analysis_service = get_analysis_service()

    intake_service.reset()
    matters_service.reset()
    analysis_service.reset()
    yield
    intake_service.reset()
    matters_service.reset()
    analysis_service.reset()


@pytest.fixture(autouse=True)
def patch_check_db_health(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid hitting a real database during tests."""

    async def _healthy() -> bool:
        await asyncio.sleep(0)
        return True

    monkeypatch.setattr("udocket_api.main.check_db_health", _healthy)


@pytest.fixture(autouse=True)
def patch_init_db(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent init_db from touching the real database."""

    async def _noop() -> None:
        await asyncio.sleep(0)

    monkeypatch.setattr("udocket_api.main.init_db", _noop)


@pytest.fixture
def test_user() -> UserStub:
    """Create test user stub."""
    return UserStub(
        id=uuid4(),
        email="test@example.com",
        full_name="Test User",
        roles=["user"],
        is_active=True,
    )


@pytest.fixture
def test_admin_user() -> UserStub:
    """Create test admin user stub."""
    return UserStub(
        id=uuid4(),
        email="admin@example.com",
        full_name="Admin User",
        roles=["user", "admin"],
        is_active=True,
    )


@pytest.fixture
def auth_headers(test_user: UserStub) -> dict[str, str]:
    """Create authentication headers with valid JWT."""
    token = create_access_token(test_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(test_admin_user: UserStub) -> dict[str, str]:
    """Create admin authentication headers with valid JWT."""
    token = create_access_token(test_admin_user)
    return {"Authorization": f"Bearer {token}"}
