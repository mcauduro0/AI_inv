-- =============================================================================
-- Investment Agent System - Seed Prompts
-- =============================================================================
-- Initial prompt library data
-- =============================================================================

-- Investment Idea Generation Prompts
INSERT INTO prompts (name, category, subcategory, description, prompt_template, system_prompt, temperature) VALUES
('theme_order_effects', 'idea_generation', 'thematic', 'Analyze first, second, and third order effects of an investment theme', 
'Analyze the investment theme: {{theme}}

Identify and explain:
1. FIRST ORDER EFFECTS - Direct and obvious beneficiaries
2. SECOND ORDER EFFECTS - Indirect beneficiaries and consequences  
3. THIRD ORDER EFFECTS - Non-obvious, long-term implications

For each order, provide:
- Specific companies or sectors affected
- Magnitude of impact (high/medium/low)
- Timeline for impact
- Investment implications

Format as structured JSON.',
'You are a senior investment strategist specializing in thematic investing.', 0.5),

('thematic_candidate_screen', 'idea_generation', 'thematic', 'Screen for investment candidates based on a theme',
'Screen for investment candidates related to theme: {{theme}}
Sector focus: {{sector}}

Identify companies that:
1. Have direct exposure to the theme
2. Are positioned to benefit from theme growth
3. Have relevant competitive advantages

For each candidate provide:
- Ticker and company name
- Market cap
- Theme exposure score (1-10)
- Key thesis points
- Potential concerns

Return top 20 candidates as JSON.',
'You are an equity research analyst specializing in thematic screening.', 0.4),

('pure_play_filter', 'idea_generation', 'thematic', 'Filter candidates for pure-play exposure to a theme',
'Filter the following candidates for pure-play exposure to theme: {{theme}}

Candidates: {{candidates}}

For each candidate, assess:
1. Revenue exposure to theme (%)
2. Strategic focus on theme
3. Competitive position in theme
4. Diversification/dilution factors

Classify each as:
- PURE_PLAY: >70% theme exposure
- HIGH_EXPOSURE: 40-70% theme exposure
- MODERATE_EXPOSURE: 20-40% theme exposure
- LOW_EXPOSURE: <20% theme exposure

Return filtered and ranked list as JSON.',
'You are a portfolio manager focused on concentrated thematic investments.', 0.3),

('institutional_clustering_13f', 'idea_generation', 'institutional', 'Analyze SEC 13F filings for institutional clustering',
'Analyze recent SEC 13F filings to identify stocks with institutional clustering.

Focus on:
1. New positions by top-performing funds
2. Increased positions by multiple funds
3. Convergence of different investment styles
4. Unusual concentration patterns

For each identified stock:
- List funds with positions
- Position sizes and changes
- Concentration score
- Historical performance of funds in similar situations

Return top 15 clustered stocks as JSON.',
'You are a quantitative analyst specializing in institutional flow analysis.', 0.3),

('insider_trading_analysis', 'idea_generation', 'insider', 'Analyze SEC Form-4 insider trading patterns',
'Analyze SEC Form-4 filings for ticker: {{ticker}}

Evaluate:
1. Recent insider transactions (buys/sells)
2. Transaction sizes relative to holdings
3. Insider roles and track records
4. Cluster buying patterns
5. Timing relative to company events

Provide:
- Signal strength (strong_buy, buy, neutral, sell, strong_sell)
- Key transactions summary
- Historical accuracy of insiders
- Risk factors

Return analysis as JSON.',
'You are a forensic analyst specializing in insider trading patterns.', 0.3),

('newsletter_idea_scraping', 'idea_generation', 'alternative', 'Extract investment ideas from newsletters',
'Scan recent investment newsletters and publications for actionable ideas.

Sources to consider:
- Substack investment newsletters
- Seeking Alpha
- Value Investors Club
- SumZero
- Industry publications

For each idea found:
- Source and author
- Ticker and thesis summary
- Key catalysts mentioned
- Risk factors noted
- Author track record if available

Return top 10 ideas as JSON.',
'You are a research analyst aggregating investment ideas from multiple sources.', 0.5),

('social_sentiment_scan', 'idea_generation', 'alternative', 'Scan social media for investment sentiment',
'Scan social media platforms for investment sentiment and emerging ideas.

Platforms: {{platforms}}

Analyze:
1. Trending tickers and themes
2. Sentiment distribution (bullish/bearish/neutral)
3. Volume of discussion vs. historical
4. Quality of discourse (retail vs. institutional)
5. Contrarian opportunities

For each significant finding:
- Ticker/theme
- Sentiment score
- Discussion volume
- Notable posts/threads
- Risk assessment

Return findings as JSON.',
'You are a social media analyst specializing in investment sentiment.', 0.5)
ON CONFLICT (name) DO NOTHING;

-- Due Diligence Prompts
INSERT INTO prompts (name, category, subcategory, description, prompt_template, system_prompt, temperature) VALUES
('business_overview_report', 'due_diligence', 'business', 'Generate comprehensive business overview',
'Generate a comprehensive business overview report for {{ticker}}.

Company Data: {{company_data}}

Cover:
1. Business Description - What they do, how they make money
2. Market Position - Industry, market share, competitive positioning
3. Growth Drivers - Historical and future growth opportunities
4. Competitive Advantages - Moat analysis
5. Key Risks - Business model and competitive risks
6. Financial Snapshot - Key metrics and trends
7. Investment Thesis Summary - Bull and bear cases

Format as structured JSON report.',
'You are a senior equity research analyst producing institutional-quality research.', 0.4),

('financial_statement_analysis', 'due_diligence', 'financial', 'Comprehensive financial statement analysis',
'Perform comprehensive financial statement analysis for {{ticker}}.

Financial Data: {{financial_data}}

Analyze:
1. Income Statement - Revenue, margins, profitability trends
2. Balance Sheet - Asset quality, leverage, liquidity
3. Cash Flow - Operating CF, FCF, capital allocation
4. Key Ratios - Profitability, efficiency, leverage, valuation
5. Trend Analysis - 5-year trends and inflection points
6. Red Flags - Accounting concerns, quality issues

Return detailed analysis as JSON.',
'You are a CFA charterholder performing detailed financial analysis.', 0.3),

('competitive_landscape', 'due_diligence', 'competitive', 'Analyze competitive landscape',
'Analyze the competitive landscape for {{ticker}}.

Company Data: {{company_data}}

Provide:
1. Industry Overview - Structure, key players, dynamics
2. Competitive Positioning - Market position, relative strengths
3. Porter''s Five Forces - Detailed analysis
4. Competitive Advantages - Moat sources and sustainability
5. Key Competitors - Direct comparison and analysis
6. Competitive Dynamics - Trends, disruption risks

Return analysis as JSON.',
'You are a strategy consultant analyzing competitive dynamics.', 0.4),

('management_quality_assessment', 'due_diligence', 'management', 'Assess management quality',
'Assess management quality for {{ticker}}.

Company Data: {{company_data}}

Evaluate:
1. CEO Assessment - Background, track record, vision
2. Management Team - Key executives, tenure, experience
3. Capital Allocation - Historical decisions, M&A track record
4. Corporate Governance - Board, compensation, alignment
5. Execution Track Record - Guidance accuracy, strategic success
6. Overall Score - Management quality rating (1-10)

Return assessment as JSON.',
'You are an institutional investor evaluating management quality.', 0.4),

('risk_assessment', 'due_diligence', 'risk', 'Comprehensive risk assessment',
'Perform comprehensive risk assessment for {{ticker}}.

Company Data: {{company_data}}

Identify and assess:
1. Business Risks - Model vulnerabilities, concentration
2. Competitive Risks - Market share, disruption threats
3. Financial Risks - Leverage, liquidity, covenants
4. Operational Risks - Execution, key person, supply chain
5. Regulatory Risks - Current and pending regulations
6. Macro Risks - Economic sensitivity, cyclicality
7. ESG Risks - Environmental, social, governance
8. Risk Matrix - Probability vs. impact assessment

Return risk analysis as JSON.',
'You are a risk analyst identifying investment risks.', 0.4),

('dcf_valuation', 'due_diligence', 'valuation', 'Perform DCF valuation',
'Perform DCF valuation for {{ticker}}.

Company Data: {{company_data}}

Provide:
1. Revenue Projections - 5-year forecast with assumptions
2. Margin Projections - Gross and operating margin path
3. Capital Requirements - Capex, working capital, D&A
4. Free Cash Flow - FCF projections and conversion
5. Discount Rate - WACC calculation with components
6. Terminal Value - Growth rate and exit multiple approaches
7. Valuation Output - EV, equity value, per share value
8. Sensitivity Analysis - WACC and growth sensitivities

Return valuation model as JSON.',
'You are a valuation analyst performing DCF analysis.', 0.3),

('bear_case_analysis', 'due_diligence', 'risk', 'Develop comprehensive bear case',
'Develop a comprehensive bear case for {{ticker}}.

Company Data: {{company_data}}

As a skeptical short-seller, identify:
1. Thesis Killers - What could go fundamentally wrong
2. Valuation Concerns - Why current valuation is too high
3. Earnings Risks - Margin pressure, growth deceleration
4. Balance Sheet Risks - Debt, asset quality issues
5. Management Concerns - Execution, incentive misalignment
6. Catalysts for Decline - Near and medium-term risks
7. Bear Case Valuation - Downside price target

Return bear case as JSON.',
'You are a short-seller building a bear case.', 0.5)
ON CONFLICT (name) DO NOTHING;

-- Macro Analysis Prompts
INSERT INTO prompts (name, category, subcategory, description, prompt_template, system_prompt, temperature) VALUES
('macro_environment_analysis', 'macro', 'environment', 'Analyze current macro environment',
'Analyze the current macroeconomic environment.

Focus on:
1. Economic Growth - GDP trends, leading indicators
2. Inflation - CPI, PCE, wage growth
3. Monetary Policy - Fed stance, rate expectations
4. Fiscal Policy - Government spending, tax policy
5. Labor Market - Employment, participation, wages
6. Global Factors - International trade, geopolitics
7. Market Implications - Sector and style preferences

Return analysis as JSON.',
'You are a macro strategist analyzing economic conditions.', 0.4),

('sector_sensitivity_analysis', 'macro', 'sector', 'Analyze sector sensitivity to macro factors',
'Analyze how {{sector}} sector responds to macro factors.

Evaluate sensitivity to:
1. Interest Rates - Rate sensitivity and duration
2. Economic Growth - GDP correlation
3. Inflation - Input costs, pricing power
4. Dollar Strength - Export/import exposure
5. Commodity Prices - Input cost sensitivity
6. Credit Conditions - Financing needs

For each factor:
- Historical correlation
- Current positioning
- Forward outlook

Return analysis as JSON.',
'You are a sector strategist analyzing macro sensitivities.', 0.4)
ON CONFLICT (name) DO NOTHING;

-- Portfolio Management Prompts
INSERT INTO prompts (name, category, subcategory, description, prompt_template, system_prompt, temperature) VALUES
('position_sizing', 'portfolio', 'sizing', 'Calculate optimal position size',
'Calculate optimal position size for {{ticker}}.

Portfolio Context:
- Portfolio Value: {{portfolio_value}}
- Current Positions: {{current_positions}}
- Risk Budget: {{risk_budget}}

Analysis:
- Conviction Level: {{conviction}}
- Volatility: {{volatility}}
- Correlation: {{correlation}}

Provide:
1. Recommended position size (%)
2. Dollar amount
3. Risk contribution
4. Sizing rationale
5. Scaling strategy

Return sizing recommendation as JSON.',
'You are a portfolio manager optimizing position sizes.', 0.3),

('portfolio_risk_analysis', 'portfolio', 'risk', 'Analyze portfolio risk',
'Analyze portfolio risk for the following positions:

Positions: {{positions}}

Calculate and assess:
1. Portfolio VaR (95%, 99%)
2. Expected Shortfall
3. Beta and correlation matrix
4. Sector/factor exposures
5. Concentration risk
6. Tail risk scenarios
7. Recommendations for risk reduction

Return risk analysis as JSON.',
'You are a risk manager analyzing portfolio risk.', 0.3)
ON CONFLICT (name) DO NOTHING;

-- Create Prefect database
CREATE DATABASE prefect;
