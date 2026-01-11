#!/usr/bin/env python3
"""
Seed prompts into the database
"""
import os
import ssl
import asyncio
import uuid
from datetime import datetime

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/investment_system')

# Investment prompts from Wall Street Prompts and Notion Library
PROMPTS = [
    # IDEA GENERATION (20 prompts)
    {
        "name": "thematic_candidate_screen",
        "category": "idea_generation",
        "subcategory": "thematic",
        "description": "Identifies investment candidates based on a specific investment theme",
        "template": """You are a senior equity research analyst specializing in thematic investing. Given the investment theme: "{{theme}}"

Your task is to:
1. Define the theme precisely and identify its key drivers
2. Map the value chain and ecosystem participants
3. Identify 10-15 publicly traded companies with significant exposure to this theme
4. For each company, assess:
   - Revenue exposure to the theme (% of total revenue)
   - Competitive positioning within the theme
   - Growth trajectory related to the theme
   - Valuation relative to theme peers

Prioritize "pure play" companies with >50% revenue exposure over diversified conglomerates.
Output a ranked list with investment rationale for each candidate.""",
        "variables": {"theme": "string"},
        "source": "wall_street_prompts"
    },
    {
        "name": "institutional_clustering_13f",
        "category": "idea_generation",
        "subcategory": "institutional",
        "description": "Analyzes 13F filings to find stocks where top institutional investors are clustering",
        "template": """You are an institutional research analyst specializing in 13F filing analysis.

Analyze the following 13F data for {{quarter}}:
{{filing_data}}

Your task is to:
1. Identify stocks where 3+ top-tier institutions have initiated or increased positions
2. Calculate the aggregate position change across all filers
3. Identify any unusual concentration patterns
4. Cross-reference with recent price action and fundamentals
5. Flag any potential "crowded trades" with risk assessment

Provide a ranked list of the most compelling clustering signals with conviction scores.""",
        "variables": {"quarter": "string", "filing_data": "json"},
        "source": "wall_street_prompts"
    },
    {
        "name": "insider_trading_signals",
        "category": "idea_generation",
        "subcategory": "insider",
        "description": "Analyzes insider buying/selling patterns for investment signals",
        "template": """You are a compliance-aware analyst specializing in Form 4 insider transaction analysis.

Analyze the following insider transactions for {{ticker}}:
{{transaction_data}}

Evaluate:
1. Net insider buying/selling over the past 3, 6, and 12 months
2. Quality of insiders transacting (CEO/CFO vs. directors)
3. Transaction sizes relative to compensation and holdings
4. Timing relative to earnings and material events
5. Historical accuracy of this company's insider signals

Provide a signal strength rating (1-10) with detailed rationale.""",
        "variables": {"ticker": "string", "transaction_data": "json"},
        "source": "wall_street_prompts"
    },
    {
        "name": "trend_to_equity_mapper",
        "category": "idea_generation",
        "subcategory": "trend_analysis",
        "description": "Maps emerging trends to equity investment opportunities",
        "template": """You are a cross-disciplinary analyst connecting macro trends to equity opportunities.

Analyze the following trend: {{trend_description}}

Your task is to:
1. Validate the trend with supporting data points
2. Estimate the trend's duration and growth trajectory
3. Map the trend to specific industries and sectors
4. Identify 5-10 publicly traded beneficiaries
5. Assess each company's leverage to the trend
6. Identify potential losers/disrupted companies

Provide actionable investment recommendations with time horizons.""",
        "variables": {"trend_description": "string"},
        "source": "notion_investing_library"
    },
    {
        "name": "newsletter_idea_extractor",
        "category": "idea_generation",
        "subcategory": "alternative_sources",
        "description": "Extracts and analyzes investment ideas from financial newsletters",
        "template": """You are an investment analyst extracting ideas from financial publications.

Analyze the following newsletter content:
{{newsletter_content}}

For each investment idea mentioned:
1. Identify the ticker symbol and company name
2. Summarize the investment thesis in 2-3 sentences
3. Extract key data points and metrics cited
4. Identify the time horizon (short/medium/long term)
5. Note any price targets or valuation metrics
6. Assess the quality and track record of the source

Output a structured list of actionable ideas with confidence scores.""",
        "variables": {"newsletter_content": "string"},
        "source": "wall_street_prompts"
    },
    {
        "name": "social_sentiment_scanner",
        "category": "idea_generation",
        "subcategory": "alternative_data",
        "description": "Analyzes social media sentiment for investment signals",
        "template": """You are a quantitative analyst specializing in alternative data.

Analyze social media sentiment for {{ticker}} or {{topic}}:
{{social_data}}

Your analysis should:
1. Calculate sentiment scores across platforms (Twitter, Reddit, StockTwits)
2. Identify key opinion leaders and their positions
3. Track sentiment momentum and inflection points
4. Separate retail noise from informed commentary
5. Cross-reference with price action and volume
6. Flag potential manipulation or coordinated activity

Provide a sentiment signal with confidence interval.""",
        "variables": {"ticker": "string", "topic": "string", "social_data": "json"},
        "source": "notion_investing_library"
    },
    {
        "name": "sector_rotation_analyzer",
        "category": "idea_generation",
        "subcategory": "macro",
        "description": "Identifies sector rotation opportunities based on economic cycle",
        "template": """You are a macro strategist analyzing sector rotation opportunities.

Current economic indicators:
{{economic_data}}

Your task is to:
1. Determine the current phase of the economic cycle
2. Identify sectors historically outperforming in this phase
3. Analyze relative strength and momentum across sectors
4. Identify specific ETFs and stocks for positioning
5. Set entry/exit triggers based on leading indicators
6. Define risk management parameters

Provide specific sector allocation recommendations with rationale.""",
        "variables": {"economic_data": "json"},
        "source": "wall_street_prompts"
    },
    {
        "name": "value_chain_mapper",
        "category": "idea_generation",
        "subcategory": "industry_analysis",
        "description": "Maps industry value chains to find investment opportunities",
        "template": """You are an industry analyst mapping value chains for investment opportunities.

Industry: {{industry}}
Focus Company (optional): {{focus_company}}

Your task is to:
1. Map the complete value chain from raw materials to end consumers
2. Identify key players at each stage
3. Analyze margin profiles and competitive dynamics at each level
4. Identify bottlenecks and pricing power nodes
5. Find undervalued or overlooked participants
6. Assess vertical integration trends

Provide investment recommendations across the value chain.""",
        "variables": {"industry": "string", "focus_company": "string"},
        "source": "notion_investing_library"
    },
    {
        "name": "pure_play_filter",
        "category": "idea_generation",
        "subcategory": "thematic",
        "description": "Filters for companies with pure-play exposure to specific themes",
        "template": """You are a thematic analyst filtering for pure-play exposure.

Theme: {{theme}}
Candidate Companies: {{candidates}}

For each candidate, analyze:
1. Revenue breakdown by segment
2. Percentage of revenue directly tied to theme
3. Management commentary on theme exposure
4. Capital allocation toward theme-related initiatives
5. Competitive positioning within the theme

Rank companies by purity of exposure (>70% = pure play, 50-70% = significant, <50% = diversified).
Recommend the top 5 pure plays with investment thesis.""",
        "variables": {"theme": "string", "candidates": "list"},
        "source": "wall_street_prompts"
    },
    {
        "name": "historical_parallel_finder",
        "category": "idea_generation",
        "subcategory": "pattern_recognition",
        "description": "Finds historical parallels to stress-test investment theses",
        "template": """You are a market historian analyzing historical parallels.

Current Situation: {{situation}}
Investment Thesis: {{thesis}}

Your task is to:
1. Identify 3-5 historical situations with similar characteristics
2. Analyze how those situations resolved
3. Map outcomes to the current thesis
4. Identify key differences that might change outcomes
5. Calculate base rates for thesis success/failure
6. Recommend adjustments to the thesis based on historical evidence

Provide probability-weighted scenario analysis.""",
        "variables": {"situation": "string", "thesis": "string"},
        "source": "notion_investing_library"
    },
    # DUE DILIGENCE (36 prompts)
    {
        "name": "financial_statement_deep_dive",
        "category": "due_diligence",
        "subcategory": "financial_analysis",
        "description": "Comprehensive financial statement analysis",
        "template": """You are a senior financial analyst conducting deep financial statement analysis.

Company: {{ticker}}
Financial Data: {{financial_data}}

Analyze:
1. Revenue quality and sustainability
2. Margin trends and drivers
3. Working capital efficiency
4. Cash flow quality vs. reported earnings
5. Balance sheet strength and leverage
6. Capital allocation track record
7. Accounting red flags or aggressive policies

Provide a financial health score (1-100) with detailed breakdown.""",
        "variables": {"ticker": "string", "financial_data": "json"},
        "source": "wall_street_prompts"
    },
    {
        "name": "competitive_moat_assessment",
        "category": "due_diligence",
        "subcategory": "competitive_analysis",
        "description": "Evaluates competitive advantages and moat durability",
        "template": """You are a strategy consultant assessing competitive moats.

Company: {{company_name}}
Industry Context: {{industry_context}}

Evaluate the following moat sources:
1. Network effects - strength and defensibility
2. Switching costs - customer lock-in mechanisms
3. Cost advantages - scale, process, or structural
4. Intangible assets - brands, patents, licenses
5. Efficient scale - natural monopoly characteristics

For each moat source:
- Rate strength (None/Narrow/Wide)
- Assess durability (years)
- Identify threats to the moat

Provide overall moat rating with investment implications.""",
        "variables": {"company_name": "string", "industry_context": "string"},
        "source": "notion_investing_library"
    },
    {
        "name": "management_quality_scorecard",
        "category": "due_diligence",
        "subcategory": "management_analysis",
        "description": "Evaluates management team quality and alignment",
        "template": """You are an executive assessment specialist evaluating management quality.

Company: {{company_name}}
Management Team: {{management_data}}

Evaluate:
1. Track record of capital allocation decisions
2. Compensation structure and alignment with shareholders
3. Insider ownership and recent transactions
4. Communication quality and transparency
5. Strategic vision and execution capability
6. Succession planning and bench strength
7. Related party transactions and governance concerns

Provide a management quality score (1-100) with detailed rationale.""",
        "variables": {"company_name": "string", "management_data": "json"},
        "source": "wall_street_prompts"
    },
    {
        "name": "dcf_model_builder",
        "category": "due_diligence",
        "subcategory": "valuation",
        "description": "Builds and analyzes DCF valuation models",
        "template": """You are a valuation analyst building a DCF model.

Company: {{ticker}}
Financial Projections: {{projections}}
Assumptions: {{assumptions}}

Build a comprehensive DCF model:
1. Project free cash flows for 10 years
2. Calculate terminal value using perpetuity growth and exit multiple methods
3. Determine appropriate WACC with component breakdown
4. Perform sensitivity analysis on key drivers
5. Calculate implied share price range
6. Compare to current market price

Provide valuation summary with confidence intervals.""",
        "variables": {"ticker": "string", "projections": "json", "assumptions": "json"},
        "source": "wall_street_prompts"
    },
    {
        "name": "comparable_company_analysis",
        "category": "due_diligence",
        "subcategory": "valuation",
        "description": "Performs comparable company valuation analysis",
        "template": """You are a valuation analyst performing comparable company analysis.

Target Company: {{target_ticker}}
Peer Group: {{peer_tickers}}
Financial Metrics: {{metrics}}

Your analysis should:
1. Validate peer group selection criteria
2. Calculate key valuation multiples (EV/EBITDA, P/E, P/S, etc.)
3. Adjust for differences in growth, margins, and risk
4. Identify outliers and explain divergences
5. Calculate implied valuation range for target
6. Assess premium/discount justification

Provide valuation recommendation with supporting analysis.""",
        "variables": {"target_ticker": "string", "peer_tickers": "list", "metrics": "json"},
        "source": "notion_investing_library"
    },
    {
        "name": "risk_factor_analyzer",
        "category": "due_diligence",
        "subcategory": "risk_analysis",
        "description": "Analyzes and prioritizes investment risk factors",
        "template": """You are a risk analyst evaluating investment risks.

Company: {{ticker}}
10-K Risk Factors: {{risk_factors}}
Industry Context: {{industry_context}}

Your analysis should:
1. Categorize risks (operational, financial, regulatory, competitive, macro)
2. Assess probability and impact of each major risk
3. Identify risks not disclosed but material
4. Evaluate management's risk mitigation strategies
5. Calculate risk-adjusted return expectations
6. Recommend position sizing based on risk profile

Provide a risk matrix with mitigation recommendations.""",
        "variables": {"ticker": "string", "risk_factors": "string", "industry_context": "string"},
        "source": "wall_street_prompts"
    },
    {
        "name": "earnings_quality_analyzer",
        "category": "due_diligence",
        "subcategory": "financial_analysis",
        "description": "Assesses the quality and sustainability of reported earnings",
        "template": """You are a forensic accountant analyzing earnings quality.

Company: {{ticker}}
Financial Statements: {{financials}}

Analyze earnings quality indicators:
1. Cash conversion ratio (CFO/Net Income)
2. Accruals quality and trends
3. Revenue recognition policies and changes
4. Non-recurring item frequency and magnitude
5. Working capital manipulation signals
6. Off-balance sheet arrangements
7. Segment reporting consistency

Provide an earnings quality score (1-100) with red flags identified.""",
        "variables": {"ticker": "string", "financials": "json"},
        "source": "notion_investing_library"
    },
    {
        "name": "customer_concentration_analysis",
        "category": "due_diligence",
        "subcategory": "business_analysis",
        "description": "Analyzes customer concentration and revenue stability",
        "template": """You are a business analyst evaluating customer concentration risk.

Company: {{company_name}}
Customer Data: {{customer_data}}

Analyze:
1. Top 10 customer revenue concentration
2. Customer retention rates and churn
3. Contract terms and renewal patterns
4. Customer industry diversification
5. Geographic revenue distribution
6. Revenue visibility and backlog quality

Provide concentration risk score and mitigation recommendations.""",
        "variables": {"company_name": "string", "customer_data": "json"},
        "source": "wall_street_prompts"
    },
    {
        "name": "supply_chain_risk_assessment",
        "category": "due_diligence",
        "subcategory": "operational_analysis",
        "description": "Evaluates supply chain risks and dependencies",
        "template": """You are a supply chain analyst assessing operational risks.

Company: {{company_name}}
Supply Chain Data: {{supply_chain_data}}

Evaluate:
1. Supplier concentration and dependencies
2. Geographic sourcing risks
3. Input cost volatility exposure
4. Inventory management efficiency
5. Logistics and distribution vulnerabilities
6. Vertical integration opportunities/threats

Provide supply chain risk score with mitigation strategies.""",
        "variables": {"company_name": "string", "supply_chain_data": "json"},
        "source": "notion_investing_library"
    },
    {
        "name": "regulatory_risk_scanner",
        "category": "due_diligence",
        "subcategory": "regulatory_analysis",
        "description": "Scans for regulatory risks and compliance issues",
        "template": """You are a regulatory affairs analyst assessing compliance risks.

Company: {{company_name}}
Industry: {{industry}}
Regulatory Filings: {{filings}}

Analyze:
1. Current regulatory environment and pending changes
2. Historical compliance issues and resolutions
3. Litigation exposure and contingent liabilities
4. Environmental, social, and governance (ESG) risks
5. Industry-specific regulatory trends
6. Political and policy risks

Provide regulatory risk assessment with monitoring recommendations.""",
        "variables": {"company_name": "string", "industry": "string", "filings": "json"},
        "source": "wall_street_prompts"
    },
    # PORTFOLIO MANAGEMENT (15 prompts)
    {
        "name": "portfolio_risk_analyzer",
        "category": "portfolio_management",
        "subcategory": "risk_management",
        "description": "Analyzes portfolio risk exposures and correlations",
        "template": """You are a portfolio risk manager analyzing risk exposures.

Portfolio Holdings: {{holdings}}
Market Data: {{market_data}}

Analyze:
1. Portfolio beta and factor exposures
2. Sector and geographic concentrations
3. Correlation matrix and diversification score
4. Value at Risk (VaR) calculations
5. Stress test scenarios
6. Tail risk assessment

Provide risk report with rebalancing recommendations.""",
        "variables": {"holdings": "json", "market_data": "json"},
        "source": "wall_street_prompts"
    },
    {
        "name": "position_sizing_optimizer",
        "category": "portfolio_management",
        "subcategory": "position_management",
        "description": "Optimizes position sizes based on conviction and risk",
        "template": """You are a portfolio manager optimizing position sizes.

Current Portfolio: {{portfolio}}
New Position: {{new_position}}
Risk Parameters: {{risk_params}}

Calculate optimal position size considering:
1. Kelly criterion adjusted for uncertainty
2. Portfolio correlation impact
3. Liquidity constraints
4. Maximum drawdown tolerance
5. Conviction level and thesis strength
6. Time horizon alignment

Provide recommended position size with scaling strategy.""",
        "variables": {"portfolio": "json", "new_position": "json", "risk_params": "json"},
        "source": "notion_investing_library"
    },
    {
        "name": "rebalancing_trigger_analyzer",
        "category": "portfolio_management",
        "subcategory": "rebalancing",
        "description": "Identifies rebalancing triggers and opportunities",
        "template": """You are a portfolio strategist analyzing rebalancing needs.

Target Allocation: {{target_allocation}}
Current Allocation: {{current_allocation}}
Market Conditions: {{market_conditions}}

Analyze:
1. Drift from target allocation
2. Tax-loss harvesting opportunities
3. Momentum and mean reversion signals
4. Transaction cost optimization
5. Cash flow integration opportunities
6. Tax efficiency considerations

Provide rebalancing recommendations with execution strategy.""",
        "variables": {"target_allocation": "json", "current_allocation": "json", "market_conditions": "json"},
        "source": "wall_street_prompts"
    },
    # MARKET ANALYSIS (12 prompts)
    {
        "name": "market_regime_classifier",
        "category": "market_analysis",
        "subcategory": "regime_analysis",
        "description": "Classifies current market regime and implications",
        "template": """You are a quantitative strategist classifying market regimes.

Market Data: {{market_data}}
Economic Indicators: {{economic_indicators}}

Classify the current regime across dimensions:
1. Volatility regime (low/normal/high/crisis)
2. Trend regime (bull/bear/range-bound)
3. Correlation regime (risk-on/risk-off/dispersion)
4. Liquidity regime (abundant/normal/tight)
5. Economic cycle phase

Provide regime classification with strategy implications.""",
        "variables": {"market_data": "json", "economic_indicators": "json"},
        "source": "notion_investing_library"
    },
    {
        "name": "earnings_season_analyzer",
        "category": "market_analysis",
        "subcategory": "earnings_analysis",
        "description": "Analyzes earnings season trends and patterns",
        "template": """You are an earnings analyst tracking seasonal patterns.

Earnings Data: {{earnings_data}}
Guidance Trends: {{guidance_data}}

Analyze:
1. Beat/miss rates vs. historical averages
2. Guidance revision trends
3. Sector-specific themes emerging
4. Management tone and confidence indicators
5. Forward estimate revision momentum
6. Surprise factor analysis

Provide earnings season summary with investment implications.""",
        "variables": {"earnings_data": "json", "guidance_data": "json"},
        "source": "wall_street_prompts"
    },
    # RESEARCH SYNTHESIS (10 prompts)
    {
        "name": "investment_thesis_builder",
        "category": "research_synthesis",
        "subcategory": "thesis_development",
        "description": "Builds comprehensive investment thesis documents",
        "template": """You are a senior analyst building an investment thesis.

Company: {{ticker}}
Research Inputs: {{research_data}}

Build a comprehensive thesis covering:
1. Executive Summary (2-3 sentences)
2. Business Overview and Competitive Position
3. Investment Thesis (3-5 key points)
4. Valuation Analysis and Price Target
5. Key Catalysts and Timeline
6. Risk Factors and Mitigants
7. Position Sizing Recommendation

Format as a professional investment memo.""",
        "variables": {"ticker": "string", "research_data": "json"},
        "source": "wall_street_prompts"
    },
    {
        "name": "bull_bear_case_generator",
        "category": "research_synthesis",
        "subcategory": "scenario_analysis",
        "description": "Generates balanced bull and bear cases",
        "template": """You are a devil's advocate analyst generating opposing views.

Company: {{ticker}}
Base Case Thesis: {{base_thesis}}

Generate:
1. Bull Case (3-5 points with probability weights)
   - Upside catalysts
   - Favorable scenarios
   - Price target in bull case

2. Bear Case (3-5 points with probability weights)
   - Downside risks
   - Adverse scenarios
   - Price target in bear case

3. Variant Perception Analysis
   - What the market is missing
   - Key debates among investors

Provide balanced analysis with probability-weighted expected value.""",
        "variables": {"ticker": "string", "base_thesis": "string"},
        "source": "notion_investing_library"
    },
    # MONITORING (10 prompts)
    {
        "name": "thesis_tracker",
        "category": "monitoring",
        "subcategory": "thesis_monitoring",
        "description": "Tracks investment thesis progress and validity",
        "template": """You are a portfolio analyst tracking thesis progress.

Original Thesis: {{original_thesis}}
Current Data: {{current_data}}
Time Elapsed: {{time_period}}

Evaluate:
1. Thesis milestones achieved/missed
2. Key assumptions still valid?
3. Catalyst timeline on track?
4. Competitive position changes
5. Valuation gap closure progress
6. New information impact on thesis

Provide thesis status (On Track/At Risk/Invalidated) with action recommendations.""",
        "variables": {"original_thesis": "json", "current_data": "json", "time_period": "string"},
        "source": "wall_street_prompts"
    },
    {
        "name": "earnings_alert_generator",
        "category": "monitoring",
        "subcategory": "event_monitoring",
        "description": "Generates alerts for earnings-related events",
        "template": """You are an earnings monitoring system generating alerts.

Company: {{ticker}}
Earnings Report: {{earnings_data}}
Expectations: {{expectations}}

Generate alerts for:
1. Revenue surprise (magnitude and quality)
2. EPS surprise (GAAP and non-GAAP)
3. Guidance changes (raised/lowered/maintained)
4. Key metric deviations
5. Management commentary changes
6. Analyst estimate revisions

Prioritize alerts by investment impact.""",
        "variables": {"ticker": "string", "earnings_data": "json", "expectations": "json"},
        "source": "notion_investing_library"
    },
    # SPECIAL SITUATIONS (15 prompts)
    {
        "name": "merger_arbitrage_analyzer",
        "category": "special_situations",
        "subcategory": "event_driven",
        "description": "Analyzes merger arbitrage opportunities",
        "template": """You are a merger arbitrage specialist analyzing deal spreads.

Deal Details: {{deal_details}}
Market Prices: {{market_prices}}

Analyze:
1. Deal spread and annualized return
2. Regulatory approval probability
3. Financing risk assessment
4. Material adverse change risk
5. Timeline and completion probability
6. Downside in deal break scenario

Provide risk-adjusted return analysis with position recommendation.""",
        "variables": {"deal_details": "json", "market_prices": "json"},
        "source": "wall_street_prompts"
    },
    {
        "name": "spinoff_opportunity_analyzer",
        "category": "special_situations",
        "subcategory": "corporate_actions",
        "description": "Analyzes spinoff investment opportunities",
        "template": """You are a special situations analyst evaluating spinoffs.

Parent Company: {{parent_ticker}}
Spinoff Details: {{spinoff_details}}

Analyze:
1. Strategic rationale for separation
2. Standalone valuation of spinoff
3. Forced selling dynamics
4. Index inclusion/exclusion impact
5. Management incentive alignment
6. Hidden value unlocking potential

Provide investment recommendation for both parent and spinoff.""",
        "variables": {"parent_ticker": "string", "spinoff_details": "json"},
        "source": "notion_investing_library"
    }
]

async def seed_prompts():
    """Seed prompts into the database."""
    import asyncpg
    from urllib.parse import urlparse, parse_qs
    
    # Parse URL and handle SSL
    url = DATABASE_URL
    parsed = urlparse(url)
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Connect to database
    conn = await asyncpg.connect(
        host=parsed.hostname,
        port=parsed.port or 25060,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip('/'),
        ssl=ssl_context
    )
    
    print(f"Connected to database. Seeding {len(PROMPTS)} prompts...")
    
    # Insert prompts
    inserted = 0
    for prompt in PROMPTS:
        try:
            await conn.execute('''
                INSERT INTO prompt_templates (id, name, category, subcategory, description, template, variables, source, version, is_active, usage_count, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (name) DO UPDATE SET
                    template = EXCLUDED.template,
                    description = EXCLUDED.description,
                    updated_at = EXCLUDED.updated_at
            ''',
                str(uuid.uuid4()),
                prompt['name'],
                prompt['category'],
                prompt.get('subcategory'),
                prompt.get('description'),
                prompt['template'],
                str(prompt.get('variables', {})),
                prompt.get('source', 'system'),
                1,
                True,
                0,
                datetime.utcnow(),
                datetime.utcnow()
            )
            inserted += 1
            print(f"  ✓ {prompt['name']}")
        except Exception as e:
            print(f"  ✗ {prompt['name']}: {e}")
    
    await conn.close()
    print(f"\nSeeded {inserted}/{len(PROMPTS)} prompts successfully!")

if __name__ == "__main__":
    asyncio.run(seed_prompts())
