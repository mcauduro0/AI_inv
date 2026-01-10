-- =============================================================================
-- Complete Prompt Library Seed Data
-- =============================================================================
-- 118 prompts from Wall Street Prompts and Notion Investing Library
-- =============================================================================

-- Clear existing prompts
TRUNCATE TABLE prompts CASCADE;

-- =============================================================================
-- CATEGORY 1: INVESTMENT IDEA GENERATION (20 prompts)
-- =============================================================================

INSERT INTO prompts (id, name, category, subcategory, description, prompt_template, input_variables, output_format, llm_provider, model_name, temperature, max_tokens, is_active, version) VALUES

-- 1. Thematic Candidate Screen
(gen_random_uuid(), 'thematic_candidate_screen', 'idea_generation', 'thematic', 
'Identifies investment candidates based on a specific investment theme',
'You are a senior equity research analyst specializing in thematic investing. Given the investment theme: "{{theme}}"

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

Output a ranked list with investment rationale for each candidate.',
'["theme"]',
'{"type": "json", "schema": {"companies": [{"ticker": "string", "name": "string", "revenue_exposure_pct": "number", "thesis": "string", "catalysts": ["string"], "risks": ["string"]}]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 2. Newsletter Idea Scraping
(gen_random_uuid(), 'newsletter_idea_scraping', 'idea_generation', 'alternative_sources',
'Extracts and analyzes investment ideas from financial newsletters',
'You are an investment analyst tasked with extracting actionable investment ideas from financial newsletters.

Analyze the following newsletter content: {{newsletter_content}}

For each investment idea mentioned:
1. Identify the ticker symbol and company name
2. Summarize the investment thesis in 2-3 sentences
3. Extract key data points and metrics cited
4. Identify the time horizon (short/medium/long term)
5. Note any price targets or valuation metrics mentioned
6. Assess the conviction level based on language used
7. Identify potential conflicts of interest or biases

Provide a structured summary suitable for further due diligence.',
'["newsletter_content"]',
'{"type": "json", "schema": {"ideas": [{"ticker": "string", "thesis": "string", "time_horizon": "string", "price_target": "number", "conviction": "string"}]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

-- 3. Institutional Clustering Analysis (SEC 13F)
(gen_random_uuid(), 'institutional_clustering_13f', 'idea_generation', 'sec_filings',
'Analyzes SEC 13F filings to identify institutional investor clustering',
'You are a quantitative analyst specializing in institutional ownership analysis.

Analyze the following 13F filing data for {{fund_name}}:
{{filing_data}}

Your analysis should:
1. Identify new positions initiated this quarter
2. Identify positions with significant increases (>25%)
3. Identify positions that were closed or significantly reduced
4. Calculate portfolio concentration metrics
5. Compare to previous quarters to identify trends
6. Cross-reference with other notable investors'' positions
7. Identify potential "crowded trades" where multiple funds are clustering

Focus on actionable insights that could inform investment decisions.',
'["fund_name", "filing_data"]',
'{"type": "json", "schema": {"new_positions": [{"ticker": "string", "shares": "number", "value": "number"}], "increased_positions": [{"ticker": "string", "change_pct": "number"}], "clustering_signals": [{"ticker": "string", "funds_count": "number"}]}}',
'openai', 'gpt-4', 0.2, 4000, true, 1),

-- 4. Theme First, Second, Third Order Effects
(gen_random_uuid(), 'theme_order_effects', 'idea_generation', 'thematic',
'Analyzes cascading effects of investment themes across industries',
'You are a strategic analyst specializing in second and third-order effects analysis.

Given the investment theme: "{{theme}}"

Map the cascading effects across the economy:

FIRST ORDER EFFECTS (Direct beneficiaries):
- Companies directly providing products/services related to the theme
- Immediate revenue impact

SECOND ORDER EFFECTS (Indirect beneficiaries):
- Suppliers and service providers to first-order companies
- Adjacent industries that benefit from theme adoption
- Infrastructure and enabling technology providers

THIRD ORDER EFFECTS (Downstream impacts):
- Industries disrupted or displaced by the theme
- New business models enabled
- Societal and regulatory changes
- Long-term structural shifts

For each order, identify 3-5 specific investment opportunities with tickers.',
'["theme"]',
'{"type": "json", "schema": {"first_order": [{"ticker": "string", "impact": "string"}], "second_order": [{"ticker": "string", "impact": "string"}], "third_order": [{"ticker": "string", "impact": "string"}]}}',
'openai', 'gpt-4', 0.4, 4000, true, 1),

-- 5. Pure-Play Filter
(gen_random_uuid(), 'pure_play_filter', 'idea_generation', 'screening',
'Filters companies to identify pure-play exposure to specific themes',
'You are an equity analyst specializing in identifying pure-play investment opportunities.

Given the theme: "{{theme}}" and the list of candidate companies: {{companies}}

For each company, analyze:
1. Revenue breakdown by segment/product line
2. Calculate percentage of revenue directly tied to the theme
3. Assess strategic focus and management commentary on the theme
4. Evaluate competitive moat within the theme
5. Consider geographic exposure to theme adoption

Classification criteria:
- PURE PLAY: >70% revenue exposure, core strategic focus
- SIGNIFICANT EXPOSURE: 30-70% revenue exposure
- DIVERSIFIED: <30% revenue exposure

Rank companies by "purity" of exposure and investment attractiveness.',
'["theme", "companies"]',
'{"type": "json", "schema": {"pure_plays": [{"ticker": "string", "exposure_pct": "number", "rationale": "string"}], "significant_exposure": [{"ticker": "string", "exposure_pct": "number"}], "diversified": [{"ticker": "string", "exposure_pct": "number"}]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

-- 6. Insider Trading Analysis (SEC Form-4)
(gen_random_uuid(), 'insider_trading_analysis', 'idea_generation', 'sec_filings',
'Analyzes SEC Form-4 filings for insider trading signals',
'You are a compliance and investment analyst specializing in insider transaction analysis.

Analyze the following Form-4 filing data for {{ticker}}:
{{form4_data}}

Your analysis should cover:
1. Transaction type (purchase, sale, option exercise, gift)
2. Transaction size relative to insider''s total holdings
3. Transaction timing (relative to earnings, announcements)
4. Insider role and historical trading patterns
5. Cluster buying/selling among multiple insiders
6. Comparison to sector peer insider activity

Provide a signal assessment:
- BULLISH: Significant open-market purchases by multiple insiders
- NEUTRAL: Routine transactions, option exercises, 10b5-1 plans
- BEARISH: Large sales outside of planned programs

Include historical context and statistical significance.',
'["ticker", "form4_data"]',
'{"type": "json", "schema": {"signal": "string", "transactions": [{"insider": "string", "type": "string", "shares": "number", "price": "number"}], "analysis": "string"}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

-- 7. Competitive Landscape & Value Chain Mapping
(gen_random_uuid(), 'competitive_landscape_mapping', 'idea_generation', 'industry',
'Maps competitive landscape and value chain for investment opportunities',
'You are a strategy consultant analyzing competitive dynamics.

For the industry/sector: "{{industry}}"

Create a comprehensive value chain and competitive landscape map:

VALUE CHAIN ANALYSIS:
1. Upstream (raw materials, components, suppliers)
2. Midstream (manufacturing, assembly, processing)
3. Downstream (distribution, retail, end customers)
4. Supporting activities (technology, logistics, services)

COMPETITIVE LANDSCAPE:
1. Market structure (fragmented, oligopoly, monopoly)
2. Key players and market shares
3. Barriers to entry
4. Competitive advantages by player
5. Disruptive threats

INVESTMENT OPPORTUNITIES:
Identify the most attractive positions in the value chain based on:
- Margin profiles
- Competitive moats
- Growth potential
- Capital intensity',
'["industry"]',
'{"type": "json", "schema": {"value_chain": {"upstream": ["string"], "midstream": ["string"], "downstream": ["string"]}, "competitors": [{"name": "string", "market_share": "number", "moat": "string"}], "opportunities": [{"ticker": "string", "position": "string", "thesis": "string"}]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 8. Sector Thesis Stress Testing
(gen_random_uuid(), 'sector_thesis_stress_test', 'idea_generation', 'risk',
'Stress tests investment theses against various scenarios',
'You are a risk analyst specializing in scenario analysis.

Given the investment thesis: "{{thesis}}"
For the sector/company: {{target}}

Stress test this thesis against:

MACRO SCENARIOS:
1. Recession (GDP -2%, unemployment +3%)
2. Inflation spike (CPI >5%)
3. Interest rate shock (+200bps)
4. Currency crisis (USD +/-20%)

SECTOR-SPECIFIC SCENARIOS:
1. Regulatory change (adverse)
2. Technological disruption
3. Competitive intensity increase
4. Supply chain disruption

For each scenario:
- Estimate revenue/earnings impact
- Assess balance sheet resilience
- Evaluate competitive position change
- Determine thesis survival probability

Provide an overall robustness score (1-10) with detailed justification.',
'["thesis", "target"]',
'{"type": "json", "schema": {"robustness_score": "number", "scenarios": [{"name": "string", "impact": "string", "thesis_survival": "boolean"}], "key_vulnerabilities": ["string"]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 9. Deep Web Trend Report Scanner
(gen_random_uuid(), 'deep_web_trend_scanner', 'idea_generation', 'alternative_sources',
'Scans alternative data sources for emerging investment trends',
'You are an alternative data analyst specializing in trend identification.

Analyze the following data sources for emerging investment trends:
{{data_sources}}

Your analysis should:
1. Identify emerging trends not yet mainstream
2. Quantify trend strength and momentum
3. Map trends to potential investment opportunities
4. Assess time horizon for trend materialization
5. Identify leading indicators to monitor

Data sources to consider:
- Patent filings and R&D trends
- Job postings and hiring patterns
- Academic research publications
- Startup funding patterns
- Social media sentiment shifts
- Search trend data
- Industry conference topics

Provide actionable investment ideas with specific tickers.',
'["data_sources"]',
'{"type": "json", "schema": {"trends": [{"name": "string", "strength": "number", "time_horizon": "string", "tickers": ["string"]}]}}',
'openai', 'gpt-4', 0.4, 4000, true, 1),

-- 10. Investment Theme Subsector Expansion
(gen_random_uuid(), 'theme_subsector_expansion', 'idea_generation', 'thematic',
'Expands investment themes into detailed subsector opportunities',
'You are a sector specialist expanding investment themes.

Given the broad investment theme: "{{theme}}"

Decompose into investable subsectors:

1. CORE SUBSECTORS (directly tied to theme)
   - Define each subsector
   - Size the addressable market
   - Identify growth drivers
   - List key players (with tickers)

2. ADJACENT SUBSECTORS (indirect beneficiaries)
   - Connection to core theme
   - Potential upside from theme adoption
   - Key players

3. ENABLING TECHNOLOGIES
   - Infrastructure requirements
   - Technology enablers
   - Service providers

For each subsector, provide:
- Market size and growth rate
- Competitive dynamics
- Top 3 investment candidates with brief thesis',
'["theme"]',
'{"type": "json", "schema": {"core_subsectors": [{"name": "string", "market_size": "string", "growth_rate": "string", "top_picks": [{"ticker": "string", "thesis": "string"}]}], "adjacent_subsectors": [{"name": "string", "connection": "string", "top_picks": [{"ticker": "string"}]}]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 11. Reddit Memestock Scraper
(gen_random_uuid(), 'reddit_memestock_scraper', 'idea_generation', 'social_sentiment',
'Analyzes Reddit for retail investor sentiment and memestock activity',
'You are a social sentiment analyst monitoring retail investor communities.

Analyze the following Reddit data from r/wallstreetbets and related subreddits:
{{reddit_data}}

Your analysis should:
1. Identify most mentioned tickers and sentiment
2. Track momentum in mentions over time
3. Identify emerging "meme" candidates
4. Assess quality of DD (due diligence) posts
5. Gauge overall market sentiment (bullish/bearish)
6. Identify potential short squeeze candidates
7. Flag pump-and-dump patterns

Provide a ranked list of tickers with:
- Mention frequency and trend
- Sentiment score (-1 to +1)
- Quality of underlying thesis
- Risk assessment for institutional investors',
'["reddit_data"]',
'{"type": "json", "schema": {"trending_tickers": [{"ticker": "string", "mentions": "number", "sentiment": "number", "quality_score": "number"}], "market_sentiment": "string", "risk_flags": ["string"]}}',
'perplexity', 'sonar-pro', 0.3, 3000, true, 1),

-- 12. Twitter Copytrading Scraper
(gen_random_uuid(), 'twitter_copytrading_scraper', 'idea_generation', 'social_sentiment',
'Monitors financial Twitter for investment ideas from notable accounts',
'You are a social media analyst tracking financial Twitter (FinTwit).

Analyze tweets from notable financial accounts:
{{twitter_data}}

Your analysis should:
1. Extract specific stock mentions and sentiment
2. Identify thesis summaries from threads
3. Track position changes announced
4. Assess credibility of sources
5. Cross-reference multiple sources for consensus
6. Identify contrarian views

For each idea extracted:
- Source credibility score
- Thesis summary
- Time horizon mentioned
- Price targets if any
- Potential conflicts of interest

Provide a curated list of high-conviction ideas from credible sources.',
'["twitter_data"]',
'{"type": "json", "schema": {"ideas": [{"ticker": "string", "source": "string", "credibility": "number", "thesis": "string", "sentiment": "string"}]}}',
'perplexity', 'sonar-pro', 0.3, 3000, true, 1),

-- 13. Under-the-Radar Discovery
(gen_random_uuid(), 'under_radar_discovery', 'idea_generation', 'screening',
'Identifies overlooked investment opportunities',
'You are a small-cap specialist identifying under-followed opportunities.

Screen for under-the-radar investment opportunities with these criteria:
- Market cap: {{market_cap_range}}
- Analyst coverage: <3 analysts
- Institutional ownership: <50%
- Trading volume: Sufficient liquidity

For qualifying companies, analyze:
1. Business quality and competitive position
2. Financial health and profitability
3. Growth trajectory
4. Management quality
5. Valuation relative to intrinsic value
6. Catalysts for re-rating

Identify why the stock may be overlooked:
- Size constraints for large funds
- Lack of sell-side coverage
- Complex business model
- Recent IPO or spin-off
- Temporary operational issues

Provide a ranked list of opportunities with investment thesis.',
'["market_cap_range"]',
'{"type": "json", "schema": {"opportunities": [{"ticker": "string", "market_cap": "number", "analyst_coverage": "number", "thesis": "string", "catalysts": ["string"], "why_overlooked": "string"}]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 14. Identifying Public Companies & Pure Plays
(gen_random_uuid(), 'identify_pure_plays', 'idea_generation', 'screening',
'Identifies publicly traded pure-play companies for specific themes',
'You are an equity research analyst identifying pure-play opportunities.

For the investment theme: "{{theme}}"

Identify all publicly traded companies with significant exposure:

SCREENING CRITERIA:
1. Direct revenue from theme >30%
2. Listed on major exchanges (NYSE, NASDAQ, LSE, etc.)
3. Market cap >$500M for liquidity
4. Positive revenue growth in theme-related segments

For each company:
- Ticker and exchange
- Revenue breakdown by segment
- Theme exposure percentage
- Competitive position
- Growth outlook
- Key risks

Categorize as:
- TIER 1: Pure plays (>70% exposure)
- TIER 2: Significant exposure (30-70%)
- TIER 3: Diversified with exposure (<30%)

Include both US and international listings.',
'["theme"]',
'{"type": "json", "schema": {"tier1": [{"ticker": "string", "exposure": "number", "thesis": "string"}], "tier2": [{"ticker": "string", "exposure": "number"}], "tier3": [{"ticker": "string", "exposure": "number"}]}}',
'openai', 'gpt-4', 0.2, 4000, true, 1),

-- 15. Connecting Disparate Trends
(gen_random_uuid(), 'connecting_disparate_trends', 'idea_generation', 'thematic',
'Identifies investment opportunities at the intersection of multiple trends',
'You are a cross-sector strategist identifying convergent opportunities.

Analyze the following trends:
{{trends}}

Identify investment opportunities at the intersection:

1. TREND CONVERGENCE ANALYSIS
   - How do these trends reinforce each other?
   - What new markets are created at intersections?
   - What existing markets are disrupted?

2. INTERSECTION OPPORTUNITIES
   - Companies positioned at multiple trend intersections
   - New business models enabled by convergence
   - Infrastructure plays benefiting from multiple trends

3. TIMING ANALYSIS
   - Which intersections are investable now?
   - Which are 2-3 years out?
   - Which are speculative (5+ years)?

For each opportunity:
- Specific ticker and thesis
- Trend exposure breakdown
- Competitive advantage from convergence
- Risk factors',
'["trends"]',
'{"type": "json", "schema": {"intersections": [{"trends": ["string"], "opportunity": "string", "tickers": [{"ticker": "string", "thesis": "string"}], "timing": "string"}]}}',
'openai', 'gpt-4', 0.4, 4000, true, 1),

-- 16. Historical Parallel Thesis Stress Testing
(gen_random_uuid(), 'historical_parallel_stress_test', 'idea_generation', 'risk',
'Tests investment theses against historical analogues',
'You are a market historian analyzing investment theses.

Given the investment thesis: "{{thesis}}"
For company/sector: {{target}}

Identify historical parallels and test the thesis:

1. HISTORICAL ANALOGUES
   - Similar market conditions in history
   - Comparable company situations
   - Relevant sector cycles

2. PARALLEL ANALYSIS
   - How did similar situations resolve?
   - What were the key success/failure factors?
   - What was the typical time horizon?

3. THESIS IMPLICATIONS
   - Does history support or refute the thesis?
   - What adjustments should be made?
   - What warning signs to monitor?

4. PROBABILITY ASSESSMENT
   - Base rate of success for similar theses
   - Key differentiating factors for this case
   - Confidence interval for outcomes

Provide specific historical examples with dates and outcomes.',
'["thesis", "target"]',
'{"type": "json", "schema": {"historical_parallels": [{"period": "string", "situation": "string", "outcome": "string", "relevance": "string"}], "thesis_assessment": "string", "success_probability": "number", "key_factors": ["string"]}}',
'anthropic', 'claude-3-opus', 0.3, 4000, true, 1),

-- 17. Niche Publication Scanner
(gen_random_uuid(), 'niche_publication_scanner', 'idea_generation', 'alternative_sources',
'Scans niche industry publications for investment ideas',
'You are a research analyst mining niche publications for ideas.

Analyze content from the following niche publications:
{{publication_content}}

Industry focus: {{industry}}

Extract investment-relevant information:

1. INDUSTRY DEVELOPMENTS
   - New product launches
   - Regulatory changes
   - Technology shifts
   - M&A activity

2. COMPANY-SPECIFIC INSIGHTS
   - Market share changes
   - Operational developments
   - Management changes
   - Financial indicators

3. COMPETITIVE DYNAMICS
   - New entrants
   - Exits or consolidation
   - Pricing trends
   - Capacity changes

4. INVESTMENT IMPLICATIONS
   - Potential winners and losers
   - Timing considerations
   - Risk factors

Provide specific, actionable insights with ticker symbols.',
'["publication_content", "industry"]',
'{"type": "json", "schema": {"insights": [{"type": "string", "description": "string", "tickers_affected": ["string"], "investment_implication": "string"}]}}',
'openai', 'gpt-4', 0.3, 3000, true, 1),

-- 18. Substack Investment Idea Scraping
(gen_random_uuid(), 'substack_idea_scraping', 'idea_generation', 'alternative_sources',
'Extracts investment ideas from Substack newsletters',
'You are an analyst curating ideas from investment Substacks.

Analyze the following Substack content:
{{substack_content}}

For each investment idea:
1. Extract the core thesis
2. Identify supporting data and analysis
3. Note the author''s track record if known
4. Assess the depth and quality of research
5. Identify potential biases or conflicts
6. Extract specific price targets or valuations
7. Note the recommended position sizing

Quality assessment criteria:
- Depth of primary research
- Quality of financial analysis
- Consideration of risks
- Clarity of thesis
- Track record of author

Provide a curated list ranked by quality and conviction.',
'["substack_content"]',
'{"type": "json", "schema": {"ideas": [{"ticker": "string", "author": "string", "thesis": "string", "quality_score": "number", "price_target": "number", "risks": ["string"]}]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

-- 19. Idea Candidates Based on Thematic Generator
(gen_random_uuid(), 'thematic_idea_generator', 'idea_generation', 'thematic',
'Generates investment candidates based on thematic analysis',
'You are a thematic investment strategist.

Generate investment candidates for the theme: "{{theme}}"

THEME ANALYSIS:
1. Define the theme and its investment relevance
2. Identify key drivers and catalysts
3. Estimate total addressable market
4. Project growth trajectory (5-10 years)

CANDIDATE GENERATION:
For each candidate, provide:
- Company name and ticker
- Business description
- Theme exposure (% of revenue)
- Competitive advantages
- Growth potential from theme
- Key risks
- Valuation context

Generate candidates across:
- Large cap leaders
- Mid cap growth
- Small cap emerging
- International exposure

Rank by risk-adjusted return potential.',
'["theme"]',
'{"type": "json", "schema": {"theme_analysis": {"tam": "string", "growth_rate": "string", "drivers": ["string"]}, "candidates": [{"ticker": "string", "market_cap": "string", "exposure": "number", "thesis": "string", "risk_adjusted_rank": "number"}]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 20. Presentation Creator
(gen_random_uuid(), 'investment_presentation_creator', 'idea_generation', 'output',
'Creates investment presentation from research',
'You are an investment banking analyst creating a pitch.

Create an investment presentation for: {{ticker}}
Based on the following research: {{research_summary}}

PRESENTATION STRUCTURE:

SLIDE 1: Executive Summary
- Investment recommendation
- Key thesis points
- Target price and upside

SLIDE 2: Company Overview
- Business description
- Key products/services
- Geographic presence

SLIDE 3: Investment Thesis
- 3-4 key thesis points
- Supporting evidence

SLIDE 4: Industry Analysis
- Market size and growth
- Competitive positioning
- Industry trends

SLIDE 5: Financial Analysis
- Revenue and earnings trends
- Margin analysis
- Balance sheet strength

SLIDE 6: Valuation
- Valuation methodology
- Comparable analysis
- DCF summary

SLIDE 7: Risks
- Key risk factors
- Mitigants

SLIDE 8: Catalysts & Timeline
- Near-term catalysts
- Investment timeline

Provide content for each slide in presentation-ready format.',
'["ticker", "research_summary"]',
'{"type": "json", "schema": {"slides": [{"title": "string", "content": ["string"], "key_points": ["string"]}]}}',
'anthropic', 'claude-3-opus', 0.3, 5000, true, 1);

-- =============================================================================
-- CATEGORY 2: DUE DILIGENCE (36 prompts)
-- =============================================================================

INSERT INTO prompts (id, name, category, subcategory, description, prompt_template, input_variables, output_format, llm_provider, model_name, temperature, max_tokens, is_active, version) VALUES

-- 21. Business Overview Report
(gen_random_uuid(), 'business_overview_report', 'due_diligence', 'business_model',
'Comprehensive business overview and model analysis',
'You are a senior equity research analyst preparing a comprehensive business overview.

Company: {{ticker}}

Provide a detailed analysis covering:

1. BUSINESS DESCRIPTION
   - What does the company do?
   - Core products and services
   - Revenue model and pricing
   - Customer segments

2. BUSINESS MODEL ANALYSIS
   - Value proposition
   - Key resources and capabilities
   - Cost structure
   - Revenue streams breakdown

3. COMPETITIVE POSITION
   - Market position and share
   - Key competitors
   - Competitive advantages (moat)
   - Barriers to entry

4. GROWTH STRATEGY
   - Organic growth initiatives
   - M&A strategy
   - Geographic expansion
   - New product development

5. KEY SUCCESS FACTORS
   - Critical success factors
   - Key performance indicators
   - Management priorities

Provide specific data points and cite sources where possible.',
'["ticker"]',
'{"type": "json", "schema": {"business_description": "string", "revenue_model": "string", "competitive_position": "string", "growth_strategy": "string", "key_metrics": {"revenue": "number", "market_share": "number"}}}',
'openai', 'gpt-4', 0.2, 5000, true, 1),

-- 22. Business Economics Analysis
(gen_random_uuid(), 'business_economics', 'due_diligence', 'business_model',
'Analyzes unit economics and business model sustainability',
'You are a business analyst evaluating unit economics.

Company: {{ticker}}

Analyze the business economics:

1. UNIT ECONOMICS
   - Customer acquisition cost (CAC)
   - Lifetime value (LTV)
   - LTV/CAC ratio
   - Payback period
   - Contribution margin

2. OPERATING LEVERAGE
   - Fixed vs variable cost structure
   - Breakeven analysis
   - Margin expansion potential

3. CAPITAL EFFICIENCY
   - Return on invested capital (ROIC)
   - Asset turnover
   - Working capital requirements
   - Capital intensity

4. SCALABILITY
   - Marginal economics at scale
   - Network effects
   - Economies of scale/scope

5. SUSTAINABILITY
   - Recurring revenue %
   - Customer retention/churn
   - Pricing power

Provide quantitative analysis with historical trends.',
'["ticker"]',
'{"type": "json", "schema": {"unit_economics": {"cac": "number", "ltv": "number", "ltv_cac_ratio": "number"}, "roic": "number", "scalability_score": "number"}}',
'openai', 'gpt-4', 0.2, 4000, true, 1),

-- 23. Growth & Margin Drivers
(gen_random_uuid(), 'growth_margin_drivers', 'due_diligence', 'financial',
'Identifies and analyzes key growth and margin drivers',
'You are a financial analyst identifying growth and margin drivers.

Company: {{ticker}}

GROWTH DRIVERS ANALYSIS:

1. REVENUE GROWTH DRIVERS
   - Volume growth (units, customers, transactions)
   - Price/mix improvement
   - New product contribution
   - Geographic expansion
   - M&A contribution

2. HISTORICAL DECOMPOSITION
   - Break down historical growth by driver
   - Identify sustainable vs one-time factors
   - Trend analysis by driver

3. MARGIN DRIVERS
   - Gross margin drivers
   - Operating leverage
   - Cost reduction initiatives
   - Mix shift impact

4. FORWARD PROJECTIONS
   - Expected contribution by driver
   - Risks to each driver
   - Sensitivity analysis

Provide specific percentages and dollar amounts where possible.',
'["ticker"]',
'{"type": "json", "schema": {"revenue_drivers": [{"driver": "string", "contribution_pct": "number", "trend": "string"}], "margin_drivers": [{"driver": "string", "impact_bps": "number"}], "projections": {"revenue_growth": "number", "margin_expansion": "number"}}}',
'openai', 'gpt-4', 0.2, 4000, true, 1),

-- 24. Financial Statement Deep Dive
(gen_random_uuid(), 'financial_statement_analysis', 'due_diligence', 'financial',
'Comprehensive financial statement analysis',
'You are a forensic accountant analyzing financial statements.

Company: {{ticker}}
Financial Data: {{financial_data}}

Perform a comprehensive analysis:

1. INCOME STATEMENT ANALYSIS
   - Revenue recognition policies
   - Gross margin trends and drivers
   - Operating expense analysis
   - Non-recurring items
   - Earnings quality assessment

2. BALANCE SHEET ANALYSIS
   - Asset quality review
   - Working capital analysis
   - Debt structure and covenants
   - Off-balance sheet items
   - Goodwill and intangibles

3. CASH FLOW ANALYSIS
   - Operating cash flow quality
   - CapEx requirements
   - Free cash flow generation
   - Cash conversion cycle

4. RED FLAGS SCREENING
   - Aggressive accounting
   - Related party transactions
   - Audit opinion issues
   - Restatement history

5. KEY RATIOS
   - Profitability ratios
   - Liquidity ratios
   - Solvency ratios
   - Efficiency ratios

Highlight any concerns or areas requiring further investigation.',
'["ticker", "financial_data"]',
'{"type": "json", "schema": {"earnings_quality_score": "number", "red_flags": ["string"], "key_ratios": {"roe": "number", "roic": "number", "debt_to_equity": "number"}, "concerns": ["string"]}}',
'openai', 'gpt-4', 0.2, 5000, true, 1),

-- 25. Management Quality Assessment
(gen_random_uuid(), 'management_quality_assessment', 'due_diligence', 'management',
'Evaluates management team quality and track record',
'You are an executive assessment specialist evaluating management.

Company: {{ticker}}

MANAGEMENT ASSESSMENT:

1. CEO EVALUATION
   - Background and experience
   - Track record at current company
   - Previous company performance
   - Leadership style
   - Compensation alignment

2. MANAGEMENT TEAM
   - Key executives and tenure
   - Depth of bench
   - Recent departures
   - Insider ownership

3. CAPITAL ALLOCATION TRACK RECORD
   - M&A history and returns
   - Organic investment returns
   - Dividend/buyback decisions
   - Balance sheet management

4. CORPORATE GOVERNANCE
   - Board composition and independence
   - Shareholder rights
   - Related party transactions
   - ESG considerations

5. COMMUNICATION & CREDIBILITY
   - Guidance accuracy
   - Transparency
   - Investor relations quality

Provide a management quality score (1-10) with justification.',
'["ticker"]',
'{"type": "json", "schema": {"management_score": "number", "ceo_assessment": "string", "capital_allocation_grade": "string", "governance_score": "number", "key_concerns": ["string"]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 26. Industry Overview
(gen_random_uuid(), 'industry_overview', 'due_diligence', 'industry',
'Comprehensive industry analysis',
'You are an industry analyst providing a sector overview.

Industry: {{industry}}

INDUSTRY ANALYSIS:

1. MARKET STRUCTURE
   - Market size and growth
   - Key segments
   - Geographic breakdown
   - Cyclicality

2. COMPETITIVE DYNAMICS
   - Porter''s Five Forces analysis
   - Market concentration
   - Key success factors
   - Barriers to entry

3. VALUE CHAIN
   - Industry value chain map
   - Margin distribution
   - Power dynamics

4. TRENDS & DISRUPTION
   - Key industry trends
   - Technology impact
   - Regulatory environment
   - ESG considerations

5. OUTLOOK
   - Growth projections
   - Key catalysts/risks
   - Structural changes

Identify the most attractive segments and positioning.',
'["industry"]',
'{"type": "json", "schema": {"market_size": "number", "growth_rate": "number", "concentration": "string", "attractiveness_score": "number", "key_trends": ["string"], "top_players": [{"name": "string", "market_share": "number"}]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 27. Competitive Analysis
(gen_random_uuid(), 'competitive_analysis', 'due_diligence', 'industry',
'Detailed competitive positioning analysis',
'You are a competitive intelligence analyst.

Company: {{ticker}}
Competitors: {{competitors}}

COMPETITIVE ANALYSIS:

1. MARKET POSITIONING
   - Market share by segment
   - Geographic positioning
   - Customer segment focus
   - Price positioning

2. COMPETITIVE ADVANTAGES
   - Source of competitive advantage
   - Sustainability of moat
   - Relative strengths/weaknesses

3. COMPARATIVE ANALYSIS
   - Financial comparison (growth, margins, returns)
   - Operational comparison
   - Strategic comparison
   - Valuation comparison

4. COMPETITIVE THREATS
   - Direct competitors
   - New entrants
   - Substitutes
   - Disruptive technologies

5. COMPETITIVE RESPONSE
   - Historical competitive actions
   - Likely responses to threats
   - Strategic options

Create a competitive scorecard with rankings.',
'["ticker", "competitors"]',
'{"type": "json", "schema": {"market_position": "string", "competitive_advantages": ["string"], "scorecard": [{"metric": "string", "company_score": "number", "peer_avg": "number"}], "threats": ["string"]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 28. Valuation Analysis
(gen_random_uuid(), 'valuation_analysis', 'due_diligence', 'valuation',
'Comprehensive valuation analysis',
'You are a valuation specialist performing intrinsic value analysis.

Company: {{ticker}}
Financial Data: {{financial_data}}

VALUATION ANALYSIS:

1. DCF VALUATION
   - Revenue projections (5-year)
   - Margin assumptions
   - CapEx and working capital
   - Terminal value assumptions
   - WACC calculation
   - Sensitivity analysis

2. COMPARABLE COMPANY ANALYSIS
   - Peer group selection
   - Trading multiples (EV/EBITDA, P/E, EV/Revenue)
   - Premium/discount justification
   - Implied valuation range

3. PRECEDENT TRANSACTIONS
   - Relevant M&A transactions
   - Transaction multiples
   - Control premium analysis

4. SUM-OF-THE-PARTS
   - Segment valuation
   - Hidden assets
   - Conglomerate discount/premium

5. VALUATION SUMMARY
   - Triangulated fair value
   - Upside/downside scenarios
   - Key value drivers
   - Margin of safety

Provide specific price targets with probability weighting.',
'["ticker", "financial_data"]',
'{"type": "json", "schema": {"dcf_value": "number", "comps_value": "number", "fair_value": "number", "current_price": "number", "upside_pct": "number", "key_assumptions": ["string"]}}',
'openai', 'gpt-4', 0.2, 5000, true, 1),

-- 29. Risk Assessment
(gen_random_uuid(), 'risk_assessment', 'due_diligence', 'risk',
'Comprehensive risk identification and assessment',
'You are a risk analyst identifying investment risks.

Company: {{ticker}}

RISK ASSESSMENT:

1. BUSINESS RISKS
   - Customer concentration
   - Supplier dependency
   - Technology obsolescence
   - Competitive threats
   - Execution risks

2. FINANCIAL RISKS
   - Leverage and liquidity
   - Currency exposure
   - Interest rate sensitivity
   - Covenant compliance
   - Pension obligations

3. REGULATORY/LEGAL RISKS
   - Regulatory environment
   - Pending litigation
   - Compliance issues
   - Political/policy risks

4. ESG RISKS
   - Environmental liabilities
   - Social/labor issues
   - Governance concerns

5. MACRO RISKS
   - Economic sensitivity
   - Geopolitical exposure
   - Commodity exposure

For each risk:
- Probability (High/Medium/Low)
- Impact (High/Medium/Low)
- Mitigants
- Monitoring indicators

Create a risk matrix and overall risk score.',
'["ticker"]',
'{"type": "json", "schema": {"overall_risk_score": "number", "risks": [{"category": "string", "risk": "string", "probability": "string", "impact": "string", "mitigant": "string"}], "key_risks": ["string"]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 30. Earnings Quality Analysis
(gen_random_uuid(), 'earnings_quality_analysis', 'due_diligence', 'financial',
'Assesses quality and sustainability of earnings',
'You are a forensic accountant assessing earnings quality.

Company: {{ticker}}
Financial Data: {{financial_data}}

EARNINGS QUALITY ASSESSMENT:

1. ACCRUALS ANALYSIS
   - Accruals ratio
   - Change in working capital
   - Deferred revenue trends
   - Accrued expenses

2. CASH CONVERSION
   - CFO to Net Income ratio
   - Free cash flow yield
   - Cash earnings vs reported

3. REVENUE QUALITY
   - Revenue recognition policies
   - Deferred revenue
   - Contract assets/liabilities
   - Channel stuffing indicators

4. EXPENSE QUALITY
   - Capitalization policies
   - Depreciation/amortization
   - Stock compensation
   - Restructuring charges

5. ONE-TIME ITEMS
   - Non-recurring gains/losses
   - Asset sales
   - Tax benefits
   - Pension adjustments

6. RED FLAGS
   - Beneish M-Score
   - Altman Z-Score
   - Piotroski F-Score
   - Audit opinion

Provide an earnings quality score (1-10) with detailed justification.',
'["ticker", "financial_data"]',
'{"type": "json", "schema": {"earnings_quality_score": "number", "cfo_to_ni_ratio": "number", "accruals_ratio": "number", "red_flags": ["string"], "adjustments": [{"item": "string", "amount": "number"}]}}',
'openai', 'gpt-4', 0.2, 4000, true, 1),

-- 31. Capital Allocation Analysis
(gen_random_uuid(), 'capital_allocation_analysis', 'due_diligence', 'financial',
'Evaluates capital allocation decisions and returns',
'You are a capital allocation specialist.

Company: {{ticker}}

CAPITAL ALLOCATION ANALYSIS:

1. HISTORICAL ALLOCATION
   - CapEx (maintenance vs growth)
   - M&A activity and returns
   - R&D investment
   - Dividends and buybacks
   - Debt paydown

2. RETURN ON CAPITAL
   - ROIC by segment
   - Incremental ROIC
   - Return on acquisitions
   - Buyback effectiveness

3. BALANCE SHEET OPTIMIZATION
   - Optimal capital structure
   - Current vs target leverage
   - Cash deployment priorities

4. MANAGEMENT FRAMEWORK
   - Stated capital allocation priorities
   - Hurdle rates
   - Decision-making process

5. FORWARD OUTLOOK
   - Expected allocation mix
   - M&A pipeline
   - Capacity for shareholder returns

Assess management''s capital allocation skill and alignment.',
'["ticker"]',
'{"type": "json", "schema": {"capital_allocation_score": "number", "roic": "number", "incremental_roic": "number", "allocation_mix": {"capex_pct": "number", "ma_pct": "number", "dividends_pct": "number", "buybacks_pct": "number"}, "assessment": "string"}}',
'openai', 'gpt-4', 0.2, 4000, true, 1),

-- 32. Short Interest Analysis
(gen_random_uuid(), 'short_interest_analysis', 'due_diligence', 'technical',
'Analyzes short interest and potential short squeeze dynamics',
'You are a quantitative analyst analyzing short interest.

Company: {{ticker}}
Short Interest Data: {{short_data}}

SHORT INTEREST ANALYSIS:

1. CURRENT METRICS
   - Short interest (shares and %)
   - Days to cover
   - Short interest ratio
   - Cost to borrow

2. HISTORICAL TRENDS
   - Short interest over time
   - Correlation with price
   - Changes around events

3. PEER COMPARISON
   - Relative short interest
   - Sector average
   - Outlier analysis

4. SHORT THESIS ASSESSMENT
   - Likely short thesis
   - Validity of concerns
   - Potential catalysts for covering

5. SQUEEZE POTENTIAL
   - Technical setup
   - Float analysis
   - Institutional ownership
   - Options market activity

Provide a short squeeze probability score and key triggers.',
'["ticker", "short_data"]',
'{"type": "json", "schema": {"short_interest_pct": "number", "days_to_cover": "number", "squeeze_probability": "number", "short_thesis": "string", "key_triggers": ["string"]}}',
'openai', 'gpt-4', 0.3, 3000, true, 1),

-- 33. Insider Activity Analysis
(gen_random_uuid(), 'insider_activity_analysis', 'due_diligence', 'technical',
'Analyzes insider buying and selling patterns',
'You are an analyst specializing in insider transaction analysis.

Company: {{ticker}}
Insider Data: {{insider_data}}

INSIDER ACTIVITY ANALYSIS:

1. RECENT TRANSACTIONS
   - Purchases vs sales
   - Transaction sizes
   - Insider roles
   - Transaction types

2. PATTERN ANALYSIS
   - Historical patterns
   - Timing relative to announcements
   - Cluster activity

3. SIGNAL ASSESSMENT
   - Open market purchases (bullish)
   - 10b5-1 plan sales (neutral)
   - Discretionary sales (potentially bearish)
   - Option exercises

4. CONTEXT
   - Compensation structure
   - Diversification needs
   - Historical accuracy of signals

5. PEER COMPARISON
   - Relative insider activity
   - Sector trends

Provide an insider sentiment score and key observations.',
'["ticker", "insider_data"]',
'{"type": "json", "schema": {"insider_sentiment_score": "number", "net_shares_traded": "number", "notable_transactions": [{"insider": "string", "type": "string", "shares": "number", "date": "string"}], "signal": "string"}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

-- 34. ESG Analysis
(gen_random_uuid(), 'esg_analysis', 'due_diligence', 'esg',
'Environmental, Social, and Governance analysis',
'You are an ESG analyst evaluating sustainability factors.

Company: {{ticker}}

ESG ANALYSIS:

1. ENVIRONMENTAL
   - Carbon footprint and targets
   - Energy efficiency
   - Waste management
   - Water usage
   - Climate risk exposure

2. SOCIAL
   - Employee relations
   - Diversity and inclusion
   - Supply chain labor practices
   - Community impact
   - Product safety

3. GOVERNANCE
   - Board composition
   - Executive compensation
   - Shareholder rights
   - Business ethics
   - Transparency

4. MATERIALITY ASSESSMENT
   - Industry-specific ESG factors
   - Financial materiality
   - Stakeholder priorities

5. RATINGS & BENCHMARKS
   - Third-party ESG ratings
   - Peer comparison
   - Improvement trajectory

6. INVESTMENT IMPLICATIONS
   - ESG risks to thesis
   - Opportunities from ESG leadership
   - Regulatory considerations

Provide ESG scores by category and overall.',
'["ticker"]',
'{"type": "json", "schema": {"overall_esg_score": "number", "environmental_score": "number", "social_score": "number", "governance_score": "number", "material_issues": ["string"], "investment_implications": "string"}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 35. Catalyst Identification
(gen_random_uuid(), 'catalyst_identification', 'due_diligence', 'catalysts',
'Identifies potential stock price catalysts',
'You are an event-driven analyst identifying catalysts.

Company: {{ticker}}

CATALYST ANALYSIS:

1. NEAR-TERM CATALYSTS (0-6 months)
   - Earnings releases
   - Product launches
   - Regulatory decisions
   - M&A announcements
   - Management changes

2. MEDIUM-TERM CATALYSTS (6-18 months)
   - Strategic initiatives
   - Market expansion
   - Cost restructuring
   - Capital returns

3. LONG-TERM CATALYSTS (18+ months)
   - Industry transformation
   - Technology adoption
   - Regulatory changes
   - Competitive dynamics

4. NEGATIVE CATALYSTS (RISKS)
   - Potential disappointments
   - Competitive threats
   - Regulatory risks
   - Macro headwinds

For each catalyst:
- Expected timing
- Probability
- Potential price impact
- How to monitor

Create a catalyst calendar with expected dates.',
'["ticker"]',
'{"type": "json", "schema": {"catalysts": [{"description": "string", "timing": "string", "probability": "number", "price_impact_pct": "number", "type": "string"}], "catalyst_calendar": [{"date": "string", "event": "string"}]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 36. Bull/Bear Case Analysis
(gen_random_uuid(), 'bull_bear_analysis', 'due_diligence', 'thesis',
'Develops bull and bear investment cases',
'You are a research analyst developing investment scenarios.

Company: {{ticker}}

SCENARIO ANALYSIS:

1. BULL CASE
   - Key assumptions
   - Revenue/earnings trajectory
   - Multiple expansion potential
   - Target price and upside
   - Probability assessment

2. BASE CASE
   - Consensus assumptions
   - Expected performance
   - Fair value estimate
   - Key drivers

3. BEAR CASE
   - Risk scenarios
   - Downside assumptions
   - Trough valuation
   - Target price and downside
   - Probability assessment

4. SCENARIO COMPARISON
   - Key differentiating factors
   - Signposts to monitor
   - Decision triggers

5. EXPECTED VALUE
   - Probability-weighted return
   - Risk/reward assessment
   - Position sizing implications

Provide specific price targets for each scenario.',
'["ticker"]',
'{"type": "json", "schema": {"bull_case": {"price_target": "number", "upside_pct": "number", "probability": "number", "key_assumptions": ["string"]}, "base_case": {"price_target": "number", "probability": "number"}, "bear_case": {"price_target": "number", "downside_pct": "number", "probability": "number"}, "expected_return": "number"}}',
'openai', 'gpt-4', 0.3, 4000, true, 1);

-- Continue with more prompts...
-- (Adding remaining prompts in subsequent INSERT statements for readability)

-- =============================================================================
-- CATEGORY 2: DUE DILIGENCE (continued)
-- =============================================================================

INSERT INTO prompts (id, name, category, subcategory, description, prompt_template, input_variables, output_format, llm_provider, model_name, temperature, max_tokens, is_active, version) VALUES

-- 37. CEO Track Record Analysis
(gen_random_uuid(), 'ceo_track_record', 'due_diligence', 'management',
'Detailed CEO track record and performance analysis',
'You are an executive assessment specialist.

Analyze the CEO track record for: {{ticker}}
CEO Name: {{ceo_name}}

CEO TRACK RECORD ANALYSIS:

1. CAREER HISTORY
   - Previous roles and companies
   - Performance at each role
   - Industry experience
   - Education and credentials

2. CURRENT TENURE
   - Time in role
   - Stock performance during tenure
   - Operational achievements
   - Strategic decisions

3. CAPITAL ALLOCATION
   - M&A track record
   - Organic investment returns
   - Shareholder return decisions

4. LEADERSHIP STYLE
   - Management philosophy
   - Organizational changes
   - Culture impact
   - Communication style

5. COMPENSATION ANALYSIS
   - Pay structure
   - Performance alignment
   - Ownership stake
   - Peer comparison

Provide a CEO quality score with detailed justification.',
'["ticker", "ceo_name"]',
'{"type": "json", "schema": {"ceo_score": "number", "tenure_years": "number", "stock_performance_vs_index": "number", "key_achievements": ["string"], "concerns": ["string"]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 38. Supply Chain Analysis
(gen_random_uuid(), 'supply_chain_analysis', 'due_diligence', 'operations',
'Analyzes supply chain risks and dependencies',
'You are a supply chain analyst.

Company: {{ticker}}

SUPPLY CHAIN ANALYSIS:

1. SUPPLIER ANALYSIS
   - Key suppliers and dependencies
   - Geographic concentration
   - Single-source risks
   - Supplier financial health

2. MANUFACTURING
   - Production facilities
   - Capacity utilization
   - Automation level
   - Quality control

3. LOGISTICS
   - Distribution network
   - Inventory management
   - Lead times
   - Transportation costs

4. RISK ASSESSMENT
   - Supply disruption risks
   - Geopolitical exposure
   - Natural disaster vulnerability
   - Commodity price exposure

5. RESILIENCE
   - Diversification efforts
   - Safety stock levels
   - Alternative sourcing
   - Vertical integration

Identify key supply chain risks and mitigants.',
'["ticker"]',
'{"type": "json", "schema": {"supply_chain_risk_score": "number", "key_suppliers": [{"name": "string", "dependency": "string", "risk": "string"}], "geographic_exposure": {"region": "string", "percentage": "number"}, "vulnerabilities": ["string"]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 39. Customer Analysis
(gen_random_uuid(), 'customer_analysis', 'due_diligence', 'business_model',
'Analyzes customer base and concentration',
'You are a customer analytics specialist.

Company: {{ticker}}

CUSTOMER ANALYSIS:

1. CUSTOMER BASE
   - Total customers/users
   - Customer segments
   - Geographic distribution
   - Customer size distribution

2. CONCENTRATION
   - Top 10 customer revenue %
   - Single customer dependency
   - Sector concentration

3. CUSTOMER ECONOMICS
   - Customer acquisition cost
   - Lifetime value
   - Retention/churn rates
   - Net revenue retention

4. CUSTOMER SATISFACTION
   - NPS scores
   - Customer reviews
   - Complaint trends
   - Competitive win rates

5. GROWTH DYNAMICS
   - New customer growth
   - Expansion revenue
   - Cross-sell/upsell success
   - Market penetration

Assess customer quality and concentration risk.',
'["ticker"]',
'{"type": "json", "schema": {"customer_quality_score": "number", "top_10_concentration": "number", "retention_rate": "number", "nrr": "number", "key_risks": ["string"]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 40. Regulatory Risk Analysis
(gen_random_uuid(), 'regulatory_risk_analysis', 'due_diligence', 'risk',
'Assesses regulatory and legal risks',
'You are a regulatory affairs analyst.

Company: {{ticker}}
Industry: {{industry}}

REGULATORY RISK ANALYSIS:

1. REGULATORY ENVIRONMENT
   - Key regulators
   - Current regulations
   - Compliance requirements
   - Licensing/permits

2. PENDING CHANGES
   - Proposed regulations
   - Legislative activity
   - Regulatory trends
   - Timeline for changes

3. COMPLIANCE STATUS
   - Historical compliance
   - Current investigations
   - Consent decrees
   - Remediation efforts

4. LITIGATION
   - Pending lawsuits
   - Class actions
   - Patent disputes
   - Potential liabilities

5. POLITICAL RISK
   - Policy sensitivity
   - Lobbying activity
   - Political exposure
   - Trade policy impact

Quantify potential financial impact of regulatory risks.',
'["ticker", "industry"]',
'{"type": "json", "schema": {"regulatory_risk_score": "number", "pending_regulations": [{"description": "string", "impact": "string", "timeline": "string"}], "litigation_exposure": "number", "key_risks": ["string"]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 41. Technology & IP Analysis
(gen_random_uuid(), 'technology_ip_analysis', 'due_diligence', 'operations',
'Analyzes technology assets and intellectual property',
'You are a technology and IP analyst.

Company: {{ticker}}

TECHNOLOGY & IP ANALYSIS:

1. TECHNOLOGY STACK
   - Core technologies
   - Proprietary systems
   - Technical capabilities
   - R&D focus areas

2. INTELLECTUAL PROPERTY
   - Patent portfolio
   - Key patents and expiration
   - Trade secrets
   - Trademarks/brands

3. COMPETITIVE ADVANTAGE
   - Technology moat
   - Barriers to replication
   - First-mover advantages
   - Network effects

4. R&D EFFECTIVENESS
   - R&D spending trends
   - Innovation output
   - Time to market
   - Success rate

5. TECHNOLOGY RISKS
   - Obsolescence risk
   - Disruption threats
   - Technical debt
   - Talent retention

Assess technology competitive advantage sustainability.',
'["ticker"]',
'{"type": "json", "schema": {"technology_moat_score": "number", "patent_count": "number", "key_patents_expiring": [{"patent": "string", "expiration": "string"}], "rd_effectiveness": "number", "disruption_risks": ["string"]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 42. M&A History Analysis
(gen_random_uuid(), 'ma_history_analysis', 'due_diligence', 'financial',
'Analyzes M&A track record and integration success',
'You are an M&A analyst evaluating acquisition history.

Company: {{ticker}}

M&A HISTORY ANALYSIS:

1. ACQUISITION HISTORY
   - List of acquisitions (last 10 years)
   - Deal sizes and multiples paid
   - Strategic rationale
   - Financing methods

2. INTEGRATION SUCCESS
   - Revenue synergies achieved
   - Cost synergies realized
   - Integration timeline
   - Cultural integration

3. RETURN ANALYSIS
   - Return on acquisitions
   - Goodwill impairments
   - Write-downs
   - Divestitures

4. CURRENT PIPELINE
   - Stated M&A strategy
   - Potential targets
   - Financial capacity
   - Regulatory constraints

5. LESSONS LEARNED
   - Successful patterns
   - Failed acquisitions
   - Management learnings

Assess M&A capability and future deal risk.',
'["ticker"]',
'{"type": "json", "schema": {"ma_track_record_score": "number", "total_acquisitions": "number", "total_spent": "number", "goodwill_impairments": "number", "synergy_achievement_rate": "number", "key_deals": [{"name": "string", "year": "number", "outcome": "string"}]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 43. Working Capital Analysis
(gen_random_uuid(), 'working_capital_analysis', 'due_diligence', 'financial',
'Analyzes working capital management and efficiency',
'You are a treasury analyst evaluating working capital.

Company: {{ticker}}
Financial Data: {{financial_data}}

WORKING CAPITAL ANALYSIS:

1. COMPONENTS
   - Accounts receivable (DSO)
   - Inventory (DIO)
   - Accounts payable (DPO)
   - Cash conversion cycle

2. TRENDS
   - Historical trends
   - Seasonal patterns
   - Peer comparison
   - Industry benchmarks

3. QUALITY ASSESSMENT
   - Receivables aging
   - Inventory obsolescence
   - Payables sustainability

4. CASH FLOW IMPACT
   - Working capital investment
   - Cash generation potential
   - Optimization opportunities

5. MANAGEMENT
   - Working capital policies
   - Supply chain financing
   - Factoring arrangements

Identify working capital optimization opportunities.',
'["ticker", "financial_data"]',
'{"type": "json", "schema": {"cash_conversion_cycle": "number", "dso": "number", "dio": "number", "dpo": "number", "working_capital_efficiency_score": "number", "optimization_opportunities": ["string"]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

-- 44. Debt Structure Analysis
(gen_random_uuid(), 'debt_structure_analysis', 'due_diligence', 'financial',
'Analyzes debt structure and credit profile',
'You are a credit analyst evaluating debt structure.

Company: {{ticker}}
Debt Data: {{debt_data}}

DEBT STRUCTURE ANALYSIS:

1. DEBT OVERVIEW
   - Total debt outstanding
   - Debt composition (bank, bonds, other)
   - Maturity profile
   - Interest rates (fixed vs floating)

2. CREDIT METRICS
   - Leverage ratios
   - Interest coverage
   - Debt/EBITDA
   - Net debt/equity

3. COVENANT ANALYSIS
   - Key covenants
   - Current compliance
   - Headroom analysis
   - Amendment history

4. REFINANCING RISK
   - Near-term maturities
   - Market access
   - Credit rating trajectory
   - Refinancing costs

5. CAPITAL STRUCTURE
   - Optimal leverage
   - Peer comparison
   - Rating agency views

Assess credit risk and refinancing capacity.',
'["ticker", "debt_data"]',
'{"type": "json", "schema": {"total_debt": "number", "net_debt_to_ebitda": "number", "interest_coverage": "number", "nearest_maturity": {"amount": "number", "date": "string"}, "credit_risk_score": "number", "covenant_headroom": "number"}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

-- 45. Segment Analysis
(gen_random_uuid(), 'segment_analysis', 'due_diligence', 'financial',
'Analyzes business segment performance',
'You are a segment analyst evaluating business units.

Company: {{ticker}}

SEGMENT ANALYSIS:

1. SEGMENT OVERVIEW
   - Business segments defined
   - Revenue by segment
   - Operating income by segment
   - Asset allocation

2. PERFORMANCE METRICS
   - Growth rates by segment
   - Margin trends
   - Return on assets
   - Market position

3. STRATEGIC FIT
   - Synergies between segments
   - Shared resources
   - Cross-selling opportunities
   - Portfolio coherence

4. VALUATION
   - Sum-of-the-parts analysis
   - Segment multiples
   - Conglomerate discount
   - Spin-off potential

5. OUTLOOK
   - Growth prospects by segment
   - Investment priorities
   - Potential divestitures

Identify value creation opportunities by segment.',
'["ticker"]',
'{"type": "json", "schema": {"segments": [{"name": "string", "revenue": "number", "growth_rate": "number", "margin": "number", "implied_value": "number"}], "sotp_value": "number", "conglomerate_discount": "number"}}',
'openai', 'gpt-4', 0.2, 4000, true, 1),

-- 46. Geographic Analysis
(gen_random_uuid(), 'geographic_analysis', 'due_diligence', 'operations',
'Analyzes geographic revenue and risk exposure',
'You are a geographic analyst evaluating regional exposure.

Company: {{ticker}}

GEOGRAPHIC ANALYSIS:

1. REVENUE BREAKDOWN
   - Revenue by region
   - Growth rates by geography
   - Market share by region
   - Customer concentration

2. OPERATIONAL FOOTPRINT
   - Manufacturing locations
   - Distribution centers
   - Employee distribution
   - R&D centers

3. REGIONAL DYNAMICS
   - Market maturity
   - Competitive intensity
   - Regulatory environment
   - Growth opportunities

4. RISK ASSESSMENT
   - Currency exposure
   - Political risk
   - Trade policy impact
   - Tax considerations

5. STRATEGIC PRIORITIES
   - Expansion plans
   - Market exits
   - Localization strategy

Identify geographic opportunities and risks.',
'["ticker"]',
'{"type": "json", "schema": {"revenue_by_region": [{"region": "string", "revenue_pct": "number", "growth_rate": "number"}], "currency_exposure": [{"currency": "string", "exposure_pct": "number"}], "geographic_risk_score": "number"}}',
'openai', 'gpt-4', 0.3, 4000, true, 1);

-- =============================================================================
-- CATEGORY 3: PORTFOLIO MANAGEMENT (19 prompts)
-- =============================================================================

INSERT INTO prompts (id, name, category, subcategory, description, prompt_template, input_variables, output_format, llm_provider, model_name, temperature, max_tokens, is_active, version) VALUES

-- 47. Portfolio Construction
(gen_random_uuid(), 'portfolio_construction', 'portfolio_management', 'construction',
'Constructs optimal portfolio based on investment objectives',
'You are a portfolio manager constructing an investment portfolio.

Investment Objectives:
- Risk tolerance: {{risk_tolerance}}
- Return target: {{return_target}}
- Time horizon: {{time_horizon}}
- Constraints: {{constraints}}

Available positions: {{positions}}

PORTFOLIO CONSTRUCTION:

1. ASSET ALLOCATION
   - Strategic allocation by asset class
   - Sector allocation
   - Geographic allocation
   - Factor exposures

2. POSITION SIZING
   - Individual position weights
   - Concentration limits
   - Liquidity considerations
   - Correlation analysis

3. RISK BUDGETING
   - Risk contribution by position
   - Diversification benefit
   - Tail risk assessment
   - Drawdown expectations

4. OPTIMIZATION
   - Mean-variance optimization
   - Risk parity considerations
   - Constraints application
   - Rebalancing triggers

Provide specific position weights and rationale.',
'["risk_tolerance", "return_target", "time_horizon", "constraints", "positions"]',
'{"type": "json", "schema": {"positions": [{"ticker": "string", "weight": "number", "rationale": "string"}], "expected_return": "number", "expected_volatility": "number", "sharpe_ratio": "number"}}',
'openai', 'gpt-4', 0.2, 4000, true, 1),

-- 48. Position Sizing
(gen_random_uuid(), 'position_sizing', 'portfolio_management', 'risk',
'Determines optimal position size based on conviction and risk',
'You are a risk manager determining position sizes.

Position: {{ticker}}
Conviction level: {{conviction}}
Portfolio context: {{portfolio}}

POSITION SIZING ANALYSIS:

1. CONVICTION ASSESSMENT
   - Thesis strength
   - Information edge
   - Catalyst clarity
   - Risk/reward profile

2. RISK METRICS
   - Position volatility
   - Beta to portfolio
   - Correlation with holdings
   - Tail risk

3. SIZING FRAMEWORKS
   - Kelly criterion
   - Risk parity
   - Equal weight baseline
   - Conviction-weighted

4. CONSTRAINTS
   - Liquidity limits
   - Concentration limits
   - Sector limits
   - Regulatory limits

5. RECOMMENDATION
   - Optimal position size
   - Entry strategy
   - Scaling approach

Provide specific position size with justification.',
'["ticker", "conviction", "portfolio"]',
'{"type": "json", "schema": {"recommended_weight": "number", "max_weight": "number", "entry_strategy": "string", "risk_contribution": "number"}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

-- 49. Rebalancing Analysis
(gen_random_uuid(), 'rebalancing_analysis', 'portfolio_management', 'execution',
'Analyzes portfolio for rebalancing needs',
'You are a portfolio manager analyzing rebalancing needs.

Current Portfolio: {{current_portfolio}}
Target Allocation: {{target_allocation}}

REBALANCING ANALYSIS:

1. DRIFT ANALYSIS
   - Current vs target weights
   - Drift by position
   - Drift by sector/factor
   - Threshold breaches

2. REBALANCING TRADES
   - Required trades
   - Trade sizes
   - Priority ranking
   - Execution timeline

3. COST ANALYSIS
   - Transaction costs
   - Tax implications
   - Market impact
   - Opportunity cost of not rebalancing

4. OPTIMIZATION
   - Tax-loss harvesting opportunities
   - Wash sale considerations
   - Lot selection

5. RECOMMENDATION
   - Rebalance now vs wait
   - Partial vs full rebalance
   - Execution strategy

Provide specific trade recommendations.',
'["current_portfolio", "target_allocation"]',
'{"type": "json", "schema": {"rebalance_recommended": "boolean", "trades": [{"ticker": "string", "action": "string", "shares": "number", "rationale": "string"}], "estimated_costs": "number", "tax_impact": "number"}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

-- 50. Risk Monitoring
(gen_random_uuid(), 'risk_monitoring', 'portfolio_management', 'risk',
'Monitors portfolio risk metrics and alerts',
'You are a risk manager monitoring portfolio risk.

Portfolio: {{portfolio}}
Risk Limits: {{risk_limits}}

RISK MONITORING:

1. RISK METRICS
   - Portfolio VaR (95%, 99%)
   - Expected shortfall
   - Beta to benchmark
   - Tracking error

2. CONCENTRATION RISK
   - Position concentration
   - Sector concentration
   - Factor concentration
   - Geographic concentration

3. STRESS TESTING
   - Historical scenarios
   - Hypothetical scenarios
   - Correlation stress
   - Liquidity stress

4. LIMIT MONITORING
   - Current vs limits
   - Breach alerts
   - Trend analysis
   - Early warning indicators

5. RECOMMENDATIONS
   - Risk reduction trades
   - Hedging opportunities
   - Limit adjustments

Provide risk dashboard with alerts.',
'["portfolio", "risk_limits"]',
'{"type": "json", "schema": {"var_95": "number", "var_99": "number", "beta": "number", "alerts": [{"type": "string", "message": "string", "severity": "string"}], "recommendations": ["string"]}}',
'openai', 'gpt-4', 0.2, 4000, true, 1),

-- 51. Performance Attribution
(gen_random_uuid(), 'performance_attribution', 'portfolio_management', 'analytics',
'Analyzes sources of portfolio performance',
'You are a performance analyst conducting attribution analysis.

Portfolio Returns: {{portfolio_returns}}
Benchmark: {{benchmark}}
Holdings: {{holdings}}

PERFORMANCE ATTRIBUTION:

1. TOTAL RETURN DECOMPOSITION
   - Portfolio return
   - Benchmark return
   - Active return (alpha)

2. BRINSON ATTRIBUTION
   - Allocation effect
   - Selection effect
   - Interaction effect

3. FACTOR ATTRIBUTION
   - Market factor
   - Size factor
   - Value factor
   - Momentum factor
   - Quality factor

4. POSITION ATTRIBUTION
   - Top contributors
   - Top detractors
   - Unexpected outcomes

5. RISK-ADJUSTED METRICS
   - Sharpe ratio
   - Information ratio
   - Sortino ratio
   - Maximum drawdown

Provide detailed attribution breakdown.',
'["portfolio_returns", "benchmark", "holdings"]',
'{"type": "json", "schema": {"total_return": "number", "alpha": "number", "allocation_effect": "number", "selection_effect": "number", "top_contributors": [{"ticker": "string", "contribution": "number"}], "top_detractors": [{"ticker": "string", "contribution": "number"}]}}',
'openai', 'gpt-4', 0.2, 4000, true, 1),

-- 52. Tax-Loss Harvesting
(gen_random_uuid(), 'tax_loss_harvesting', 'portfolio_management', 'tax',
'Identifies tax-loss harvesting opportunities',
'You are a tax-aware portfolio manager.

Portfolio: {{portfolio}}
Tax Situation: {{tax_situation}}

TAX-LOSS HARVESTING ANALYSIS:

1. LOSS IDENTIFICATION
   - Positions with unrealized losses
   - Short-term vs long-term
   - Loss amounts
   - Cost basis by lot

2. HARVESTING OPPORTUNITIES
   - Harvestable losses
   - Tax benefit calculation
   - Wash sale considerations
   - Replacement securities

3. STRATEGY
   - Prioritization of harvests
   - Timing considerations
   - Year-end planning
   - Carry-forward analysis

4. IMPLEMENTATION
   - Specific trades
   - Replacement positions
   - Holding period management

5. PROJECTED BENEFIT
   - Tax savings
   - After-tax return impact
   - Multi-year planning

Provide specific harvesting recommendations.',
'["portfolio", "tax_situation"]',
'{"type": "json", "schema": {"harvestable_losses": "number", "tax_savings": "number", "trades": [{"sell": "string", "buy_replacement": "string", "loss_amount": "number"}], "wash_sale_warnings": ["string"]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

-- 53. Liquidity Analysis
(gen_random_uuid(), 'liquidity_analysis', 'portfolio_management', 'risk',
'Analyzes portfolio liquidity and execution capacity',
'You are a liquidity analyst evaluating portfolio tradability.

Portfolio: {{portfolio}}

LIQUIDITY ANALYSIS:

1. POSITION LIQUIDITY
   - Average daily volume
   - Days to liquidate
   - Bid-ask spreads
   - Market depth

2. PORTFOLIO LIQUIDITY
   - Aggregate liquidity score
   - Liquidity distribution
   - Concentration in illiquid names

3. STRESS SCENARIOS
   - Liquidity under stress
   - Fire sale discounts
   - Correlation of liquidity

4. EXECUTION ANALYSIS
   - Expected market impact
   - Optimal execution strategy
   - Time to execute

5. RECOMMENDATIONS
   - Liquidity improvements
   - Position adjustments
   - Execution guidelines

Provide liquidity risk assessment.',
'["portfolio"]',
'{"type": "json", "schema": {"liquidity_score": "number", "days_to_liquidate_50pct": "number", "days_to_liquidate_100pct": "number", "illiquid_positions": [{"ticker": "string", "days_to_liquidate": "number"}], "recommendations": ["string"]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

-- 54. Correlation Analysis
(gen_random_uuid(), 'correlation_analysis', 'portfolio_management', 'analytics',
'Analyzes portfolio correlations and diversification',
'You are a quantitative analyst evaluating correlations.

Portfolio: {{portfolio}}
Time Period: {{time_period}}

CORRELATION ANALYSIS:

1. CORRELATION MATRIX
   - Pairwise correlations
   - Rolling correlations
   - Correlation stability

2. CLUSTER ANALYSIS
   - Correlated groups
   - Hidden exposures
   - Diversification gaps

3. FACTOR CORRELATIONS
   - Correlation to factors
   - Factor crowding
   - Unintended bets

4. STRESS CORRELATIONS
   - Correlation in drawdowns
   - Tail dependence
   - Diversification breakdown

5. RECOMMENDATIONS
   - Diversification improvements
   - Correlation hedges
   - Position adjustments

Provide correlation insights and recommendations.',
'["portfolio", "time_period"]',
'{"type": "json", "schema": {"average_correlation": "number", "highly_correlated_pairs": [{"pair": ["string", "string"], "correlation": "number"}], "diversification_score": "number", "recommendations": ["string"]}}',
'openai', 'gpt-4', 0.2, 4000, true, 1),

-- 55. Scenario Analysis
(gen_random_uuid(), 'scenario_analysis', 'portfolio_management', 'risk',
'Analyzes portfolio performance under various scenarios',
'You are a scenario analyst stress testing portfolios.

Portfolio: {{portfolio}}
Scenarios: {{scenarios}}

SCENARIO ANALYSIS:

1. SCENARIO DEFINITIONS
   - Macro scenarios
   - Market scenarios
   - Sector scenarios
   - Idiosyncratic scenarios

2. IMPACT ANALYSIS
   - Portfolio P&L by scenario
   - Position-level impacts
   - Factor exposures under stress

3. HISTORICAL SCENARIOS
   - 2008 Financial Crisis
   - 2020 COVID Crash
   - 2022 Rate Shock
   - Sector-specific events

4. HYPOTHETICAL SCENARIOS
   - Recession
   - Inflation spike
   - Geopolitical crisis
   - Technology disruption

5. RISK MITIGATION
   - Hedging strategies
   - Position adjustments
   - Tail risk protection

Provide scenario impact analysis.',
'["portfolio", "scenarios"]',
'{"type": "json", "schema": {"scenario_results": [{"scenario": "string", "portfolio_impact_pct": "number", "worst_positions": [{"ticker": "string", "impact_pct": "number"}]}], "recommendations": ["string"]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

-- 56-65: Additional Portfolio Management prompts
(gen_random_uuid(), 'factor_exposure_analysis', 'portfolio_management', 'analytics',
'Analyzes portfolio factor exposures',
'Analyze factor exposures for portfolio: {{portfolio}}

Evaluate exposures to: Market, Size, Value, Momentum, Quality, Volatility, Dividend Yield.

Provide factor loadings, risk contribution, and recommendations for factor tilts.',
'["portfolio"]',
'{"type": "json", "schema": {"factor_exposures": [{"factor": "string", "loading": "number", "risk_contribution": "number"}]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'benchmark_comparison', 'portfolio_management', 'analytics',
'Compares portfolio to benchmark',
'Compare portfolio {{portfolio}} to benchmark {{benchmark}}.

Analyze: Active weights, tracking error, information ratio, sector/factor deviations.',
'["portfolio", "benchmark"]',
'{"type": "json", "schema": {"tracking_error": "number", "information_ratio": "number", "active_weights": [{"ticker": "string", "active_weight": "number"}]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'drawdown_analysis', 'portfolio_management', 'risk',
'Analyzes portfolio drawdown characteristics',
'Analyze drawdown history for portfolio: {{portfolio}}

Evaluate: Maximum drawdown, drawdown duration, recovery time, drawdown frequency.',
'["portfolio"]',
'{"type": "json", "schema": {"max_drawdown": "number", "avg_drawdown": "number", "avg_recovery_days": "number", "current_drawdown": "number"}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'sector_rotation_analysis', 'portfolio_management', 'strategy',
'Analyzes sector rotation opportunities',
'Analyze sector rotation opportunities based on: {{market_conditions}}

Evaluate sector momentum, valuations, and economic sensitivity.',
'["market_conditions"]',
'{"type": "json", "schema": {"overweight_sectors": ["string"], "underweight_sectors": ["string"], "rotation_trades": [{"from": "string", "to": "string", "rationale": "string"}]}}',
'openai', 'gpt-4', 0.3, 3000, true, 1),

(gen_random_uuid(), 'options_overlay_strategy', 'portfolio_management', 'hedging',
'Designs options overlay for portfolio hedging',
'Design options overlay strategy for portfolio: {{portfolio}}

Objective: {{objective}} (income, protection, or both)',
'["portfolio", "objective"]',
'{"type": "json", "schema": {"strategy": "string", "positions": [{"type": "string", "strike": "number", "expiry": "string", "quantity": "number"}], "cost": "number", "protection_level": "number"}}',
'openai', 'gpt-4', 0.3, 3000, true, 1),

(gen_random_uuid(), 'currency_hedging_analysis', 'portfolio_management', 'hedging',
'Analyzes currency exposure and hedging needs',
'Analyze currency exposure for portfolio: {{portfolio}}

Evaluate: FX exposure by currency, hedging costs, optimal hedge ratio.',
'["portfolio"]',
'{"type": "json", "schema": {"currency_exposures": [{"currency": "string", "exposure_pct": "number"}], "recommended_hedges": [{"currency": "string", "hedge_ratio": "number", "cost_bps": "number"}]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'income_analysis', 'portfolio_management', 'analytics',
'Analyzes portfolio income generation',
'Analyze income characteristics for portfolio: {{portfolio}}

Evaluate: Dividend yield, dividend growth, income stability, tax efficiency.',
'["portfolio"]',
'{"type": "json", "schema": {"portfolio_yield": "number", "dividend_growth_rate": "number", "income_stability_score": "number", "top_income_contributors": [{"ticker": "string", "yield": "number", "income_contribution": "number"}]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'esg_portfolio_analysis', 'portfolio_management', 'esg',
'Analyzes portfolio ESG characteristics',
'Analyze ESG profile for portfolio: {{portfolio}}

Evaluate: ESG scores, carbon footprint, controversies, alignment with objectives.',
'["portfolio"]',
'{"type": "json", "schema": {"portfolio_esg_score": "number", "carbon_intensity": "number", "controversies": [{"ticker": "string", "issue": "string"}], "improvement_opportunities": ["string"]}}',
'openai', 'gpt-4', 0.3, 3000, true, 1),

(gen_random_uuid(), 'transition_management', 'portfolio_management', 'execution',
'Plans portfolio transition strategy',
'Plan transition from {{current_portfolio}} to {{target_portfolio}}

Optimize for: Minimizing costs, tax efficiency, market impact.',
'["current_portfolio", "target_portfolio"]',
'{"type": "json", "schema": {"transition_trades": [{"ticker": "string", "action": "string", "shares": "number", "priority": "number"}], "estimated_cost": "number", "timeline_days": "number"}}',
'openai', 'gpt-4', 0.2, 4000, true, 1),

(gen_random_uuid(), 'investment_policy_compliance', 'portfolio_management', 'compliance',
'Checks portfolio compliance with investment policy',
'Check compliance of {{portfolio}} against investment policy: {{policy}}

Identify violations and remediation actions.',
'["portfolio", "policy"]',
'{"type": "json", "schema": {"compliant": "boolean", "violations": [{"rule": "string", "current_value": "number", "limit": "number", "remediation": "string"}]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1);

-- =============================================================================
-- CATEGORY 4: MACRO ANALYSIS (16 prompts)
-- =============================================================================

INSERT INTO prompts (id, name, category, subcategory, description, prompt_template, input_variables, output_format, llm_provider, model_name, temperature, max_tokens, is_active, version) VALUES

(gen_random_uuid(), 'macro_environment_analysis', 'macro', 'economic',
'Comprehensive macroeconomic environment analysis',
'Analyze the current macroeconomic environment:

Data: {{macro_data}}

Cover: GDP growth, inflation, employment, monetary policy, fiscal policy, global trade.

Provide investment implications by asset class and sector.',
'["macro_data"]',
'{"type": "json", "schema": {"gdp_outlook": "string", "inflation_outlook": "string", "rate_outlook": "string", "sector_implications": [{"sector": "string", "outlook": "string"}]}}',
'perplexity', 'sonar-pro', 0.3, 4000, true, 1),

(gen_random_uuid(), 'fed_policy_analysis', 'macro', 'monetary',
'Federal Reserve policy analysis and implications',
'Analyze Federal Reserve policy stance and outlook:

Recent communications: {{fed_communications}}

Evaluate: Rate path, QT, forward guidance, market implications.',
'["fed_communications"]',
'{"type": "json", "schema": {"current_rate": "number", "expected_terminal_rate": "number", "next_move_probability": {"hike": "number", "cut": "number", "hold": "number"}, "market_implications": "string"}}',
'perplexity', 'sonar-pro', 0.3, 3000, true, 1),

(gen_random_uuid(), 'economic_indicator_analysis', 'macro', 'economic',
'Analyzes key economic indicators',
'Analyze economic indicators: {{indicators}}

Evaluate: Trend, surprise vs consensus, leading indicator signals, recession probability.',
'["indicators"]',
'{"type": "json", "schema": {"indicator_summary": [{"name": "string", "value": "number", "trend": "string", "signal": "string"}], "recession_probability": "number"}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'global_macro_scan', 'macro', 'global',
'Scans global macro conditions across regions',
'Scan global macro conditions:

Regions: US, Europe, China, Japan, Emerging Markets

Evaluate: Growth, policy, risks, investment opportunities by region.',
'[]',
'{"type": "json", "schema": {"regions": [{"region": "string", "growth_outlook": "string", "policy_stance": "string", "key_risks": ["string"], "opportunities": ["string"]}]}}',
'perplexity', 'sonar-pro', 0.3, 4000, true, 1),

(gen_random_uuid(), 'inflation_analysis', 'macro', 'economic',
'Deep dive inflation analysis',
'Analyze inflation dynamics:

Data: {{inflation_data}}

Evaluate: Components, drivers, persistence, policy implications, investment hedges.',
'["inflation_data"]',
'{"type": "json", "schema": {"headline_cpi": "number", "core_cpi": "number", "drivers": [{"component": "string", "contribution": "number"}], "outlook": "string", "hedges": ["string"]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'credit_cycle_analysis', 'macro', 'credit',
'Analyzes credit cycle position and implications',
'Analyze credit cycle conditions:

Data: {{credit_data}}

Evaluate: Spreads, defaults, lending standards, cycle position, sector implications.',
'["credit_data"]',
'{"type": "json", "schema": {"cycle_position": "string", "ig_spread": "number", "hy_spread": "number", "default_outlook": "string", "recommendations": ["string"]}}',
'openai', 'gpt-4', 0.3, 3000, true, 1),

(gen_random_uuid(), 'currency_analysis', 'macro', 'fx',
'Analyzes currency trends and drivers',
'Analyze currency dynamics for: {{currency_pair}}

Evaluate: Fundamentals, technicals, carry, positioning, outlook.',
'["currency_pair"]',
'{"type": "json", "schema": {"current_rate": "number", "fair_value": "number", "drivers": ["string"], "outlook": "string", "trade_recommendation": "string"}}',
'openai', 'gpt-4', 0.3, 3000, true, 1),

(gen_random_uuid(), 'commodity_analysis', 'macro', 'commodities',
'Analyzes commodity markets and trends',
'Analyze commodity market: {{commodity}}

Evaluate: Supply/demand, inventory, cost curve, price outlook, equity implications.',
'["commodity"]',
'{"type": "json", "schema": {"current_price": "number", "supply_demand_balance": "string", "inventory_days": "number", "price_outlook": "string", "equity_plays": ["string"]}}',
'openai', 'gpt-4', 0.3, 3000, true, 1),

(gen_random_uuid(), 'geopolitical_risk_analysis', 'macro', 'geopolitical',
'Analyzes geopolitical risks and market implications',
'Analyze geopolitical risks:

Current events: {{events}}

Evaluate: Risk scenarios, probability, market impact, hedging strategies.',
'["events"]',
'{"type": "json", "schema": {"risks": [{"event": "string", "probability": "number", "market_impact": "string"}], "hedging_strategies": ["string"]}}',
'perplexity', 'sonar-pro', 0.4, 3000, true, 1),

(gen_random_uuid(), 'sector_sensitivity_analysis', 'macro', 'sector',
'Analyzes sector sensitivity to macro factors',
'Analyze sector sensitivity to macro factors:

Sector: {{sector}}
Macro factors: Interest rates, GDP, inflation, USD, oil

Provide sensitivity coefficients and current positioning.',
'["sector"]',
'{"type": "json", "schema": {"sensitivities": [{"factor": "string", "beta": "number", "current_exposure": "string"}], "positioning_recommendation": "string"}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'yield_curve_analysis', 'macro', 'rates',
'Analyzes yield curve shape and implications',
'Analyze yield curve:

Data: {{yield_data}}

Evaluate: Shape, term premium, inversion signals, sector implications.',
'["yield_data"]',
'{"type": "json", "schema": {"curve_shape": "string", "2y10y_spread": "number", "term_premium": "number", "recession_signal": "boolean", "sector_implications": [{"sector": "string", "impact": "string"}]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'earnings_season_preview', 'macro', 'earnings',
'Previews upcoming earnings season',
'Preview earnings season:

Key reporters: {{companies}}
Macro context: {{macro_context}}

Evaluate: Expectations, key themes, potential surprises, trading strategies.',
'["companies", "macro_context"]',
'{"type": "json", "schema": {"overall_outlook": "string", "key_themes": ["string"], "companies_to_watch": [{"ticker": "string", "expectation": "string", "risk": "string"}]}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

(gen_random_uuid(), 'market_regime_analysis', 'macro', 'regime',
'Identifies current market regime',
'Analyze current market regime:

Data: {{market_data}}

Classify regime: Risk-on/off, trending/ranging, vol regime. Provide strategy implications.',
'["market_data"]',
'{"type": "json", "schema": {"regime": "string", "confidence": "number", "characteristics": ["string"], "strategy_implications": "string"}}',
'openai', 'gpt-4', 0.3, 3000, true, 1),

(gen_random_uuid(), 'liquidity_conditions_analysis', 'macro', 'liquidity',
'Analyzes market liquidity conditions',
'Analyze market liquidity conditions:

Evaluate: Fed balance sheet, repo markets, money markets, equity market liquidity.',
'[]',
'{"type": "json", "schema": {"liquidity_score": "number", "fed_balance_sheet_trend": "string", "stress_indicators": ["string"], "outlook": "string"}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'china_macro_analysis', 'macro', 'china',
'Deep dive China macro analysis',
'Analyze China macro conditions:

Data: {{china_data}}

Evaluate: Growth, policy, property, trade, investment implications for global markets.',
'["china_data"]',
'{"type": "json", "schema": {"gdp_growth": "number", "policy_stance": "string", "property_outlook": "string", "global_implications": ["string"], "investment_ideas": ["string"]}}',
'perplexity', 'sonar-pro', 0.3, 4000, true, 1),

(gen_random_uuid(), 'election_impact_analysis', 'macro', 'political',
'Analyzes election impact on markets',
'Analyze election impact:

Election: {{election}}
Scenarios: {{scenarios}}

Evaluate: Policy implications, sector winners/losers, positioning strategies.',
'["election", "scenarios"]',
'{"type": "json", "schema": {"scenarios": [{"outcome": "string", "probability": "number", "market_impact": "string", "sector_winners": ["string"], "sector_losers": ["string"]}]}}',
'openai', 'gpt-4', 0.4, 4000, true, 1);

-- =============================================================================
-- CATEGORY 5: THESIS DEVELOPMENT (10 prompts from Notion Library)
-- =============================================================================

INSERT INTO prompts (id, name, category, subcategory, description, prompt_template, input_variables, output_format, llm_provider, model_name, temperature, max_tokens, is_active, version) VALUES

(gen_random_uuid(), 'investment_thesis_synthesis', 'thesis', 'synthesis',
'Synthesizes research into coherent investment thesis',
'Synthesize an investment thesis for: {{ticker}}

Based on research: {{research_summary}}

Structure:
1. One-sentence thesis
2. Key thesis points (3-5)
3. Supporting evidence
4. Key assumptions
5. What could go wrong
6. Catalysts and timeline
7. Valuation and target price

Write in assertive, sell-side style.',
'["ticker", "research_summary"]',
'{"type": "json", "schema": {"thesis_statement": "string", "key_points": ["string"], "target_price": "number", "time_horizon": "string", "conviction": "string"}}',
'anthropic', 'claude-3-opus', 0.3, 5000, true, 1),

(gen_random_uuid(), 'investment_memo', 'thesis', 'output',
'Creates formal investment memorandum',
'Create an investment memorandum for: {{ticker}}

Research: {{research}}

Include: Executive summary, business overview, investment thesis, financial analysis, valuation, risks, recommendation.

Format for investment committee presentation.',
'["ticker", "research"]',
'{"type": "json", "schema": {"sections": [{"title": "string", "content": "string"}], "recommendation": "string", "position_size": "string"}}',
'anthropic', 'claude-3-opus', 0.3, 6000, true, 1),

(gen_random_uuid(), 'thesis_monitoring_framework', 'thesis', 'monitoring',
'Creates framework for monitoring investment thesis',
'Create monitoring framework for thesis: {{thesis}}

Company: {{ticker}}

Define:
1. Key performance indicators to track
2. Thesis confirmation signals
3. Thesis invalidation triggers
4. Data sources and frequency
5. Review schedule',
'["thesis", "ticker"]',
'{"type": "json", "schema": {"kpis": [{"metric": "string", "target": "string", "frequency": "string"}], "confirmation_signals": ["string"], "invalidation_triggers": ["string"]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'variant_perception', 'thesis', 'edge',
'Identifies variant perception vs consensus',
'Identify variant perception for: {{ticker}}

Consensus view: {{consensus}}

Analyze:
1. Where does our view differ from consensus?
2. Why might we be right?
3. What does the market not understand?
4. What would prove us right/wrong?
5. Time horizon for thesis to play out',
'["ticker", "consensus"]',
'{"type": "json", "schema": {"consensus_view": "string", "our_view": "string", "key_differences": ["string"], "edge_source": "string", "catalyst_timeline": "string"}}',
'openai', 'gpt-4', 0.3, 3000, true, 1),

(gen_random_uuid(), 'pre_mortem_analysis', 'thesis', 'risk',
'Conducts pre-mortem on investment thesis',
'Conduct pre-mortem analysis for investment in: {{ticker}}

Thesis: {{thesis}}

Imagine the investment failed. Analyze:
1. What went wrong?
2. What did we miss?
3. What assumptions were wrong?
4. What external factors hurt us?
5. How could we have known?

Provide probability-weighted risk assessment.',
'["ticker", "thesis"]',
'{"type": "json", "schema": {"failure_scenarios": [{"scenario": "string", "probability": "number", "could_have_known": "boolean"}], "key_blind_spots": ["string"], "mitigation_strategies": ["string"]}}',
'openai', 'gpt-4', 0.4, 4000, true, 1),

(gen_random_uuid(), 'thesis_update', 'thesis', 'monitoring',
'Updates investment thesis based on new information',
'Update investment thesis for: {{ticker}}

Original thesis: {{original_thesis}}
New information: {{new_info}}

Evaluate:
1. Does new info confirm or challenge thesis?
2. What assumptions need updating?
3. How does fair value change?
4. Should position size change?
5. Updated conviction level',
'["ticker", "original_thesis", "new_info"]',
'{"type": "json", "schema": {"thesis_status": "string", "updated_assumptions": ["string"], "new_fair_value": "number", "position_action": "string", "conviction_change": "string"}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'exit_strategy', 'thesis', 'execution',
'Develops exit strategy for position',
'Develop exit strategy for: {{ticker}}

Current position: {{position}}
Thesis: {{thesis}}

Define:
1. Target price exit
2. Stop-loss levels
3. Time-based exit
4. Thesis invalidation exit
5. Scaling strategy',
'["ticker", "position", "thesis"]',
'{"type": "json", "schema": {"target_exit_price": "number", "stop_loss_price": "number", "time_exit_date": "string", "invalidation_triggers": ["string"], "scaling_plan": "string"}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'peer_thesis_comparison', 'thesis', 'analysis',
'Compares investment thesis across peer group',
'Compare investment thesis for peer group: {{peers}}

For each company:
1. Investment thesis summary
2. Key differentiators
3. Relative valuation
4. Risk/reward ranking

Recommend best idea in the group.',
'["peers"]',
'{"type": "json", "schema": {"peer_comparison": [{"ticker": "string", "thesis": "string", "upside": "number", "risk_score": "number"}], "top_pick": "string", "rationale": "string"}}',
'openai', 'gpt-4', 0.3, 4000, true, 1),

(gen_random_uuid(), 'contrarian_thesis_development', 'thesis', 'strategy',
'Develops contrarian investment thesis',
'Develop contrarian thesis for: {{ticker}}

Current sentiment: {{sentiment}}

Analyze:
1. Why is sentiment so negative/positive?
2. What is the market missing?
3. What would change sentiment?
4. Historical precedents
5. Risk/reward of contrarian bet',
'["ticker", "sentiment"]',
'{"type": "json", "schema": {"contrarian_thesis": "string", "market_misconception": "string", "sentiment_change_catalyst": "string", "historical_precedent": "string", "risk_reward": "string"}}',
'openai', 'gpt-4', 0.4, 4000, true, 1),

(gen_random_uuid(), 'thesis_presentation', 'thesis', 'output',
'Creates thesis presentation for stakeholders',
'Create thesis presentation for: {{ticker}}

Audience: {{audience}}
Research: {{research}}

Structure for 10-minute pitch:
1. Hook/headline
2. Company overview
3. Investment thesis
4. Key evidence
5. Valuation
6. Risks and mitigants
7. Recommendation',
'["ticker", "audience", "research"]',
'{"type": "json", "schema": {"slides": [{"title": "string", "key_points": ["string"], "visual_suggestion": "string"}], "talking_points": ["string"]}}',
'anthropic', 'claude-3-opus', 0.3, 5000, true, 1);

-- =============================================================================
-- CATEGORY 6: OTHER/UTILITY (7 prompts)
-- =============================================================================

INSERT INTO prompts (id, name, category, subcategory, description, prompt_template, input_variables, output_format, llm_provider, model_name, temperature, max_tokens, is_active, version) VALUES

(gen_random_uuid(), 'earnings_call_analysis', 'other', 'earnings',
'Analyzes earnings call transcript',
'Analyze earnings call transcript for: {{ticker}}

Transcript: {{transcript}}

Extract:
1. Key financial highlights
2. Management tone and confidence
3. Forward guidance changes
4. Analyst concerns
5. Strategic priorities
6. Red flags or concerns',
'["ticker", "transcript"]',
'{"type": "json", "schema": {"highlights": ["string"], "tone_score": "number", "guidance_change": "string", "key_quotes": ["string"], "concerns": ["string"]}}',
'anthropic', 'claude-3-opus', 0.2, 4000, true, 1),

(gen_random_uuid(), 'sec_filing_analysis', 'other', 'filings',
'Analyzes SEC filing for key information',
'Analyze SEC filing for: {{ticker}}

Filing type: {{filing_type}}
Content: {{filing_content}}

Extract key information relevant to investment thesis.',
'["ticker", "filing_type", "filing_content"]',
'{"type": "json", "schema": {"key_findings": ["string"], "risk_factors": ["string"], "material_changes": ["string"], "red_flags": ["string"]}}',
'anthropic', 'claude-3-opus', 0.2, 4000, true, 1),

(gen_random_uuid(), 'news_sentiment_analysis', 'other', 'sentiment',
'Analyzes news sentiment for company',
'Analyze news sentiment for: {{ticker}}

News articles: {{news}}

Evaluate: Overall sentiment, key themes, potential market impact, trading implications.',
'["ticker", "news"]',
'{"type": "json", "schema": {"overall_sentiment": "number", "key_themes": ["string"], "market_impact": "string", "trading_implication": "string"}}',
'openai', 'gpt-4', 0.3, 3000, true, 1),

(gen_random_uuid(), 'research_report_summary', 'other', 'research',
'Summarizes sell-side research report',
'Summarize research report for: {{ticker}}

Report: {{report}}

Extract: Rating, price target, key thesis points, risks, catalysts.',
'["ticker", "report"]',
'{"type": "json", "schema": {"rating": "string", "price_target": "number", "thesis_summary": "string", "key_points": ["string"], "risks": ["string"]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'competitor_earnings_comparison', 'other', 'earnings',
'Compares earnings across competitors',
'Compare earnings for competitors: {{tickers}}

Earnings data: {{earnings_data}}

Analyze: Relative performance, market share trends, margin comparison, guidance comparison.',
'["tickers", "earnings_data"]',
'{"type": "json", "schema": {"comparison": [{"ticker": "string", "revenue_growth": "number", "eps_surprise": "number", "guidance": "string"}], "winner": "string", "loser": "string"}}',
'openai', 'gpt-4', 0.2, 3000, true, 1),

(gen_random_uuid(), 'daily_market_briefing', 'other', 'market',
'Creates daily market briefing',
'Create daily market briefing:

Market data: {{market_data}}
News: {{news}}

Include: Market summary, key movers, sector performance, economic calendar, key themes.',
'["market_data", "news"]',
'{"type": "json", "schema": {"market_summary": "string", "key_movers": [{"ticker": "string", "change": "number", "reason": "string"}], "themes": ["string"], "calendar": ["string"]}}',
'perplexity', 'sonar-pro', 0.3, 3000, true, 1),

(gen_random_uuid(), 'watchlist_screening', 'other', 'screening',
'Screens watchlist for actionable opportunities',
'Screen watchlist for opportunities: {{watchlist}}

Criteria: {{criteria}}

Identify stocks meeting criteria and rank by attractiveness.',
'["watchlist", "criteria"]',
'{"type": "json", "schema": {"matches": [{"ticker": "string", "score": "number", "key_factors": ["string"]}], "top_picks": ["string"]}}',
'openai', 'gpt-4', 0.2, 3000, true, 1);

-- =============================================================================
-- Create indexes for better query performance
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category);
CREATE INDEX IF NOT EXISTS idx_prompts_subcategory ON prompts(subcategory);
CREATE INDEX IF NOT EXISTS idx_prompts_name ON prompts(name);
CREATE INDEX IF NOT EXISTS idx_prompts_is_active ON prompts(is_active);

-- =============================================================================
-- Verify prompt count
-- =============================================================================

DO $$
DECLARE
    prompt_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO prompt_count FROM prompts;
    RAISE NOTICE 'Total prompts loaded: %', prompt_count;
END $$;

-- =====================================================
-- DUE DILIGENCE PROMPTS (36 prompts)
-- =====================================================

-- DD001: Financial Statement Deep Dive
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'dd-001',
    'Financial Statement Deep Dive',
    'due_diligence',
    'financial_analysis',
    'Comprehensive analysis of company financial statements including income statement, balance sheet, and cash flow',
    'You are a senior financial analyst with expertise in forensic accounting and financial statement analysis. Analyze financial statements with extreme attention to detail, looking for trends, anomalies, and red flags.',
    'Perform a comprehensive financial statement analysis for {{company_name}} ({{ticker}}).

Analyze the following:
1. **Income Statement Analysis**
   - Revenue trends and growth rates
   - Gross margin evolution
   - Operating leverage
   - Non-recurring items
   
2. **Balance Sheet Analysis**
   - Asset quality and composition
   - Liability structure
   - Working capital trends
   - Off-balance sheet items
   
3. **Cash Flow Analysis**
   - Operating cash flow quality
   - CapEx requirements
   - Free cash flow generation
   - Cash conversion cycle

4. **Key Ratios**
   - Profitability ratios
   - Liquidity ratios
   - Solvency ratios
   - Efficiency ratios

5. **Red Flags**
   - Accounting anomalies
   - Aggressive revenue recognition
   - Unusual related party transactions

Provide specific numbers and year-over-year comparisons.',
    'json',
    ARRAY['sec_filings', 'fmp', 'polygon'],
    'anthropic',
    'claude-3-opus-20240229',
    0.3,
    8000,
    ARRAY['financial', 'accounting', 'due_diligence', 'statements'],
    '1.0',
    true
);

-- DD002: Management Quality Assessment
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'dd-002',
    'Management Quality Assessment',
    'due_diligence',
    'management',
    'Evaluate management team quality, track record, compensation alignment, and governance',
    'You are an executive recruiter and corporate governance expert. Evaluate management teams based on their track record, integrity, capital allocation skills, and alignment with shareholders.',
    'Assess the management quality for {{company_name}} ({{ticker}}).

Evaluate:
1. **CEO Track Record**
   - Previous roles and performance
   - Tenure at current company
   - Strategic decisions made
   - Communication style and transparency

2. **Management Team**
   - Key executives and backgrounds
   - Turnover rates
   - Depth of bench
   - Industry experience

3. **Capital Allocation History**
   - M&A track record (returns on acquisitions)
   - Dividend policy
   - Share buyback effectiveness
   - R&D investment returns

4. **Compensation Analysis**
   - Pay vs performance correlation
   - Equity ownership by management
   - Incentive structure alignment
   - Peer comparison

5. **Governance**
   - Board independence
   - Related party transactions
   - Shareholder rights
   - ESG practices

Provide a 1-10 score for each category with justification.',
    'json',
    ARRAY['sec_filings', 'news', 'linkedin'],
    'openai',
    'gpt-4-turbo',
    0.4,
    6000,
    ARRAY['management', 'governance', 'due_diligence'],
    '1.0',
    true
);

-- DD003: Competitive Moat Analysis
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'dd-003',
    'Competitive Moat Analysis',
    'due_diligence',
    'competitive',
    'Analyze sustainable competitive advantages and economic moats',
    'You are a strategy consultant specializing in competitive analysis. Identify and evaluate economic moats using the framework of network effects, switching costs, intangible assets, cost advantages, and efficient scale.',
    'Analyze the competitive moat for {{company_name}} ({{ticker}}) in the {{industry}} industry.

Evaluate each moat source:

1. **Network Effects**
   - Type (direct, indirect, data)
   - Strength and defensibility
   - Evidence of network effects

2. **Switching Costs**
   - Customer lock-in mechanisms
   - Integration depth
   - Contractual barriers

3. **Intangible Assets**
   - Brand value and recognition
   - Patents and IP portfolio
   - Regulatory licenses
   - Proprietary data/algorithms

4. **Cost Advantages**
   - Scale economies
   - Process advantages
   - Location benefits
   - Unique assets

5. **Efficient Scale**
   - Market size limitations
   - Natural monopoly characteristics
   - Rational competition dynamics

**Moat Durability Assessment:**
- Threats to each moat source
- Historical moat evolution
- 5-year moat outlook

Provide an overall moat rating: None, Narrow, or Wide.',
    'json',
    ARRAY['sec_filings', 'industry_reports', 'news'],
    'anthropic',
    'claude-3-opus-20240229',
    0.4,
    7000,
    ARRAY['moat', 'competitive', 'strategy', 'due_diligence'],
    '1.0',
    true
);

-- DD004: Valuation Multi-Method Analysis
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'dd-004',
    'Valuation Multi-Method Analysis',
    'due_diligence',
    'valuation',
    'Comprehensive valuation using DCF, comparable companies, and precedent transactions',
    'You are a senior investment banker with expertise in valuation. Perform rigorous valuations using multiple methodologies and clearly state assumptions.',
    'Perform a comprehensive valuation analysis for {{company_name}} ({{ticker}}).

**1. Discounted Cash Flow (DCF)**
- Revenue projections (5 years)
- Margin assumptions
- CapEx and working capital
- Terminal value (perpetuity growth and exit multiple)
- WACC calculation
- Sensitivity analysis

**2. Comparable Company Analysis**
- Select 5-8 relevant peers
- Key multiples: EV/Revenue, EV/EBITDA, P/E, P/FCF
- Apply appropriate premium/discount
- Derive implied valuation range

**3. Precedent Transactions**
- Identify relevant M&A transactions
- Transaction multiples
- Control premium analysis
- Implied valuation range

**4. Sum-of-the-Parts (if applicable)**
- Segment-by-segment valuation
- Conglomerate discount consideration

**5. Valuation Summary**
- Football field chart data
- Base, bull, and bear cases
- Key value drivers
- Recommendation with price target',
    'json',
    ARRAY['fmp', 'polygon', 'sec_filings'],
    'openai',
    'gpt-4-turbo',
    0.3,
    8000,
    ARRAY['valuation', 'dcf', 'multiples', 'due_diligence'],
    '1.0',
    true
);

-- DD005: Risk Factor Analysis
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'dd-005',
    'Risk Factor Analysis',
    'due_diligence',
    'risk',
    'Comprehensive risk assessment including business, financial, regulatory, and ESG risks',
    'You are a risk management professional. Identify, categorize, and assess all material risks facing a company, providing probability and impact assessments.',
    'Perform a comprehensive risk analysis for {{company_name}} ({{ticker}}).

**1. Business Risks**
- Customer concentration
- Supplier dependencies
- Technology disruption
- Competitive threats
- Key person risk

**2. Financial Risks**
- Leverage and debt covenants
- Liquidity risk
- Currency exposure
- Interest rate sensitivity
- Pension obligations

**3. Regulatory Risks**
- Current regulatory environment
- Pending legislation
- Compliance history
- Litigation exposure

**4. Operational Risks**
- Supply chain vulnerabilities
- Cybersecurity
- Business continuity
- Quality control

**5. ESG Risks**
- Environmental liabilities
- Social/labor issues
- Governance concerns

**Risk Matrix:**
For each risk, provide:
- Probability (Low/Medium/High)
- Impact (Low/Medium/High)
- Trend (Improving/Stable/Deteriorating)
- Mitigants',
    'json',
    ARRAY['sec_filings', 'news', 'regulatory'],
    'anthropic',
    'claude-3-opus-20240229',
    0.3,
    7000,
    ARRAY['risk', 'due_diligence', 'esg'],
    '1.0',
    true
);

-- DD006: Industry Deep Dive
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'dd-006',
    'Industry Deep Dive',
    'due_diligence',
    'industry',
    'Comprehensive industry analysis including structure, dynamics, and outlook',
    'You are an industry analyst with deep expertise in sector research. Provide comprehensive industry analysis using Porter''s Five Forces, value chain analysis, and trend identification.',
    'Perform a deep dive analysis on the {{industry}} industry.

**1. Industry Overview**
- Market size and growth
- Key segments
- Geographic breakdown
- Industry lifecycle stage

**2. Porter''s Five Forces**
- Threat of new entrants
- Bargaining power of suppliers
- Bargaining power of buyers
- Threat of substitutes
- Competitive rivalry

**3. Value Chain Analysis**
- Key value chain stages
- Margin distribution
- Critical success factors
- Vertical integration trends

**4. Competitive Landscape**
- Market share breakdown
- Key players and strategies
- Recent M&A activity
- Emerging disruptors

**5. Industry Trends**
- Technology disruption
- Regulatory changes
- Consumer behavior shifts
- Sustainability trends

**6. Outlook**
- 5-year growth forecast
- Key catalysts and risks
- Investment implications',
    'json',
    ARRAY['industry_reports', 'news', 'sec_filings'],
    'perplexity',
    'sonar-pro',
    0.4,
    7000,
    ARRAY['industry', 'sector', 'due_diligence'],
    '1.0',
    true
);

-- DD007: Short Interest Analysis
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'dd-007',
    'Short Interest Analysis',
    'due_diligence',
    'technical',
    'Analyze short interest data and potential short squeeze dynamics',
    'You are a quantitative analyst specializing in market microstructure. Analyze short interest data to identify potential risks and opportunities.',
    'Analyze the short interest dynamics for {{company_name}} ({{ticker}}).

**1. Current Short Interest**
- Shares short
- Short interest ratio (days to cover)
- Short % of float
- Short % of shares outstanding

**2. Historical Trends**
- 6-month short interest trend
- Correlation with price movements
- Notable spikes or drops

**3. Peer Comparison**
- Short interest vs industry peers
- Relative positioning

**4. Short Squeeze Potential**
- Days to cover analysis
- Borrow cost trends
- Institutional ownership
- Float characteristics

**5. Bear Thesis Analysis**
- Why are shorts betting against?
- Validity of bear arguments
- Counter-arguments

**6. Implications**
- Risk/reward assessment
- Potential catalysts for covering
- Trading considerations',
    'json',
    ARRAY['polygon', 'fmp', 'finra'],
    'openai',
    'gpt-4-turbo',
    0.3,
    5000,
    ARRAY['short_interest', 'technical', 'due_diligence'],
    '1.0',
    true
);

-- DD008: Insider Trading Analysis
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'dd-008',
    'Insider Trading Analysis (SEC Form 4)',
    'due_diligence',
    'ownership',
    'Analyze insider buying and selling patterns from SEC Form 4 filings',
    'You are a securities analyst specializing in insider trading patterns. Analyze Form 4 filings to identify meaningful insider activity and its implications.',
    'Analyze insider trading activity for {{company_name}} ({{ticker}}).

**1. Recent Insider Transactions (Last 12 Months)**
- List all Form 4 filings
- Buyer/seller, title, date
- Transaction type (buy, sell, option exercise)
- Shares and dollar amounts

**2. Insider Buying Analysis**
- Open market purchases
- Cluster buying patterns
- Price levels of purchases
- Buyer profiles (CEO, CFO, directors)

**3. Insider Selling Analysis**
- Distinguish 10b5-1 plans vs discretionary
- Selling as % of holdings
- Timing relative to news/earnings
- Unusual patterns

**4. Historical Context**
- Compare to historical insider activity
- Correlation with stock performance
- Accuracy of insider timing

**5. Ownership Summary**
- Total insider ownership %
- Changes over time
- Pledged shares

**6. Signal Interpretation**
- Bullish/bearish signals
- Confidence level
- Key takeaways',
    'json',
    ARRAY['sec_filings', 'fmp'],
    'openai',
    'gpt-4-turbo',
    0.3,
    6000,
    ARRAY['insider', 'form4', 'ownership', 'due_diligence'],
    '1.0',
    true
);

-- DD009: Institutional Ownership Analysis
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'dd-009',
    'Institutional Ownership Analysis (13F)',
    'due_diligence',
    'ownership',
    'Analyze institutional ownership patterns from 13F filings',
    'You are an institutional research analyst. Analyze 13F filings to understand institutional positioning and identify smart money movements.',
    'Analyze institutional ownership for {{company_name}} ({{ticker}}).

**1. Ownership Overview**
- Total institutional ownership %
- Number of institutional holders
- Top 10 holders with % ownership

**2. Recent Changes (Quarter-over-Quarter)**
- New positions initiated
- Positions increased
- Positions decreased
- Positions closed
- Net institutional buying/selling

**3. Holder Analysis by Type**
- Hedge funds
- Mutual funds
- Pension funds
- ETFs
- Sovereign wealth funds

**4. Notable Holders**
- High-conviction positions (>5% of fund)
- Activist investors
- Value investors (Buffett disciples)
- Growth investors

**5. Clustering Analysis**
- Which top investors share this position?
- Common investment themes
- Correlated holdings

**6. Implications**
- Institutional sentiment
- Potential overhang
- Catalyst for flows',
    'json',
    ARRAY['sec_filings', 'fmp'],
    'openai',
    'gpt-4-turbo',
    0.3,
    6000,
    ARRAY['institutional', '13f', 'ownership', 'due_diligence'],
    '1.0',
    true
);

-- DD010: Earnings Quality Analysis
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'dd-010',
    'Earnings Quality Analysis',
    'due_diligence',
    'financial_analysis',
    'Assess the quality and sustainability of reported earnings',
    'You are a forensic accountant specializing in earnings quality analysis. Identify accounting red flags and assess the sustainability of reported earnings.',
    'Analyze earnings quality for {{company_name}} ({{ticker}}).

**1. Accruals Analysis**
- Total accruals / Total assets
- Change in accruals over time
- Comparison to peers
- Sloan accrual anomaly check

**2. Cash Flow vs Earnings**
- Operating cash flow / Net income ratio
- Trend over 5 years
- Divergence analysis
- Free cash flow conversion

**3. Revenue Quality**
- Revenue recognition policies
- Deferred revenue trends
- Accounts receivable growth vs revenue growth
- Days sales outstanding trend

**4. Expense Quality**
- Capitalization policies
- R&D capitalization
- Depreciation assumptions
- Stock-based compensation adjustments

**5. One-Time Items**
- Restructuring charges frequency
- Asset impairments
- Gains/losses on sales
- Adjusted vs GAAP earnings gap

**6. Red Flags**
- Beneish M-Score
- Altman Z-Score
- Unusual accounting changes
- Auditor concerns

**Quality Score:** 1-10 with detailed justification',
    'json',
    ARRAY['sec_filings', 'fmp'],
    'anthropic',
    'claude-3-opus-20240229',
    0.3,
    7000,
    ARRAY['earnings', 'accounting', 'quality', 'due_diligence'],
    '1.0',
    true
);

-- =====================================================
-- PORTFOLIO MANAGEMENT PROMPTS (19 prompts)
-- =====================================================

-- PM001: Portfolio Risk Analysis
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'pm-001',
    'Portfolio Risk Analysis',
    'portfolio_management',
    'risk',
    'Comprehensive portfolio risk assessment including VaR, factor exposures, and stress testing',
    'You are a portfolio risk manager at a top hedge fund. Analyze portfolio risk using quantitative methods and provide actionable insights.',
    'Analyze the risk profile of the following portfolio:

{{portfolio_holdings}}

**1. Risk Metrics**
- Portfolio volatility (annualized)
- Value at Risk (95% and 99%)
- Expected Shortfall / CVaR
- Maximum drawdown (historical)

**2. Factor Exposures**
- Market beta
- Size factor (SMB)
- Value factor (HML)
- Momentum factor
- Quality factor
- Sector exposures

**3. Concentration Risk**
- Top 5 holdings weight
- Herfindahl index
- Single stock risk
- Sector concentration

**4. Correlation Analysis**
- Correlation matrix
- Diversification ratio
- Marginal contribution to risk

**5. Stress Testing**
- 2008 Financial Crisis scenario
- 2020 COVID crash scenario
- Rising rates scenario
- Sector rotation scenario

**6. Recommendations**
- Risk reduction opportunities
- Hedging suggestions
- Rebalancing needs',
    'json',
    ARRAY['polygon', 'fmp', 'fred'],
    'openai',
    'gpt-4-turbo',
    0.3,
    7000,
    ARRAY['portfolio', 'risk', 'var', 'stress_test'],
    '1.0',
    true
);

-- PM002: Position Sizing Optimizer
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'pm-002',
    'Position Sizing Optimizer',
    'portfolio_management',
    'allocation',
    'Optimize position sizes based on conviction, risk, and portfolio constraints',
    'You are a quantitative portfolio manager. Optimize position sizes using Kelly criterion, risk parity, and mean-variance optimization principles.',
    'Optimize position sizing for adding {{ticker}} to the portfolio.

**Current Portfolio:**
{{portfolio_holdings}}

**New Position Analysis:**
- Ticker: {{ticker}}
- Conviction level: {{conviction}} (1-10)
- Investment thesis: {{thesis}}
- Target holding period: {{holding_period}}

**Calculate:**
1. **Kelly Criterion Sizing**
   - Win probability estimate
   - Win/loss ratio
   - Optimal Kelly fraction
   - Half-Kelly recommendation

2. **Risk-Based Sizing**
   - Volatility-adjusted size
   - Correlation with portfolio
   - Marginal VaR contribution
   - Maximum position based on risk budget

3. **Fundamental Sizing**
   - Upside/downside ratio
   - Conviction-adjusted size
   - Liquidity constraints

4. **Constraints Check**
   - Single position limit
   - Sector exposure limit
   - Factor exposure impact

**Recommendation:**
- Suggested position size (% of portfolio)
- Entry strategy (all at once vs scale in)
- Risk management levels',
    'json',
    ARRAY['polygon', 'fmp'],
    'openai',
    'gpt-4-turbo',
    0.3,
    5000,
    ARRAY['position_sizing', 'kelly', 'portfolio'],
    '1.0',
    true
);

-- PM003: Rebalancing Analyzer
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'pm-003',
    'Portfolio Rebalancing Analyzer',
    'portfolio_management',
    'rebalancing',
    'Analyze portfolio drift and recommend rebalancing actions',
    'You are a portfolio manager focused on maintaining optimal portfolio construction. Analyze drift from targets and recommend tax-efficient rebalancing.',
    'Analyze rebalancing needs for the portfolio:

**Current Holdings:**
{{current_holdings}}

**Target Allocation:**
{{target_allocation}}

**Analysis:**
1. **Drift Analysis**
   - Current vs target weights
   - Absolute drift by position
   - Sector drift
   - Factor drift

2. **Rebalancing Triggers**
   - Positions exceeding threshold
   - Underweight positions
   - New capital deployment needs

3. **Tax Considerations**
   - Short-term vs long-term gains
   - Tax loss harvesting opportunities
   - Wash sale considerations
   - Net tax impact estimate

4. **Transaction Cost Analysis**
   - Estimated trading costs
   - Market impact for large positions
   - Optimal execution strategy

5. **Rebalancing Recommendations**
   - Priority order of trades
   - Suggested trade sizes
   - Timeline for execution
   - Cash flow considerations',
    'json',
    ARRAY['polygon', 'fmp'],
    'openai',
    'gpt-4-turbo',
    0.3,
    5000,
    ARRAY['rebalancing', 'portfolio', 'tax'],
    '1.0',
    true
);

-- =====================================================
-- MACRO PROMPTS (16 prompts)
-- =====================================================

-- MAC001: Economic Indicator Dashboard
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'mac-001',
    'Economic Indicator Dashboard',
    'macro',
    'economic',
    'Comprehensive analysis of key economic indicators and their investment implications',
    'You are a macro strategist at a global investment firm. Analyze economic indicators to assess the current economic environment and investment implications.',
    'Provide a comprehensive economic indicator analysis.

**1. Growth Indicators**
- GDP growth (real and nominal)
- Industrial production
- Retail sales
- PMI (manufacturing and services)
- Leading Economic Index

**2. Labor Market**
- Unemployment rate
- Non-farm payrolls
- Jobless claims
- Wage growth
- Labor force participation

**3. Inflation**
- CPI and Core CPI
- PCE and Core PCE
- PPI
- Inflation expectations
- Wage-price dynamics

**4. Monetary Policy**
- Fed funds rate
- Fed balance sheet
- Market rate expectations
- Real rates
- Financial conditions

**5. Credit & Financial**
- Credit spreads
- Bank lending standards
- Consumer credit
- Yield curve shape

**6. Investment Implications**
- Current economic phase
- Sector rotation implications
- Asset allocation recommendations
- Key risks to monitor',
    'json',
    ARRAY['fred', 'trading_economics'],
    'perplexity',
    'sonar-pro',
    0.4,
    7000,
    ARRAY['macro', 'economic', 'indicators'],
    '1.0',
    true
);

-- MAC002: Fed Policy Analysis
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'mac-002',
    'Federal Reserve Policy Analysis',
    'macro',
    'monetary_policy',
    'Analyze Fed policy stance, communications, and market implications',
    'You are a Fed watcher and monetary policy expert. Analyze Federal Reserve communications, policy decisions, and their market implications.',
    'Analyze the current Federal Reserve policy stance.

**1. Current Policy**
- Fed funds rate target
- Balance sheet size and composition
- QT pace
- Forward guidance

**2. Recent Communications**
- Latest FOMC statement analysis
- Press conference key points
- Dot plot interpretation
- Fed speaker highlights

**3. Economic Assessment**
- Fed''s view on growth
- Fed''s view on inflation
- Fed''s view on employment
- Risks highlighted

**4. Policy Path**
- Market-implied rate path
- Fed dot plot path
- Divergence analysis
- Key data dependencies

**5. Historical Context**
- Comparison to past cycles
- Policy rule estimates (Taylor rule)
- Stance relative to neutral

**6. Market Implications**
- Impact on rates
- Impact on equities
- Impact on dollar
- Sector implications
- Duration positioning',
    'json',
    ARRAY['fred', 'news', 'fed_communications'],
    'anthropic',
    'claude-3-opus-20240229',
    0.4,
    6000,
    ARRAY['fed', 'monetary_policy', 'macro'],
    '1.0',
    true
);

-- MAC003: Global Macro Scan
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'mac-003',
    'Global Macro Scan',
    'macro',
    'global',
    'Scan global macro environment across major economies',
    'You are a global macro strategist. Provide a comprehensive scan of the global macroeconomic environment and identify key themes and risks.',
    'Provide a global macro scan covering major economies.

**1. United States**
- Growth outlook
- Inflation trajectory
- Fed policy path
- Key risks

**2. Europe**
- Eurozone growth
- ECB policy
- Energy situation
- Political risks

**3. China**
- Growth and stimulus
- Property sector
- Trade tensions
- Policy direction

**4. Japan**
- BOJ policy shift
- Yen dynamics
- Growth outlook

**5. Emerging Markets**
- Growth leaders/laggards
- Currency pressures
- Commodity exposure
- Political risks

**6. Global Themes**
- Trade flows
- Supply chain shifts
- Geopolitical risks
- Climate/energy transition

**7. Cross-Asset Implications**
- Equity regions to favor/avoid
- Fixed income positioning
- Currency views
- Commodity outlook',
    'json',
    ARRAY['fred', 'trading_economics', 'news'],
    'perplexity',
    'sonar-pro',
    0.5,
    7000,
    ARRAY['global', 'macro', 'international'],
    '1.0',
    true
);

-- =====================================================
-- ALTERNATIVE DATA PROMPTS
-- =====================================================

-- ALT001: Reddit Sentiment Scanner
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'alt-001',
    'Reddit Sentiment Scanner',
    'alternative_data',
    'social_sentiment',
    'Scan Reddit for stock mentions and sentiment analysis',
    'You are a social media analyst specializing in retail investor sentiment. Analyze Reddit discussions to gauge sentiment and identify emerging narratives.',
    'Scan Reddit for sentiment on {{ticker}} ({{company_name}}).

**Subreddits to analyze:**
- r/wallstreetbets
- r/stocks
- r/investing
- r/options
- Sector-specific subreddits

**Analysis:**
1. **Mention Volume**
   - Daily mention count trend
   - Comparison to baseline
   - Spike detection

2. **Sentiment Analysis**
   - Overall sentiment score (-1 to +1)
   - Bullish vs bearish ratio
   - Sentiment trend

3. **Key Narratives**
   - Main bull thesis points
   - Main bear thesis points
   - Emerging themes
   - Meme potential

4. **Influential Posts**
   - Top upvoted DD posts
   - Key opinion leaders
   - Viral content

5. **Options Activity Discussion**
   - Popular strikes/expirations
   - YOLO plays mentioned
   - Gamma squeeze potential

6. **Signal Quality**
   - Noise vs signal assessment
   - Contrarian indicator potential
   - Historical accuracy',
    'json',
    ARRAY['reddit'],
    'openai',
    'gpt-4-turbo',
    0.5,
    5000,
    ARRAY['reddit', 'sentiment', 'social', 'alternative'],
    '1.0',
    true
);

-- ALT002: Twitter/X Financial Sentiment
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'alt-002',
    'Twitter/X Financial Sentiment',
    'alternative_data',
    'social_sentiment',
    'Analyze Twitter/X for financial sentiment and influential opinions',
    'You are a social media analyst tracking financial Twitter. Identify influential voices, trending topics, and sentiment shifts.',
    'Analyze Twitter/X sentiment for {{ticker}} ({{company_name}}).

**1. Mention Analysis**
- Tweet volume trend
- Engagement metrics
- Reach estimates

**2. Influencer Tracking**
- FinTwit mentions
- Analyst commentary
- Fund manager views
- Journalist coverage

**3. Sentiment Breakdown**
- Overall sentiment
- Institutional vs retail
- Bull/bear ratio
- Sentiment momentum

**4. Trending Topics**
- Key hashtags
- Viral threads
- Breaking news
- Rumor tracking

**5. Historical Patterns**
- Pre-earnings sentiment
- Post-news reaction
- Correlation with price

**6. Actionable Insights**
- Consensus vs contrarian
- Information edge potential
- Risk of crowded trade',
    'json',
    ARRAY['twitter'],
    'openai',
    'gpt-4-turbo',
    0.5,
    5000,
    ARRAY['twitter', 'sentiment', 'social', 'alternative'],
    '1.0',
    true
);

-- =====================================================
-- BUSINESS UNDERSTANDING PROMPTS (from Notion)
-- =====================================================

-- BUS001: Business Overview Report
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'bus-001',
    'Business Overview Report',
    'business_understanding',
    'overview',
    'Comprehensive business overview including model, economics, and competitive position',
    'You are a senior equity research analyst. Provide a comprehensive business overview that would help an investor understand the company from scratch.',
    'Create a comprehensive business overview report for {{company_name}} ({{ticker}}).

**1. Company Overview**
- What does the company do? (2-3 sentence summary)
- History and key milestones
- Headquarters and geographic presence
- Employee count and culture

**2. Business Model**
- How does the company make money?
- Revenue streams breakdown
- Customer segments
- Pricing model
- Unit economics

**3. Products & Services**
- Core offerings
- Product portfolio
- Service capabilities
- Technology/IP

**4. Market Position**
- Target market size (TAM/SAM/SOM)
- Market share
- Competitive positioning
- Key competitors

**5. Growth Strategy**
- Organic growth drivers
- M&A strategy
- Geographic expansion
- New product pipeline

**6. Key Success Factors**
- What makes this company win?
- Sustainable advantages
- Critical dependencies

**7. Investment Highlights**
- Bull case summary
- Bear case summary
- Key metrics to watch',
    'json',
    ARRAY['sec_filings', 'company_website', 'news'],
    'perplexity',
    'sonar-pro',
    0.4,
    8000,
    ARRAY['business', 'overview', 'fundamental'],
    '1.0',
    true
);

-- BUS002: Growth & Margin Drivers
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'bus-002',
    'Growth & Margin Drivers Analysis',
    'business_understanding',
    'economics',
    'Deep dive into revenue growth drivers and margin expansion opportunities',
    'You are a fundamental analyst focused on understanding business economics. Analyze the key drivers of revenue growth and profitability.',
    'Analyze growth and margin drivers for {{company_name}} ({{ticker}}).

**1. Revenue Growth Drivers**
- Volume vs price decomposition
- New customer acquisition
- Existing customer expansion
- Geographic growth
- Product mix shift
- Market share gains

**2. Historical Growth Analysis**
- 5-year revenue CAGR
- Growth by segment
- Organic vs inorganic
- Cyclicality patterns

**3. Gross Margin Drivers**
- Input cost trends
- Pricing power evidence
- Mix shift impact
- Scale benefits
- Technology/automation

**4. Operating Margin Drivers**
- Operating leverage
- SG&A efficiency
- R&D productivity
- Fixed vs variable costs

**5. Future Growth Outlook**
- Near-term catalysts
- Medium-term opportunities
- Long-term optionality
- Growth sustainability

**6. Margin Expansion Potential**
- Path to target margins
- Peer margin comparison
- Management guidance
- Risks to margins',
    'json',
    ARRAY['sec_filings', 'fmp', 'earnings_calls'],
    'anthropic',
    'claude-3-opus-20240229',
    0.4,
    7000,
    ARRAY['growth', 'margins', 'economics', 'fundamental'],
    '1.0',
    true
);

-- BUS003: Business Economics Deep Dive
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'bus-003',
    'Business Economics Deep Dive',
    'business_understanding',
    'economics',
    'Analyze unit economics, capital efficiency, and return on invested capital',
    'You are a business analyst focused on unit economics and capital efficiency. Analyze the fundamental economics of the business.',
    'Perform a business economics deep dive for {{company_name}} ({{ticker}}).

**1. Unit Economics**
- Customer acquisition cost (CAC)
- Lifetime value (LTV)
- LTV/CAC ratio
- Payback period
- Churn/retention rates

**2. Capital Efficiency**
- Revenue per employee
- Revenue per dollar of assets
- Asset turnover
- Working capital efficiency

**3. Return Analysis**
- Return on Equity (ROE)
- Return on Assets (ROA)
- Return on Invested Capital (ROIC)
- ROIC vs WACC spread
- DuPont decomposition

**4. Cash Generation**
- Cash conversion cycle
- Free cash flow margin
- CapEx intensity
- Maintenance vs growth CapEx

**5. Reinvestment**
- Reinvestment rate
- Incremental ROIC
- Growth vs returns tradeoff
- Capital allocation track record

**6. Economic Moat Indicators**
- Sustainable ROIC above WACC
- Pricing power evidence
- Scale advantages
- Network effects',
    'json',
    ARRAY['sec_filings', 'fmp'],
    'anthropic',
    'claude-3-opus-20240229',
    0.3,
    7000,
    ARRAY['economics', 'roic', 'unit_economics', 'fundamental'],
    '1.0',
    true
);

-- =====================================================
-- RISK IDENTIFICATION PROMPTS (from Notion)
-- =====================================================

-- RISK001: Bear Case Builder
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'risk-001',
    'Bear Case Builder',
    'risk_identification',
    'thesis_testing',
    'Systematically build the bear case against an investment',
    'You are a short-seller and skeptical analyst. Your job is to find every possible reason why an investment could fail. Be thorough and adversarial.',
    'Build a comprehensive bear case for {{company_name}} ({{ticker}}).

**1. Business Model Risks**
- Structural challenges
- Disruption threats
- Competitive vulnerabilities
- Customer concentration

**2. Financial Risks**
- Earnings quality concerns
- Balance sheet risks
- Cash flow sustainability
- Accounting red flags

**3. Valuation Concerns**
- Current valuation vs history
- Valuation vs peers
- Implied expectations
- Downside scenarios

**4. Management Concerns**
- Track record issues
- Alignment concerns
- Governance red flags
- Key person risk

**5. Industry/Macro Risks**
- Cyclical exposure
- Regulatory threats
- Technology disruption
- Competitive dynamics

**6. Catalyst for Decline**
- Near-term risks
- What could go wrong?
- Consensus blind spots
- Short thesis summary

**Bear Case Price Target:**
- Methodology
- Key assumptions
- Downside magnitude',
    'json',
    ARRAY['sec_filings', 'news', 'short_reports'],
    'anthropic',
    'claude-3-opus-20240229',
    0.5,
    7000,
    ARRAY['bear_case', 'risk', 'short', 'thesis_testing'],
    '1.0',
    true
);

-- RISK002: Key Risk Factors
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'risk-002',
    'Key Risk Factors Identification',
    'risk_identification',
    'risk_assessment',
    'Identify and prioritize key risk factors for an investment',
    'You are a risk analyst. Identify, categorize, and prioritize all material risks that could impact the investment thesis.',
    'Identify key risk factors for {{company_name}} ({{ticker}}).

For each risk, provide:
- Description
- Probability (Low/Medium/High)
- Impact (Low/Medium/High)
- Mitigants
- Monitoring indicators

**Risk Categories:**

1. **Strategic Risks**
2. **Operational Risks**
3. **Financial Risks**
4. **Regulatory Risks**
5. **Market Risks**
6. **Technology Risks**
7. **ESG Risks**

**Risk Prioritization Matrix:**
- Plot risks on probability vs impact grid
- Identify top 5 risks to monitor
- Suggest risk mitigation strategies

**Early Warning Indicators:**
- What metrics to watch?
- What events would trigger concern?
- Position management rules',
    'json',
    ARRAY['sec_filings', 'news'],
    'openai',
    'gpt-4-turbo',
    0.4,
    6000,
    ARRAY['risk', 'risk_factors', 'monitoring'],
    '1.0',
    true
);

-- =====================================================
-- REPORT GENERATION PROMPTS
-- =====================================================

-- RPT001: Investment Memo Generator
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'rpt-001',
    'Investment Memo Generator',
    'report_generation',
    'memo',
    'Generate a comprehensive investment memo for committee presentation',
    'You are a senior analyst preparing an investment memo for the investment committee. Write a clear, compelling, and well-structured memo.',
    'Generate an investment memo for {{company_name}} ({{ticker}}).

**INVESTMENT MEMO**

**Executive Summary**
- Recommendation (Buy/Hold/Sell)
- Price target and upside
- Key thesis points (3-5 bullets)
- Position sizing recommendation

**Company Overview**
- Business description
- Key products/services
- Market position

**Investment Thesis**
- Primary thesis driver #1
- Primary thesis driver #2
- Primary thesis driver #3

**Financial Analysis**
- Historical performance
- Forward projections
- Key metrics and ratios

**Valuation**
- Methodology used
- Key assumptions
- Valuation summary
- Scenario analysis

**Risks**
- Key risks (top 3-5)
- Mitigants
- What would make us wrong?

**Catalysts**
- Near-term catalysts
- Medium-term catalysts
- Catalyst timeline

**Recommendation**
- Entry price
- Position size
- Time horizon
- Exit criteria',
    'markdown',
    ARRAY['all_research'],
    'anthropic',
    'claude-3-opus-20240229',
    0.4,
    10000,
    ARRAY['memo', 'report', 'recommendation'],
    '1.0',
    true
);

-- RPT002: Earnings Preview
INSERT INTO prompts (id, name, category, subcategory, description, system_prompt, user_prompt_template, output_format, required_data_sources, llm_provider, model, temperature, max_tokens, tags, version, is_active)
VALUES (
    'rpt-002',
    'Earnings Preview Report',
    'report_generation',
    'earnings',
    'Generate an earnings preview report ahead of quarterly results',
    'You are an equity research analyst preparing an earnings preview. Provide expectations, key items to watch, and potential stock reaction scenarios.',
    'Generate an earnings preview for {{company_name}} ({{ticker}}) for {{quarter}} {{year}}.

**Earnings Preview**

**1. Consensus Expectations**
- Revenue estimate
- EPS estimate
- Key segment estimates
- Guidance expectations

**2. Our Expectations**
- Revenue (vs consensus)
- EPS (vs consensus)
- Key variances and rationale

**3. Key Items to Watch**
- Metric #1 and why it matters
- Metric #2 and why it matters
- Metric #3 and why it matters
- Management commentary focus areas

**4. Recent Trends**
- Industry data points
- Competitor results
- Channel checks
- Macro factors

**5. Historical Patterns**
- Beat/miss history
- Stock reaction to earnings
- Guidance patterns

**6. Scenario Analysis**
- Bull case: What drives upside?
- Base case: Consensus outcome
- Bear case: What drives downside?
- Stock reaction estimates

**7. Trading Considerations**
- Options implied move
- Position into earnings?
- Post-earnings strategy',
    'markdown',
    ARRAY['fmp', 'sec_filings', 'news'],
    'openai',
    'gpt-4-turbo',
    0.4,
    6000,
    ARRAY['earnings', 'preview', 'report'],
    '1.0',
    true
);

-- Commit the transaction
COMMIT;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category);
CREATE INDEX IF NOT EXISTS idx_prompts_subcategory ON prompts(subcategory);
CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_prompts_is_active ON prompts(is_active);
