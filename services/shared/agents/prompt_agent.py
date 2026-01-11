# =============================================================================
# Prompt-Driven Agent Base Class
# =============================================================================
# Base class for agents that load prompts from database and use real data
# =============================================================================

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import structlog

from .base import BaseAgent, AgentTask, AgentResult, TaskPriority
from shared.clients.data_service import get_data_service, DataService
from shared.prompts.loader import render_template

logger = structlog.get_logger(__name__)


class PromptDrivenAgent(BaseAgent):
    """
    Base class for agents that use database prompts and real market data.
    
    This class provides:
    1. Automatic prompt loading from database
    2. Real data fetching from market APIs
    3. Dynamic prompt rendering with actual data
    4. Consistent result formatting
    """
    
    # Override in subclass
    AGENT_CATEGORY = "general"  # idea_generation, due_diligence, portfolio_management, etc.
    
    def __init__(self, agent_type: str):
        super().__init__(agent_type=agent_type)
        self.data_service = get_data_service()
        self._prompt_cache: Dict[str, Dict[str, Any]] = {}
    
    async def execute_with_prompt(
        self,
        prompt_template: str,
        input_data: Dict[str, Any],
        system_prompt: str = None,
        fetch_data_for: List[str] = None
    ) -> Dict[str, Any]:
        """
        Execute analysis using a prompt template and real data.
        
        Args:
            prompt_template: The prompt template string with {{variable}} placeholders
            input_data: Input data containing variables and parameters
            system_prompt: Optional system prompt override
            fetch_data_for: List of tickers to fetch real data for
        
        Returns:
            Dict with analysis results, data sources, and metadata
        """
        # Fetch real market data if tickers provided
        market_data = {}
        if fetch_data_for:
            for ticker in fetch_data_for[:10]:  # Limit to 10 tickers
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
                        "revenue": context.revenue,
                        "revenue_growth": context.revenue_growth,
                        "gross_margin": context.gross_margin,
                        "operating_margin": context.operating_margin,
                        "net_margin": context.net_margin,
                        "roe": context.roe,
                        "debt_to_equity": context.debt_to_equity,
                        "analyst_rating": context.analyst_rating,
                        "price_target": context.price_target,
                        "recent_news": context.recent_news[:3] if context.recent_news else []
                    }
                except Exception as e:
                    self.logger.warning(f"Failed to fetch data for {ticker}: {e}")
        
        # Add market data to input
        if market_data:
            input_data["market_data"] = market_data
            input_data["market_data_json"] = json.dumps(market_data, indent=2)
        
        # Render the prompt template
        rendered_prompt = render_template(prompt_template, input_data)
        
        # Add real data context if available
        if market_data:
            rendered_prompt += f"\n\n=== REAL MARKET DATA ===\n{json.dumps(market_data, indent=2)}"
        
        # Default system prompt based on agent category
        if not system_prompt:
            system_prompt = self._get_default_system_prompt()
        
        # Call LLM
        response, tokens = await self.call_llm(
            prompt=rendered_prompt,
            system_prompt=system_prompt,
            temperature=0.4,
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
            result = {"analysis": response, "raw_response": True}
        
        # Add metadata
        result["tokens_used"] = tokens
        result["data_sources"] = list(market_data.keys()) if market_data else []
        result["timestamp"] = datetime.utcnow().isoformat()
        result["agent_type"] = self.agent_type
        
        return result
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt based on agent category."""
        prompts = {
            "idea_generation": """You are a senior equity research analyst at a top-tier investment firm. 
You specialize in identifying high-conviction investment opportunities through rigorous fundamental analysis.
Always provide specific, actionable recommendations backed by data and clear reasoning.
Format your responses as structured JSON for easy parsing.""",
            
            "due_diligence": """You are a meticulous due diligence analyst performing comprehensive company analysis.
You examine financial statements, competitive positioning, management quality, and risk factors.
Provide detailed, balanced analysis with specific data points and clear conclusions.
Format your responses as structured JSON.""",
            
            "portfolio_management": """You are a portfolio manager at an institutional investment firm.
You specialize in portfolio construction, risk management, and asset allocation.
Provide specific, quantitative recommendations with clear rationale.
Format your responses as structured JSON.""",
            
            "macro_analysis": """You are a macro strategist at a global investment bank.
You analyze economic indicators, market regimes, and cross-asset relationships.
Provide actionable insights with specific positioning recommendations.
Format your responses as structured JSON.""",
            
            "risk_analysis": """You are a risk analyst specializing in investment risk assessment.
You identify, quantify, and provide mitigation strategies for various risk factors.
Be thorough and specific in your risk assessments.
Format your responses as structured JSON.""",
            
            "sentiment_analysis": """You are a sentiment analyst evaluating market and stock sentiment.
You analyze news, social media, analyst ratings, and insider activity.
Provide clear sentiment scores with supporting evidence.
Format your responses as structured JSON."""
        }
        
        return prompts.get(self.AGENT_CATEGORY, prompts["idea_generation"])
    
    async def execute_generic(
        self,
        prompt_name: str,
        input_data: Dict[str, Any],
        prompt_template: str = None
    ) -> Dict[str, Any]:
        """
        Generic execution handler for any prompt.
        
        If prompt_template is not provided, generates a reasonable prompt
        based on the prompt_name and input_data.
        """
        # Extract tickers from input data
        tickers = []
        if "ticker" in input_data:
            tickers.append(input_data["ticker"])
        if "tickers" in input_data:
            tickers.extend(input_data["tickers"])
        if "holdings" in input_data:
            tickers.extend([h.get("ticker") for h in input_data["holdings"] if h.get("ticker")])
        
        # Generate prompt if not provided
        if not prompt_template:
            prompt_template = f"""Perform {prompt_name.replace('_', ' ')} analysis.

Input Parameters:
{{input_json}}

Provide comprehensive analysis in JSON format with:
1. Key findings
2. Recommendations
3. Risk factors
4. Confidence level"""
            
            input_data["input_json"] = json.dumps(input_data, indent=2)
        
        return await self.execute_with_prompt(
            prompt_template=prompt_template,
            input_data=input_data,
            fetch_data_for=tickers
        )
