# =============================================================================
# Sentiment Analysis Agent
# =============================================================================
# Specialized agent for market and stock sentiment analysis
# =============================================================================

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import structlog
import json
import sys
sys.path.insert(0, "/app")

from shared.agents.base import BaseAgent, AgentTask, AgentResult
from shared.llm.provider import get_llm_provider
from shared.clients.polygon_client import get_polygon_client
from shared.clients.fmp_client import get_fmp_client
from shared.clients.data_service import get_data_service

logger = structlog.get_logger(__name__)


class SentimentAnalysisAgent(BaseAgent):
    """Agent specialized in sentiment analysis."""
    
    SUPPORTED_PROMPTS = [
        "stock_sentiment_analysis",
        "market_sentiment",
        "social_media_sentiment",
        "news_sentiment",
        "analyst_sentiment"
    ]
    
    def __init__(self):
        super().__init__(agent_type="sentiment_analysis_agent")
        self.polygon = get_polygon_client()
        self.fmp = get_fmp_client()
        self.data_service = get_data_service()
    
    def get_supported_prompts(self) -> List[str]:
        return self.SUPPORTED_PROMPTS
    
    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute a sentiment analysis task."""
        start_time = datetime.utcnow()
        prompt_name = task.prompt_name
        input_data = task.input_data
        
        self.logger.info("Executing sentiment analysis task", prompt_name=prompt_name)
        
        try:
            if prompt_name == "stock_sentiment_analysis":
                result = await self._stock_sentiment_analysis(input_data)
            elif prompt_name == "market_sentiment":
                result = await self._market_sentiment(input_data)
            else:
                result = await self._generic_sentiment_analysis(prompt_name, input_data)
            
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
    
    async def _stock_sentiment_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment for a specific stock using REAL data."""
        ticker = input_data.get("ticker", "AAPL")
        
        self.logger.info("Running stock sentiment analysis", ticker=ticker)
        
        # Get company context with news
        context = await self.data_service.get_company_context(ticker)
        
        stock_data = {
            "ticker": ticker,
            "name": context.name,
            "sector": context.sector,
            "current_price": context.current_price,
            "price_change_1d": context.price_change_1d,
            "price_change_ytd": context.price_change_ytd,
            "analyst_rating": context.analyst_rating,
            "price_target": context.price_target,
            "num_analysts": context.num_analysts,
            "insider_buying": context.insider_buying,
            "insider_selling": context.insider_selling,
            "recent_news": context.recent_news[:5] if context.recent_news else []
        }
        
        prompt = f"""Analyze sentiment for {ticker}.

STOCK DATA (REAL):
{json.dumps(stock_data, indent=2)}

Analyze:
1. **ANALYST SENTIMENT**
   - Consensus rating interpretation
   - Price target vs current price
   - Rating changes trend

2. **INSIDER SENTIMENT**
   - Buying vs selling activity
   - Signal interpretation

3. **NEWS SENTIMENT**
   - Recent news tone
   - Key themes
   - Potential catalysts

4. **TECHNICAL SENTIMENT**
   - Price momentum
   - Trend analysis

5. **OVERALL SENTIMENT SCORE**
   - Bullish/Bearish/Neutral
   - Confidence level
   - Key drivers

Format as JSON:
{{
    "overall_sentiment": {{
        "score": 7,
        "direction": "bullish/bearish/neutral",
        "confidence": 0.75
    }},
    "analyst_sentiment": {{
        "rating": "buy/hold/sell",
        "upside_potential": 15,
        "trend": "improving/stable/deteriorating"
    }},
    "insider_sentiment": {{
        "signal": "bullish/bearish/neutral",
        "recent_activity": "description"
    }},
    "news_sentiment": {{
        "tone": "positive/negative/neutral",
        "key_themes": ["theme1"],
        "catalysts": ["catalyst1"]
    }},
    "recommendation": {{
        "action": "buy/hold/sell",
        "rationale": "explanation"
    }}
}}"""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a sentiment analyst evaluating stock sentiment from multiple data sources.",
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
        result["stock_data"] = stock_data
        result["data_sources"] = ["Analyst Ratings", "Insider Activity", "News"]
        return result
    
    async def _market_sentiment(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall market sentiment."""
        self.logger.info("Running market sentiment analysis")
        
        # Get market indicators
        sentiment_indicators = [
            {"ticker": "SPY", "represents": "S&P 500"},
            {"ticker": "VIX", "represents": "Volatility Index"},
            {"ticker": "TLT", "represents": "Treasury Bonds"},
            {"ticker": "HYG", "represents": "High Yield Credit"},
            {"ticker": "GLD", "represents": "Gold (Safe Haven)"}
        ]
        
        market_data = []
        for ind in sentiment_indicators:
            try:
                context = await self.data_service.get_company_context(ind["ticker"])
                market_data.append({
                    "indicator": ind["represents"],
                    "ticker": ind["ticker"],
                    "price_change_1d": context.price_change_1d,
                    "price_change_ytd": context.price_change_ytd
                })
            except:
                pass
        
        prompt = f"""Analyze overall market sentiment:

MARKET INDICATORS (REAL DATA):
{json.dumps(market_data, indent=2)}

Provide:
1. Overall market sentiment (fear/greed scale)
2. Risk appetite assessment
3. Key sentiment drivers
4. Contrarian signals
5. Positioning recommendations

Format as JSON."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a market sentiment analyst.",
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
        result["market_data"] = market_data
        return result
    
    async def _generic_sentiment_analysis(self, prompt_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic sentiment analysis handler."""
        prompt = f"""Perform {prompt_name.replace('_', ' ')} analysis.
Input: {json.dumps(input_data, indent=2)}
Provide comprehensive sentiment analysis in JSON format."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a sentiment analyst.",
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
