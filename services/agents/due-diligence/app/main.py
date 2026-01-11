"""
Due Diligence Agent - FastAPI Service
"""
import os
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog
import redis.asyncio as redis

import sys
sys.path.insert(0, '/app/due-diligence')
from app.agent import DueDiligenceAgent

logger = structlog.get_logger(__name__)

# Global instances
agent: Optional[DueDiligenceAgent] = None
redis_client: Optional[redis.Redis] = None


# =============================================================================
# Request/Response Models
# =============================================================================

class DueDiligenceRequest(BaseModel):
    """Request model for due diligence analysis."""
    ticker: str = Field(..., description="Stock ticker symbol")
    analysis_type: str = Field(..., description="Type of analysis to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")
    depth: str = Field(default="standard", description="Analysis depth: quick, standard, deep")


class ComprehensiveDDRequest(BaseModel):
    """Request for comprehensive due diligence."""
    ticker: str = Field(..., description="Stock ticker symbol")
    include_sections: List[str] = Field(
        default=["business", "financials", "management", "risks", "valuation"],
        description="Sections to include in the analysis"
    )
    depth: str = Field(default="deep", description="Analysis depth")


class TaskResponse(BaseModel):
    """Response model for task submission."""
    task_id: str
    status: str
    message: str


class DDResponse(BaseModel):
    """Response model for due diligence results."""
    task_id: str
    status: str
    ticker: str
    analysis_type: str
    timestamp: str
    result: Dict[str, Any]
    execution_time_seconds: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    agent: str
    version: str
    prompts_loaded: int
    uptime_seconds: float


class AnalysisTypeInfo(BaseModel):
    """Information about an available analysis type."""
    id: str
    name: str
    category: str
    description: str
    required_parameters: List[str] = []
    estimated_time_seconds: int = 30


# =============================================================================
# Lifespan Management
# =============================================================================

startup_time = datetime.utcnow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global agent, redis_client
    
    logger.info("Starting Due Diligence Agent service...")
    
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
    agent = DueDiligenceAgent()
    logger.info("Due Diligence Agent initialized")
    
    yield
    
    # Cleanup
    if redis_client:
        await redis_client.close()
    logger.info("Due Diligence Agent service stopped")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Due Diligence Agent",
    description="AI-powered comprehensive company due diligence service",
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
    prompts_loaded = len(agent.SUPPORTED_PROMPTS) if agent else 0
    
    return HealthResponse(
        status="healthy" if agent else "initializing",
        agent="due-diligence",
        version="1.0.0",
        prompts_loaded=prompts_loaded,
        uptime_seconds=uptime
    )


@app.get("/analysis-types", response_model=List[AnalysisTypeInfo])
async def get_analysis_types():
    """Get available due diligence analysis types."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    analysis_types = [
        # Business Understanding
        AnalysisTypeInfo(
            id="business_overview_report",
            name="Business Overview Report",
            category="Business Understanding",
            description="Comprehensive overview of the company's business model, market position, and strategy",
            required_parameters=["ticker"],
            estimated_time_seconds=45
        ),
        AnalysisTypeInfo(
            id="business_economics",
            name="Business Economics",
            category="Business Understanding",
            description="Deep dive into unit economics, pricing power, and profitability drivers",
            required_parameters=["ticker"],
            estimated_time_seconds=40
        ),
        AnalysisTypeInfo(
            id="growth_margin_drivers",
            name="Growth & Margin Drivers",
            category="Business Understanding",
            description="Analysis of revenue growth drivers and margin expansion opportunities",
            required_parameters=["ticker"],
            estimated_time_seconds=35
        ),
        
        # Industry Analysis
        AnalysisTypeInfo(
            id="industry_overview",
            name="Industry Overview",
            category="Industry Analysis",
            description="Comprehensive industry analysis including market size, trends, and dynamics",
            required_parameters=["ticker"],
            estimated_time_seconds=50
        ),
        AnalysisTypeInfo(
            id="competitive_landscape",
            name="Competitive Landscape",
            category="Industry Analysis",
            description="Analysis of competitive positioning and market share dynamics",
            required_parameters=["ticker"],
            estimated_time_seconds=45
        ),
        AnalysisTypeInfo(
            id="value_chain_mapping",
            name="Value Chain Mapping",
            category="Industry Analysis",
            description="Map the industry value chain and identify strategic positioning",
            required_parameters=["ticker"],
            estimated_time_seconds=40
        ),
        
        # Financial Analysis
        AnalysisTypeInfo(
            id="financial_statement_analysis",
            name="Financial Statement Analysis",
            category="Financial Analysis",
            description="Deep dive into income statement, balance sheet, and cash flows",
            required_parameters=["ticker"],
            estimated_time_seconds=50
        ),
        AnalysisTypeInfo(
            id="earnings_quality",
            name="Earnings Quality Assessment",
            category="Financial Analysis",
            description="Analyze earnings quality, accounting practices, and red flags",
            required_parameters=["ticker"],
            estimated_time_seconds=45
        ),
        AnalysisTypeInfo(
            id="capital_allocation",
            name="Capital Allocation Analysis",
            category="Financial Analysis",
            description="Evaluate management's capital allocation decisions and ROIC",
            required_parameters=["ticker"],
            estimated_time_seconds=40
        ),
        
        # Management Evaluation
        AnalysisTypeInfo(
            id="management_quality_assessment",
            name="Management Quality Assessment",
            category="Management Evaluation",
            description="Comprehensive evaluation of management team quality and track record",
            required_parameters=["ticker"],
            estimated_time_seconds=45
        ),
        AnalysisTypeInfo(
            id="ceo_track_record",
            name="CEO Track Record",
            category="Management Evaluation",
            description="Deep dive into CEO's history, decisions, and performance",
            required_parameters=["ticker"],
            estimated_time_seconds=40
        ),
        AnalysisTypeInfo(
            id="compensation_analysis",
            name="Compensation Analysis",
            category="Management Evaluation",
            description="Analyze executive compensation structure and alignment",
            required_parameters=["ticker"],
            estimated_time_seconds=35
        ),
        
        # Risk Assessment
        AnalysisTypeInfo(
            id="risk_assessment",
            name="Comprehensive Risk Assessment",
            category="Risk Assessment",
            description="Identify and analyze all material risks facing the company",
            required_parameters=["ticker"],
            estimated_time_seconds=50
        ),
        AnalysisTypeInfo(
            id="bear_case_analysis",
            name="Bear Case Analysis",
            category="Risk Assessment",
            description="Develop and stress-test the bear case scenario",
            required_parameters=["ticker"],
            estimated_time_seconds=45
        ),
        AnalysisTypeInfo(
            id="regulatory_risk",
            name="Regulatory Risk Analysis",
            category="Risk Assessment",
            description="Analyze regulatory environment and potential risks",
            required_parameters=["ticker"],
            estimated_time_seconds=40
        ),
        
        # Valuation
        AnalysisTypeInfo(
            id="dcf_valuation",
            name="DCF Valuation",
            category="Valuation",
            description="Discounted cash flow valuation with scenario analysis",
            required_parameters=["ticker"],
            estimated_time_seconds=60
        ),
        AnalysisTypeInfo(
            id="comparable_analysis",
            name="Comparable Company Analysis",
            category="Valuation",
            description="Relative valuation using comparable companies",
            required_parameters=["ticker"],
            estimated_time_seconds=45
        ),
        AnalysisTypeInfo(
            id="sum_of_parts",
            name="Sum of Parts Valuation",
            category="Valuation",
            description="Break-up valuation for diversified companies",
            required_parameters=["ticker"],
            estimated_time_seconds=50
        )
    ]
    
    return analysis_types


@app.post("/analyze", response_model=DDResponse)
async def analyze(request: DueDiligenceRequest):
    """
    Perform due diligence analysis on a company.
    
    This is a synchronous endpoint that waits for results.
    For comprehensive analysis, use /analyze/comprehensive instead.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    start_time = datetime.utcnow()
    
    try:
        # Create task for the agent
        from shared.agents.base import AgentTask
        
        task = AgentTask(
            task_id=f"dd-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            prompt_name=request.analysis_type,
            input_data={
                "ticker": request.ticker,
                "depth": request.depth,
                **request.parameters
            }
        )
        
        result = await agent.execute(task)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)
        
        return DDResponse(
            task_id=task.task_id,
            status="completed",
            ticker=request.ticker,
            analysis_type=request.analysis_type,
            timestamp=datetime.utcnow().isoformat(),
            result=result.data,
            execution_time_seconds=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in due diligence analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/comprehensive", response_model=TaskResponse)
async def analyze_comprehensive(
    request: ComprehensiveDDRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit a comprehensive due diligence analysis.
    
    This runs multiple analysis types in parallel and compiles results.
    Results can be retrieved via /tasks/{task_id}.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    task_id = f"dd-comp-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    
    # Store task status in Redis
    if redis_client:
        await redis_client.hset(f"task:{task_id}", mapping={
            "status": "pending",
            "ticker": request.ticker,
            "sections": ",".join(request.include_sections),
            "created_at": datetime.utcnow().isoformat()
        })
    
    # Add background task
    background_tasks.add_task(
        _execute_comprehensive_dd,
        task_id,
        request.ticker,
        request.include_sections,
        request.depth
    )
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        message=f"Comprehensive DD submitted. Poll /tasks/{task_id} for results."
    )


async def _execute_comprehensive_dd(
    task_id: str,
    ticker: str,
    sections: List[str],
    depth: str
):
    """Execute comprehensive due diligence in background."""
    try:
        # Update status
        if redis_client:
            await redis_client.hset(f"task:{task_id}", "status", "running")
        
        # Map sections to analysis types
        section_analyses = {
            "business": ["business_overview_report", "business_economics", "growth_margin_drivers"],
            "financials": ["financial_statement_analysis", "earnings_quality", "capital_allocation"],
            "management": ["management_quality_assessment", "ceo_track_record", "compensation_analysis"],
            "risks": ["risk_assessment", "bear_case_analysis", "regulatory_risk"],
            "valuation": ["dcf_valuation", "comparable_analysis"]
        }
        
        # Collect all analyses to run
        analyses_to_run = []
        for section in sections:
            if section in section_analyses:
                analyses_to_run.extend(section_analyses[section])
        
        # Run analyses in parallel
        from shared.agents.base import AgentTask
        
        tasks = []
        for analysis_type in analyses_to_run:
            task = AgentTask(
                task_id=f"{task_id}-{analysis_type}",
                prompt_name=analysis_type,
                input_data={"ticker": ticker, "depth": depth}
            )
            tasks.append(agent.execute(task))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile results
        compiled_results = {
            "ticker": ticker,
            "sections": {}
        }
        
        for section in sections:
            compiled_results["sections"][section] = {}
            for analysis_type in section_analyses.get(section, []):
                idx = analyses_to_run.index(analysis_type) if analysis_type in analyses_to_run else -1
                if idx >= 0 and idx < len(results):
                    result = results[idx]
                    if isinstance(result, Exception):
                        compiled_results["sections"][section][analysis_type] = {"error": str(result)}
                    else:
                        compiled_results["sections"][section][analysis_type] = result.data if result.success else {"error": result.error}
        
        # Store result
        if redis_client:
            import json
            await redis_client.hset(f"task:{task_id}", mapping={
                "status": "completed",
                "result": json.dumps(compiled_results),
                "completed_at": datetime.utcnow().isoformat()
            })
            await redis_client.expire(f"task:{task_id}", 7200)  # 2 hour TTL
                
    except Exception as e:
        logger.error(f"Comprehensive DD failed: {e}", exc_info=True)
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
        "ticker": task_data.get("ticker"),
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
    """Get the list of supported prompts."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return {
        "count": len(agent.SUPPORTED_PROMPTS),
        "prompts": agent.SUPPORTED_PROMPTS
    }


# =============================================================================
# Quick Analysis Endpoints
# =============================================================================

@app.get("/quick/{ticker}")
async def quick_analysis(ticker: str):
    """
    Get a quick overview of a company.
    
    Returns basic company info and key metrics without deep analysis.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        company_data = await agent._fetch_company_data(ticker)
        
        return {
            "ticker": ticker,
            "timestamp": datetime.utcnow().isoformat(),
            "data": company_data
        }
        
    except Exception as e:
        logger.error(f"Quick analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Run Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8004")),
        reload=os.getenv("ENV", "development") == "development"
    )
