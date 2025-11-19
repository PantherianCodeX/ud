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
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core import Base, get_db
from src.main import app
from src.platform.auth.jwt import UserStub, create_access_token

# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine():
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
async def db_session(db_engine: Any) -> AsyncGenerator[AsyncSession, None]:  # noqa: ANN401 - pytest fixture type
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
def client(db_session: AsyncSession) -> Generator[TestClient, None, None]:
    """Create test client with database override."""

    def override_get_db() -> Generator[AsyncSession, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


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
