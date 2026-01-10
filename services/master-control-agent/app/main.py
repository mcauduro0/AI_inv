# =============================================================================
# Master Control Agent - Main Application
# =============================================================================
# Central orchestration service for the investment agent system
# =============================================================================

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog

import sys
sys.path.insert(0, "/app")

from shared.config.settings import settings
from shared.db.repository import (
    get_session, init_db, WorkflowRepository, AgentTaskRepository,
    ResearchProjectRepository
)
from shared.db.models import TaskStatus, WorkflowStatus
from shared.clients.redis_client import get_redis_client
from shared.agents.base import AgentTask, AgentResult, TaskPriority

logger = structlog.get_logger(__name__)


# =============================================================================
# Pydantic Models
# =============================================================================

class WorkflowCreateRequest(BaseModel):
    """Request to create a new workflow."""
    name: str
    workflow_type: str
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    schedule: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Workflow response model."""
    id: str
    name: str
    workflow_type: str
    description: Optional[str]
    status: str
    config: Dict[str, Any]
    schedule: Optional[str]
    last_run_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TaskCreateRequest(BaseModel):
    """Request to create a new agent task."""
    agent_type: str
    prompt_name: str
    input_data: Dict[str, Any]
    priority: str = "normal"


class TaskResponse(BaseModel):
    """Task response model."""
    task_id: str
    agent_type: str
    prompt_name: str
    status: str
    priority: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    
    class Config:
        from_attributes = True


class ResearchRequest(BaseModel):
    """Request to start a research workflow."""
    ticker: str
    research_type: str = "full"  # quick, standard, full, deep
    focus_areas: List[str] = Field(default_factory=list)
    custom_questions: List[str] = Field(default_factory=list)


class ScreeningRequest(BaseModel):
    """Request to run a screening workflow."""
    screener_name: str
    criteria: Dict[str, Any]
    universe: str = "us_stocks"  # us_stocks, global, etfs, etc.
    limit: int = 100


class IdeaGenerationRequest(BaseModel):
    """Request to generate investment ideas."""
    theme: Optional[str] = None
    sector: Optional[str] = None
    strategy: str = "thematic"  # thematic, value, growth, momentum, contrarian
    sources: List[str] = Field(default_factory=list)


# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Master Control Agent")
    await init_db()
    
    # Start background task processor
    redis = get_redis_client()
    await redis.connect()
    
    yield
    
    await redis.disconnect()
    logger.info("Shutting down Master Control Agent")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Investment Agent System - Master Control Agent",
    description="Central orchestration service for investment research workflows",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Workflow Management Routes
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    redis = get_redis_client()
    redis_ok = await redis.ping()
    
    return {
        "status": "healthy" if redis_ok else "degraded",
        "service": "master-control-agent",
        "redis": "connected" if redis_ok else "disconnected"
    }


@app.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(request: WorkflowCreateRequest):
    """Create a new workflow."""
    async with get_session() as session:
        workflow_repo = WorkflowRepository(session)
        
        workflow = await workflow_repo.create(
            name=request.name,
            workflow_type=request.workflow_type,
            description=request.description,
            config=request.config,
            schedule=request.schedule,
            user_id=None  # TODO: Get from auth
        )
        
        logger.info("Workflow created", workflow_id=str(workflow.id))
        
        return WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            workflow_type=workflow.workflow_type,
            description=workflow.description,
            status=workflow.status.value,
            config=workflow.config,
            schedule=workflow.schedule,
            last_run_at=workflow.last_run_at,
            created_at=workflow.created_at
        )


@app.get("/workflows", response_model=List[WorkflowResponse])
async def list_workflows(
    workflow_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """List all workflows."""
    async with get_session() as session:
        workflow_repo = WorkflowRepository(session)
        
        filters = {}
        if workflow_type:
            filters["workflow_type"] = workflow_type
        if status:
            filters["status"] = status
        
        workflows = await workflow_repo.get_all(skip=skip, limit=limit, **filters)
        
        return [
            WorkflowResponse(
                id=str(w.id),
                name=w.name,
                workflow_type=w.workflow_type,
                description=w.description,
                status=w.status.value,
                config=w.config,
                schedule=w.schedule,
                last_run_at=w.last_run_at,
                created_at=w.created_at
            )
            for w in workflows
        ]


@app.post("/workflows/{workflow_id}/run")
async def run_workflow(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    input_data: Optional[Dict[str, Any]] = None
):
    """Trigger a workflow run."""
    async with get_session() as session:
        workflow_repo = WorkflowRepository(session)
        workflow = await workflow_repo.get(UUID(workflow_id))
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        # Create workflow run record
        from shared.db.models import WorkflowRun
        run = WorkflowRun(
            workflow_id=workflow.id,
            status=TaskStatus.PENDING,
            input_data=input_data or {}
        )
        session.add(run)
        await session.flush()
        
        run_id = str(run.id)
        
        # Queue the workflow execution
        redis = get_redis_client()
        await redis.publish(
            f"{settings.redis.channel_prefix}:workflows",
            json.dumps({
                "workflow_id": workflow_id,
                "run_id": run_id,
                "workflow_type": workflow.workflow_type,
                "config": workflow.config,
                "input_data": input_data or {}
            })
        )
        
        logger.info(
            "Workflow run queued",
            workflow_id=workflow_id,
            run_id=run_id
        )
        
        return {
            "message": "Workflow run started",
            "run_id": run_id,
            "status": "pending"
        }


# =============================================================================
# Task Management Routes
# =============================================================================

@app.post("/tasks", response_model=TaskResponse)
async def create_task(request: TaskCreateRequest):
    """Create and queue a new agent task."""
    task = AgentTask(
        agent_type=request.agent_type,
        prompt_name=request.prompt_name,
        input_data=request.input_data,
        priority=TaskPriority(request.priority)
    )
    
    # Store task in database
    async with get_session() as session:
        task_repo = AgentTaskRepository(session)
        
        task_record = await task_repo.create(
            task_id=task.task_id,
            agent_type=task.agent_type,
            prompt_name=task.prompt_name,
            input_data=task.input_data,
            priority=task.priority.value,
            status=TaskStatus.PENDING
        )
    
    # Queue task for processing
    redis = get_redis_client()
    channel = f"{settings.redis.channel_prefix}:tasks:{request.agent_type}"
    await redis.publish(channel, task.model_dump_json())
    
    logger.info(
        "Task created and queued",
        task_id=task.task_id,
        agent_type=request.agent_type
    )
    
    return TaskResponse(
        task_id=task.task_id,
        agent_type=task.agent_type,
        prompt_name=task.prompt_name,
        status="pending",
        priority=task.priority.value,
        created_at=task.created_at,
        started_at=None,
        completed_at=None,
        result=None,
        error=None
    )


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get task status and result."""
    async with get_session() as session:
        task_repo = AgentTaskRepository(session)
        task = await task_repo.get_by_task_id(task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return TaskResponse(
            task_id=task.task_id,
            agent_type=task.agent_type,
            prompt_name=task.prompt_name,
            status=task.status.value,
            priority=task.priority,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            result=task.output_data,
            error=task.error_message
        )


@app.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """List tasks with optional filtering."""
    async with get_session() as session:
        task_repo = AgentTaskRepository(session)
        
        filters = {}
        if agent_type:
            filters["agent_type"] = agent_type
        if status:
            filters["status"] = status
        
        tasks = await task_repo.get_all(skip=skip, limit=limit, **filters)
        
        return [
            TaskResponse(
                task_id=t.task_id,
                agent_type=t.agent_type,
                prompt_name=t.prompt_name,
                status=t.status.value,
                priority=t.priority,
                created_at=t.created_at,
                started_at=t.started_at,
                completed_at=t.completed_at,
                result=t.output_data,
                error=t.error_message
            )
            for t in tasks
        ]


# =============================================================================
# Research Workflow Routes
# =============================================================================

@app.post("/research/start")
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start a comprehensive research workflow for a ticker."""
    
    # Define the research workflow based on type
    workflow_steps = []
    
    if request.research_type in ["quick", "standard", "full", "deep"]:
        # Phase 1: Business Understanding
        workflow_steps.append({
            "agent": "business_model_agent",
            "prompt": "business_overview_report",
            "input": {"ticker": request.ticker}
        })
        
        if request.research_type in ["standard", "full", "deep"]:
            # Phase 2: Industry Analysis
            workflow_steps.append({
                "agent": "industry_agent",
                "prompt": "industry_overview",
                "input": {"ticker": request.ticker}
            })
            workflow_steps.append({
                "agent": "industry_agent",
                "prompt": "competitive_landscape",
                "input": {"ticker": request.ticker}
            })
        
        if request.research_type in ["full", "deep"]:
            # Phase 3: Financial Analysis
            workflow_steps.append({
                "agent": "financial_agent",
                "prompt": "financial_statement_analysis",
                "input": {"ticker": request.ticker}
            })
            workflow_steps.append({
                "agent": "valuation_agent",
                "prompt": "dcf_valuation",
                "input": {"ticker": request.ticker}
            })
            
            # Phase 4: Risk Assessment
            workflow_steps.append({
                "agent": "risk_agent",
                "prompt": "risk_assessment",
                "input": {"ticker": request.ticker}
            })
        
        if request.research_type == "deep":
            # Phase 5: Management Evaluation
            workflow_steps.append({
                "agent": "management_agent",
                "prompt": "management_quality_assessment",
                "input": {"ticker": request.ticker}
            })
            
            # Phase 6: Thesis Development
            workflow_steps.append({
                "agent": "thesis_agent",
                "prompt": "investment_thesis_synthesis",
                "input": {"ticker": request.ticker}
            })
    
    # Create research project
    async with get_session() as session:
        project_repo = ResearchProjectRepository(session)
        
        project = await project_repo.create(
            name=f"Research: {request.ticker}",
            ticker=request.ticker.upper(),
            status="screening",
            user_id=None  # TODO: Get from auth
        )
        
        project_id = str(project.id)
    
    # Queue the workflow
    redis = get_redis_client()
    await redis.publish(
        f"{settings.redis.channel_prefix}:research",
        json.dumps({
            "project_id": project_id,
            "ticker": request.ticker,
            "research_type": request.research_type,
            "steps": workflow_steps,
            "focus_areas": request.focus_areas,
            "custom_questions": request.custom_questions
        })
    )
    
    logger.info(
        "Research workflow started",
        project_id=project_id,
        ticker=request.ticker,
        research_type=request.research_type
    )
    
    return {
        "message": "Research workflow started",
        "project_id": project_id,
        "ticker": request.ticker,
        "steps_count": len(workflow_steps)
    }


@app.get("/research/{project_id}")
async def get_research_status(project_id: str):
    """Get research project status and results."""
    async with get_session() as session:
        project_repo = ResearchProjectRepository(session)
        project = await project_repo.get_with_notes(UUID(project_id))
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research project not found"
            )
        
        return {
            "id": str(project.id),
            "name": project.name,
            "ticker": project.ticker,
            "status": project.status.value,
            "thesis_summary": project.thesis_summary,
            "bull_case": project.bull_case,
            "bear_case": project.bear_case,
            "key_catalysts": project.key_catalysts,
            "key_risks": project.key_risks,
            "target_price": project.target_price,
            "conviction_level": project.conviction_level.value if project.conviction_level else None,
            "notes_count": len(project.notes) if project.notes else 0,
            "created_at": project.created_at,
            "updated_at": project.updated_at
        }


# =============================================================================
# Screening Workflow Routes
# =============================================================================

@app.post("/screening/run")
async def run_screening(request: ScreeningRequest, background_tasks: BackgroundTasks):
    """Run a stock screening workflow."""
    
    # Queue the screening workflow
    redis = get_redis_client()
    await redis.publish(
        f"{settings.redis.channel_prefix}:screening",
        json.dumps({
            "screener_name": request.screener_name,
            "criteria": request.criteria,
            "universe": request.universe,
            "limit": request.limit
        })
    )
    
    logger.info(
        "Screening workflow started",
        screener_name=request.screener_name
    )
    
    return {
        "message": "Screening workflow started",
        "screener_name": request.screener_name
    }


# =============================================================================
# Idea Generation Routes
# =============================================================================

@app.post("/ideas/generate")
async def generate_ideas(request: IdeaGenerationRequest, background_tasks: BackgroundTasks):
    """Generate investment ideas based on strategy."""
    
    # Define idea generation workflow
    workflow_steps = []
    
    if request.strategy == "thematic":
        if request.theme:
            workflow_steps.append({
                "agent": "idea_generation_agent",
                "prompt": "thematic_candidate_screen",
                "input": {"theme": request.theme}
            })
            workflow_steps.append({
                "agent": "idea_generation_agent",
                "prompt": "theme_order_effects",
                "input": {"theme": request.theme}
            })
    
    elif request.strategy == "value":
        workflow_steps.append({
            "agent": "idea_generation_agent",
            "prompt": "value_screen",
            "input": {"sector": request.sector}
        })
    
    elif request.strategy == "contrarian":
        workflow_steps.append({
            "agent": "idea_generation_agent",
            "prompt": "contrarian_opportunities",
            "input": {}
        })
    
    # Add source scanning if specified
    for source in request.sources:
        if source == "newsletters":
            workflow_steps.append({
                "agent": "idea_generation_agent",
                "prompt": "newsletter_idea_scraping",
                "input": {}
            })
        elif source == "sec_filings":
            workflow_steps.append({
                "agent": "idea_generation_agent",
                "prompt": "institutional_clustering_13f",
                "input": {}
            })
        elif source == "social":
            workflow_steps.append({
                "agent": "idea_generation_agent",
                "prompt": "social_sentiment_scan",
                "input": {}
            })
    
    # Queue the workflow
    redis = get_redis_client()
    await redis.publish(
        f"{settings.redis.channel_prefix}:idea_generation",
        json.dumps({
            "strategy": request.strategy,
            "theme": request.theme,
            "sector": request.sector,
            "steps": workflow_steps
        })
    )
    
    logger.info(
        "Idea generation workflow started",
        strategy=request.strategy
    )
    
    return {
        "message": "Idea generation workflow started",
        "strategy": request.strategy,
        "steps_count": len(workflow_steps)
    }


# =============================================================================
# Metrics and Monitoring Routes
# =============================================================================

@app.get("/metrics/tasks")
async def get_task_metrics(days: int = 7):
    """Get task execution metrics."""
    async with get_session() as session:
        task_repo = AgentTaskRepository(session)
        metrics = await task_repo.get_metrics(days=days)
        
        return {
            "period_days": days,
            "by_agent": metrics
        }


@app.get("/agents")
async def list_available_agents():
    """List all available agents and their capabilities."""
    return {
        "agents": [
            {
                "type": "idea_generation_agent",
                "name": "Investment Idea Generation Agent",
                "description": "Generates investment ideas from various sources",
                "prompts": [
                    "thematic_candidate_screen",
                    "newsletter_idea_scraping",
                    "institutional_clustering_13f",
                    "theme_order_effects",
                    "pure_play_filter"
                ]
            },
            {
                "type": "business_model_agent",
                "name": "Business Model Analysis Agent",
                "description": "Analyzes company business models and economics",
                "prompts": [
                    "business_overview_report",
                    "business_economics",
                    "growth_margin_drivers",
                    "unit_economics"
                ]
            },
            {
                "type": "industry_agent",
                "name": "Industry Analysis Agent",
                "description": "Analyzes industry dynamics and competitive landscape",
                "prompts": [
                    "industry_overview",
                    "competitive_landscape",
                    "value_chain_mapping",
                    "market_sizing"
                ]
            },
            {
                "type": "financial_agent",
                "name": "Financial Analysis Agent",
                "description": "Performs financial statement analysis",
                "prompts": [
                    "financial_statement_analysis",
                    "earnings_quality",
                    "capital_allocation",
                    "cash_flow_analysis"
                ]
            },
            {
                "type": "valuation_agent",
                "name": "Valuation Agent",
                "description": "Performs company valuations",
                "prompts": [
                    "dcf_valuation",
                    "comparable_analysis",
                    "sum_of_parts",
                    "scenario_analysis"
                ]
            },
            {
                "type": "risk_agent",
                "name": "Risk Assessment Agent",
                "description": "Identifies and assesses investment risks",
                "prompts": [
                    "risk_assessment",
                    "bear_case_analysis",
                    "regulatory_risk",
                    "competitive_risk"
                ]
            },
            {
                "type": "management_agent",
                "name": "Management Evaluation Agent",
                "description": "Evaluates management quality and track record",
                "prompts": [
                    "management_quality_assessment",
                    "ceo_track_record",
                    "capital_allocation_history",
                    "insider_activity"
                ]
            },
            {
                "type": "macro_agent",
                "name": "Macro Analysis Agent",
                "description": "Analyzes macroeconomic factors",
                "prompts": [
                    "macro_environment",
                    "sector_sensitivity",
                    "interest_rate_impact",
                    "currency_exposure"
                ]
            },
            {
                "type": "thesis_agent",
                "name": "Thesis Development Agent",
                "description": "Synthesizes research into investment thesis",
                "prompts": [
                    "investment_thesis_synthesis",
                    "catalyst_identification",
                    "position_sizing",
                    "monitoring_framework"
                ]
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
