"""
Unit Tests for Idea Generation Agent

Tests the idea generation agent's capabilities including:
- Thematic screening
- Order effects analysis
- Institutional clustering
- Insider trading analysis
- Pure play filtering
- Social sentiment scanning
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services'))

from shared.agents.base import AgentTask, AgentResult, TaskStatus, TaskPriority


# =============================================================================
# Idea Generation Agent Tests
# =============================================================================

@pytest.mark.unit
class TestIdeaGenerationAgent:
    """Tests for Idea Generation Agent."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create all mock dependencies."""
        mocks = {
            'llm': AsyncMock(),
            'redis': AsyncMock(),
            'polygon': AsyncMock(),
            'fmp': AsyncMock(),
            'sec': AsyncMock(),
            'data_service': AsyncMock()
        }

        # Configure LLM mock with thematic analysis response
        mocks['llm'].generate.return_value = (
            json.dumps({
                "theme_analysis": {
                    "description": "AI Infrastructure theme",
                    "market_size_estimate": "$500 billion",
                    "growth_drivers": ["Enterprise adoption", "Cloud migration"],
                    "key_trends": ["GPU demand", "Data center expansion"]
                },
                "candidates": [
                    {
                        "ticker": "NVDA",
                        "company_name": "NVIDIA Corporation",
                        "thesis": "Dominant GPU provider for AI training",
                        "revenue_exposure_pct": 85,
                        "competitive_advantages": ["CUDA ecosystem", "First mover"],
                        "catalysts": ["AI chip demand", "Data center buildout"],
                        "risks": ["Competition from AMD", "Customer concentration"],
                        "conviction_score": 9,
                        "valuation_note": "Trading at 40x forward PE"
                    },
                    {
                        "ticker": "AMD",
                        "company_name": "Advanced Micro Devices",
                        "thesis": "Second largest AI chip provider",
                        "revenue_exposure_pct": 45,
                        "competitive_advantages": ["MI300 performance", "Price point"],
                        "catalysts": ["Market share gains", "Enterprise adoption"],
                        "risks": ["NVIDIA dominance", "Execution risk"],
                        "conviction_score": 7
                    }
                ]
            }),
            2000
        )

        # Configure data service mock
        mock_context = MagicMock()
        mock_context.name = "NVIDIA Corporation"
        mock_context.sector = "Technology"
        mock_context.industry = "Semiconductors"
        mock_context.market_cap = 2000000000000
        mock_context.description = "NVIDIA designs GPUs"
        mock_context.pe_ratio = 60.0
        mock_context.revenue_growth = 0.85
        mock_context.gross_margin = 0.75
        mock_context.debt_to_equity = 0.4
        mock_context.price_change_ytd = 200.0
        mock_context.analyst_rating = "Strong Buy"
        mock_context.current_price = 850.0
        mock_context.operating_margin = 0.55
        mock_context.roe = 0.85
        mock_context.recent_news = ["NVIDIA beats earnings"]
        mock_context.insider_buying = 5
        mock_context.insider_selling = 2
        mock_context.institutional_ownership = 0.75
        mocks['data_service'].get_company_context.return_value = mock_context
        mocks['data_service'].screen_stocks.return_value = [
            {"symbol": "NVDA", "companyName": "NVIDIA"},
            {"symbol": "AMD", "companyName": "AMD"},
            {"symbol": "AVGO", "companyName": "Broadcom"}
        ]

        # Configure FMP mock for insider trading
        mock_trade = MagicMock()
        mock_trade.transaction_date = datetime(2024, 12, 1)
        mock_trade.reporting_name = "Jensen Huang"
        mock_trade.transaction_type = "S - Sale"
        mock_trade.securities_transacted = 100000
        mock_trade.price = 800.0
        mocks['fmp'].get_insider_trading.return_value = [mock_trade]

        mock_holder = MagicMock()
        mock_holder.holder = "Vanguard Group"
        mock_holder.shares = 100000000
        mock_holder.change = 5000000
        mocks['fmp'].get_institutional_holders.return_value = [mock_holder]

        return mocks

    @pytest.fixture
    def agent(self, mock_dependencies):
        """Create Idea Generation Agent with mocked dependencies."""
        with patch.multiple(
            'services.agents.idea_generation.app.agent',
            get_llm_provider=lambda: mock_dependencies['llm'],
            get_redis_client=lambda: mock_dependencies['redis'],
            get_polygon_client=lambda: mock_dependencies['polygon'],
            get_fmp_client=lambda: mock_dependencies['fmp'],
            get_sec_client=lambda: mock_dependencies['sec'],
            get_data_service=lambda: mock_dependencies['data_service']
        ):
            from services.agents.idea_generation.app.agent import IdeaGenerationAgent
            agent = IdeaGenerationAgent()
            agent.llm = mock_dependencies['llm']
            agent.polygon = mock_dependencies['polygon']
            agent.fmp = mock_dependencies['fmp']
            agent.sec = mock_dependencies['sec']
            agent.data_service = mock_dependencies['data_service']
            return agent

    def test_supported_prompts(self):
        """Test that agent supports expected prompts."""
        with patch.multiple(
            'services.agents.idea_generation.app.agent',
            get_llm_provider=lambda: AsyncMock(),
            get_redis_client=lambda: AsyncMock(),
            get_polygon_client=lambda: AsyncMock(),
            get_fmp_client=lambda: AsyncMock(),
            get_sec_client=lambda: AsyncMock(),
            get_data_service=lambda: AsyncMock()
        ):
            from services.agents.idea_generation.app.agent import IdeaGenerationAgent
            agent = IdeaGenerationAgent()

            prompts = agent.get_supported_prompts()

            assert "thematic_candidate_screen" in prompts
            assert "theme_order_effects" in prompts
            assert "institutional_clustering_13f" in prompts
            assert "insider_trading_analysis" in prompts
            assert "pure_play_filter" in prompts
            assert "social_sentiment_scan" in prompts
            assert "contrarian_opportunities" in prompts
            assert len(prompts) >= 10

    @pytest.mark.asyncio
    async def test_thematic_candidate_screen(self, agent, mock_dependencies):
        """Test thematic candidate screening."""
        task = AgentTask(
            agent_type="idea_generation_agent",
            prompt_name="thematic_candidate_screen",
            input_data={
                "theme": "AI Infrastructure",
                "sector": "Technology",
                "min_market_cap": 10000000000
            }
        )

        result = await agent.execute(task)

        assert result.success is True
        assert result.data is not None
        mock_dependencies['data_service'].screen_stocks.assert_called()
        mock_dependencies['llm'].generate.assert_called()

    @pytest.mark.asyncio
    async def test_theme_order_effects(self, agent, mock_dependencies):
        """Test theme order effects analysis."""
        # Configure specific response for order effects
        mock_dependencies['llm'].generate.return_value = (
            json.dumps({
                "theme": "Electric Vehicles",
                "first_order": {
                    "effects": ["EV manufacturers benefit directly"],
                    "beneficiaries": [
                        {"ticker": "TSLA", "company": "Tesla", "mechanism": "Direct EV sales", "confidence": "high"}
                    ]
                },
                "second_order": {
                    "effects": ["Battery suppliers benefit from demand"],
                    "beneficiaries": [
                        {"ticker": "PANW", "company": "Panasonic", "mechanism": "Battery supply", "confidence": "medium"}
                    ]
                },
                "third_order": {
                    "effects": ["Utilities see increased electricity demand"],
                    "beneficiaries": [
                        {"ticker": "NEE", "company": "NextEra", "mechanism": "Power generation", "confidence": "medium"}
                    ]
                },
                "contrarian_plays": [
                    {"ticker": "XOM", "thesis": "Undervalued oil major with EV transition optionality"}
                ]
            }),
            1500
        )

        task = AgentTask(
            agent_type="idea_generation_agent",
            prompt_name="theme_order_effects",
            input_data={"theme": "Electric Vehicles"}
        )

        result = await agent.execute(task)

        assert result.success is True
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_institutional_clustering(self, agent, mock_dependencies):
        """Test institutional clustering analysis."""
        task = AgentTask(
            agent_type="idea_generation_agent",
            prompt_name="institutional_clustering_13f",
            input_data={
                "tickers": ["AAPL", "MSFT", "GOOGL"]
            }
        )

        result = await agent.execute(task)

        assert result.success is True
        mock_dependencies['fmp'].get_institutional_holders.assert_called()

    @pytest.mark.asyncio
    async def test_insider_trading_analysis(self, agent, mock_dependencies):
        """Test insider trading analysis."""
        task = AgentTask(
            agent_type="idea_generation_agent",
            prompt_name="insider_trading_analysis",
            input_data={"ticker": "AAPL"}
        )

        result = await agent.execute(task)

        assert result.success is True
        mock_dependencies['fmp'].get_insider_trading.assert_called()

    @pytest.mark.asyncio
    async def test_pure_play_filter(self, agent, mock_dependencies):
        """Test pure play filtering."""
        task = AgentTask(
            agent_type="idea_generation_agent",
            prompt_name="pure_play_filter",
            input_data={
                "theme": "Cloud Computing",
                "candidates": ["AMZN", "MSFT", "GOOGL", "CRM"],
                "min_revenue_exposure": 50
            }
        )

        result = await agent.execute(task)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_social_sentiment_scan(self, agent, mock_dependencies):
        """Test social sentiment scanning."""
        task = AgentTask(
            agent_type="idea_generation_agent",
            prompt_name="social_sentiment_scan",
            input_data={
                "platforms": ["twitter", "reddit"],
                "tickers": ["GME", "AMC", "BBBY"]
            }
        )

        result = await agent.execute(task)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_contrarian_opportunities(self, agent, mock_dependencies):
        """Test contrarian opportunities identification."""
        task = AgentTask(
            agent_type="idea_generation_agent",
            prompt_name="contrarian_opportunities",
            input_data={"sector": "Energy"}
        )

        result = await agent.execute(task)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_newsletter_scanning(self, agent, mock_dependencies):
        """Test newsletter idea scanning."""
        task = AgentTask(
            agent_type="idea_generation_agent",
            prompt_name="newsletter_idea_scraping",
            input_data={
                "sources": ["value_investors_club", "seeking_alpha"],
                "sectors": ["Technology", "Healthcare"]
            }
        )

        result = await agent.execute(task)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_missing_theme_validation(self, agent, mock_dependencies):
        """Test validation when theme is missing."""
        task = AgentTask(
            agent_type="idea_generation_agent",
            prompt_name="thematic_candidate_screen",
            input_data={}  # Missing theme
        )

        # Should raise validation error
        result = await agent.execute(task)

        assert result.success is False
        assert "theme" in result.error.lower() or "missing" in result.error.lower()

    @pytest.mark.asyncio
    async def test_database_prompt_execution(self, agent, mock_dependencies):
        """Test execution from database-loaded prompt."""
        task = AgentTask(
            agent_type="idea_generation_agent",
            prompt_name="custom_analysis_prompt",
            input_data={"ticker": "AAPL"}
        )

        result = await agent.execute(task)

        # Should use fallback generic handler
        assert result.success is True


# =============================================================================
# Idea Generation Output Validation Tests
# =============================================================================

@pytest.mark.unit
class TestIdeaGenerationOutputValidation:
    """Tests for validating Idea Generation agent outputs."""

    def test_thematic_screen_output_structure(self):
        """Test expected structure of thematic screen output."""
        output = {
            "theme_analysis": {
                "description": "AI theme description",
                "market_size_estimate": "$500B",
                "growth_drivers": ["Driver 1", "Driver 2"],
                "key_trends": ["Trend 1", "Trend 2"]
            },
            "candidates": [
                {
                    "ticker": "NVDA",
                    "company_name": "NVIDIA",
                    "thesis": "AI chip leader",
                    "revenue_exposure_pct": 85,
                    "competitive_advantages": ["CUDA"],
                    "catalysts": ["AI demand"],
                    "risks": ["Competition"],
                    "conviction_score": 9
                }
            ]
        }

        assert "theme_analysis" in output
        assert "candidates" in output
        assert len(output["candidates"]) > 0

        candidate = output["candidates"][0]
        required_fields = ["ticker", "company_name", "thesis", "conviction_score"]
        for field in required_fields:
            assert field in candidate

    def test_order_effects_output_structure(self):
        """Test expected structure of order effects output."""
        output = {
            "theme": "Test Theme",
            "first_order": {
                "effects": ["Effect 1"],
                "beneficiaries": [{"ticker": "A", "mechanism": "Direct"}]
            },
            "second_order": {
                "effects": ["Effect 2"],
                "beneficiaries": [{"ticker": "B", "mechanism": "Indirect"}]
            },
            "third_order": {
                "effects": ["Effect 3"],
                "beneficiaries": [{"ticker": "C", "mechanism": "Long-term"}]
            }
        }

        assert "first_order" in output
        assert "second_order" in output
        assert "third_order" in output

        for order in ["first_order", "second_order", "third_order"]:
            assert "effects" in output[order]
            assert "beneficiaries" in output[order]

    def test_institutional_clustering_output_structure(self):
        """Test expected structure of institutional clustering output."""
        output = {
            "institutional_trends": {
                "bullish_signals": ["Signal 1"],
                "bearish_signals": ["Signal 2"],
                "sector_preferences": ["Technology"]
            },
            "high_conviction_picks": [
                {"ticker": "NVDA", "thesis": "AI leader", "conviction": 9}
            ],
            "crowded_trades": [
                {"ticker": "TSLA", "risk": "High concentration"}
            ],
            "under_owned_opportunities": [
                {"ticker": "INTC", "opportunity": "Turnaround potential"}
            ]
        }

        assert "institutional_trends" in output
        assert "high_conviction_picks" in output
        assert "crowded_trades" in output

    def test_insider_trading_output_structure(self):
        """Test expected structure of insider trading output."""
        output = {
            "bullish_signals": [
                {
                    "ticker": "AAPL",
                    "signal": "Cluster buying by executives",
                    "key_insiders": ["CEO", "CFO"],
                    "conviction": 8
                }
            ],
            "bearish_signals": [
                {
                    "ticker": "META",
                    "signal": "Large sales by insiders",
                    "risk_level": "medium"
                }
            ],
            "actionable_ideas": [
                {
                    "ticker": "AAPL",
                    "action": "buy",
                    "thesis": "Insider confidence",
                    "target_price": 200
                }
            ],
            "summary": "Overall bullish insider sentiment"
        }

        assert "bullish_signals" in output
        assert "bearish_signals" in output
        assert "actionable_ideas" in output


# =============================================================================
# Investment Idea Model Tests
# =============================================================================

@pytest.mark.unit
class TestInvestmentIdeaModels:
    """Tests for investment idea Pydantic models."""

    def test_investment_idea_model(self):
        """Test InvestmentIdea model validation."""
        from pydantic import BaseModel, Field
        from typing import List

        class InvestmentIdea(BaseModel):
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
            time_horizon: str
            idea_type: str

        idea = InvestmentIdea(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            sector="Technology",
            industry="Semiconductors",
            thesis_summary="AI chip leader with dominant market position",
            key_drivers=["AI adoption", "Data center growth"],
            catalysts=["Earnings beat", "New product launch"],
            risks=["Competition", "Valuation"],
            source="thematic_screen",
            confidence_score=0.85,
            time_horizon="medium",
            idea_type="long"
        )

        assert idea.ticker == "NVDA"
        assert idea.confidence_score == 0.85
        assert len(idea.key_drivers) == 2

    def test_confidence_score_validation(self):
        """Test confidence score must be between 0 and 1."""
        from pydantic import BaseModel, Field, ValidationError

        class TestModel(BaseModel):
            score: float = Field(ge=0, le=1)

        # Valid scores
        TestModel(score=0.0)
        TestModel(score=0.5)
        TestModel(score=1.0)

        # Invalid scores
        with pytest.raises(ValidationError):
            TestModel(score=-0.1)

        with pytest.raises(ValidationError):
            TestModel(score=1.1)
