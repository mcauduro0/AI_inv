# AI Investment Agent System - Technical Improvement Plan

## Executive Summary

This document provides a detailed, actionable technical plan to transform the current AI Investment Agent System into a state-of-the-art systematic investment platform. Based on the comprehensive system review, this plan addresses critical gaps and outlines implementation steps for achieving institutional-grade capabilities.

---

## Table of Contents

1. [Phase 1: Foundation & Testing](#phase-1-foundation--testing)
2. [Phase 2: Knowledge Base & RAG](#phase-2-knowledge-base--rag)
3. [Phase 3: Quantitative Models](#phase-3-quantitative-models)
4. [Phase 4: Real-time Data & Monitoring](#phase-4-real-time-data--monitoring)
5. [Phase 5: Advanced Agent Capabilities](#phase-5-advanced-agent-capabilities)
6. [Phase 6: Production Hardening](#phase-6-production-hardening)
7. [Implementation Priorities](#implementation-priorities)

---

## Phase 1: Foundation & Testing

### 1.1 Complete Testing Infrastructure

**Objective:** Achieve 80%+ test coverage across all services

#### Tasks

```yaml
1.1.1 Configure pytest for all services:
  files:
    - services/shared/pytest.ini
    - services/api-gateway/pytest.ini
    - services/master-control-agent/pytest.ini
  actions:
    - Add pytest-asyncio configuration
    - Configure coverage thresholds
    - Set up test markers (unit, integration, e2e)

1.1.2 Create shared test fixtures:
  file: tests/conftest.py
  fixtures:
    - mock_llm_provider: Mock LLM responses
    - mock_data_service: Mock market data
    - test_database: In-memory PostgreSQL
    - redis_mock: Mock Redis pub/sub
    - authenticated_client: Pre-authenticated HTTP client

1.1.3 Implement CI/CD pipeline:
  file: .github/workflows/test.yml
  stages:
    - lint: ruff, mypy, black
    - unit_tests: pytest -m unit
    - integration_tests: pytest -m integration
    - coverage_report: codecov upload
    - security_scan: bandit, safety
```

#### Implementation Code

```python
# tests/conftest.py - Core fixtures
import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def mock_llm():
    """Mock LLM provider for testing."""
    mock = AsyncMock()
    mock.generate.return_value = ('{"analysis": "test"}', 100)
    return mock

@pytest.fixture
async def test_db():
    """Create test database session."""
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost/test_db",
        echo=False
    )
    async with AsyncSession(engine) as session:
        yield session

@pytest.fixture
async def api_client(test_db, mock_llm):
    """Create authenticated API test client."""
    from services.api_gateway.app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Authenticate
        response = await client.post("/api/auth/login", json={
            "email": "test@test.com",
            "password": "testpass"
        })
        token = response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        yield client
```

### 1.2 GitHub Actions CI/CD

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install ruff mypy black
      - name: Run linters
        run: |
          ruff check services/
          black --check services/
          mypy services/ --ignore-missing-imports

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r tests/requirements-test.txt
          pip install -r services/shared/requirements.txt
      - name: Run tests
        run: |
          pytest tests/ -v --cov=services --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run security scan
        run: |
          pip install bandit safety
          bandit -r services/ -ll
          safety check
```

---

## Phase 2: Knowledge Base & RAG

### 2.1 Qdrant Vector Database Integration

**Objective:** Enable semantic search and retrieval-augmented generation

#### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Research       │────▶│  Embedding      │────▶│    Qdrant       │
│  Documents      │     │  Pipeline       │     │  Vector Store   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
┌─────────────────┐     ┌─────────────────┐            │
│  Agent Query    │────▶│  RAG Pipeline   │◀───────────┘
└─────────────────┘     └─────────────────┘
                               │
                        ┌──────▼──────┐
                        │ LLM with    │
                        │ Context     │
                        └─────────────┘
```

#### Implementation

```python
# services/shared/clients/qdrant_client.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import openai
from typing import List, Dict, Any
import hashlib

class VectorStore:
    """Qdrant-based vector store for research documents."""

    COLLECTION_NAME = "investment_research"
    EMBEDDING_DIM = 1536  # OpenAI ada-002

    def __init__(self, host: str = "qdrant", port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if not exists."""
        collections = self.client.get_collections().collections
        if self.COLLECTION_NAME not in [c.name for c in collections]:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        response = await openai.Embedding.acreate(
            model="text-embedding-ada-002",
            input=text
        )
        return response["data"][0]["embedding"]

    async def store_document(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Store document with embedding."""
        doc_id = hashlib.md5(content.encode()).hexdigest()
        embedding = await self.generate_embedding(content)

        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[
                PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload={
                        "content": content,
                        **metadata
                    }
                )
            ]
        )
        return doc_id

    async def search(
        self,
        query: str,
        limit: int = 5,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Semantic search for relevant documents."""
        query_embedding = await self.generate_embedding(query)

        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_embedding,
            limit=limit,
            query_filter=filters
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "content": hit.payload["content"],
                "metadata": {k: v for k, v in hit.payload.items() if k != "content"}
            }
            for hit in results
        ]


# RAG Pipeline
class RAGPipeline:
    """Retrieval-Augmented Generation pipeline."""

    def __init__(self, vector_store: VectorStore, llm_provider):
        self.vector_store = vector_store
        self.llm = llm_provider

    async def generate_with_context(
        self,
        query: str,
        prompt_template: str,
        ticker: str = None,
        max_context_docs: int = 5
    ) -> str:
        """Generate response with retrieved context."""

        # Build search filters
        filters = {}
        if ticker:
            filters["ticker"] = ticker

        # Retrieve relevant documents
        relevant_docs = await self.vector_store.search(
            query=query,
            limit=max_context_docs,
            filters=filters
        )

        # Build context string
        context = "\n\n---\n\n".join([
            f"[Source: {doc['metadata'].get('source', 'Unknown')}]\n{doc['content']}"
            for doc in relevant_docs
        ])

        # Render prompt with context
        prompt = prompt_template.format(
            query=query,
            context=context,
            ticker=ticker or ""
        )

        # Generate response
        response, tokens = await self.llm.generate(prompt)

        return {
            "response": response,
            "sources": [doc["metadata"] for doc in relevant_docs],
            "tokens_used": tokens
        }
```

### 2.2 Document Ingestion Pipeline

```python
# services/shared/pipelines/document_ingestion.py
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import asyncio

@dataclass
class Document:
    content: str
    source_type: str  # sec_filing, earnings_call, research_note, news
    ticker: str
    date: datetime
    metadata: dict

class DocumentIngestionPipeline:
    """Pipeline for ingesting and indexing research documents."""

    def __init__(self, vector_store, sec_client, fmp_client):
        self.vector_store = vector_store
        self.sec = sec_client
        self.fmp = fmp_client

    async def ingest_sec_filings(
        self,
        ticker: str,
        filing_types: List[str] = ["10-K", "10-Q", "8-K"]
    ) -> int:
        """Ingest SEC filings for a ticker."""
        ingested = 0

        for filing_type in filing_types:
            filings = await self.sec.get_filings(ticker, filing_type, limit=5)

            for filing in filings:
                # Extract text content
                content = await self.sec.get_filing_text(filing.url)

                # Chunk large documents
                chunks = self._chunk_document(content, max_tokens=1000)

                for i, chunk in enumerate(chunks):
                    await self.vector_store.store_document(
                        content=chunk,
                        metadata={
                            "ticker": ticker,
                            "source_type": "sec_filing",
                            "filing_type": filing_type,
                            "filing_date": str(filing.date),
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        }
                    )
                    ingested += 1

        return ingested

    async def ingest_earnings_calls(self, ticker: str, quarters: int = 4) -> int:
        """Ingest earnings call transcripts."""
        transcripts = await self.fmp.get_earnings_transcripts(ticker, limit=quarters)
        ingested = 0

        for transcript in transcripts:
            chunks = self._chunk_document(transcript.content, max_tokens=1000)

            for i, chunk in enumerate(chunks):
                await self.vector_store.store_document(
                    content=chunk,
                    metadata={
                        "ticker": ticker,
                        "source_type": "earnings_call",
                        "quarter": transcript.quarter,
                        "year": transcript.year,
                        "chunk_index": i
                    }
                )
                ingested += 1

        return ingested

    def _chunk_document(self, text: str, max_tokens: int = 1000) -> List[str]:
        """Split document into chunks."""
        # Simple sentence-based chunking
        sentences = text.split(". ")
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_tokens = len(sentence.split())

            if current_length + sentence_tokens > max_tokens:
                chunks.append(". ".join(current_chunk) + ".")
                current_chunk = [sentence]
                current_length = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_length += sentence_tokens

        if current_chunk:
            chunks.append(". ".join(current_chunk))

        return chunks
```

---

## Phase 3: Quantitative Models

### 3.1 Factor Model Implementation

**Objective:** Add quantitative factor analysis to complement LLM insights

```python
# services/shared/quant/factor_models.py
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class FactorExposure:
    """Factor exposure for a security."""
    ticker: str
    market_beta: float
    size_factor: float  # SMB
    value_factor: float  # HML
    momentum_factor: float  # MOM
    quality_factor: float
    volatility_factor: float
    r_squared: float

class FamaFrenchModel:
    """Fama-French factor model implementation."""

    def __init__(self, data_client):
        self.data = data_client

    async def calculate_factor_exposures(
        self,
        ticker: str,
        lookback_days: int = 252
    ) -> FactorExposure:
        """Calculate factor exposures for a ticker."""

        # Fetch price data
        prices = await self.data.get_daily_prices(ticker, days=lookback_days)
        returns = prices.pct_change().dropna()

        # Fetch factor returns (from Kenneth French data library)
        factors = await self._get_factor_returns(lookback_days)

        # Align data
        aligned = pd.concat([returns, factors], axis=1).dropna()

        # Run regression
        X = aligned[['Mkt-RF', 'SMB', 'HML', 'Mom']].values
        X = np.column_stack([np.ones(len(X)), X])  # Add intercept
        y = aligned[ticker].values - aligned['RF'].values  # Excess returns

        # OLS regression
        beta, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)

        # Calculate R-squared
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot)

        return FactorExposure(
            ticker=ticker,
            market_beta=beta[1],
            size_factor=beta[2],
            value_factor=beta[3],
            momentum_factor=beta[4],
            quality_factor=await self._calculate_quality_score(ticker),
            volatility_factor=np.std(returns) * np.sqrt(252),
            r_squared=r_squared
        )

    async def _calculate_quality_score(self, ticker: str) -> float:
        """Calculate quality factor score."""
        financials = await self.data.get_financials(ticker)

        # Quality metrics
        roe = financials.get('roe', 0)
        debt_equity = financials.get('debt_to_equity', 1)
        earnings_stability = financials.get('earnings_variability', 1)

        # Normalize and combine
        quality = (
            0.4 * min(roe / 0.20, 1.0) +  # ROE contribution
            0.3 * max(1 - debt_equity / 2, 0) +  # Low leverage
            0.3 * max(1 - earnings_stability, 0)  # Stable earnings
        )

        return quality


class RiskModel:
    """Portfolio risk model."""

    async def calculate_var(
        self,
        positions: Dict[str, float],
        confidence: float = 0.95,
        horizon_days: int = 1
    ) -> Dict[str, float]:
        """Calculate Value at Risk."""

        # Get returns for all positions
        returns_data = {}
        for ticker, weight in positions.items():
            prices = await self.data.get_daily_prices(ticker, days=252)
            returns_data[ticker] = prices.pct_change().dropna()

        returns_df = pd.DataFrame(returns_data)
        weights = np.array(list(positions.values()))

        # Portfolio returns
        portfolio_returns = returns_df.dot(weights)

        # Historical VaR
        var_historical = np.percentile(portfolio_returns, (1 - confidence) * 100)

        # Parametric VaR (assuming normal distribution)
        mu = portfolio_returns.mean()
        sigma = portfolio_returns.std()
        var_parametric = mu - sigma * stats.norm.ppf(confidence)

        # Scale to horizon
        var_historical *= np.sqrt(horizon_days)
        var_parametric *= np.sqrt(horizon_days)

        return {
            "var_historical": abs(var_historical),
            "var_parametric": abs(var_parametric),
            "expected_shortfall": abs(portfolio_returns[portfolio_returns < var_historical].mean()),
            "confidence": confidence,
            "horizon_days": horizon_days
        }
```

### 3.2 Portfolio Optimization

```python
# services/shared/quant/portfolio_optimization.py
import numpy as np
from scipy.optimize import minimize
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class OptimizationResult:
    weights: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float

class PortfolioOptimizer:
    """Mean-variance and Black-Litterman portfolio optimization."""

    def __init__(self, data_client):
        self.data = data_client

    async def optimize_mean_variance(
        self,
        tickers: List[str],
        target_return: Optional[float] = None,
        risk_free_rate: float = 0.05,
        constraints: Dict = None
    ) -> OptimizationResult:
        """Mean-variance optimization."""

        # Get historical returns
        returns_data = {}
        for ticker in tickers:
            prices = await self.data.get_daily_prices(ticker, days=252)
            returns_data[ticker] = prices.pct_change().dropna()

        returns_df = pd.DataFrame(returns_data)

        # Calculate expected returns and covariance
        mu = returns_df.mean() * 252  # Annualized
        cov = returns_df.cov() * 252  # Annualized

        n = len(tickers)

        # Objective: minimize variance
        def portfolio_variance(weights):
            return weights @ cov @ weights

        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # Weights sum to 1
        ]

        if target_return:
            constraints_list.append({
                'type': 'eq',
                'fun': lambda w: w @ mu - target_return
            })

        # Bounds (default: long-only, max 20% per position)
        max_weight = constraints.get('max_weight', 0.20) if constraints else 0.20
        bounds = [(0, max_weight) for _ in range(n)]

        # Initial guess: equal weight
        x0 = np.ones(n) / n

        # Optimize
        result = minimize(
            portfolio_variance,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list
        )

        optimal_weights = result.x
        port_return = optimal_weights @ mu
        port_vol = np.sqrt(portfolio_variance(optimal_weights))
        sharpe = (port_return - risk_free_rate) / port_vol

        return OptimizationResult(
            weights={t: w for t, w in zip(tickers, optimal_weights)},
            expected_return=port_return,
            volatility=port_vol,
            sharpe_ratio=sharpe,
            max_drawdown=await self._calculate_max_drawdown(returns_df, optimal_weights)
        )

    async def black_litterman(
        self,
        tickers: List[str],
        views: Dict[str, float],  # ticker -> expected excess return
        view_confidence: Dict[str, float],  # ticker -> confidence (0-1)
        tau: float = 0.05
    ) -> OptimizationResult:
        """Black-Litterman optimization with investor views."""

        # Get market data
        returns_data = {}
        market_caps = {}

        for ticker in tickers:
            prices = await self.data.get_daily_prices(ticker, days=252)
            returns_data[ticker] = prices.pct_change().dropna()
            profile = await self.data.get_company_profile(ticker)
            market_caps[ticker] = profile.market_cap

        returns_df = pd.DataFrame(returns_data)
        cov = returns_df.cov() * 252

        # Market cap weights (equilibrium)
        total_cap = sum(market_caps.values())
        w_mkt = np.array([market_caps[t] / total_cap for t in tickers])

        # Implied equilibrium returns
        delta = 2.5  # Risk aversion
        pi = delta * cov @ w_mkt

        # Build view matrices
        P = []  # Pick matrix
        Q = []  # View returns
        omega_diag = []  # View uncertainty

        for i, ticker in enumerate(tickers):
            if ticker in views:
                row = np.zeros(len(tickers))
                row[i] = 1
                P.append(row)
                Q.append(views[ticker])
                confidence = view_confidence.get(ticker, 0.5)
                omega_diag.append((1 - confidence) * cov.iloc[i, i])

        if P:
            P = np.array(P)
            Q = np.array(Q)
            omega = np.diag(omega_diag)

            # Black-Litterman formula
            cov_tau = tau * cov
            M = np.linalg.inv(
                np.linalg.inv(cov_tau) + P.T @ np.linalg.inv(omega) @ P
            )
            adjusted_returns = M @ (
                np.linalg.inv(cov_tau) @ pi + P.T @ np.linalg.inv(omega) @ Q
            )
        else:
            adjusted_returns = pi

        # Optimize with adjusted returns
        return await self._optimize_with_returns(tickers, adjusted_returns, cov)
```

---

## Phase 4: Real-time Data & Monitoring

### 4.1 Real-time Price Streaming

```python
# services/shared/streaming/price_stream.py
import asyncio
import websockets
from typing import Callable, Dict, List
import json

class PriceStreamClient:
    """Real-time price streaming client."""

    def __init__(self, api_key: str, provider: str = "polygon"):
        self.api_key = api_key
        self.provider = provider
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.ws = None

    async def connect(self):
        """Establish WebSocket connection."""
        if self.provider == "polygon":
            uri = f"wss://socket.polygon.io/stocks"

        self.ws = await websockets.connect(uri)

        # Authenticate
        await self.ws.send(json.dumps({
            "action": "auth",
            "params": self.api_key
        }))

        # Start listening
        asyncio.create_task(self._listen())

    async def subscribe(self, tickers: List[str], callback: Callable):
        """Subscribe to price updates for tickers."""
        for ticker in tickers:
            if ticker not in self.subscriptions:
                self.subscriptions[ticker] = []

                # Subscribe on WebSocket
                await self.ws.send(json.dumps({
                    "action": "subscribe",
                    "params": f"T.{ticker}"
                }))

            self.subscriptions[ticker].append(callback)

    async def _listen(self):
        """Listen for incoming messages."""
        async for message in self.ws:
            data = json.loads(message)

            for event in data:
                if event.get("ev") == "T":  # Trade event
                    ticker = event.get("sym")
                    price_data = {
                        "ticker": ticker,
                        "price": event.get("p"),
                        "size": event.get("s"),
                        "timestamp": event.get("t")
                    }

                    # Notify subscribers
                    for callback in self.subscriptions.get(ticker, []):
                        await callback(price_data)


# Alert System
class AlertManager:
    """Price and event alert system."""

    def __init__(self, redis_client, notification_service):
        self.redis = redis_client
        self.notifications = notification_service
        self.alerts: Dict[str, List[dict]] = {}

    async def create_alert(
        self,
        user_id: str,
        ticker: str,
        condition: str,  # price_above, price_below, percent_change
        threshold: float,
        notification_type: str = "email"
    ) -> str:
        """Create a price alert."""
        alert_id = f"alert:{user_id}:{ticker}:{condition}"

        alert = {
            "id": alert_id,
            "user_id": user_id,
            "ticker": ticker,
            "condition": condition,
            "threshold": threshold,
            "notification_type": notification_type,
            "triggered": False,
            "created_at": datetime.utcnow().isoformat()
        }

        await self.redis.hset(f"alerts:{ticker}", alert_id, json.dumps(alert))

        return alert_id

    async def check_price(self, ticker: str, price: float):
        """Check if any alerts should trigger."""
        alerts = await self.redis.hgetall(f"alerts:{ticker}")

        for alert_id, alert_json in alerts.items():
            alert = json.loads(alert_json)

            if alert["triggered"]:
                continue

            triggered = False

            if alert["condition"] == "price_above" and price > alert["threshold"]:
                triggered = True
            elif alert["condition"] == "price_below" and price < alert["threshold"]:
                triggered = True

            if triggered:
                await self._trigger_alert(alert, price)

    async def _trigger_alert(self, alert: dict, current_price: float):
        """Trigger an alert notification."""
        alert["triggered"] = True

        message = f"{alert['ticker']} has reached ${current_price:.2f} ({alert['condition']})"

        await self.notifications.send(
            user_id=alert["user_id"],
            message=message,
            channel=alert["notification_type"]
        )
```

### 4.2 Monitoring Dashboard

```python
# services/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import structlog

logger = structlog.get_logger(__name__)

# Custom registry
REGISTRY = CollectorRegistry()

# Metrics
TASK_COUNTER = Counter(
    'agent_tasks_total',
    'Total number of agent tasks',
    ['agent_type', 'prompt_name', 'status'],
    registry=REGISTRY
)

TASK_DURATION = Histogram(
    'agent_task_duration_seconds',
    'Agent task execution duration',
    ['agent_type', 'prompt_name'],
    buckets=[1, 5, 10, 30, 60, 120, 300],
    registry=REGISTRY
)

LLM_TOKENS = Counter(
    'llm_tokens_total',
    'Total LLM tokens used',
    ['provider', 'model', 'operation'],
    registry=REGISTRY
)

LLM_LATENCY = Histogram(
    'llm_latency_seconds',
    'LLM API call latency',
    ['provider', 'model'],
    buckets=[0.5, 1, 2, 5, 10, 20, 30],
    registry=REGISTRY
)

ACTIVE_RESEARCH = Gauge(
    'active_research_projects',
    'Number of active research projects',
    registry=REGISTRY
)

API_ERRORS = Counter(
    'external_api_errors_total',
    'External API errors',
    ['api', 'error_type'],
    registry=REGISTRY
)


class MetricsCollector:
    """Collect and export metrics."""

    @staticmethod
    def record_task(agent_type: str, prompt_name: str, status: str, duration: float):
        """Record task completion metrics."""
        TASK_COUNTER.labels(
            agent_type=agent_type,
            prompt_name=prompt_name,
            status=status
        ).inc()

        TASK_DURATION.labels(
            agent_type=agent_type,
            prompt_name=prompt_name
        ).observe(duration)

    @staticmethod
    def record_llm_call(provider: str, model: str, tokens: int, latency: float):
        """Record LLM API call metrics."""
        LLM_TOKENS.labels(
            provider=provider,
            model=model,
            operation="completion"
        ).inc(tokens)

        LLM_LATENCY.labels(
            provider=provider,
            model=model
        ).observe(latency)
```

---

## Phase 5: Advanced Agent Capabilities

### 5.1 Multi-Agent Collaboration

```python
# services/shared/agents/collaboration.py
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio

@dataclass
class AgentMessage:
    from_agent: str
    to_agent: str
    message_type: str  # request, response, broadcast
    content: Dict[str, Any]
    conversation_id: str

class AgentOrchestrator:
    """Orchestrate multi-agent collaboration."""

    def __init__(self, agents: Dict[str, BaseAgent], redis_client):
        self.agents = agents
        self.redis = redis_client
        self.conversations: Dict[str, List[AgentMessage]] = {}

    async def execute_collaborative_task(
        self,
        task_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a task requiring multiple agents."""

        conversation_id = str(uuid.uuid4())
        results = {}

        # Define collaboration workflow
        workflow = task_definition.get("workflow", [])
        context = task_definition.get("initial_context", {})

        for step in workflow:
            agent_type = step["agent"]
            prompt_name = step["prompt"]
            dependencies = step.get("depends_on", [])

            # Wait for dependencies
            for dep in dependencies:
                while dep not in results:
                    await asyncio.sleep(0.1)

            # Build input with context from previous steps
            input_data = {**context}
            for dep in dependencies:
                input_data[f"{dep}_result"] = results[dep]

            # Execute agent task
            agent = self.agents[agent_type]
            task = AgentTask(
                agent_type=agent_type,
                prompt_name=prompt_name,
                input_data=input_data
            )

            result = await agent.execute(task)
            results[step["name"]] = result.data

            # Broadcast result to other agents
            await self._broadcast(
                conversation_id=conversation_id,
                from_agent=agent_type,
                content=result.data
            )

        return {
            "conversation_id": conversation_id,
            "results": results,
            "final_synthesis": await self._synthesize_results(results)
        }

    async def _synthesize_results(self, results: Dict[str, Any]) -> str:
        """Synthesize results from multiple agents."""
        synthesis_agent = self.agents.get("thesis_agent")

        if synthesis_agent:
            task = AgentTask(
                agent_type="thesis_agent",
                prompt_name="multi_agent_synthesis",
                input_data={"agent_results": results}
            )
            result = await synthesis_agent.execute(task)
            return result.data

        return results
```

### 5.2 Autonomous Research Loops

```python
# services/shared/agents/autonomous.py
class AutonomousResearchAgent:
    """Autonomous research agent with self-directed exploration."""

    def __init__(self, base_agent: BaseAgent, knowledge_base: VectorStore):
        self.agent = base_agent
        self.kb = knowledge_base
        self.max_iterations = 10
        self.confidence_threshold = 0.8

    async def research(
        self,
        ticker: str,
        research_question: str
    ) -> Dict[str, Any]:
        """Conduct autonomous research on a topic."""

        iteration = 0
        confidence = 0.0
        findings = []
        questions_explored = [research_question]

        while iteration < self.max_iterations and confidence < self.confidence_threshold:
            iteration += 1

            # Get current question
            current_question = questions_explored[-1]

            # Search knowledge base
            relevant_docs = await self.kb.search(
                query=current_question,
                filters={"ticker": ticker},
                limit=5
            )

            # Generate analysis
            result = await self.agent.execute(AgentTask(
                agent_type=self.agent.agent_type,
                prompt_name="autonomous_analysis",
                input_data={
                    "ticker": ticker,
                    "question": current_question,
                    "context": relevant_docs,
                    "previous_findings": findings
                }
            ))

            analysis = result.data
            findings.append({
                "question": current_question,
                "answer": analysis.get("answer"),
                "confidence": analysis.get("confidence", 0.5),
                "sources": analysis.get("sources", [])
            })

            # Update overall confidence
            confidence = self._calculate_confidence(findings)

            # Generate follow-up questions if needed
            if confidence < self.confidence_threshold:
                follow_ups = analysis.get("follow_up_questions", [])
                if follow_ups:
                    questions_explored.append(follow_ups[0])
                else:
                    break

        return {
            "ticker": ticker,
            "original_question": research_question,
            "findings": findings,
            "final_confidence": confidence,
            "iterations": iteration,
            "synthesis": await self._synthesize_findings(findings)
        }

    def _calculate_confidence(self, findings: List[Dict]) -> float:
        """Calculate overall confidence from findings."""
        if not findings:
            return 0.0

        # Weighted average based on recency
        weights = [0.5 ** i for i in range(len(findings))]
        confidences = [f["confidence"] for f in findings]

        return sum(w * c for w, c in zip(weights, confidences)) / sum(weights)
```

---

## Phase 6: Production Hardening

### 6.1 Rate Limiting & Circuit Breakers

```python
# services/shared/resilience/circuit_breaker.py
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, TypeVar, Generic
import functools

T = TypeVar('T')

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker(Generic[T]):
    """Circuit breaker for external API calls."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_requests: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime = None

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_requests:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        if self.last_failure_time is None:
            return True

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout


# Rate Limiter
class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, rate: float, burst: int):
        self.rate = rate  # tokens per second
        self.burst = burst  # max tokens
        self.tokens = burst
        self.last_update = datetime.utcnow()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens, waiting if necessary."""
        async with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            # Calculate wait time
            needed = tokens - self.tokens
            wait_time = needed / self.rate

            await asyncio.sleep(wait_time)
            self._refill()
            self.tokens -= tokens
            return True

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = datetime.utcnow()
        elapsed = (now - self.last_update).total_seconds()
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_update = now
```

### 6.2 Security Hardening

```python
# services/shared/security/security.py
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional
import jwt

class SecurityManager:
    """Security utilities for the investment agent system."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def generate_api_key(self) -> tuple[str, str]:
        """Generate API key and hash."""
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return key, key_hash

    def verify_api_key(self, key: str, key_hash: str) -> bool:
        """Verify API key against hash."""
        computed_hash = hashlib.sha256(key.encode()).hexdigest()
        return hmac.compare_digest(computed_hash, key_hash)

    def sign_request(self, payload: dict, timestamp: datetime) -> str:
        """Sign inter-service request."""
        message = f"{timestamp.isoformat()}:{json.dumps(payload, sort_keys=True)}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def verify_request_signature(
        self,
        payload: dict,
        timestamp: datetime,
        signature: str,
        max_age_seconds: int = 300
    ) -> bool:
        """Verify inter-service request signature."""
        # Check timestamp freshness
        age = (datetime.utcnow() - timestamp).total_seconds()
        if age > max_age_seconds:
            return False

        expected = self.sign_request(payload, timestamp)
        return hmac.compare_digest(expected, signature)

    def encrypt_sensitive_config(self, value: str) -> str:
        """Encrypt sensitive configuration value."""
        from cryptography.fernet import Fernet

        key = hashlib.sha256(self.secret_key.encode()).digest()
        key = base64.urlsafe_b64encode(key)

        f = Fernet(key)
        return f.encrypt(value.encode()).decode()
```

---

## Implementation Priorities

### Priority Matrix

| Priority | Task | Impact | Effort | Dependencies |
|----------|------|--------|--------|--------------|
| **P0** | Complete test infrastructure | High | Medium | None |
| **P0** | Implement Qdrant integration | High | Medium | None |
| **P1** | Add RAG pipeline | High | Medium | Qdrant |
| **P1** | Implement caching layer | High | Low | Redis |
| **P2** | Add factor models | Medium | High | Data clients |
| **P2** | Portfolio optimization | Medium | High | Factor models |
| **P3** | Real-time streaming | Medium | Medium | None |
| **P3** | Alert system | Medium | Low | Streaming |
| **P4** | Multi-agent collaboration | Medium | High | All agents |
| **P4** | Autonomous research | Low | High | RAG, agents |

### Recommended Execution Order

```mermaid
gantt
    title Implementation Timeline
    dateFormat  YYYY-MM-DD

    section Phase 1
    Test Infrastructure    :p1a, 2024-01-15, 5d
    CI/CD Pipeline        :p1b, after p1a, 3d

    section Phase 2
    Qdrant Integration    :p2a, after p1b, 5d
    RAG Pipeline          :p2b, after p2a, 5d
    Document Ingestion    :p2c, after p2a, 3d

    section Phase 3
    Factor Models         :p3a, after p2b, 7d
    Portfolio Optimization :p3b, after p3a, 7d
    Risk Models           :p3c, after p3a, 5d

    section Phase 4
    Price Streaming       :p4a, after p2b, 5d
    Alert System          :p4b, after p4a, 3d
    Monitoring Dashboard  :p4c, after p4b, 5d

    section Phase 5
    Multi-Agent           :p5a, after p3b, 7d
    Autonomous Research   :p5b, after p5a, 7d

    section Phase 6
    Security Hardening    :p6a, after p4c, 5d
    Production Deploy     :p6b, after p6a, 3d
```

---

## Success Metrics

### Technical Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Test Coverage | 0% | 80%+ |
| API Response Time (p95) | ~5s | <2s |
| LLM Cost per Analysis | ~$0.50 | <$0.30 |
| Knowledge Base Documents | 0 | 10,000+ |
| Factor Model Coverage | 0 | 5 factors |

### Business Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Ideas Generated/Day | 0 | 50+ |
| Research Reports/Week | 0 | 20+ |
| Active Portfolios | 0 | 10+ |
| User Satisfaction | N/A | >4.5/5 |

---

## Conclusion

This Technical Improvement Plan provides a comprehensive roadmap for evolving the AI Investment Agent System into a state-of-the-art systematic investment platform. The prioritized implementation phases ensure that foundational elements (testing, knowledge base) are established before advanced capabilities (multi-agent, autonomous research) are built.

Key success factors:
1. **Rigorous testing** at every phase
2. **Incremental delivery** with measurable milestones
3. **Production-first mindset** for all new features
4. **Continuous monitoring** and optimization

---

*Document Version: 1.0*
*Last Updated: 2026-01-11*
*Author: Senior Full Stack Engineer*
