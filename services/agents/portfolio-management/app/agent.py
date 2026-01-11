# =============================================================================
# Portfolio Management Agent
# =============================================================================
# Specialized agent for portfolio analysis, optimization, and risk management
# =============================================================================

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
import structlog
import json

import sys
sys.path.insert(0, "/app")

from shared.agents.base import BaseAgent, AgentTask, AgentResult, TaskPriority
from shared.llm.provider import get_llm_provider
from shared.clients.polygon_client import get_polygon_client
from shared.clients.fmp_client import get_fmp_client
from shared.clients.data_service import get_data_service

logger = structlog.get_logger(__name__)


# =============================================================================
# Portfolio Management Agent
# =============================================================================

class PortfolioManagementAgent(BaseAgent):
    """
    Agent specialized in portfolio analysis and optimization.
    
    Capabilities:
    - Portfolio risk analysis
    - Position sizing recommendations
    - Correlation analysis
    - Rebalancing suggestions
    - Sector/factor exposure analysis
    """
    
    SUPPORTED_PROMPTS = [
        "portfolio_risk_analysis",
        "position_sizing",
        "correlation_analysis",
        "rebalancing_recommendation",
        "sector_exposure",
        "factor_exposure",
        "drawdown_analysis",
        "portfolio_optimization"
    ]
    
    def __init__(self):
        super().__init__(agent_type="portfolio_management_agent")
        self.polygon = get_polygon_client()
        self.fmp = get_fmp_client()
        self.data_service = get_data_service()
    
    def get_supported_prompts(self) -> List[str]:
        return self.SUPPORTED_PROMPTS
    
    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute a portfolio management task."""
        start_time = datetime.utcnow()
        
        prompt_name = task.prompt_name
        input_data = task.input_data
        
        self.logger.info(
            "Executing portfolio management task",
            prompt_name=prompt_name
        )
        
        try:
            if prompt_name == "portfolio_risk_analysis":
                result = await self._portfolio_risk_analysis(input_data)
            elif prompt_name == "position_sizing":
                result = await self._position_sizing(input_data)
            elif prompt_name == "correlation_analysis":
                result = await self._correlation_analysis(input_data)
            elif prompt_name == "rebalancing_recommendation":
                result = await self._rebalancing_recommendation(input_data)
            elif prompt_name == "sector_exposure":
                result = await self._sector_exposure(input_data)
            else:
                result = await self._generic_portfolio_analysis(prompt_name, input_data)
            
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
            self.logger.error("Task execution failed", error=str(e), exc_info=True)
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=False,
                error=str(e),
                execution_time_seconds=execution_time
            )
    
    async def _portfolio_risk_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio risk with REAL market data."""
        holdings = input_data.get("holdings", [])
        
        if not holdings:
            # Use sample portfolio for demonstration
            holdings = [
                {"ticker": "AAPL", "weight": 0.15},
                {"ticker": "MSFT", "weight": 0.12},
                {"ticker": "GOOGL", "weight": 0.10},
                {"ticker": "AMZN", "weight": 0.10},
                {"ticker": "NVDA", "weight": 0.08},
                {"ticker": "JPM", "weight": 0.08},
                {"ticker": "V", "weight": 0.07},
                {"ticker": "JNJ", "weight": 0.07},
                {"ticker": "XOM", "weight": 0.06},
                {"ticker": "PG", "weight": 0.05}
            ]
        
        self.logger.info("Running portfolio risk analysis with real data", num_holdings=len(holdings))
        
        # Fetch real data for each holding
        portfolio_data = []
        for holding in holdings[:15]:  # Limit to 15 positions
            ticker = holding.get("ticker")
            weight = holding.get("weight", 0)
            
            try:
                context = await self.data_service.get_company_context(ticker)
                portfolio_data.append({
                    "ticker": ticker,
                    "name": context.name,
                    "weight_pct": weight * 100,
                    "sector": context.sector,
                    "industry": context.industry,
                    "market_cap": context.market_cap,
                    "beta": 1.0,  # Would need to calculate
                    "pe_ratio": context.pe_ratio,
                    "dividend_yield": context.dividend_yield,
                    "price_change_ytd": context.price_change_ytd,
                    "volatility_52w": abs(context.fifty_two_week_high - context.fifty_two_week_low) / context.current_price * 100 if context.current_price else 0,
                    "debt_to_equity": context.debt_to_equity
                })
            except Exception as e:
                self.logger.warning(f"Failed to get data for {ticker}: {e}")
        
        prompt = f"""You are a portfolio risk analyst evaluating a portfolio using REAL market data.

PORTFOLIO HOLDINGS (REAL DATA):
{json.dumps(portfolio_data, indent=2)}

Analyze the portfolio for:

1. **CONCENTRATION RISK**
   - Single stock concentration
   - Sector concentration
   - Geographic concentration
   - Factor concentration

2. **MARKET RISK**
   - Overall portfolio beta
   - Sensitivity to market movements
   - Correlation to major indices

3. **SECTOR RISK**
   - Sector allocation breakdown
   - Over/underweight vs benchmark
   - Cyclical vs defensive mix

4. **VALUATION RISK**
   - Weighted average P/E
   - Expensive vs cheap positions
   - Valuation dispersion

5. **QUALITY METRICS**
   - Weighted average debt/equity
   - Dividend coverage
   - Earnings quality

6. **RECOMMENDATIONS**
   - Key risks to address
   - Suggested rebalancing
   - Hedging strategies

Format as JSON:
{{
    "risk_summary": {{
        "overall_risk_score": 7,
        "risk_level": "moderate/high/low",
        "key_concerns": ["concern1", "concern2"]
    }},
    "concentration_analysis": {{
        "top_5_weight": 55,
        "hhi_index": 0.12,
        "sector_concentration": {{"Technology": 45, "Financials": 15}}
    }},
    "risk_metrics": {{
        "estimated_beta": 1.1,
        "weighted_pe": 25,
        "weighted_debt_equity": 0.8
    }},
    "recommendations": [
        {{
            "action": "Reduce concentration in X",
            "rationale": "Why",
            "priority": "high/medium/low"
        }}
    ]
}}"""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a professional portfolio risk analyst. Analyze the portfolio using the real data provided and give specific, actionable recommendations.",
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
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        result["data_sources"] = ["FMP Company Profiles", "Market Data"]
        result["holdings_analyzed"] = len(portfolio_data)
        result["portfolio_data"] = portfolio_data
        return result
    
    async def _position_sizing(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal position sizes based on risk parameters."""
        ticker = input_data.get("ticker", "AAPL")
        portfolio_value = input_data.get("portfolio_value", 100000)
        risk_tolerance = input_data.get("risk_tolerance", "moderate")
        max_position_pct = input_data.get("max_position_pct", 10)
        
        self.logger.info("Calculating position size with real data", ticker=ticker)
        
        # Get real data for the stock
        context = await self.data_service.get_company_context(ticker)
        
        stock_data = {
            "ticker": ticker,
            "name": context.name,
            "current_price": context.current_price,
            "market_cap": context.market_cap,
            "pe_ratio": context.pe_ratio,
            "volatility_range": abs(context.fifty_two_week_high - context.fifty_two_week_low) / context.current_price * 100 if context.current_price else 0,
            "avg_volume": context.avg_volume,
            "sector": context.sector,
            "analyst_rating": context.analyst_rating
        }
        
        prompt = f"""You are a portfolio manager calculating optimal position size.

STOCK DATA (REAL):
{json.dumps(stock_data, indent=2)}

PORTFOLIO PARAMETERS:
- Portfolio Value: ${portfolio_value:,}
- Risk Tolerance: {risk_tolerance}
- Max Position Size: {max_position_pct}%

Calculate:
1. Recommended position size (% of portfolio)
2. Dollar amount to invest
3. Number of shares
4. Risk-adjusted rationale
5. Entry strategy (all at once vs. scaling in)

Consider:
- Stock volatility
- Liquidity (can you exit easily?)
- Conviction level based on fundamentals
- Portfolio diversification needs

Format as JSON:
{{
    "recommendation": {{
        "position_size_pct": 5.0,
        "dollar_amount": 5000,
        "shares": 30,
        "entry_strategy": "Scale in over 3 tranches"
    }},
    "rationale": {{
        "volatility_assessment": "...",
        "liquidity_assessment": "...",
        "conviction_level": "high/medium/low",
        "key_factors": ["factor1", "factor2"]
    }},
    "risk_management": {{
        "stop_loss_pct": 10,
        "stop_loss_price": 150,
        "take_profit_levels": [{{price: 180, sell_pct: 25}}]
    }}
}}"""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a quantitative portfolio manager specializing in position sizing and risk management.",
            temperature=0.3,
            max_tokens=2048
        )
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        result["stock_data"] = stock_data
        return result
    
    async def _correlation_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze correlations between portfolio holdings."""
        tickers = input_data.get("tickers", ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"])
        
        self.logger.info("Running correlation analysis", tickers=tickers)
        
        # Get data for all tickers
        holdings_data = []
        for ticker in tickers[:10]:
            try:
                context = await self.data_service.get_company_context(ticker)
                holdings_data.append({
                    "ticker": ticker,
                    "name": context.name,
                    "sector": context.sector,
                    "industry": context.industry,
                    "price_change_ytd": context.price_change_ytd,
                    "market_cap": context.market_cap
                })
            except Exception as e:
                self.logger.warning(f"Failed to get data for {ticker}: {e}")
        
        prompt = f"""Analyze the correlation characteristics of these holdings:

HOLDINGS DATA:
{json.dumps(holdings_data, indent=2)}

Provide:
1. Expected correlation matrix (qualitative assessment)
2. Diversification score
3. Common risk factors
4. Suggestions for reducing correlation

Format as JSON with correlation insights and recommendations."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a quantitative analyst specializing in portfolio correlation and diversification.",
            temperature=0.4,
            max_tokens=2048
        )
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        result["holdings_data"] = holdings_data
        return result
    
    async def _rebalancing_recommendation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rebalancing recommendations."""
        current_holdings = input_data.get("current_holdings", [])
        target_allocation = input_data.get("target_allocation", {})
        
        if not current_holdings:
            current_holdings = [
                {"ticker": "AAPL", "current_weight": 0.18, "target_weight": 0.12},
                {"ticker": "MSFT", "current_weight": 0.15, "target_weight": 0.12},
                {"ticker": "GOOGL", "current_weight": 0.08, "target_weight": 0.10},
                {"ticker": "JPM", "current_weight": 0.05, "target_weight": 0.08}
            ]
        
        # Enrich with real data
        enriched_holdings = []
        for h in current_holdings[:10]:
            try:
                context = await self.data_service.get_company_context(h["ticker"])
                enriched_holdings.append({
                    **h,
                    "name": context.name,
                    "current_price": context.current_price,
                    "price_change_ytd": context.price_change_ytd,
                    "pe_ratio": context.pe_ratio
                })
            except:
                enriched_holdings.append(h)
        
        prompt = f"""Generate rebalancing recommendations for this portfolio:

CURRENT VS TARGET ALLOCATIONS:
{json.dumps(enriched_holdings, indent=2)}

Provide:
1. Specific trades to execute
2. Tax-efficient rebalancing strategy
3. Priority order for trades
4. Market timing considerations

Format as JSON with specific trade recommendations."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a portfolio manager specializing in tax-efficient rebalancing strategies.",
            temperature=0.3,
            max_tokens=2048
        )
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        return result
    
    async def _sector_exposure(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sector exposure of portfolio."""
        holdings = input_data.get("holdings", [
            {"ticker": "AAPL", "weight": 0.15},
            {"ticker": "MSFT", "weight": 0.12},
            {"ticker": "JPM", "weight": 0.10},
            {"ticker": "XOM", "weight": 0.08},
            {"ticker": "JNJ", "weight": 0.08}
        ])
        
        # Get sector data for each holding
        sector_data = []
        for h in holdings[:15]:
            try:
                context = await self.data_service.get_company_context(h["ticker"])
                sector_data.append({
                    "ticker": h["ticker"],
                    "weight": h["weight"],
                    "sector": context.sector,
                    "industry": context.industry
                })
            except:
                pass
        
        prompt = f"""Analyze the sector exposure of this portfolio:

HOLDINGS BY SECTOR:
{json.dumps(sector_data, indent=2)}

Provide:
1. Sector allocation breakdown
2. Comparison to S&P 500 weights
3. Over/underweight analysis
4. Sector rotation recommendations

Format as JSON."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a sector strategist analyzing portfolio allocations.",
            temperature=0.4,
            max_tokens=2048
        )
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        result["sector_data"] = sector_data
        return result
    
    async def _generic_portfolio_analysis(self, prompt_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic portfolio analysis handler."""
        prompt = f"""Perform {prompt_name.replace('_', ' ')} analysis.

Input: {json.dumps(input_data, indent=2)}

Provide comprehensive analysis in JSON format."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a portfolio management expert.",
            temperature=0.4,
            max_tokens=2048
        )
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        return result
