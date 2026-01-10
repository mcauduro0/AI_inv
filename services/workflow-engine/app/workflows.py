# =============================================================================
# Workflow Engine - Investment Research Workflows
# =============================================================================
# Prefect-based workflow orchestration for investment research pipelines
# =============================================================================

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
from prefect.artifacts import create_markdown_artifact
import structlog

import sys
sys.path.insert(0, "/app")

from shared.config.settings import settings
from shared.db.repository import (
    get_session, ResearchProjectRepository, WorkflowRepository,
    AgentTaskRepository, ScreenerResultRepository
)
from shared.db.models import ResearchStatus, TaskStatus, ConvictionLevel
from shared.clients.redis_client import get_redis_client
from shared.agents.base import AgentTask, TaskPriority

logger = structlog.get_logger(__name__)


# =============================================================================
# Task Definitions
# =============================================================================

@task(
    name="dispatch_agent_task",
    retries=3,
    retry_delay_seconds=30,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1)
)
async def dispatch_agent_task(
    agent_type: str,
    prompt_name: str,
    input_data: Dict[str, Any],
    priority: str = "normal",
    timeout_seconds: int = 300
) -> Dict[str, Any]:
    """
    Dispatch a task to an agent and wait for the result.
    """
    log = get_run_logger()
    
    task = AgentTask(
        agent_type=agent_type,
        prompt_name=prompt_name,
        input_data=input_data,
        priority=TaskPriority(priority)
    )
    
    log.info(f"Dispatching task {task.task_id} to {agent_type}")
    
    # Store task in database
    async with get_session() as session:
        task_repo = AgentTaskRepository(session)
        await task_repo.create(
            task_id=task.task_id,
            agent_type=agent_type,
            prompt_name=prompt_name,
            input_data=input_data,
            priority=priority,
            status=TaskStatus.PENDING
        )
    
    # Publish task to agent channel
    redis = get_redis_client()
    await redis.connect()
    
    channel = f"{settings.redis.channel_prefix}:tasks:{agent_type}"
    await redis.publish(channel, task.model_dump_json())
    
    # Wait for result
    result_channel = f"{settings.redis.channel_prefix}:results:{task.task_id}"
    result = None
    
    async def handle_result(ch: str, message: str):
        nonlocal result
        result = json.loads(message)
    
    # Subscribe and wait with timeout
    try:
        await asyncio.wait_for(
            redis.subscribe([result_channel], handle_result),
            timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        log.warning(f"Task {task.task_id} timed out after {timeout_seconds}s")
        result = {
            "success": False,
            "error": f"Task timed out after {timeout_seconds} seconds"
        }
    
    # Update task status in database
    async with get_session() as session:
        task_repo = AgentTaskRepository(session)
        await task_repo.update(
            task.task_id,
            status=TaskStatus.COMPLETED if result.get("success") else TaskStatus.FAILED,
            output_data=result.get("data", {}),
            error_message=result.get("error"),
            completed_at=datetime.utcnow()
        )
    
    await redis.disconnect()
    
    return result


@task(name="aggregate_results")
def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate results from multiple agent tasks."""
    log = get_run_logger()
    
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    log.info(f"Aggregating {len(successful)} successful, {len(failed)} failed results")
    
    return {
        "total_tasks": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "results": [r.get("data", {}) for r in successful],
        "errors": [r.get("error") for r in failed if r.get("error")]
    }


@task(name="save_research_findings")
async def save_research_findings(
    project_id: str,
    findings: Dict[str, Any]
) -> None:
    """Save research findings to the database."""
    log = get_run_logger()
    
    async with get_session() as session:
        project_repo = ResearchProjectRepository(session)
        
        update_data = {}
        
        if "thesis_summary" in findings:
            update_data["thesis_summary"] = findings["thesis_summary"]
        if "bull_case" in findings:
            update_data["bull_case"] = findings["bull_case"]
        if "bear_case" in findings:
            update_data["bear_case"] = findings["bear_case"]
        if "key_catalysts" in findings:
            update_data["key_catalysts"] = findings["key_catalysts"]
        if "key_risks" in findings:
            update_data["key_risks"] = findings["key_risks"]
        if "target_price" in findings:
            update_data["target_price"] = findings["target_price"]
        if "conviction_level" in findings:
            update_data["conviction_level"] = ConvictionLevel(findings["conviction_level"])
        
        if update_data:
            await project_repo.update(UUID(project_id), **update_data)
            log.info(f"Updated research project {project_id}")


# =============================================================================
# Research Workflows
# =============================================================================

@flow(name="quick_research_workflow")
async def quick_research_workflow(
    ticker: str,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Quick research workflow for initial screening.
    
    Steps:
    1. Business overview
    2. Key metrics summary
    3. Quick risk assessment
    """
    log = get_run_logger()
    log.info(f"Starting quick research for {ticker}")
    
    # Phase 1: Business Overview
    overview_result = await dispatch_agent_task(
        agent_type="due_diligence_agent",
        prompt_name="business_overview_report",
        input_data={"ticker": ticker},
        priority="high"
    )
    
    # Phase 2: Quick Risk Assessment
    risk_result = await dispatch_agent_task(
        agent_type="due_diligence_agent",
        prompt_name="risk_assessment",
        input_data={"ticker": ticker},
        priority="normal"
    )
    
    # Aggregate results
    aggregated = aggregate_results([overview_result, risk_result])
    
    # Save findings if project_id provided
    if project_id and aggregated["successful"] > 0:
        findings = {
            "thesis_summary": overview_result.get("data", {}).get("investment_thesis_summary"),
            "key_risks": risk_result.get("data", {}).get("key_risks", [])
        }
        await save_research_findings(project_id, findings)
    
    # Create artifact
    await create_markdown_artifact(
        key=f"quick-research-{ticker}",
        markdown=f"""
# Quick Research: {ticker}

## Business Overview
{json.dumps(overview_result.get('data', {}), indent=2)}

## Risk Assessment
{json.dumps(risk_result.get('data', {}), indent=2)}
        """,
        description=f"Quick research summary for {ticker}"
    )
    
    return aggregated


@flow(name="standard_research_workflow")
async def standard_research_workflow(
    ticker: str,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Standard research workflow for detailed analysis.
    
    Steps:
    1. Business overview
    2. Industry analysis
    3. Financial analysis
    4. Competitive landscape
    5. Risk assessment
    6. Initial valuation
    """
    log = get_run_logger()
    log.info(f"Starting standard research for {ticker}")
    
    results = []
    
    # Phase 1: Business Understanding
    overview = await dispatch_agent_task(
        agent_type="due_diligence_agent",
        prompt_name="business_overview_report",
        input_data={"ticker": ticker}
    )
    results.append(overview)
    
    economics = await dispatch_agent_task(
        agent_type="due_diligence_agent",
        prompt_name="business_economics",
        input_data={"ticker": ticker}
    )
    results.append(economics)
    
    # Phase 2: Industry Analysis
    industry = await dispatch_agent_task(
        agent_type="due_diligence_agent",
        prompt_name="industry_overview",
        input_data={"ticker": ticker}
    )
    results.append(industry)
    
    competitive = await dispatch_agent_task(
        agent_type="due_diligence_agent",
        prompt_name="competitive_landscape",
        input_data={"ticker": ticker}
    )
    results.append(competitive)
    
    # Phase 3: Financial Analysis
    financials = await dispatch_agent_task(
        agent_type="due_diligence_agent",
        prompt_name="financial_statement_analysis",
        input_data={"ticker": ticker}
    )
    results.append(financials)
    
    # Phase 4: Risk Assessment
    risks = await dispatch_agent_task(
        agent_type="due_diligence_agent",
        prompt_name="risk_assessment",
        input_data={"ticker": ticker}
    )
    results.append(risks)
    
    # Phase 5: Valuation
    valuation = await dispatch_agent_task(
        agent_type="due_diligence_agent",
        prompt_name="dcf_valuation",
        input_data={"ticker": ticker}
    )
    results.append(valuation)
    
    # Aggregate
    aggregated = aggregate_results(results)
    
    # Save findings
    if project_id:
        findings = {
            "thesis_summary": overview.get("data", {}).get("investment_thesis_summary"),
            "bull_case": overview.get("data", {}).get("bull_case"),
            "bear_case": risks.get("data", {}).get("bear_case"),
            "key_risks": risks.get("data", {}).get("key_risks", []),
            "target_price": valuation.get("data", {}).get("per_share_value")
        }
        await save_research_findings(project_id, findings)
    
    return aggregated


@flow(name="deep_research_workflow")
async def deep_research_workflow(
    ticker: str,
    project_id: Optional[str] = None,
    custom_questions: List[str] = None
) -> Dict[str, Any]:
    """
    Deep research workflow for comprehensive analysis.
    
    Includes all standard research plus:
    - Management quality assessment
    - Earnings quality analysis
    - Bear case development
    - Multiple valuation approaches
    - Thesis synthesis
    """
    log = get_run_logger()
    log.info(f"Starting deep research for {ticker}")
    
    results = []
    
    # Run standard research first
    standard_results = await standard_research_workflow(ticker, project_id)
    results.extend(standard_results.get("results", []))
    
    # Additional deep dive analyses
    
    # Management Assessment
    management = await dispatch_agent_task(
        agent_type="due_diligence_agent",
        prompt_name="management_quality_assessment",
        input_data={"ticker": ticker}
    )
    results.append(management.get("data", {}))
    
    # Earnings Quality
    earnings = await dispatch_agent_task(
        agent_type="due_diligence_agent",
        prompt_name="earnings_quality",
        input_data={"ticker": ticker}
    )
    results.append(earnings.get("data", {}))
    
    # Bear Case
    bear_case = await dispatch_agent_task(
        agent_type="due_diligence_agent",
        prompt_name="bear_case_analysis",
        input_data={"ticker": ticker}
    )
    results.append(bear_case.get("data", {}))
    
    # Growth/Margin Drivers
    growth = await dispatch_agent_task(
        agent_type="due_diligence_agent",
        prompt_name="growth_margin_drivers",
        input_data={"ticker": ticker}
    )
    results.append(growth.get("data", {}))
    
    # Handle custom questions
    if custom_questions:
        for question in custom_questions:
            custom_result = await dispatch_agent_task(
                agent_type="due_diligence_agent",
                prompt_name="custom_analysis",
                input_data={"ticker": ticker, "question": question}
            )
            results.append(custom_result.get("data", {}))
    
    return {
        "ticker": ticker,
        "research_type": "deep",
        "results": results,
        "completed_at": datetime.utcnow().isoformat()
    }


# =============================================================================
# Idea Generation Workflows
# =============================================================================

@flow(name="thematic_idea_generation_workflow")
async def thematic_idea_generation_workflow(
    theme: str,
    sector: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate investment ideas based on a theme.
    
    Steps:
    1. Theme analysis with order effects
    2. Candidate screening
    3. Pure-play filtering
    4. Quick due diligence on top candidates
    """
    log = get_run_logger()
    log.info(f"Starting thematic idea generation for: {theme}")
    
    # Phase 1: Theme Analysis
    theme_analysis = await dispatch_agent_task(
        agent_type="idea_generation_agent",
        prompt_name="theme_order_effects",
        input_data={"theme": theme}
    )
    
    # Phase 2: Candidate Screening
    candidates = await dispatch_agent_task(
        agent_type="idea_generation_agent",
        prompt_name="thematic_candidate_screen",
        input_data={"theme": theme, "sector": sector}
    )
    
    # Phase 3: Pure-Play Filtering
    pure_plays = await dispatch_agent_task(
        agent_type="idea_generation_agent",
        prompt_name="pure_play_filter",
        input_data={
            "theme": theme,
            "candidates": candidates.get("data", {}).get("candidates", [])
        }
    )
    
    # Phase 4: Quick DD on top candidates
    top_candidates = pure_plays.get("data", {}).get("pure_plays", [])[:5]
    dd_results = []
    
    for candidate in top_candidates:
        ticker = candidate.get("ticker")
        if ticker:
            dd = await dispatch_agent_task(
                agent_type="due_diligence_agent",
                prompt_name="business_overview_report",
                input_data={"ticker": ticker},
                priority="normal"
            )
            dd_results.append({
                "ticker": ticker,
                "analysis": dd.get("data", {})
            })
    
    return {
        "theme": theme,
        "theme_analysis": theme_analysis.get("data", {}),
        "all_candidates": candidates.get("data", {}),
        "pure_plays": pure_plays.get("data", {}),
        "detailed_analysis": dd_results
    }


@flow(name="institutional_clustering_workflow")
async def institutional_clustering_workflow() -> Dict[str, Any]:
    """
    Identify stocks with institutional clustering.
    
    Steps:
    1. 13F clustering analysis
    2. Insider trading overlay
    3. Quick DD on top signals
    """
    log = get_run_logger()
    log.info("Starting institutional clustering analysis")
    
    # Phase 1: 13F Analysis
    clustering = await dispatch_agent_task(
        agent_type="idea_generation_agent",
        prompt_name="institutional_clustering_13f",
        input_data={}
    )
    
    # Phase 2: Insider Trading Overlay
    top_clusters = clustering.get("data", {}).get("clusters", [])[:10]
    insider_results = []
    
    for cluster in top_clusters:
        ticker = cluster.get("ticker")
        if ticker:
            insider = await dispatch_agent_task(
                agent_type="idea_generation_agent",
                prompt_name="insider_trading_analysis",
                input_data={"ticker": ticker}
            )
            insider_results.append({
                "ticker": ticker,
                "institutional": cluster,
                "insider": insider.get("data", {})
            })
    
    # Rank by combined signal strength
    ranked = sorted(
        insider_results,
        key=lambda x: (
            x["institutional"].get("concentration_score", 0) +
            (1 if x["insider"].get("signal_strength") == "strong_buy" else 0)
        ),
        reverse=True
    )
    
    return {
        "clustering_analysis": clustering.get("data", {}),
        "combined_signals": ranked,
        "top_ideas": ranked[:5]
    }


# =============================================================================
# Screening Workflows
# =============================================================================

@flow(name="value_screening_workflow")
async def value_screening_workflow(
    universe: str = "us_stocks",
    min_market_cap: float = 1_000_000_000
) -> Dict[str, Any]:
    """
    Screen for value opportunities.
    """
    log = get_run_logger()
    log.info("Starting value screening")
    
    # Define value criteria
    criteria = {
        "pe_ratio": {"max": 15},
        "pb_ratio": {"max": 2},
        "dividend_yield": {"min": 2},
        "debt_to_equity": {"max": 1},
        "roe": {"min": 10}
    }
    
    # Run screening
    screen_result = await dispatch_agent_task(
        agent_type="idea_generation_agent",
        prompt_name="value_screen",
        input_data={
            "criteria": criteria,
            "universe": universe,
            "min_market_cap": min_market_cap
        }
    )
    
    # Quick DD on top results
    top_results = screen_result.get("data", {}).get("results", [])[:10]
    dd_results = []
    
    for result in top_results:
        ticker = result.get("ticker")
        if ticker:
            dd = await dispatch_agent_task(
                agent_type="due_diligence_agent",
                prompt_name="business_overview_report",
                input_data={"ticker": ticker}
            )
            dd_results.append({
                "ticker": ticker,
                "screening_data": result,
                "analysis": dd.get("data", {})
            })
    
    # Save results
    async with get_session() as session:
        screener_repo = ScreenerResultRepository(session)
        for result in top_results:
            await screener_repo.create(
                screener_name="value_screen",
                screener_config=criteria,
                ticker=result.get("ticker"),
                company_name=result.get("company_name"),
                sector=result.get("sector"),
                overall_score=result.get("score", 0),
                scores_breakdown=result.get("scores", {}),
                ai_summary=result.get("summary")
            )
    
    return {
        "criteria": criteria,
        "total_results": len(top_results),
        "detailed_results": dd_results
    }


# =============================================================================
# Scheduled Workflows
# =============================================================================

@flow(name="daily_market_scan")
async def daily_market_scan() -> Dict[str, Any]:
    """
    Daily market scan for new opportunities.
    
    Runs:
    1. Institutional clustering update
    2. Insider trading signals
    3. Social sentiment scan
    4. Newsletter idea scan
    """
    log = get_run_logger()
    log.info("Starting daily market scan")
    
    results = {}
    
    # Institutional clustering
    clustering = await dispatch_agent_task(
        agent_type="idea_generation_agent",
        prompt_name="institutional_clustering_13f",
        input_data={}
    )
    results["institutional"] = clustering.get("data", {})
    
    # Social sentiment
    sentiment = await dispatch_agent_task(
        agent_type="idea_generation_agent",
        prompt_name="social_sentiment_scan",
        input_data={"platforms": ["twitter", "reddit", "stocktwits"]}
    )
    results["sentiment"] = sentiment.get("data", {})
    
    # Newsletter scan
    newsletters = await dispatch_agent_task(
        agent_type="idea_generation_agent",
        prompt_name="newsletter_idea_scraping",
        input_data={}
    )
    results["newsletters"] = newsletters.get("data", {})
    
    # Contrarian opportunities
    contrarian = await dispatch_agent_task(
        agent_type="idea_generation_agent",
        prompt_name="contrarian_opportunities",
        input_data={}
    )
    results["contrarian"] = contrarian.get("data", {})
    
    # Create daily report artifact
    await create_markdown_artifact(
        key=f"daily-scan-{datetime.utcnow().strftime('%Y-%m-%d')}",
        markdown=f"""
# Daily Market Scan - {datetime.utcnow().strftime('%Y-%m-%d')}

## Institutional Clustering Signals
{json.dumps(results.get('institutional', {}), indent=2)}

## Social Sentiment
{json.dumps(results.get('sentiment', {}), indent=2)}

## Newsletter Ideas
{json.dumps(results.get('newsletters', {}), indent=2)}

## Contrarian Opportunities
{json.dumps(results.get('contrarian', {}), indent=2)}
        """,
        description="Daily market scan results"
    )
    
    return results


# =============================================================================
# Workflow Runner
# =============================================================================

if __name__ == "__main__":
    # Example: Run a workflow
    import asyncio
    
    async def main():
        # Quick research example
        result = await quick_research_workflow("AAPL")
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())
