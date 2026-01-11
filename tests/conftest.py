"""
Pytest Configuration and Fixtures for AI Investment Agent System

This module provides shared fixtures and configuration for all tests.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
import json

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'shared'))

# Import after path setup
from shared.config.settings import settings
from shared.db.models import Base
from shared.agents.base import AgentTask, AgentResult, TaskStatus, TaskPriority


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db_engine():
    """Create a test database engine."""
    test_db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres123@localhost:5432/investment_agents_test"
    )

    engine = create_async_engine(
        test_db_url,
        poolclass=NullPool,
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session."""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for testing without API calls."""
    mock = AsyncMock()
    mock.generate.return_value = (
        '{"analysis": "Test analysis result", "recommendations": ["Buy", "Hold"]}',
        100  # tokens used
    )
    return mock


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    mock = AsyncMock()
    mock.ping.return_value = True
    mock.publish.return_value = None
    mock.subscribe.return_value = None
    mock.get.return_value = None
    mock.set.return_value = True
    return mock


@pytest.fixture
def mock_fmp_client():
    """Mock FMP client for testing."""
    mock = AsyncMock()

    # Mock company profile
    mock_profile = MagicMock()
    mock_profile.company_name = "Apple Inc."
    mock_profile.sector = "Technology"
    mock_profile.industry = "Consumer Electronics"
    mock_profile.description = "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide."
    mock_profile.mkt_cap = 3000000000000
    mock_profile.full_time_employees = 164000
    mock_profile.ceo = "Tim Cook"
    mock.get_company_profile.return_value = mock_profile

    # Mock quote
    mock_quote = MagicMock()
    mock_quote.price = 185.50
    mock_quote.change_percentage = 1.5
    mock_quote.ytd = 25.0
    mock.get_quote.return_value = mock_quote

    # Mock income statement
    mock_income = MagicMock()
    mock_income.date = datetime(2024, 9, 30)
    mock_income.revenue = 391000000000
    mock_income.gross_profit = 170000000000
    mock_income.operating_income = 114000000000
    mock_income.net_income = 94000000000
    mock_income.eps = 6.15
    mock.get_income_statement.return_value = [mock_income]

    # Mock key metrics
    mock_metrics = MagicMock()
    mock_metrics.date = datetime(2024, 9, 30)
    mock_metrics.pe_ratio = 30.5
    mock_metrics.pb_ratio = 45.0
    mock_metrics.roe = 1.47
    mock_metrics.roic = 0.55
    mock_metrics.debt_to_equity = 1.87
    mock_metrics.free_cash_flow_per_share = 6.50
    mock.get_key_metrics.return_value = [mock_metrics]

    return mock


@pytest.fixture
def mock_polygon_client():
    """Mock Polygon client for testing."""
    mock = AsyncMock()

    mock.get_quote.return_value = {"close": 185.50, "volume": 50000000}
    mock.get_news.return_value = [
        MagicMock(title="Apple announces new product"),
        MagicMock(title="Apple beats earnings expectations")
    ]

    return mock


@pytest.fixture
def mock_sec_client():
    """Mock SEC client for testing."""
    mock = AsyncMock()
    mock.lookup_cik.return_value = "0000320193"
    mock.get_company_filings.return_value = []
    return mock


# =============================================================================
# Agent Task Fixtures
# =============================================================================

@pytest.fixture
def sample_task():
    """Create a sample agent task for testing."""
    return AgentTask(
        task_id="test-task-001",
        agent_type="due_diligence_agent",
        prompt_name="business_overview_report",
        input_data={"ticker": "AAPL"},
        priority=TaskPriority.NORMAL,
        status=TaskStatus.PENDING,
        metadata={"test": True}
    )


@pytest.fixture
def sample_thematic_task():
    """Create a thematic screening task."""
    return AgentTask(
        task_id="test-task-002",
        agent_type="idea_generation_agent",
        prompt_name="thematic_candidate_screen",
        input_data={
            "theme": "AI Infrastructure",
            "sector": "Technology",
            "min_market_cap": 10000000000
        },
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING
    )


@pytest.fixture
def sample_successful_result():
    """Create a sample successful agent result."""
    return AgentResult(
        task_id="test-task-001",
        agent_type="due_diligence_agent",
        success=True,
        data={
            "analysis": "Comprehensive business overview",
            "key_metrics": {"revenue": 391000000000, "profit_margin": 0.24},
            "recommendation": "Buy"
        },
        execution_time_seconds=5.5,
        tokens_used=1500,
        model_used="gpt-4"
    )


# =============================================================================
# API Client Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def api_gateway_client():
    """Create an async client for API Gateway testing."""
    from services.api_gateway.app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def auth_client():
    """Create an async client for Auth Service testing."""
    from services.auth_service.app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def mca_client():
    """Create an async client for Master Control Agent testing."""
    from services.master_control_agent.app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


# =============================================================================
# Authentication Fixtures
# =============================================================================

@pytest.fixture
def test_user_credentials():
    """Test user credentials."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }


@pytest.fixture
def test_jwt_token():
    """Generate a test JWT token."""
    import jwt
    from datetime import timedelta

    payload = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }

    return jwt.encode(payload, settings.auth.jwt_secret, algorithm="HS256")


@pytest.fixture
def auth_headers(test_jwt_token):
    """Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {test_jwt_token}"}


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_company_data():
    """Sample company data for testing."""
    return {
        "ticker": "AAPL",
        "profile": {
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "market_cap": 3000000000000,
            "employees": 164000,
            "ceo": "Tim Cook",
            "description": "Apple Inc. designs, manufactures, and markets smartphones."
        },
        "income_statements": [
            {
                "date": "2024-09-30",
                "revenue": 391000000000,
                "gross_profit": 170000000000,
                "operating_income": 114000000000,
                "net_income": 94000000000,
                "eps": 6.15
            }
        ],
        "key_metrics": [
            {
                "date": "2024-09-30",
                "pe_ratio": 30.5,
                "pb_ratio": 45.0,
                "roe": 1.47,
                "roic": 0.55,
                "debt_to_equity": 1.87
            }
        ],
        "current_price": 185.50
    }


@pytest.fixture
def sample_prompts():
    """Sample prompts for testing."""
    return [
        {
            "id": "prompt-001",
            "name": "business_overview_report",
            "category": "due_diligence",
            "description": "Generate comprehensive business overview",
            "template": "Analyze {{ticker}} business model...",
            "is_active": True
        },
        {
            "id": "prompt-002",
            "name": "thematic_candidate_screen",
            "category": "idea_generation",
            "description": "Screen for thematic investment candidates",
            "template": "Identify companies exposed to {{theme}}...",
            "is_active": True
        }
    ]


@pytest.fixture
def sample_research_project():
    """Sample research project for testing."""
    return {
        "id": "project-001",
        "name": "Apple Deep Dive",
        "ticker": "AAPL",
        "status": "screening",
        "user_id": "user-001",
        "thesis_summary": None,
        "bull_case": None,
        "bear_case": None,
        "key_catalysts": [],
        "key_risks": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }


# =============================================================================
# Test Configuration
# =============================================================================

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "WARNING"
    yield
    os.environ.pop("TESTING", None)


@pytest.fixture
def clean_environment(monkeypatch):
    """Provide a clean environment for testing."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")


# =============================================================================
# Performance Testing Fixtures
# =============================================================================

@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing."""
    return {
        "api_response_time_ms": 500,
        "agent_execution_time_s": 30,
        "database_query_time_ms": 100,
        "llm_response_time_s": 15,
        "concurrent_requests": 100,
        "throughput_rps": 50
    }


# =============================================================================
# Prompt Validation Fixtures
# =============================================================================

@pytest.fixture
def prompt_validation_schema():
    """Schema for validating prompt outputs."""
    return {
        "business_overview_report": {
            "required_fields": ["business_description", "market_position", "competitive_advantages"],
            "output_type": "json"
        },
        "thematic_candidate_screen": {
            "required_fields": ["theme_analysis", "candidates"],
            "output_type": "json"
        },
        "dcf_valuation": {
            "required_fields": ["revenue_projections", "valuation_output", "sensitivity_analysis"],
            "output_type": "json"
        }
    }
