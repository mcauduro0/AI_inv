"""
Investment Agent System - API Gateway Service
==============================================
Central entry point for all API requests with routing, authentication, 
rate limiting, WebSocket support, and comprehensive error handling.
"""

import os
import time
import json
import uuid
import httpx
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends, status, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import jwt
import redis.asyncio as aioredis
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# =============================================================================
# Configuration
# =============================================================================

class Settings:
    # Service URLs
    AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
    MCA_SERVICE_URL = os.getenv("MCA_SERVICE_URL", "http://master-control-agent:8002")
    WORKFLOW_ENGINE_URL = os.getenv("WORKFLOW_ENGINE_URL", "http://workflow-engine:8003")
    IDEA_AGENT_URL = os.getenv("IDEA_AGENT_URL", "http://idea-generation-agent:8010")
    DD_AGENT_URL = os.getenv("DD_AGENT_URL", "http://due-diligence-agent:8011")
    MACRO_AGENT_URL = os.getenv("MACRO_AGENT_URL", "http://macro-agent:8012")
    PORTFOLIO_AGENT_URL = os.getenv("PORTFOLIO_AGENT_URL", "http://portfolio-agent:8013")
    
    # Database & Cache
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/investment_agent")
    
    # Security
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt-secret-change-in-production")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    
    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

settings = Settings()

# =============================================================================
# Prometheus Metrics
# =============================================================================

REQUEST_COUNT = Counter(
    "api_gateway_requests_total",
    "Total API Gateway requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "api_gateway_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"]
)
ACTIVE_CONNECTIONS = Counter(
    "api_gateway_websocket_connections_total",
    "Total WebSocket connections"
)

# =============================================================================
# Pydantic Models
# =============================================================================

class UserCreate(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: Dict[str, Any]

class ResearchRequest(BaseModel):
    type: str = Field(..., description="Research type: idea_generation, due_diligence, thematic, full_analysis")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: str = Field(default="normal", description="Priority: low, normal, high, urgent")
    ticker: Optional[str] = None
    theme: Optional[str] = None

class ResearchResponse(BaseModel):
    research_id: str
    status: str
    type: str
    created_at: str
    estimated_completion: Optional[str] = None

class PromptExecutionRequest(BaseModel):
    prompt_id: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    llm_provider: str = Field(default="openai")
    model: Optional[str] = None

class AgentTaskRequest(BaseModel):
    agent_type: str
    task_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class WorkflowStartRequest(BaseModel):
    workflow_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    schedule: Optional[str] = None

# =============================================================================
# Global State
# =============================================================================

http_client: Optional[httpx.AsyncClient] = None
redis_client: Optional[aioredis.Redis] = None

# =============================================================================
# Lifespan Management
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global http_client, redis_client
    
    # Startup
    http_client = httpx.AsyncClient(timeout=120.0)
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    
    yield
    
    # Shutdown
    if http_client:
        await http_client.aclose()
    if redis_client:
        await redis_client.close()

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Investment Agent System API",
    description="""
    ## Investment Agent System API Gateway
    
    A comprehensive API for systematic investment research powered by AI agents.
    
    ### Features
    - **Investment Idea Generation**: Scan multiple sources for investment opportunities
    - **Due Diligence**: Comprehensive company analysis
    - **Thematic Research**: Theme-based investment analysis
    - **Portfolio Management**: Portfolio optimization and risk analysis
    - **Macro Analysis**: Macroeconomic research and forecasting
    
    ### Authentication
    All endpoints (except health checks) require JWT authentication.
    Use `/api/auth/login` to obtain a token.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# =============================================================================
# Middleware
# =============================================================================

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Track request metrics and add request ID."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()
    
    response = await call_next(request)
    
    latency = time.time() - start_time
    endpoint = request.url.path
    method = request.method
    status_code = response.status_code
    
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{latency:.3f}s"
    
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )

# =============================================================================
# Authentication Helpers
# =============================================================================

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token and return user data."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

async def optional_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """Optional authentication - returns None if no token provided."""
    if not credentials:
        return None
    try:
        return await verify_token(credentials)
    except HTTPException:
        return None

# =============================================================================
# Health & Metrics Endpoints
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    services_status = {}
    
    # Check Redis
    try:
        await redis_client.ping()
        services_status["redis"] = "healthy"
    except:
        services_status["redis"] = "unhealthy"
    
    # Check downstream services
    service_urls = {
        "auth": settings.AUTH_SERVICE_URL,
        "mca": settings.MCA_SERVICE_URL,
        "workflow": settings.WORKFLOW_ENGINE_URL,
    }
    
    for name, url in service_urls.items():
        try:
            response = await http_client.get(f"{url}/health", timeout=5.0)
            services_status[name] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            services_status[name] = "unavailable"
    
    overall = "healthy" if all(s == "healthy" for s in services_status.values()) else "degraded"
    
    return {
        "status": overall,
        "service": "api-gateway",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": services_status
    }

@app.get("/metrics", tags=["Health"])
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "name": "Investment Agent System API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

# =============================================================================
# Authentication Routes
# =============================================================================

@app.post("/api/auth/register", response_model=TokenResponse, tags=["Authentication"])
async def register(user: UserCreate):
    """Register a new user."""
    try:
        response = await http_client.post(
            f"{settings.AUTH_SERVICE_URL}/register",
            json=user.model_dump()
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Registration failed"))
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")

@app.post("/api/auth/login", response_model=TokenResponse, tags=["Authentication"])
async def login(credentials: UserLogin):
    """Login and get access token."""
    try:
        response = await http_client.post(
            f"{settings.AUTH_SERVICE_URL}/login",
            json=credentials.model_dump()
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Login failed"))
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")

@app.post("/api/auth/refresh", tags=["Authentication"])
async def refresh_token(request: Request):
    """Refresh access token."""
    body = await request.json()
    try:
        response = await http_client.post(f"{settings.AUTH_SERVICE_URL}/refresh", json=body)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")

@app.get("/api/auth/me", tags=["Authentication"])
async def get_current_user(user: dict = Depends(verify_token)):
    """Get current user info."""
    try:
        response = await http_client.get(f"{settings.AUTH_SERVICE_URL}/users/{user['sub']}")
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.RequestError:
        return user

@app.post("/api/auth/logout", tags=["Authentication"])
async def logout(user: dict = Depends(verify_token)):
    """Logout and invalidate token."""
    await redis_client.setex(f"blacklist:{user.get('jti', '')}", 86400, "1")
    return {"message": "Logged out successfully"}

# =============================================================================
# Research Routes
# =============================================================================

@app.post("/api/research", response_model=ResearchResponse, tags=["Research"])
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_token)
):
    """Start a new research workflow."""
    research_id = str(uuid.uuid4())
    
    # Store research request
    research_data = {
        "id": research_id,
        "user_id": user["sub"],
        "type": request.type,
        "parameters": json.dumps(request.parameters),
        "ticker": request.ticker,
        "theme": request.theme,
        "priority": request.priority,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    await redis_client.hset(f"research:{research_id}", mapping=research_data)
    await redis_client.lpush(f"user_research:{user['sub']}", research_id)
    
    # Send to MCA for orchestration
    try:
        response = await http_client.post(
            f"{settings.MCA_SERVICE_URL}/orchestrate",
            json={
                "research_id": research_id,
                "type": request.type,
                "parameters": request.parameters,
                "ticker": request.ticker,
                "theme": request.theme,
                "priority": request.priority,
                "user_id": user["sub"]
            },
            timeout=10.0
        )
        if response.status_code == 200:
            await redis_client.hset(f"research:{research_id}", "status", "processing")
    except httpx.RequestError:
        pass  # Will be picked up by background processor
    
    return ResearchResponse(
        research_id=research_id,
        status="pending",
        type=request.type,
        created_at=research_data["created_at"]
    )

@app.get("/api/research", tags=["Research"])
async def list_research(
    user: dict = Depends(verify_token),
    status: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0
):
    """List user's research requests."""
    research_ids = await redis_client.lrange(f"user_research:{user['sub']}", offset, offset + limit - 1)
    
    results = []
    for rid in research_ids:
        data = await redis_client.hgetall(f"research:{rid}")
        if data:
            if status and data.get("status") != status:
                continue
            if type and data.get("type") != type:
                continue
            data["parameters"] = json.loads(data.get("parameters", "{}"))
            results.append(data)
    
    return {"items": results, "total": len(results), "limit": limit, "offset": offset}

@app.get("/api/research/{research_id}", tags=["Research"])
async def get_research(research_id: str, user: dict = Depends(verify_token)):
    """Get research details and results."""
    data = await redis_client.hgetall(f"research:{research_id}")
    
    if not data:
        raise HTTPException(status_code=404, detail="Research not found")
    
    if data.get("user_id") != user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    data["parameters"] = json.loads(data.get("parameters", "{}"))
    
    # Get results if available
    results = await redis_client.get(f"research_results:{research_id}")
    if results:
        data["results"] = json.loads(results)
    
    # Get progress
    progress = await redis_client.hgetall(f"research_progress:{research_id}")
    if progress:
        data["progress"] = progress
    
    return data

@app.delete("/api/research/{research_id}", tags=["Research"])
async def cancel_research(research_id: str, user: dict = Depends(verify_token)):
    """Cancel a research request."""
    data = await redis_client.hgetall(f"research:{research_id}")
    
    if not data:
        raise HTTPException(status_code=404, detail="Research not found")
    
    if data.get("user_id") != user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if data.get("status") in ["completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed research")
    
    await redis_client.hset(f"research:{research_id}", "status", "cancelled")
    
    # Notify MCA
    try:
        await http_client.post(f"{settings.MCA_SERVICE_URL}/cancel/{research_id}")
    except:
        pass
    
    return {"message": "Research cancelled", "research_id": research_id}

# =============================================================================
# Agent Routes
# =============================================================================

@app.get("/api/agents", tags=["Agents"])
async def list_agents(user: dict = Depends(verify_token)):
    """List available agents and their status."""
    agents = [
        {"name": "Idea Generation Agent", "type": "idea-generation", "url": settings.IDEA_AGENT_URL},
        {"name": "Due Diligence Agent", "type": "due-diligence", "url": settings.DD_AGENT_URL},
        {"name": "Macro Analysis Agent", "type": "macro", "url": settings.MACRO_AGENT_URL},
        {"name": "Portfolio Management Agent", "type": "portfolio", "url": settings.PORTFOLIO_AGENT_URL},
    ]
    
    results = []
    for agent in agents:
        try:
            response = await http_client.get(f"{agent['url']}/health", timeout=5.0)
            status = "online" if response.status_code == 200 else "offline"
            info = response.json() if response.status_code == 200 else {}
        except:
            status = "offline"
            info = {}
        
        results.append({
            "name": agent["name"],
            "type": agent["type"],
            "status": status,
            "capabilities": info.get("capabilities", []),
            "prompt_count": info.get("prompt_count", 0)
        })
    
    return {"agents": results}

@app.post("/api/agents/execute", tags=["Agents"])
async def execute_agent_task(
    request: AgentTaskRequest,
    user: dict = Depends(verify_token)
):
    """Execute a specific agent task."""
    agent_urls = {
        "idea-generation": settings.IDEA_AGENT_URL,
        "due-diligence": settings.DD_AGENT_URL,
        "macro": settings.MACRO_AGENT_URL,
        "portfolio": settings.PORTFOLIO_AGENT_URL
    }
    
    if request.agent_type not in agent_urls:
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {request.agent_type}")
    
    try:
        response = await http_client.post(
            f"{agent_urls[request.agent_type]}/execute",
            json={
                "task_type": request.task_type,
                "parameters": request.parameters,
                "user_id": user["sub"]
            },
            timeout=180.0
        )
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Agent unavailable: {str(e)}")

# =============================================================================
# Prompt Library Routes
# =============================================================================

@app.get("/api/prompts", tags=["Prompts"])
async def list_prompts(
    category: Optional[str] = None,
    agent_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    user: dict = Depends(optional_auth)
):
    """List available prompts from the library."""
    try:
        response = await http_client.get(
            f"{settings.MCA_SERVICE_URL}/prompts",
            params={
                "category": category,
                "agent_type": agent_type,
                "search": search,
                "limit": limit,
                "offset": offset
            }
        )
        return response.json()
    except httpx.RequestError:
        # Fallback to Redis cache
        all_prompts = await redis_client.smembers("prompts:all")
        results = []
        for prompt_id in list(all_prompts)[offset:offset + limit]:
            prompt_data = await redis_client.hgetall(f"prompt:{prompt_id}")
            if prompt_data:
                if category and prompt_data.get("category") != category:
                    continue
                if agent_type and prompt_data.get("agent_type") != agent_type:
                    continue
                results.append(prompt_data)
        return {"items": results, "total": len(results)}

@app.get("/api/prompts/categories", tags=["Prompts"])
async def list_prompt_categories(user: dict = Depends(optional_auth)):
    """List all prompt categories with counts."""
    try:
        response = await http_client.get(f"{settings.MCA_SERVICE_URL}/prompts/categories")
        return response.json()
    except httpx.RequestError:
        # Fallback to Redis cache
        categories = await redis_client.smembers("prompts:categories")
        result = []
        for cat in categories:
            count = await redis_client.scard(f"prompts:category:{cat}")
            result.append({"name": cat, "count": count})
        return {"categories": sorted(result, key=lambda x: x["count"], reverse=True)}

@app.get("/api/prompts/{prompt_id}", tags=["Prompts"])
async def get_prompt(prompt_id: str, user: dict = Depends(optional_auth)):
    """Get a specific prompt by ID."""
    try:
        response = await http_client.get(f"{settings.MCA_SERVICE_URL}/prompts/{prompt_id}")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Prompt not found")
        return response.json()
    except httpx.RequestError:
        # Fallback to Redis cache
        prompt_data = await redis_client.hgetall(f"prompt:{prompt_id}")
        if not prompt_data:
            raise HTTPException(status_code=404, detail="Prompt not found")
        return prompt_data

@app.post("/api/prompts/execute", tags=["Prompts"])
async def execute_prompt(
    request: PromptExecutionRequest,
    user: dict = Depends(verify_token)
):
    """Execute a prompt directly with an LLM."""
    try:
        response = await http_client.post(
            f"{settings.MCA_SERVICE_URL}/execute-prompt",
            json={
                "prompt_id": request.prompt_id,
                "variables": request.variables,
                "llm_provider": request.llm_provider,
                "model": request.model,
                "user_id": user["sub"]
            },
            timeout=180.0
        )
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

# =============================================================================
# Workflow Routes
# =============================================================================

@app.get("/api/workflows", tags=["Workflows"])
async def list_workflows(user: dict = Depends(verify_token)):
    """List available workflow templates."""
    return {
        "workflows": [
            {
                "id": "idea_generation",
                "name": "Investment Idea Generation",
                "description": "Generate investment ideas from multiple sources including newsletters, SEC filings, and social media",
                "stages": ["source_scanning", "theme_analysis", "candidate_screening", "pure_play_identification"],
                "estimated_time": "15-30 minutes",
                "prompts_used": 20
            },
            {
                "id": "due_diligence",
                "name": "Due Diligence Analysis",
                "description": "Comprehensive due diligence on a company including business model, financials, competition, and risks",
                "stages": ["business_overview", "financial_analysis", "competitive_analysis", "management_evaluation", "risk_assessment", "valuation"],
                "estimated_time": "30-60 minutes",
                "prompts_used": 36
            },
            {
                "id": "thematic_research",
                "name": "Thematic Research",
                "description": "Research investment themes and identify companies benefiting from secular trends",
                "stages": ["theme_definition", "market_sizing", "value_chain_mapping", "company_identification", "pure_play_filter"],
                "estimated_time": "20-40 minutes",
                "prompts_used": 15
            },
            {
                "id": "macro_analysis",
                "name": "Macro Analysis",
                "description": "Analyze macroeconomic trends and their impact on markets and sectors",
                "stages": ["economic_indicators", "policy_analysis", "sector_impact", "scenario_modeling"],
                "estimated_time": "20-30 minutes",
                "prompts_used": 16
            },
            {
                "id": "portfolio_review",
                "name": "Portfolio Review",
                "description": "Analyze portfolio holdings, risk exposures, and optimization opportunities",
                "stages": ["holdings_analysis", "risk_assessment", "correlation_analysis", "rebalancing_recommendations"],
                "estimated_time": "15-25 minutes",
                "prompts_used": 19
            },
            {
                "id": "full_analysis",
                "name": "Full Investment Analysis",
                "description": "End-to-end investment analysis combining idea generation, due diligence, and valuation",
                "stages": ["idea_generation", "initial_screening", "deep_dive", "valuation", "recommendation"],
                "estimated_time": "60-120 minutes",
                "prompts_used": 50
            }
        ]
    }

@app.post("/api/workflows/{workflow_id}/start", tags=["Workflows"])
async def start_workflow(
    workflow_id: str,
    request: WorkflowStartRequest,
    user: dict = Depends(verify_token)
):
    """Start a specific workflow."""
    try:
        response = await http_client.post(
            f"{settings.WORKFLOW_ENGINE_URL}/workflows/{workflow_id}/start",
            json={
                "parameters": request.parameters,
                "schedule": request.schedule,
                "user_id": user["sub"]
            }
        )
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Workflow engine unavailable: {str(e)}")

@app.get("/api/workflows/runs", tags=["Workflows"])
async def list_workflow_runs(
    user: dict = Depends(verify_token),
    status: Optional[str] = None,
    limit: int = Query(default=20, le=100)
):
    """List user's workflow runs."""
    try:
        response = await http_client.get(
            f"{settings.WORKFLOW_ENGINE_URL}/runs",
            params={"user_id": user["sub"], "status": status, "limit": limit}
        )
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Workflow engine unavailable: {str(e)}")

@app.get("/api/workflows/runs/{run_id}", tags=["Workflows"])
async def get_workflow_run(run_id: str, user: dict = Depends(verify_token)):
    """Get workflow run details."""
    try:
        response = await http_client.get(
            f"{settings.WORKFLOW_ENGINE_URL}/runs/{run_id}",
            headers={"X-User-ID": user["sub"]}
        )
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Workflow engine unavailable: {str(e)}")

# =============================================================================
# Market Data Routes
# =============================================================================

@app.get("/api/market/quote/{ticker}", tags=["Market Data"])
async def get_quote(ticker: str, user: dict = Depends(verify_token)):
    """Get current quote for a ticker."""
    try:
        response = await http_client.get(
            f"{settings.MCA_SERVICE_URL}/market/quote/{ticker}",
            headers={"X-User-ID": user["sub"]}
        )
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.get("/api/market/company/{ticker}", tags=["Market Data"])
async def get_company_info(ticker: str, user: dict = Depends(verify_token)):
    """Get company information."""
    try:
        response = await http_client.get(
            f"{settings.MCA_SERVICE_URL}/market/company/{ticker}",
            headers={"X-User-ID": user["sub"]}
        )
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.get("/api/market/financials/{ticker}", tags=["Market Data"])
async def get_financials(
    ticker: str,
    period: str = Query(default="annual", description="annual or quarterly"),
    limit: int = Query(default=5, le=20),
    user: dict = Depends(verify_token)
):
    """Get company financials."""
    try:
        response = await http_client.get(
            f"{settings.MCA_SERVICE_URL}/market/financials/{ticker}",
            params={"period": period, "limit": limit},
            headers={"X-User-ID": user["sub"]}
        )
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.get("/api/market/news/{ticker}", tags=["Market Data"])
async def get_news(
    ticker: str,
    limit: int = Query(default=10, le=50),
    user: dict = Depends(verify_token)
):
    """Get news for a ticker."""
    try:
        response = await http_client.get(
            f"{settings.MCA_SERVICE_URL}/market/news/{ticker}",
            params={"limit": limit},
            headers={"X-User-ID": user["sub"]}
        )
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

# =============================================================================
# WebSocket for Real-time Updates
# =============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        ACTIVE_CONNECTIONS.inc()
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
    
    async def send_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time research updates."""
    # Verify token
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload["sub"]
    except:
        await websocket.close(code=4001)
        return
    
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            elif data.startswith("subscribe:"):
                research_id = data.split(":")[1]
                await redis_client.sadd(f"ws_subscriptions:{user_id}", research_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# =============================================================================
# Admin Routes
# =============================================================================

@app.get("/api/admin/stats", tags=["Admin"])
async def get_system_stats(user: dict = Depends(verify_token)):
    """Get system statistics."""
    # Get various stats from Redis
    total_research = await redis_client.dbsize()
    prompt_count = await redis_client.scard("prompts:all")
    
    return {
        "total_research_requests": total_research,
        "total_prompts": prompt_count,
        "active_websockets": sum(len(conns) for conns in manager.active_connections.values()),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/admin/prompts/reload", tags=["Admin"])
async def reload_prompts(user: dict = Depends(verify_token)):
    """Reload prompts from database to cache."""
    try:
        response = await http_client.post(f"{settings.MCA_SERVICE_URL}/admin/reload-prompts")
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

# =============================================================================
# Run Application
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
