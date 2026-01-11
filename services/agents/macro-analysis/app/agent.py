# =============================================================================
# Macro Analysis Agent
# =============================================================================
# Specialized agent for macroeconomic analysis and market regime classification
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


class MacroAnalysisAgent(BaseAgent):
    """
    Agent specialized in macroeconomic analysis.
    
    Capabilities:
    - Market regime classification
    - Economic indicator analysis
    - Interest rate impact assessment
    - Global macro themes
    """
    
    SUPPORTED_PROMPTS = [
        "market_regime_classification",
        "economic_indicator_analysis",
        "interest_rate_impact",
        "global_macro_themes",
        "recession_probability"
    ]
    
    def __init__(self):
        super().__init__(agent_type="macro_analysis_agent")
        self.polygon = get_polygon_client()
        self.fmp = get_fmp_client()
        self.data_service = get_data_service()
    
    def get_supported_prompts(self) -> List[str]:
        return self.SUPPORTED_PROMPTS
    
    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute a macro analysis task."""
        start_time = datetime.utcnow()
        prompt_name = task.prompt_name
        input_data = task.input_data
        
        self.logger.info("Executing macro analysis task", prompt_name=prompt_name)
        
        try:
            if prompt_name == "market_regime_classification":
                result = await self._market_regime_classification(input_data)
            elif prompt_name == "economic_indicator_analysis":
                result = await self._economic_indicator_analysis(input_data)
            else:
                result = await self._generic_macro_analysis(prompt_name, input_data)
            
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
    
    async def _market_regime_classification(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify current market regime using REAL market data."""
        self.logger.info("Running market regime classification with real data")
        
        # Fetch real market data
        market_tickers = ["SPY", "QQQ", "IWM", "DIA", "TLT", "GLD"]
        market_data = []
        
        for ticker in market_tickers:
            try:
                context = await self.data_service.get_company_context(ticker)
                market_data.append({
                    "ticker": ticker,
                    "name": context.name,
                    "price": context.current_price,
                    "change_ytd": context.price_change_ytd,
                    "52w_high": context.fifty_two_week_high,
                    "52w_low": context.fifty_two_week_low
                })
            except Exception as e:
                self.logger.warning(f"Failed to get data for {ticker}: {e}")
        
        # Get sector performance
        sector_etfs = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLP", "XLU", "XLY"]
        sector_data = []
        
        for etf in sector_etfs:
            try:
                context = await self.data_service.get_company_context(etf)
                sector_data.append({
                    "sector_etf": etf,
                    "price_change_ytd": context.price_change_ytd
                })
            except:
                pass
        
        prompt = f"""You are a macro strategist classifying the current market regime.

MARKET DATA (REAL):
{json.dumps(market_data, indent=2)}

SECTOR PERFORMANCE (REAL):
{json.dumps(sector_data, indent=2)}

Classify the current market regime and provide positioning recommendations.

Format as JSON:
{{
    "regime_classification": {{
        "primary_regime": "Bull Market - Mid Cycle",
        "risk_appetite": "risk-on/risk-off",
        "confidence": 0.75
    }},
    "market_conditions": {{
        "trend": "uptrend/downtrend/sideways",
        "volatility": "low/normal/elevated",
        "breadth": "strong/moderate/weak"
    }},
    "sector_analysis": {{
        "leaders": ["sector1"],
        "laggards": ["sector1"]
    }},
    "positioning": {{
        "equity_allocation": "overweight/neutral/underweight",
        "sector_tilts": {{"Technology": "overweight"}}
    }}
}}"""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a macro strategist analyzing real market data.",
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
        result["data_sources"] = ["Market ETFs", "Sector ETFs"]
        result["market_data"] = market_data
        return result
    
    async def _economic_indicator_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze economic indicators using market proxies."""
        self.logger.info("Running economic indicator analysis")
        
        economic_proxies = [
            {"ticker": "SPY", "represents": "Equity Market"},
            {"ticker": "TLT", "represents": "Interest Rates"},
            {"ticker": "HYG", "represents": "Credit Conditions"},
            {"ticker": "XLI", "represents": "Industrial Activity"},
            {"ticker": "GLD", "represents": "Inflation Hedge"}
        ]
        
        indicator_data = []
        for proxy in economic_proxies:
            try:
                context = await self.data_service.get_company_context(proxy["ticker"])
                indicator_data.append({
                    "indicator": proxy["represents"],
                    "ticker": proxy["ticker"],
                    "price_change_ytd": context.price_change_ytd
                })
            except:
                pass
        
        prompt = f"""Analyze economic conditions based on market indicators:

MARKET-BASED INDICATORS (REAL DATA):
{json.dumps(indicator_data, indent=2)}

Provide economic outlook and investment implications in JSON format."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a chief economist analyzing market-based indicators.",
            temperature=0.4,
            max_tokens=3000
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
        result["indicator_data"] = indicator_data
        return result
    
    async def _generic_macro_analysis(self, prompt_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic macro analysis handler."""
        prompt = f"""Perform {prompt_name.replace('_', ' ')} analysis.
Input: {json.dumps(input_data, indent=2)}
Provide comprehensive analysis in JSON format."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a macro economist.",
            temperature=0.4,
            max_tokens=3000
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
