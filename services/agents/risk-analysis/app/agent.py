# =============================================================================
# Risk Analysis Agent
# =============================================================================
# Specialized agent for investment risk analysis and assessment
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


class RiskAnalysisAgent(BaseAgent):
    """Agent specialized in investment risk analysis."""
    
    SUPPORTED_PROMPTS = [
        "company_risk_assessment",
        "portfolio_var_analysis",
        "stress_test",
        "tail_risk_analysis",
        "liquidity_risk"
    ]
    
    def __init__(self):
        super().__init__(agent_type="risk_analysis_agent")
        self.polygon = get_polygon_client()
        self.fmp = get_fmp_client()
        self.data_service = get_data_service()
    
    def get_supported_prompts(self) -> List[str]:
        return self.SUPPORTED_PROMPTS
    
    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute a risk analysis task."""
        start_time = datetime.utcnow()
        prompt_name = task.prompt_name
        input_data = task.input_data
        
        self.logger.info("Executing risk analysis task", prompt_name=prompt_name)
        
        try:
            if prompt_name == "company_risk_assessment":
                result = await self._company_risk_assessment(input_data)
            elif prompt_name == "stress_test":
                result = await self._stress_test(input_data)
            else:
                result = await self._generic_risk_analysis(prompt_name, input_data)
            
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
    
    async def _company_risk_assessment(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess company-specific risks with REAL data."""
        ticker = input_data.get("ticker", "AAPL")
        
        self.logger.info("Running company risk assessment", ticker=ticker)
        
        # Get comprehensive company data
        context = await self.data_service.get_company_context(ticker)
        
        company_data = {
            "ticker": ticker,
            "name": context.name,
            "sector": context.sector,
            "industry": context.industry,
            "market_cap": context.market_cap,
            "debt_to_equity": context.debt_to_equity,
            "current_ratio": context.current_ratio,
            "pe_ratio": context.pe_ratio,
            "revenue_growth": context.revenue_growth,
            "gross_margin": context.gross_margin,
            "operating_margin": context.operating_margin,
            "roe": context.roe,
            "price_change_ytd": context.price_change_ytd,
            "52w_high": context.fifty_two_week_high,
            "52w_low": context.fifty_two_week_low,
            "current_price": context.current_price,
            "analyst_rating": context.analyst_rating
        }
        
        prompt = f"""Perform comprehensive risk assessment for {ticker}.

COMPANY DATA (REAL):
{json.dumps(company_data, indent=2)}

Analyze:
1. **FINANCIAL RISK**
   - Leverage and debt coverage
   - Liquidity position
   - Cash flow stability

2. **BUSINESS RISK**
   - Competitive position
   - Customer concentration
   - Regulatory exposure

3. **MARKET RISK**
   - Valuation risk
   - Volatility assessment
   - Correlation to market

4. **OPERATIONAL RISK**
   - Margin sustainability
   - Execution challenges
   - Key person risk

Format as JSON:
{{
    "overall_risk_score": 6,
    "risk_level": "moderate",
    "financial_risk": {{
        "score": 5,
        "concerns": ["concern1"],
        "mitigants": ["mitigant1"]
    }},
    "business_risk": {{
        "score": 6,
        "concerns": ["concern1"],
        "mitigants": ["mitigant1"]
    }},
    "market_risk": {{
        "score": 7,
        "concerns": ["concern1"]
    }},
    "key_risks": ["risk1", "risk2"],
    "risk_mitigation_recommendations": ["rec1", "rec2"]
}}"""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a risk analyst assessing investment risks using real financial data.",
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
        result["company_data"] = company_data
        result["data_sources"] = ["FMP Company Profile", "Financial Ratios"]
        return result
    
    async def _stress_test(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform stress test on portfolio or position."""
        tickers = input_data.get("tickers", ["AAPL", "MSFT", "GOOGL"])
        
        # Get data for stress test
        holdings_data = []
        for ticker in tickers[:10]:
            try:
                context = await self.data_service.get_company_context(ticker)
                holdings_data.append({
                    "ticker": ticker,
                    "name": context.name,
                    "sector": context.sector,
                    "current_price": context.current_price,
                    "pe_ratio": context.pe_ratio,
                    "debt_to_equity": context.debt_to_equity,
                    "52w_range_pct": (context.fifty_two_week_high - context.fifty_two_week_low) / context.current_price * 100 if context.current_price else 0
                })
            except:
                pass
        
        prompt = f"""Perform stress test analysis on these holdings:

HOLDINGS DATA (REAL):
{json.dumps(holdings_data, indent=2)}

Stress scenarios to analyze:
1. Market crash (-20% S&P 500)
2. Interest rate spike (+200bps)
3. Recession scenario
4. Sector rotation

For each scenario, estimate:
- Expected loss
- Most vulnerable positions
- Hedging recommendations

Format as JSON."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a risk manager performing stress tests.",
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
        result["holdings_data"] = holdings_data
        return result
    
    async def _generic_risk_analysis(self, prompt_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic risk analysis handler."""
        prompt = f"""Perform {prompt_name.replace('_', ' ')} analysis.
Input: {json.dumps(input_data, indent=2)}
Provide comprehensive risk analysis in JSON format."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a risk analyst.",
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
