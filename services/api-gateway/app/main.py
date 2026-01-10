"""
Investment Agent System - API Gateway Service
==============================================
Central entry point for all API requests with routing, authentication, and rate limiting.
"""

import os
import time
import httpx
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# Configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
MCA_SERVICE_URL = os.getenv("MCA_SERVICE_URL", "http://master-control-agent:8000")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Prometheus metrics
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

# HTTP client
http_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global http_client
    http_client = httpx.AsyncClient(timeout=60.0)
    yield
    await http_client.aclose()

# FastAPI app
app = FastAPI(
    title="Investment Agent System API",
    description="API Gateway for the Investment Agent System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
async def metrics_middleware(request: Request, call_next):
    """Track request metrics."""
    start_time = time.time()
    
    response = await call_next(request)
    
    latency = time.time() - start_time
    endpoint = request.url.path
    method = request.method
    status_code = response.status_code
    
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
    
    return response


# =============================================================================
# Authentication
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
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
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

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api-gateway"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# =============================================================================
# Auth Proxy Routes
# =============================================================================

@app.post("/api/auth/register")
async def register(request: Request):
    """Proxy registration to auth service."""
    body = await request.json()
    response = await http_client.post(f"{AUTH_SERVICE_URL}/register", json=body)
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.post("/api/auth/login")
async def login(request: Request):
    """Proxy login to auth service."""
    body = await request.json()
    response = await http_client.post(f"{AUTH_SERVICE_URL}/login", json=body)
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.post("/api/auth/refresh")
async def refresh_token(request: Request):
    """Proxy token refresh to auth service."""
    body = await request.json()
    response = await http_client.post(f"{AUTH_SERVICE_URL}/refresh", json=body)
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.get("/api/auth/me")
async def get_current_user(user: dict = Depends(verify_token)):
    """Get current user info."""
    response = await http_client.get(
        f"{AUTH_SERVICE_URL}/users/{user['sub']}"
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


# =============================================================================
# Research Project Routes
# =============================================================================

@app.get("/api/projects")
async def list_projects(user: dict = Depends(verify_token)):
    """List user's research projects."""
    response = await http_client.get(
        f"{MCA_SERVICE_URL}/projects",
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.post("/api/projects")
async def create_project(request: Request, user: dict = Depends(verify_token)):
    """Create a new research project."""
    body = await request.json()
    response = await http_client.post(
        f"{MCA_SERVICE_URL}/projects",
        json=body,
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str, user: dict = Depends(verify_token)):
    """Get a specific research project."""
    response = await http_client.get(
        f"{MCA_SERVICE_URL}/projects/{project_id}",
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.put("/api/projects/{project_id}")
async def update_project(project_id: str, request: Request, user: dict = Depends(verify_token)):
    """Update a research project."""
    body = await request.json()
    response = await http_client.put(
        f"{MCA_SERVICE_URL}/projects/{project_id}",
        json=body,
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str, user: dict = Depends(verify_token)):
    """Delete a research project."""
    response = await http_client.delete(
        f"{MCA_SERVICE_URL}/projects/{project_id}",
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


# =============================================================================
# Research Task Routes
# =============================================================================

@app.post("/api/research/analyze")
async def analyze_company(request: Request, user: dict = Depends(verify_token)):
    """Start a company analysis task."""
    body = await request.json()
    response = await http_client.post(
        f"{MCA_SERVICE_URL}/research/analyze",
        json=body,
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.post("/api/research/screen")
async def screen_stocks(request: Request, user: dict = Depends(verify_token)):
    """Run a stock screening task."""
    body = await request.json()
    response = await http_client.post(
        f"{MCA_SERVICE_URL}/research/screen",
        json=body,
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.post("/api/research/ideas")
async def generate_ideas(request: Request, user: dict = Depends(verify_token)):
    """Generate investment ideas."""
    body = await request.json()
    response = await http_client.post(
        f"{MCA_SERVICE_URL}/research/ideas",
        json=body,
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.get("/api/research/tasks/{task_id}")
async def get_task_status(task_id: str, user: dict = Depends(verify_token)):
    """Get status of a research task."""
    response = await http_client.get(
        f"{MCA_SERVICE_URL}/tasks/{task_id}",
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


# =============================================================================
# Workflow Routes
# =============================================================================

@app.get("/api/workflows")
async def list_workflows(user: dict = Depends(verify_token)):
    """List user's workflows."""
    response = await http_client.get(
        f"{MCA_SERVICE_URL}/workflows",
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.post("/api/workflows")
async def create_workflow(request: Request, user: dict = Depends(verify_token)):
    """Create a new workflow."""
    body = await request.json()
    response = await http_client.post(
        f"{MCA_SERVICE_URL}/workflows",
        json=body,
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.post("/api/workflows/{workflow_id}/run")
async def run_workflow(workflow_id: str, request: Request, user: dict = Depends(verify_token)):
    """Run a workflow."""
    body = await request.json() if await request.body() else {}
    response = await http_client.post(
        f"{MCA_SERVICE_URL}/workflows/{workflow_id}/run",
        json=body,
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


# =============================================================================
# Market Data Routes
# =============================================================================

@app.get("/api/market/quote/{ticker}")
async def get_quote(ticker: str, user: dict = Depends(verify_token)):
    """Get current quote for a ticker."""
    response = await http_client.get(
        f"{MCA_SERVICE_URL}/market/quote/{ticker}",
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.get("/api/market/company/{ticker}")
async def get_company_info(ticker: str, user: dict = Depends(verify_token)):
    """Get company information."""
    response = await http_client.get(
        f"{MCA_SERVICE_URL}/market/company/{ticker}",
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.get("/api/market/financials/{ticker}")
async def get_financials(ticker: str, user: dict = Depends(verify_token)):
    """Get company financials."""
    response = await http_client.get(
        f"{MCA_SERVICE_URL}/market/financials/{ticker}",
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


# =============================================================================
# Prompt Library Routes
# =============================================================================

@app.get("/api/prompts")
async def list_prompts(
    category: Optional[str] = None,
    user: dict = Depends(verify_token)
):
    """List available prompts."""
    params = {"category": category} if category else {}
    response = await http_client.get(
        f"{MCA_SERVICE_URL}/prompts",
        params=params,
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.get("/api/prompts/{prompt_name}")
async def get_prompt(prompt_name: str, user: dict = Depends(verify_token)):
    """Get a specific prompt."""
    response = await http_client.get(
        f"{MCA_SERVICE_URL}/prompts/{prompt_name}",
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.post("/api/prompts/{prompt_name}/execute")
async def execute_prompt(prompt_name: str, request: Request, user: dict = Depends(verify_token)):
    """Execute a prompt with given inputs."""
    body = await request.json()
    response = await http_client.post(
        f"{MCA_SERVICE_URL}/prompts/{prompt_name}/execute",
        json=body,
        headers={"X-User-ID": user["sub"]}
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
