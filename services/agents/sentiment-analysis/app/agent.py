# =============================================================================
# Investment Idea Generation Agent
# =============================================================================
# Specialized agent for generating investment ideas from various sources
# =============================================================================

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
import structlog

import sys
sys.path.insert(0, "/app")

from shared.agents.base import BaseAgent, AgentTask, AgentResult, TaskPriority
from shared.llm.provider import get_llm_provider
from shared.clients.polygon_client import get_polygon_client
from shared.clients.fmp_client import get_fmp_client
from shared.clients.sec_client import get_sec_client
from shared.clients.redis_client import get_redis_client

logger = structlog.get_logger(__name__)


# =============================================================================
# Output Models
# =============================================================================

class InvestmentIdea(BaseModel):
    """A generated investment idea."""
    ticker: str
    company_name: str
    sector: str
    industry: str
    thesis_summary: str
    key_drivers: List[str]
    catalysts: List[str]
    risks: List[str]
    source: str
    confidence_score: float = Field(ge=0, le=1)
    time_horizon: str  # short, medium, long
    idea_type: str  # long, short, pair_trade


class ThematicAnalysis(BaseModel):
    """Analysis of a thematic investment opportunity."""
    theme: str
    description: str
    market_size: Optional[str] = None
    growth_rate: Optional[str] = None
    key_trends: List[str]
    first_order_effects: List[str]
    second_order_effects: List[str]
    third_order_effects: List[str]
    pure_play_candidates: List[Dict[str, Any]]
    diversified_exposure: List[Dict[str, Any]]


class InstitutionalCluster(BaseModel):
    """Institutional clustering analysis result."""
    ticker: str
    company_name: str
    top_holders: List[Dict[str, Any]]
    recent_activity: str  # accumulating, reducing, stable
    concentration_score: float
    smart_money_signal: str


class ScreeningResult(BaseModel):
    """Stock screening result."""
    ticker: str
    company_name: str
    sector: str
    scores: Dict[str, float]
    overall_score: float
    key_metrics: Dict[str, Any]
    recommendation: str


# =============================================================================
# Idea Generation Agent
# =============================================================================

class SentimentAnalysisAgent(BaseAgent):
    """
    Agent specialized in generating investment ideas.
    
    Capabilities:
    - Thematic idea generation
    - Newsletter and publication scanning
    - SEC 13F institutional clustering analysis
    - Insider trading pattern detection
    - Social sentiment analysis
    - Pure-play identification
    """
    
    SUPPORTED_PROMPTS = [
        "thematic_candidate_screen",
        "newsletter_idea_scraping",
        "niche_publication_scanner",
        "institutional_clustering_13f",
        "insider_trading_analysis",
        "theme_order_effects",
        "pure_play_filter",
        "deep_web_trend_scanner",
        "social_sentiment_scan",
        "contrarian_opportunities",
        "sector_thesis_stress_test"
    ]
    
    def __init__(self):
        super().__init__(agent_type="idea_generation_agent")
        self.polygon = get_polygon_client()
        self.fmp = get_fmp_client()
        self.sec = get_sec_client()
    
    def get_supported_prompts(self) -> List[str]:
        return self.SUPPORTED_PROMPTS
    
    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute an idea generation task."""
        start_time = datetime.utcnow()
        
        prompt_name = task.prompt_name
        input_data = task.input_data
        
        self.logger.info(
            "Executing idea generation task",
            prompt_name=prompt_name,
            input_data=input_data
        )
        
        try:
            # Route to appropriate handler
            if prompt_name == "thematic_candidate_screen":
                result = await self._thematic_candidate_screen(input_data)
            elif prompt_name == "theme_order_effects":
                result = await self._theme_order_effects(input_data)
            elif prompt_name == "institutional_clustering_13f":
                result = await self._institutional_clustering(input_data)
            elif prompt_name == "insider_trading_analysis":
                result = await self._insider_trading_analysis(input_data)
            elif prompt_name == "pure_play_filter":
                result = await self._pure_play_filter(input_data)
            elif prompt_name == "newsletter_idea_scraping":
                result = await self._newsletter_scanning(input_data)
            elif prompt_name == "social_sentiment_scan":
                result = await self._social_sentiment_scan(input_data)
            elif prompt_name == "contrarian_opportunities":
                result = await self._contrarian_opportunities(input_data)
            else:
                raise ValueError(f"Unsupported prompt: {prompt_name}")
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=True,
                data=result,
                execution_time_seconds=execution_time,
                tokens_used=result.get("tokens_used", 0),
                model_used=result.get("model_used", "")
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(
                "Task execution failed",
                error=str(e),
                exc_info=True
            )
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=False,
                error=str(e),
                execution_time_seconds=execution_time
            )
    
    # =========================================================================
    # Thematic Analysis
    # =========================================================================
    
    async def _thematic_candidate_screen(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Screen for investment candidates based on a theme."""
        theme = input_data.get("theme", "")
        sector = input_data.get("sector")
        min_market_cap = input_data.get("min_market_cap", 1_000_000_000)
        
        self.validate_input(input_data, ["theme"])
        
        # Build the prompt
        prompt = f"""You are a senior equity research analyst specializing in thematic investing.

THEME: {theme}
{f"SECTOR FOCUS: {sector}" if sector else ""}

Your task is to identify the most compelling investment candidates that benefit from this theme.

For each candidate, provide:
1. Company name and ticker
2. Why this company is well-positioned for the theme
3. Revenue exposure to the theme (% of total revenue)
4. Key competitive advantages
5. Potential catalysts
6. Main risks
7. Conviction level (1-10)

Consider:
- Pure-play vs. diversified exposure
- Market position and competitive moat
- Management track record in the space
- Valuation relative to growth
- Liquidity and market cap requirements

Provide 5-10 candidates ranked by conviction level.

Format your response as a JSON object with the following structure:
{{
    "theme_analysis": {{
        "description": "...",
        "market_size": "...",
        "growth_drivers": ["..."]
    }},
    "candidates": [
        {{
            "ticker": "...",
            "company_name": "...",
            "thesis": "...",
            "revenue_exposure": "...",
            "competitive_advantages": ["..."],
            "catalysts": ["..."],
            "risks": ["..."],
            "conviction_score": 8
        }}
    ]
}}"""

        system_prompt = """You are a world-class equity research analyst with deep expertise in thematic investing. 
You have access to comprehensive market data and can identify emerging trends before they become mainstream.
Always provide specific, actionable investment ideas backed by solid fundamental analysis."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5
        )
        
        # Parse the response
        import json
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"raw_response": response}
        
        result["tokens_used"] = tokens
        result["model_used"] = "default"
        
        return result
    
    async def _theme_order_effects(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze first, second, and third order effects of a theme."""
        theme = input_data.get("theme", "")
        
        self.validate_input(input_data, ["theme"])
        
        prompt = f"""You are analyzing the investment implications of the following theme/trend:

THEME: {theme}

Perform a comprehensive order-of-effects analysis:

**FIRST ORDER EFFECTS (Direct Impact)**
- Companies/sectors that directly benefit or suffer
- Immediate revenue/cost implications
- Obvious winners and losers

**SECOND ORDER EFFECTS (Indirect Impact)**
- Supply chain implications
- Adjacent industries affected
- Competitive dynamics shifts
- Consumer behavior changes

**THIRD ORDER EFFECTS (Non-Obvious Implications)**
- Long-term structural changes
- Unexpected beneficiaries
- Contrarian opportunities
- Regulatory/policy responses

For each order, identify:
1. Specific companies (with tickers) that could benefit
2. The mechanism of impact
3. Time horizon for the effect to materialize
4. Confidence level in the thesis

Format as JSON:
{{
    "theme": "{theme}",
    "first_order": {{
        "effects": ["..."],
        "beneficiaries": [{{"ticker": "...", "company": "...", "mechanism": "...", "confidence": "high/medium/low"}}]
    }},
    "second_order": {{
        "effects": ["..."],
        "beneficiaries": [...]
    }},
    "third_order": {{
        "effects": ["..."],
        "beneficiaries": [...]
    }},
    "contrarian_plays": [...]
}}"""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a strategic investment analyst known for identifying non-obvious investment opportunities.",
            temperature=0.6
        )
        
        import json
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"raw_response": response}
        
        result["tokens_used"] = tokens
        return result
    
    # =========================================================================
    # Institutional Analysis
    # =========================================================================
    
    async def _institutional_clustering(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze institutional holdings clustering from 13F filings."""
        focus_managers = input_data.get("managers", [])
        min_position_value = input_data.get("min_position_value", 10_000_000)
        
        # This would integrate with SEC 13F data
        # For now, use LLM to analyze the concept
        
        prompt = """You are analyzing institutional investor behavior from SEC 13F filings.

Identify stocks where multiple high-quality institutional investors have been accumulating positions.

Consider these "smart money" indicators:
1. Concentration of top hedge funds
2. Recent position increases
3. New positions from respected managers
4. Convergence of different investment styles
5. Insider buying alongside institutional accumulation

Provide analysis of:
1. Stocks with unusual institutional clustering
2. The quality of the institutional holders
3. Recent changes in positioning
4. Potential thesis behind the accumulation
5. Risk of crowded trade

Format as JSON with specific tickers and analysis."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are an expert in analyzing institutional investor behavior and 13F filings.",
            temperature=0.4
        )
        
        import json
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"raw_response": response}
        
        result["tokens_used"] = tokens
        return result
    
    async def _insider_trading_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze insider trading patterns from SEC Form 4 filings."""
        ticker = input_data.get("ticker")
        lookback_days = input_data.get("lookback_days", 90)
        
        # Fetch insider trading data if ticker provided
        insider_data = []
        if ticker:
            try:
                insider_trades = await self.fmp.get_insider_trading(ticker, limit=50)
                insider_data = [
                    {
                        "date": str(t.transaction_date),
                        "name": t.reporting_name,
                        "type": t.transaction_type,
                        "shares": t.securities_transacted,
                        "price": t.price
                    }
                    for t in insider_trades
                ]
            except Exception as e:
                self.logger.warning(f"Failed to fetch insider data: {e}")
        
        prompt = f"""Analyze insider trading patterns for investment signals.

{f"TICKER: {ticker}" if ticker else "MARKET-WIDE ANALYSIS"}
{f"INSIDER DATA: {insider_data}" if insider_data else ""}

Identify:
1. Unusual insider buying clusters
2. Significant purchases by executives (not just option exercises)
3. Pattern of multiple insiders buying
4. Timing relative to company events
5. Historical accuracy of insider signals for this company/sector

Provide:
- Summary of insider activity
- Signal strength (strong buy signal, moderate, weak, neutral, sell signal)
- Key transactions to highlight
- Recommended action

Format as JSON."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are an expert in analyzing insider trading patterns and their predictive value.",
            temperature=0.3
        )
        
        import json
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"raw_response": response}
        
        result["tokens_used"] = tokens
        result["insider_data"] = insider_data
        return result
    
    # =========================================================================
    # Pure Play Analysis
    # =========================================================================
    
    async def _pure_play_filter(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter and rank pure-play exposure to a theme."""
        theme = input_data.get("theme", "")
        candidates = input_data.get("candidates", [])
        min_revenue_exposure = input_data.get("min_revenue_exposure", 50)
        
        self.validate_input(input_data, ["theme"])
        
        prompt = f"""You are evaluating companies for pure-play exposure to:

THEME: {theme}
MINIMUM REVENUE EXPOSURE: {min_revenue_exposure}%
{f"CANDIDATES TO EVALUATE: {candidates}" if candidates else ""}

For each company, assess:
1. Revenue exposure to the theme (% of total)
2. Profit exposure (may differ from revenue)
3. Strategic commitment to the theme
4. Competitive position within the theme
5. Valuation premium/discount for pure-play status

Rank companies by:
- Pure-play score (higher = more focused exposure)
- Quality score (competitive position, management, financials)
- Value score (valuation relative to growth)

Identify:
- True pure-plays (>70% exposure)
- Focused players (50-70% exposure)
- Diversified exposure (<50% but meaningful)

Format as JSON with detailed scoring."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are an expert at identifying pure-play investment opportunities.",
            temperature=0.4
        )
        
        import json
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"raw_response": response}
        
        result["tokens_used"] = tokens
        return result
    
    # =========================================================================
    # Source Scanning
    # =========================================================================
    
    async def _newsletter_scanning(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scan investment newsletters for ideas."""
        sources = input_data.get("sources", [])
        focus_sectors = input_data.get("sectors", [])
        
        prompt = f"""You are scanning investment newsletters and publications for actionable ideas.

{f"FOCUS SECTORS: {focus_sectors}" if focus_sectors else ""}

Identify investment ideas from:
1. Prominent investment newsletters (Substack, etc.)
2. Hedge fund letters
3. Research publications
4. Industry expert commentary

For each idea found:
- Source and author credibility
- Core thesis summary
- Key data points supporting the thesis
- Potential catalysts mentioned
- Risks identified
- Your assessment of the idea quality

Prioritize:
- Non-consensus ideas
- Ideas with specific, verifiable catalysts
- Ideas from managers with strong track records

Format as JSON with source attribution."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a research analyst who synthesizes investment ideas from multiple sources.",
            temperature=0.5
        )
        
        import json
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"raw_response": response}
        
        result["tokens_used"] = tokens
        return result
    
    async def _social_sentiment_scan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scan social media for sentiment and emerging ideas."""
        platforms = input_data.get("platforms", ["twitter", "reddit", "stocktwits"])
        tickers = input_data.get("tickers", [])
        
        prompt = f"""Analyze social media sentiment for investment signals.

PLATFORMS: {platforms}
{f"TICKERS TO MONITOR: {tickers}" if tickers else "SCAN FOR EMERGING IDEAS"}

Identify:
1. Unusual volume of discussion
2. Sentiment shifts (bullish/bearish)
3. Emerging narratives
4. Retail vs. institutional sentiment divergence
5. Potential meme stock candidates
6. Contrarian opportunities (hated stocks)

For each signal:
- Platform and reach
- Sentiment score
- Key narratives
- Risk of sentiment-driven volatility
- Actionability for institutional investors

Format as JSON."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You analyze social media sentiment while filtering noise from signal.",
            temperature=0.5
        )
        
        import json
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"raw_response": response}
        
        result["tokens_used"] = tokens
        return result
    
    async def _contrarian_opportunities(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify contrarian investment opportunities."""
        sector = input_data.get("sector")
        
        prompt = f"""Identify contrarian investment opportunities.

{f"SECTOR FOCUS: {sector}" if sector else "MARKET-WIDE SCAN"}

Look for:
1. **Hated stocks** - Companies with extremely negative sentiment that may be overdone
2. **Fallen angels** - Quality companies that have fallen out of favor
3. **Turnaround situations** - Companies with improving fundamentals not yet recognized
4. **Sector rotations** - Out-of-favor sectors due for a comeback
5. **Short squeezes** - High short interest with improving fundamentals

For each opportunity:
- Why the market hates it
- Why the market may be wrong
- Catalysts for re-rating
- Downside risks if consensus is right
- Time horizon for thesis to play out
- Position sizing recommendation given risk

Format as JSON with conviction scores."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a contrarian investor who profits from market overreactions.",
            temperature=0.6
        )
        
        import json
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"raw_response": response}
        
        result["tokens_used"] = tokens
        return result


# =============================================================================
# Agent Runner
# =============================================================================

async def run_agent():
    """Run the idea generation agent as a service."""
    agent = IdeaGenerationAgent()
    redis = get_redis_client()
    await redis.connect()
    
    channel = f"investment-agents:tasks:idea_generation_agent"
    
    logger.info("Idea Generation Agent started, listening for tasks...")
    
    async def handle_message(channel: str, message: str):
        import json
        task_data = json.loads(message)
        task = AgentTask(**task_data)
        
        result = await agent.run(task)
        
        # Publish result
        result_channel = f"investment-agents:results:{task.task_id}"
        await redis.publish(result_channel, result.model_dump_json())
    
    await redis.subscribe([channel], handle_message)


if __name__ == "__main__":
    asyncio.run(run_agent())
