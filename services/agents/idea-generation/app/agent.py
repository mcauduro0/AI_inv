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
from shared.clients.data_service import get_data_service, DataService

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

class IdeaGenerationAgent(BaseAgent):
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
        self.data_service = get_data_service()
    
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
                # Use generic handler for database-loaded prompts
                result = await self._execute_from_database_prompt(prompt_name, input_data)
            
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
        """Screen for investment candidates based on a theme with REAL market data."""
        theme = input_data.get("theme", "")
        sector = input_data.get("sector")
        min_market_cap = input_data.get("min_market_cap", 1_000_000_000)
        
        self.validate_input(input_data, ["theme"])
        
        self.logger.info("Running thematic screen with real data", theme=theme, sector=sector)
        
        # Step 1: Screen stocks from FMP based on criteria
        screen_criteria = {
            "market_cap_more_than": min_market_cap,
            "limit": 100
        }
        if sector:
            screen_criteria["sector"] = sector
        
        try:
            screened_stocks = await self.data_service.screen_stocks(screen_criteria)
            self.logger.info(f"Screened {len(screened_stocks)} stocks")
        except Exception as e:
            self.logger.warning(f"Stock screening failed: {e}")
            screened_stocks = []
        
        # Step 2: Get detailed data for top candidates
        candidate_data = []
        for stock in screened_stocks[:20]:  # Analyze top 20
            ticker = stock.get("symbol")
            if ticker:
                try:
                    context = await self.data_service.get_company_context(ticker)
                    candidate_data.append({
                        "ticker": ticker,
                        "name": context.name,
                        "sector": context.sector,
                        "industry": context.industry,
                        "market_cap": context.market_cap,
                        "description": context.description[:300] if context.description else "",
                        "pe_ratio": context.pe_ratio,
                        "revenue_growth": context.revenue_growth,
                        "gross_margin": context.gross_margin,
                        "debt_to_equity": context.debt_to_equity,
                        "price_change_ytd": context.price_change_ytd,
                        "analyst_rating": context.analyst_rating
                    })
                except Exception as e:
                    self.logger.warning(f"Failed to get context for {ticker}: {e}")
        
        self.logger.info(f"Got detailed data for {len(candidate_data)} candidates")
        
        # Step 3: Use LLM to analyze theme fit with real data
        import json
        prompt = f"""You are a senior equity research analyst specializing in thematic investing.

THEME: {theme}
{f"SECTOR FOCUS: {sector}" if sector else ""}

I have screened the following companies with REAL financial data. Analyze each for theme relevance:

CANDIDATE COMPANIES (REAL DATA):
{json.dumps(candidate_data, indent=2)}

For each company that fits the theme "{theme}", provide:
1. Why this company is well-positioned for the theme
2. Estimated revenue exposure to the theme (% of total revenue)
3. Key competitive advantages
4. Potential catalysts
5. Main risks
6. Conviction level (1-10)

IMPORTANT: 
- Only include companies that genuinely benefit from this theme
- Use the actual financial data provided to support your analysis
- Reference specific metrics (PE ratio, revenue growth, margins) in your thesis
- Be selective - quality over quantity

Format your response as JSON:
{{
    "theme_analysis": {{
        "description": "Brief description of the theme",
        "market_size_estimate": "$X billion",
        "growth_drivers": ["driver1", "driver2"],
        "key_trends": ["trend1", "trend2"]
    }},
    "candidates": [
        {{
            "ticker": "SYMBOL",
            "company_name": "Name",
            "thesis": "Why this company benefits from the theme",
            "revenue_exposure_pct": 30,
            "competitive_advantages": ["advantage1", "advantage2"],
            "catalysts": ["catalyst1", "catalyst2"],
            "risks": ["risk1", "risk2"],
            "conviction_score": 8,
            "valuation_note": "Brief note on valuation using provided metrics"
        }}
    ],
    "excluded_companies": [
        {{
            "ticker": "SYMBOL",
            "reason": "Why excluded from theme"
        }}
    ]
}}"""

        system_prompt = """You are a world-class equity research analyst with deep expertise in thematic investing.
You analyze REAL financial data to identify companies that benefit from specific themes.
Always provide specific, actionable investment ideas backed by the actual data provided.
Be selective - only recommend companies with genuine theme exposure."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=4096
        )
        
        # Parse response
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"raw_response": response, "candidates": []}
        
        result["tokens_used"] = tokens
        result["model_used"] = "default"
        result["data_sources"] = ["FMP Stock Screener", "Company Profiles", "Financial Ratios"]
        result["screened_count"] = len(screened_stocks)
        result["analyzed_count"] = len(candidate_data)
        
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
        """Analyze institutional holdings clustering from 13F filings with REAL data."""
        sample_tickers = input_data.get("tickers", ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B", "JPM", "V"])
        
        self.logger.info("Running institutional clustering analysis with real data")
        
        # Fetch real institutional holdings data
        import json
        holdings_data = []
        for ticker in sample_tickers[:10]:
            try:
                holders = await self.fmp.get_institutional_holders(ticker)
                context = await self.data_service.get_company_context(ticker)
                
                top_holders = [
                    {"name": h.holder, "shares": h.shares, "change": h.change}
                    for h in holders[:10]
                ]
                
                holdings_data.append({
                    "ticker": ticker,
                    "name": context.name,
                    "market_cap": context.market_cap,
                    "institutional_ownership": context.institutional_ownership,
                    "top_holders": top_holders,
                    "recent_news": context.recent_news[:3],
                    "price_change_ytd": context.price_change_ytd,
                    "insider_buying": context.insider_buying,
                    "insider_selling": context.insider_selling
                })
            except Exception as e:
                self.logger.warning(f"Failed to get holdings for {ticker}: {e}")
        
        prompt = f"""You are an institutional investor analyst tracking smart money flows.

Analyze the following REAL institutional holdings data:

{json.dumps(holdings_data, indent=2)}

Identify:
1. Which stocks are seeing increased institutional buying
2. Common themes among top institutional picks
3. Potential crowded trades (high concentration risk)
4. Under-owned stocks that institutions might be accumulating
5. Stocks where institutions are reducing positions
6. Correlation between institutional and insider activity

Format as JSON:
{{
    "institutional_trends": {{
        "bullish_signals": ["signal1", "signal2"],
        "bearish_signals": ["signal1", "signal2"],
        "sector_preferences": ["sector1", "sector2"]
    }},
    "high_conviction_picks": [
        {{
            "ticker": "SYMBOL",
            "thesis": "Why institutions are buying",
            "key_holders": ["holder1", "holder2"],
            "conviction": 8
        }}
    ],
    "crowded_trades": [
        {{
            "ticker": "SYMBOL",
            "risk": "Why this is crowded"
        }}
    ],
    "under_owned_opportunities": [
        {{
            "ticker": "SYMBOL",
            "opportunity": "Why this could see increased institutional interest"
        }}
    ]
}}"""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are an expert at analyzing institutional investor behavior and 13F filings. Identify patterns in smart money positioning and provide actionable insights.",
            temperature=0.5,
            max_tokens=4096
        )
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"raw_response": response}
        
        result["tokens_used"] = tokens
        result["data_sources"] = ["FMP Institutional Holdings", "13F Filings"]
        result["stocks_analyzed"] = len(holdings_data)
        return result
    
    async def _insider_trading_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze insider trading patterns from SEC Form 4 filings with REAL data."""
        tickers = input_data.get("tickers", input_data.get("ticker"))
        if isinstance(tickers, str):
            tickers = [tickers]
        if not tickers:
            tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
        
        self.logger.info("Running insider trading analysis with real data", tickers=tickers)
        
        import json
        all_insider_data = []
        for ticker in tickers[:10]:
            try:
                trades = await self.fmp.get_insider_trading(ticker, limit=20)
                context = await self.data_service.get_company_context(ticker)
                
                recent_trades = [
                    {
                        "date": str(t.transaction_date),
                        "insider": t.reporting_name,
                        "type": t.transaction_type,
                        "shares": t.securities_transacted,
                        "price": t.price
                    }
                    for t in trades[:10]
                ]
                
                all_insider_data.append({
                    "ticker": ticker,
                    "name": context.name,
                    "current_price": context.current_price,
                    "market_cap": context.market_cap,
                    "insider_buying_count": context.insider_buying,
                    "insider_selling_count": context.insider_selling,
                    "recent_trades": recent_trades,
                    "price_change_ytd": context.price_change_ytd,
                    "analyst_rating": context.analyst_rating
                })
            except Exception as e:
                self.logger.warning(f"Failed to get insider data for {ticker}: {e}")
        
        prompt = f"""You are an expert at analyzing insider trading patterns for investment signals.

Analyze the following REAL insider trading data:

{json.dumps(all_insider_data, indent=2)}

Evaluate:
1. Significant insider buying (bullish signal)
2. Cluster buying by multiple insiders
3. Unusual selling patterns (potential warning)
4. Price levels where insiders are transacting vs current price
5. Quality of insiders (CEO/CFO vs. directors)

Format as JSON:
{{
    "bullish_signals": [
        {{
            "ticker": "SYMBOL",
            "signal": "Description of bullish insider activity",
            "key_insiders": ["insider1", "insider2"],
            "conviction": 8
        }}
    ],
    "bearish_signals": [
        {{
            "ticker": "SYMBOL",
            "signal": "Description of concerning insider activity",
            "risk_level": "high/medium/low"
        }}
    ],
    "actionable_ideas": [
        {{
            "ticker": "SYMBOL",
            "action": "buy/sell/hold",
            "thesis": "Why based on insider activity",
            "target_price": 100
        }}
    ],
    "summary": "Overall insider sentiment across analyzed stocks"
}}"""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are an expert in interpreting insider trading signals. Focus on cluster buying, CEO/CFO transactions, and unusual patterns. Distinguish between routine selling and concerning liquidation.",
            temperature=0.4,
            max_tokens=4096
        )
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"raw_response": response}
        
        result["tokens_used"] = tokens
        result["data_sources"] = ["FMP Insider Trading", "Form 4 Filings"]
        result["stocks_analyzed"] = len(all_insider_data)
        result["raw_data"] = all_insider_data
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
    
    async def _execute_from_database_prompt(
        self,
        prompt_name: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute analysis using a prompt loaded from the database.
        
        This allows the agent to handle any prompt defined in the database,
        not just the hardcoded ones.
        """
        import json
        from shared.prompts.loader import render_template
        
        self.logger.info(f"Executing database prompt: {prompt_name}")
        
        # Extract tickers from input data for real data fetching
        tickers = []
        if "ticker" in input_data:
            tickers.append(input_data["ticker"])
        if "tickers" in input_data:
            tickers.extend(input_data["tickers"])
        if "theme" in input_data:
            # For thematic analysis, we might want to screen for relevant stocks
            pass
        
        # Fetch real market data for any tickers
        market_data = {}
        for ticker in tickers[:10]:
            try:
                context = await self.data_service.get_company_context(ticker)
                market_data[ticker] = {
                    "name": context.name,
                    "sector": context.sector,
                    "industry": context.industry,
                    "market_cap": context.market_cap,
                    "current_price": context.current_price,
                    "price_change_ytd": context.price_change_ytd,
                    "pe_ratio": context.pe_ratio,
                    "revenue_growth": context.revenue_growth,
                    "gross_margin": context.gross_margin,
                    "operating_margin": context.operating_margin,
                    "roe": context.roe,
                    "debt_to_equity": context.debt_to_equity,
                    "analyst_rating": context.analyst_rating,
                    "recent_news": context.recent_news[:3] if context.recent_news else []
                }
            except Exception as e:
                self.logger.warning(f"Failed to fetch data for {ticker}: {e}")
        
        # Build a comprehensive prompt
        prompt = f"""You are a senior investment analyst performing {prompt_name.replace('_', ' ')} analysis.

ANALYSIS TYPE: {prompt_name}

INPUT PARAMETERS:
{json.dumps(input_data, indent=2)}

"""
        
        if market_data:
            prompt += f"""REAL MARKET DATA:
{json.dumps(market_data, indent=2)}

"""
        
        prompt += """Provide comprehensive analysis in JSON format with:
1. Key findings and insights
2. Specific recommendations with rationale
3. Risk factors and concerns
4. Confidence level (1-10)
5. Data sources used

Be specific and actionable. Use the real market data provided."""
        
        system_prompt = """You are a world-class equity research analyst with deep expertise in investment analysis.
You have access to real market data and provide specific, actionable recommendations.
Always format your response as valid JSON."""
        
        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4,
            max_tokens=4096
        )
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"analysis": response, "raw_response": True}
        
        result["tokens_used"] = tokens
        result["prompt_name"] = prompt_name
        result["data_sources"] = list(market_data.keys()) if market_data else []
        result["market_data"] = market_data
        
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
