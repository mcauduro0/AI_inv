"""
Risk Analysis Agent - FastAPI Service
"""
import os
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog
import redis.asyncio as redis

import sys
sys.path.insert(0, '/app/risk-analysis')
from app.agent import RiskAnalysisAgent

logger = structlog.get_logger(__name__)

# Global instances
agent: Optional[RiskAnalysisAgent] = None
redis_client: Optional[redis.Redis] = None


# =============================================================================
# Request/Response Models
# =============================================================================

class IdeaGenerationRequest(BaseModel):
    """Request model for idea generation."""
    strategy: str = Field(..., description="Idea generation strategy to use")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    priority: str = Field(default="normal", description="Task priority: low, normal, high, critical")
    callback_url: Optional[str] = Field(default=None, description="Webhook URL for async results")


class TaskResponse(BaseModel):
    """Response model for task submission."""
    task_id: str
    status: str
    message: str


class IdeaGenerationResponse(BaseModel):
    """Response model for idea generation results."""
    task_id: str
    status: str
    strategy: str
    timestamp: str
    ideas: List[Dict[str, Any]]
    analysis: Dict[str, Any]
    metadata: Dict[str, Any]
    execution_time_seconds: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    agent: str
    version: str
    prompts_loaded: int
    uptime_seconds: float


class StrategyInfo(BaseModel):
    """Information about an available strategy."""
    id: str
    name: str
    description: str
    required_parameters: List[str] = []
    optional_parameters: List[str] = []


# =============================================================================
# Lifespan Management
# =============================================================================

startup_time = datetime.utcnow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global agent, redis_client
    
    logger.info("Starting Risk Analysis Agent service...")
    
    # Initialize Redis connection
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        await redis_client.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        redis_client = None
    
    # Initialize agent
    agent = RiskAnalysisAgent()
    logger.info("Risk Analysis Agent initialized")
    
    yield
    
    # Cleanup
    if redis_client:
        await redis_client.close()
    logger.info("Risk Analysis Agent service stopped")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Risk Analysis Agent",
    description="AI-powered risk analysis and assessment service",
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


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    uptime = (datetime.utcnow() - startup_time).total_seconds()
    prompts_loaded = len(agent.prompts) if agent else 0
    
    return HealthResponse(
        status="healthy" if agent else "initializing",
        agent="risk-analysis",
        version="1.0.0",
        prompts_loaded=prompts_loaded,
        uptime_seconds=uptime
    )


@app.get("/strategies", response_model=List[StrategyInfo])
async def get_strategies():
    """Get available idea generation strategies."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    strategies = [
        StrategyInfo(
            id="thematic",
            name="Thematic Investing",
            description="Generate ideas based on investment themes and macro trends",
            required_parameters=["theme"],
            optional_parameters=["sectors", "market_cap_min", "market_cap_max"]
        ),
        StrategyInfo(
            id="institutional_clustering",
            name="Institutional Clustering (13F)",
            description="Find stocks where top institutional investors are clustering",
            required_parameters=[],
            optional_parameters=["investors", "min_holders", "lookback_quarters"]
        ),
        StrategyInfo(
            id="insider_signals",
            name="Insider Trading Signals",
            description="Analyze insider buying/selling patterns for signals",
            required_parameters=[],
            optional_parameters=["lookback_days", "min_transaction_value", "transaction_type"]
        ),
        StrategyInfo(
            id="trend_analysis",
            name="Trend Analysis",
            description="Identify emerging trends and connect them to equity opportunities",
            required_parameters=[],
            optional_parameters=["sources", "sectors"]
        ),
        StrategyInfo(
            id="publication_scan",
            name="Publication Scanner",
            description="Scan investment newsletters and publications for ideas",
            required_parameters=[],
            optional_parameters=["types", "focus_areas"]
        ),
        StrategyInfo(
            id="social_sentiment",
            name="Social Sentiment",
            description="Analyze social media for investment sentiment",
            required_parameters=[],
            optional_parameters=["platforms", "subreddits", "twitter_accounts"]
        ),
        StrategyInfo(
            id="sector_rotation",
            name="Sector Rotation",
            description="Identify sector rotation opportunities based on economic cycle",
            required_parameters=[],
            optional_parameters=["sectors", "economic_cycle"]
        ),
        StrategyInfo(
            id="value_chain",
            name="Value Chain Mapping",
            description="Map industry value chains to find investment opportunities",
            required_parameters=["industry"],
            optional_parameters=["focus_company"]
        ),
        StrategyInfo(
            id="pure_play_filter",
            name="Pure-Play Filter",
            description="Filter for companies with pure-play exposure to themes",
            required_parameters=["theme"],
            optional_parameters=["candidates", "min_revenue_exposure"]
        ),
        StrategyInfo(
            id="historical_parallel",
            name="Historical Parallels",
            description="Find historical parallels to stress-test investment theses",
            required_parameters=["situation", "thesis"],
            optional_parameters=[]
        )
    ]
    
    return strategies


@app.post("/generate", response_model=IdeaGenerationResponse)
async def generate_ideas(request: IdeaGenerationRequest):
    """
    Generate investment ideas using the specified strategy.
    
    This is a synchronous endpoint that waits for results.
    For long-running tasks, use /generate/async instead.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    start_time = datetime.utcnow()
    
    try:
        result = await agent.execute({
            "strategy": request.strategy,
            "parameters": request.parameters
        })
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return IdeaGenerationResponse(
            task_id=f"ig-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            status="completed",
            strategy=request.strategy,
            timestamp=result.get("timestamp", datetime.utcnow().isoformat()),
            ideas=result.get("ideas", []),
            analysis=result.get("analysis", {}),
            metadata=result.get("metadata", {}),
            execution_time_seconds=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating ideas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/async", response_model=TaskResponse)
async def generate_ideas_async(
    request: IdeaGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit an async idea generation task.
    
    Results will be sent to the callback_url if provided,
    or can be retrieved via /tasks/{task_id}.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    task_id = f"ig-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    
    # Store task status in Redis
    if redis_client:
        await redis_client.hset(f"task:{task_id}", mapping={
            "status": "pending",
            "strategy": request.strategy,
            "created_at": datetime.utcnow().isoformat()
        })
    
    # Add background task
    background_tasks.add_task(
        _execute_async_task,
        task_id,
        request.strategy,
        request.parameters,
        request.callback_url
    )
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        message=f"Task submitted. Poll /tasks/{task_id} for results."
    )


async def _execute_async_task(
    task_id: str,
    strategy: str,
    parameters: Dict[str, Any],
    callback_url: Optional[str]
):
    """Execute an async task in the background."""
    try:
        # Update status
        if redis_client:
            await redis_client.hset(f"task:{task_id}", "status", "running")
        
        # Execute
        result = await agent.execute({
            "strategy": strategy,
            "parameters": parameters
        })
        
        # Store result
        if redis_client:
            import json
            await redis_client.hset(f"task:{task_id}", mapping={
                "status": "completed",
                "result": json.dumps(result),
                "completed_at": datetime.utcnow().isoformat()
            })
            await redis_client.expire(f"task:{task_id}", 3600)  # 1 hour TTL
        
        # Send callback if provided
        if callback_url:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(callback_url, json={
                    "task_id": task_id,
                    "status": "completed",
                    "result": result
                })
                
    except Exception as e:
        logger.error(f"Async task failed: {e}", exc_info=True)
        if redis_client:
            await redis_client.hset(f"task:{task_id}", mapping={
                "status": "failed",
                "error": str(e)
            })


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get the status and results of an async task."""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    task_data = await redis_client.hgetall(f"task:{task_id}")
    
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    result = {
        "task_id": task_id,
        "status": task_data.get("status"),
        "strategy": task_data.get("strategy"),
        "created_at": task_data.get("created_at"),
        "completed_at": task_data.get("completed_at")
    }
    
    if task_data.get("result"):
        import json
        result["result"] = json.loads(task_data["result"])
    
    if task_data.get("error"):
        result["error"] = task_data["error"]
    
    return result


@app.get("/prompts")
async def get_prompts():
    """Get the list of prompts loaded by this agent."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return {
        "count": len(agent.prompts),
        "prompts": [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category.value if hasattr(p.category, 'value') else str(p.category),
                "description": p.description
            }
            for p in agent.prompts.values()
        ] if hasattr(agent, 'prompts') else []
    }


# =============================================================================
# Run Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8014")),
        reload=os.getenv("ENV", "development") == "development"
    )
