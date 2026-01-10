# =============================================================================
# Due Diligence Agent
# =============================================================================
# Specialized agent for comprehensive company due diligence
# =============================================================================

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
import structlog

import sys
sys.path.insert(0, "/app")

from shared.agents.base import BaseAgent, AgentTask, AgentResult
from shared.llm.provider import get_llm_provider
from shared.clients.polygon_client import get_polygon_client
from shared.clients.fmp_client import get_fmp_client
from shared.clients.sec_client import get_sec_client
from shared.clients.redis_client import get_redis_client

logger = structlog.get_logger(__name__)


# =============================================================================
# Due Diligence Agent
# =============================================================================

class DueDiligenceAgent(BaseAgent):
    """
    Agent specialized in comprehensive company due diligence.
    
    Capabilities:
    - Business model analysis
    - Financial statement deep dive
    - Management quality assessment
    - Competitive positioning
    - Risk identification
    - Valuation analysis
    """
    
    SUPPORTED_PROMPTS = [
        # Business Understanding
        "business_overview_report",
        "business_economics",
        "growth_margin_drivers",
        "unit_economics",
        "customer_analysis",
        "revenue_quality",
        
        # Industry Analysis
        "industry_overview",
        "competitive_landscape",
        "value_chain_mapping",
        "market_sizing",
        "porter_five_forces",
        
        # Financial Analysis
        "financial_statement_analysis",
        "earnings_quality",
        "capital_allocation",
        "cash_flow_analysis",
        "balance_sheet_strength",
        "working_capital_analysis",
        
        # Management Evaluation
        "management_quality_assessment",
        "ceo_track_record",
        "compensation_analysis",
        "corporate_governance",
        
        # Risk Assessment
        "risk_assessment",
        "bear_case_analysis",
        "regulatory_risk",
        "competitive_risk",
        "financial_risk",
        
        # Valuation
        "dcf_valuation",
        "comparable_analysis",
        "sum_of_parts",
        "scenario_analysis"
    ]
    
    def __init__(self):
        super().__init__(agent_type="due_diligence_agent")
        self.polygon = get_polygon_client()
        self.fmp = get_fmp_client()
        self.sec = get_sec_client()
    
    def get_supported_prompts(self) -> List[str]:
        return self.SUPPORTED_PROMPTS
    
    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute a due diligence task."""
        start_time = datetime.utcnow()
        
        prompt_name = task.prompt_name
        input_data = task.input_data
        
        self.logger.info(
            "Executing due diligence task",
            prompt_name=prompt_name,
            ticker=input_data.get("ticker")
        )
        
        try:
            # Fetch company data if ticker provided
            ticker = input_data.get("ticker")
            company_data = {}
            
            if ticker:
                company_data = await self._fetch_company_data(ticker)
            
            # Route to appropriate handler
            if prompt_name == "business_overview_report":
                result = await self._business_overview(input_data, company_data)
            elif prompt_name == "business_economics":
                result = await self._business_economics(input_data, company_data)
            elif prompt_name == "growth_margin_drivers":
                result = await self._growth_margin_drivers(input_data, company_data)
            elif prompt_name == "financial_statement_analysis":
                result = await self._financial_analysis(input_data, company_data)
            elif prompt_name == "earnings_quality":
                result = await self._earnings_quality(input_data, company_data)
            elif prompt_name == "competitive_landscape":
                result = await self._competitive_landscape(input_data, company_data)
            elif prompt_name == "management_quality_assessment":
                result = await self._management_assessment(input_data, company_data)
            elif prompt_name == "risk_assessment":
                result = await self._risk_assessment(input_data, company_data)
            elif prompt_name == "dcf_valuation":
                result = await self._dcf_valuation(input_data, company_data)
            elif prompt_name == "bear_case_analysis":
                result = await self._bear_case(input_data, company_data)
            else:
                result = await self._generic_analysis(prompt_name, input_data, company_data)
            
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
    
    async def _fetch_company_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch comprehensive company data from multiple sources."""
        data = {"ticker": ticker}
        
        try:
            # Company profile
            profile = await self.fmp.get_company_profile(ticker)
            if profile:
                data["profile"] = {
                    "name": profile.company_name,
                    "sector": profile.sector,
                    "industry": profile.industry,
                    "description": profile.description,
                    "market_cap": profile.mkt_cap,
                    "employees": profile.full_time_employees,
                    "ceo": profile.ceo
                }
            
            # Financial statements
            income = await self.fmp.get_income_statement(ticker, period="annual", limit=5)
            if income:
                data["income_statements"] = [
                    {
                        "date": str(i.date),
                        "revenue": i.revenue,
                        "gross_profit": i.gross_profit,
                        "operating_income": i.operating_income,
                        "net_income": i.net_income,
                        "eps": i.eps
                    }
                    for i in income
                ]
            
            # Key metrics
            metrics = await self.fmp.get_key_metrics(ticker, limit=5)
            if metrics:
                data["key_metrics"] = [
                    {
                        "date": str(m.date),
                        "pe_ratio": m.pe_ratio,
                        "pb_ratio": m.pb_ratio,
                        "roe": m.roe,
                        "roic": m.roic,
                        "debt_to_equity": m.debt_to_equity,
                        "free_cash_flow_per_share": m.free_cash_flow_per_share
                    }
                    for m in metrics
                ]
            
            # Stock price
            quote = await self.polygon.get_quote(ticker)
            if quote:
                data["current_price"] = quote.get("close")
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch some company data: {e}")
        
        return data
    
    # =========================================================================
    # Business Analysis
    # =========================================================================
    
    async def _business_overview(self, input_data: Dict, company_data: Dict) -> Dict:
        """Generate comprehensive business overview report."""
        ticker = input_data.get("ticker", "")
        
        prompt = f"""Generate a comprehensive business overview report for {ticker}.

COMPANY DATA:
{company_data}

Provide a detailed analysis covering:

1. **BUSINESS DESCRIPTION**
   - What does the company do?
   - Core products/services
   - Business model (how they make money)
   - Revenue streams breakdown

2. **MARKET POSITION**
   - Industry and sector
   - Market share
   - Competitive positioning
   - Key differentiators

3. **GROWTH DRIVERS**
   - Historical growth trajectory
   - Future growth opportunities
   - TAM/SAM/SOM analysis
   - Key growth initiatives

4. **COMPETITIVE ADVANTAGES**
   - Moat analysis (brand, network effects, switching costs, etc.)
   - Sustainability of advantages
   - Barriers to entry

5. **KEY RISKS**
   - Business model risks
   - Competitive threats
   - Regulatory risks
   - Execution risks

6. **FINANCIAL SNAPSHOT**
   - Revenue and profitability trends
   - Key financial metrics
   - Capital allocation priorities

7. **INVESTMENT THESIS SUMMARY**
   - Bull case
   - Bear case
   - Key metrics to monitor

Format as a structured JSON report."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a senior equity research analyst producing institutional-quality research.",
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
            result = {"report": response}
        
        result["tokens_used"] = tokens
        result["company_data"] = company_data
        return result
    
    async def _business_economics(self, input_data: Dict, company_data: Dict) -> Dict:
        """Analyze business economics and unit economics."""
        ticker = input_data.get("ticker", "")
        
        prompt = f"""Analyze the business economics for {ticker}.

COMPANY DATA:
{company_data}

Provide detailed analysis of:

1. **REVENUE MODEL**
   - Revenue recognition
   - Pricing power
   - Revenue visibility/predictability
   - Customer concentration

2. **COST STRUCTURE**
   - Fixed vs. variable costs
   - Operating leverage
   - Cost trends
   - Margin expansion/compression drivers

3. **UNIT ECONOMICS**
   - Customer acquisition cost (CAC)
   - Lifetime value (LTV)
   - LTV/CAC ratio
   - Payback period
   - Cohort analysis insights

4. **CAPITAL INTENSITY**
   - Capex requirements
   - Working capital needs
   - Return on invested capital (ROIC)
   - Capital efficiency trends

5. **SCALABILITY**
   - Incremental margins
   - Network effects
   - Platform dynamics
   - Economies of scale

6. **QUALITY OF EARNINGS**
   - Cash conversion
   - Accounting quality
   - One-time items
   - Sustainability of margins

Format as JSON with specific metrics and analysis."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a financial analyst specializing in business model analysis.",
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
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        return result
    
    async def _growth_margin_drivers(self, input_data: Dict, company_data: Dict) -> Dict:
        """Analyze growth and margin drivers."""
        ticker = input_data.get("ticker", "")
        
        prompt = f"""Analyze growth and margin drivers for {ticker}.

COMPANY DATA:
{company_data}

Provide analysis of:

1. **REVENUE GROWTH DRIVERS**
   - Volume vs. price
   - New products/services
   - Geographic expansion
   - Market share gains
   - M&A contribution

2. **MARGIN DRIVERS**
   - Gross margin trends and drivers
   - Operating leverage
   - Mix shift impact
   - Pricing power
   - Cost optimization initiatives

3. **HISTORICAL ANALYSIS**
   - 5-year growth CAGR
   - Margin trajectory
   - Key inflection points
   - What drove past performance

4. **FORWARD OUTLOOK**
   - Growth sustainability
   - Margin expansion potential
   - Key assumptions
   - Risks to projections

5. **PEER COMPARISON**
   - Growth vs. peers
   - Margin vs. peers
   - Relative positioning

Format as JSON with specific metrics."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a growth equity analyst evaluating company fundamentals.",
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
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        return result
    
    # =========================================================================
    # Financial Analysis
    # =========================================================================
    
    async def _financial_analysis(self, input_data: Dict, company_data: Dict) -> Dict:
        """Perform comprehensive financial statement analysis."""
        ticker = input_data.get("ticker", "")
        
        prompt = f"""Perform comprehensive financial statement analysis for {ticker}.

FINANCIAL DATA:
{company_data}

Analyze:

1. **INCOME STATEMENT ANALYSIS**
   - Revenue trends and growth rates
   - Gross margin analysis
   - Operating margin trends
   - Net margin and EPS growth
   - Quality of revenue growth

2. **BALANCE SHEET ANALYSIS**
   - Asset composition and quality
   - Liability structure
   - Working capital management
   - Debt levels and coverage
   - Equity and book value

3. **CASH FLOW ANALYSIS**
   - Operating cash flow trends
   - Free cash flow generation
   - Cash conversion cycle
   - Capital expenditure analysis
   - Dividend and buyback capacity

4. **KEY RATIOS**
   - Profitability ratios (ROE, ROA, ROIC)
   - Liquidity ratios
   - Leverage ratios
   - Efficiency ratios
   - Valuation ratios

5. **TREND ANALYSIS**
   - 5-year trends
   - Quarterly seasonality
   - Cyclicality assessment

6. **RED FLAGS**
   - Accounting concerns
   - Quality of earnings issues
   - Balance sheet risks

Format as JSON with specific numbers and analysis."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a CFA charterholder performing detailed financial analysis.",
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
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        return result
    
    async def _earnings_quality(self, input_data: Dict, company_data: Dict) -> Dict:
        """Assess earnings quality."""
        ticker = input_data.get("ticker", "")
        
        prompt = f"""Assess earnings quality for {ticker}.

FINANCIAL DATA:
{company_data}

Evaluate:

1. **CASH CONVERSION**
   - Net income to operating cash flow
   - Accruals analysis
   - Working capital changes

2. **REVENUE QUALITY**
   - Revenue recognition policies
   - Deferred revenue trends
   - Customer concentration
   - Contract terms

3. **EXPENSE QUALITY**
   - Capitalization policies
   - Depreciation/amortization
   - Stock-based compensation
   - One-time items

4. **ACCOUNTING ANALYSIS**
   - Accounting policy changes
   - Estimates and assumptions
   - Related party transactions
   - Off-balance sheet items

5. **EARNINGS MANIPULATION INDICATORS**
   - Beneish M-Score components
   - Altman Z-Score
   - Piotroski F-Score
   - Red flags

6. **OVERALL ASSESSMENT**
   - Earnings quality score (1-10)
   - Key concerns
   - Adjustments needed

Format as JSON with specific analysis."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a forensic accountant analyzing earnings quality.",
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
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        return result
    
    # =========================================================================
    # Competitive Analysis
    # =========================================================================
    
    async def _competitive_landscape(self, input_data: Dict, company_data: Dict) -> Dict:
        """Analyze competitive landscape."""
        ticker = input_data.get("ticker", "")
        
        prompt = f"""Analyze the competitive landscape for {ticker}.

COMPANY DATA:
{company_data}

Provide:

1. **INDUSTRY OVERVIEW**
   - Industry structure
   - Key players and market shares
   - Industry growth rate
   - Profitability dynamics

2. **COMPETITIVE POSITIONING**
   - Company's market position
   - Relative strengths/weaknesses
   - Strategic group mapping

3. **PORTER'S FIVE FORCES**
   - Threat of new entrants
   - Bargaining power of suppliers
   - Bargaining power of buyers
   - Threat of substitutes
   - Competitive rivalry

4. **COMPETITIVE ADVANTAGES**
   - Sources of moat
   - Sustainability assessment
   - Moat trend (widening/narrowing)

5. **KEY COMPETITORS**
   - Direct competitors analysis
   - Comparative metrics
   - Strategic differences

6. **COMPETITIVE DYNAMICS**
   - Industry trends
   - Disruption risks
   - Consolidation potential

Format as JSON with detailed analysis."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a strategy consultant analyzing competitive dynamics.",
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
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        return result
    
    # =========================================================================
    # Management Assessment
    # =========================================================================
    
    async def _management_assessment(self, input_data: Dict, company_data: Dict) -> Dict:
        """Assess management quality."""
        ticker = input_data.get("ticker", "")
        
        prompt = f"""Assess management quality for {ticker}.

COMPANY DATA:
{company_data}

Evaluate:

1. **CEO ASSESSMENT**
   - Background and experience
   - Track record
   - Strategic vision
   - Communication quality
   - Skin in the game

2. **MANAGEMENT TEAM**
   - Key executives
   - Tenure and stability
   - Relevant experience
   - Succession planning

3. **CAPITAL ALLOCATION**
   - Historical decisions
   - M&A track record
   - Dividend/buyback policy
   - Investment priorities
   - ROIC track record

4. **CORPORATE GOVERNANCE**
   - Board composition
   - Independence
   - Compensation alignment
   - Shareholder friendliness

5. **EXECUTION TRACK RECORD**
   - Guidance accuracy
   - Strategic initiatives success
   - Operational improvements
   - Crisis management

6. **OVERALL SCORE**
   - Management quality (1-10)
   - Key strengths
   - Key concerns
   - Red flags

Format as JSON with specific examples."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are an institutional investor evaluating management quality.",
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
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        return result
    
    # =========================================================================
    # Risk Assessment
    # =========================================================================
    
    async def _risk_assessment(self, input_data: Dict, company_data: Dict) -> Dict:
        """Comprehensive risk assessment."""
        ticker = input_data.get("ticker", "")
        
        prompt = f"""Perform comprehensive risk assessment for {ticker}.

COMPANY DATA:
{company_data}

Identify and assess:

1. **BUSINESS RISKS**
   - Business model vulnerabilities
   - Customer concentration
   - Supplier dependencies
   - Technology risks

2. **COMPETITIVE RISKS**
   - Market share threats
   - Disruption risks
   - New entrant threats
   - Substitute products

3. **FINANCIAL RISKS**
   - Leverage and liquidity
   - Interest rate sensitivity
   - Currency exposure
   - Covenant risks

4. **OPERATIONAL RISKS**
   - Execution risks
   - Key person risk
   - Supply chain risks
   - Cybersecurity

5. **REGULATORY RISKS**
   - Current regulations
   - Pending legislation
   - Compliance costs
   - Litigation exposure

6. **MACRO RISKS**
   - Economic sensitivity
   - Cyclicality
   - Geopolitical exposure

7. **ESG RISKS**
   - Environmental
   - Social
   - Governance

8. **RISK MATRIX**
   - Probability vs. impact
   - Risk mitigation factors
   - Monitoring indicators

Format as JSON with risk scores and analysis."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a risk analyst identifying investment risks.",
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
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        return result
    
    async def _bear_case(self, input_data: Dict, company_data: Dict) -> Dict:
        """Develop comprehensive bear case."""
        ticker = input_data.get("ticker", "")
        
        prompt = f"""Develop a comprehensive bear case for {ticker}.

COMPANY DATA:
{company_data}

As a skeptical short-seller, identify:

1. **THESIS KILLERS**
   - What could go fundamentally wrong?
   - Structural challenges
   - Secular headwinds

2. **VALUATION CONCERNS**
   - Why current valuation is too high
   - Historical valuation comparison
   - Peer comparison
   - Downside scenarios

3. **EARNINGS RISKS**
   - Margin pressure sources
   - Revenue growth deceleration
   - Cost inflation
   - Competition impact

4. **BALANCE SHEET RISKS**
   - Debt concerns
   - Asset quality issues
   - Off-balance sheet risks

5. **MANAGEMENT CONCERNS**
   - Execution risks
   - Incentive misalignment
   - Track record issues

6. **CATALYSTS FOR DECLINE**
   - Near-term risks
   - Medium-term structural issues
   - Black swan scenarios

7. **BEAR CASE VALUATION**
   - Downside price target
   - Key assumptions
   - Probability assessment

Format as JSON with specific bear case thesis."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a short-seller building a bear case.",
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
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        return result
    
    # =========================================================================
    # Valuation
    # =========================================================================
    
    async def _dcf_valuation(self, input_data: Dict, company_data: Dict) -> Dict:
        """Perform DCF valuation."""
        ticker = input_data.get("ticker", "")
        
        prompt = f"""Perform DCF valuation for {ticker}.

COMPANY DATA:
{company_data}

Provide:

1. **REVENUE PROJECTIONS**
   - 5-year revenue forecast
   - Growth rate assumptions
   - Key drivers

2. **MARGIN PROJECTIONS**
   - Gross margin trajectory
   - Operating margin path
   - Terminal margins

3. **CAPITAL REQUIREMENTS**
   - Capex projections
   - Working capital needs
   - D&A assumptions

4. **FREE CASH FLOW**
   - FCF projections
   - FCF conversion
   - Terminal FCF

5. **DISCOUNT RATE**
   - WACC calculation
   - Cost of equity (CAPM)
   - Cost of debt
   - Capital structure

6. **TERMINAL VALUE**
   - Terminal growth rate
   - Exit multiple approach
   - Perpetuity approach

7. **VALUATION OUTPUT**
   - Enterprise value
   - Equity value
   - Per share value
   - Implied upside/downside

8. **SENSITIVITY ANALYSIS**
   - WACC sensitivity
   - Growth sensitivity
   - Margin sensitivity

Format as JSON with specific numbers."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a valuation analyst performing DCF analysis.",
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
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        return result
    
    async def _generic_analysis(self, prompt_name: str, input_data: Dict, company_data: Dict) -> Dict:
        """Handle generic analysis requests."""
        ticker = input_data.get("ticker", "")
        
        prompt = f"""Perform {prompt_name.replace('_', ' ')} analysis for {ticker}.

COMPANY DATA:
{company_data}

Provide comprehensive analysis relevant to {prompt_name}.

Format as JSON with detailed findings."""

        response, tokens = await self.call_llm(
            prompt=prompt,
            system_prompt="You are a senior equity research analyst.",
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
            result = {"analysis": response}
        
        result["tokens_used"] = tokens
        return result


# =============================================================================
# Agent Runner
# =============================================================================

async def run_agent():
    """Run the due diligence agent as a service."""
    agent = DueDiligenceAgent()
    redis = get_redis_client()
    await redis.connect()
    
    channel = f"investment-agents:tasks:due_diligence_agent"
    
    logger.info("Due Diligence Agent started, listening for tasks...")
    
    async def handle_message(channel: str, message: str):
        import json
        task_data = json.loads(message)
        task = AgentTask(**task_data)
        
        result = await agent.run(task)
        
        result_channel = f"investment-agents:results:{task.task_id}"
        await redis.publish(result_channel, result.model_dump_json())
    
    await redis.subscribe([channel], handle_message)


if __name__ == "__main__":
    asyncio.run(run_agent())
