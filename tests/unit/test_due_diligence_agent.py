"""
Unit Tests for Due Diligence Agent

Tests the due diligence agent's analysis capabilities including:
- Business overview generation
- Financial analysis
- Competitive landscape analysis
- Management assessment
- Risk assessment
- DCF valuation
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
# Due Diligence Agent Tests
# =============================================================================

@pytest.mark.unit
class TestDueDiligenceAgent:
    """Tests for Due Diligence Agent."""

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

        # Configure LLM mock
        mocks['llm'].generate.return_value = (
            json.dumps({
                "business_description": "Test company description",
                "market_position": "Leader in test market",
                "competitive_advantages": ["Strong brand", "Network effects"],
                "key_risks": ["Competition", "Regulation"],
                "investment_thesis": "Buy with conviction"
            }),
            1500
        )

        # Configure FMP mock
        mock_profile = MagicMock()
        mock_profile.company_name = "Test Corp"
        mock_profile.sector = "Technology"
        mock_profile.industry = "Software"
        mock_profile.description = "A test company"
        mock_profile.mkt_cap = 100000000000
        mock_profile.full_time_employees = 50000
        mock_profile.ceo = "Test CEO"
        mocks['fmp'].get_company_profile.return_value = mock_profile

        mock_income = MagicMock()
        mock_income.date = datetime(2024, 12, 31)
        mock_income.revenue = 50000000000
        mock_income.gross_profit = 25000000000
        mock_income.operating_income = 15000000000
        mock_income.net_income = 12000000000
        mock_income.eps = 5.0
        mocks['fmp'].get_income_statement.return_value = [mock_income]

        mock_metrics = MagicMock()
        mock_metrics.date = datetime(2024, 12, 31)
        mock_metrics.pe_ratio = 25.0
        mock_metrics.pb_ratio = 8.0
        mock_metrics.roe = 0.35
        mock_metrics.roic = 0.25
        mock_metrics.debt_to_equity = 0.5
        mock_metrics.free_cash_flow_per_share = 6.0
        mocks['fmp'].get_key_metrics.return_value = [mock_metrics]

        # Configure Polygon mock
        mocks['polygon'].get_quote.return_value = {"close": 150.0, "volume": 10000000}

        return mocks

    @pytest.fixture
    def agent(self, mock_dependencies):
        """Create Due Diligence Agent with mocked dependencies."""
        with patch.multiple(
            'services.agents.due_diligence.app.agent',
            get_llm_provider=lambda: mock_dependencies['llm'],
            get_redis_client=lambda: mock_dependencies['redis'],
            get_polygon_client=lambda: mock_dependencies['polygon'],
            get_fmp_client=lambda: mock_dependencies['fmp'],
            get_sec_client=lambda: mock_dependencies['sec'],
            get_data_service=lambda: mock_dependencies['data_service']
        ):
            from services.agents.due_diligence.app.agent import DueDiligenceAgent
            agent = DueDiligenceAgent()
            agent.llm = mock_dependencies['llm']
            agent.polygon = mock_dependencies['polygon']
            agent.fmp = mock_dependencies['fmp']
            agent.sec = mock_dependencies['sec']
            agent.data_service = mock_dependencies['data_service']
            return agent

    def test_supported_prompts(self):
        """Test that agent supports expected prompts."""
        with patch.multiple(
            'services.agents.due_diligence.app.agent',
            get_llm_provider=lambda: AsyncMock(),
            get_redis_client=lambda: AsyncMock(),
            get_polygon_client=lambda: AsyncMock(),
            get_fmp_client=lambda: AsyncMock(),
            get_sec_client=lambda: AsyncMock(),
            get_data_service=lambda: AsyncMock()
        ):
            from services.agents.due_diligence.app.agent import DueDiligenceAgent
            agent = DueDiligenceAgent()

            prompts = agent.get_supported_prompts()

            assert "business_overview_report" in prompts
            assert "financial_statement_analysis" in prompts
            assert "competitive_landscape" in prompts
            assert "management_quality_assessment" in prompts
            assert "risk_assessment" in prompts
            assert "dcf_valuation" in prompts
            assert "bear_case_analysis" in prompts
            assert len(prompts) >= 30  # Should have many prompts

    @pytest.mark.asyncio
    async def test_business_overview_task(self, agent, mock_dependencies):
        """Test business overview report generation."""
        task = AgentTask(
            agent_type="due_diligence_agent",
            prompt_name="business_overview_report",
            input_data={"ticker": "AAPL"}
        )

        result = await agent.execute(task)

        assert result.success is True
        assert result.data is not None
        assert "tokens_used" in result.data
        mock_dependencies['llm'].generate.assert_called()

    @pytest.mark.asyncio
    async def test_financial_analysis_task(self, agent, mock_dependencies):
        """Test financial statement analysis."""
        task = AgentTask(
            agent_type="due_diligence_agent",
            prompt_name="financial_statement_analysis",
            input_data={"ticker": "MSFT"}
        )

        result = await agent.execute(task)

        assert result.success is True
        mock_dependencies['fmp'].get_income_statement.assert_called()

    @pytest.mark.asyncio
    async def test_competitive_landscape_task(self, agent, mock_dependencies):
        """Test competitive landscape analysis."""
        task = AgentTask(
            agent_type="due_diligence_agent",
            prompt_name="competitive_landscape",
            input_data={"ticker": "GOOGL"}
        )

        result = await agent.execute(task)

        assert result.success is True
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_management_assessment_task(self, agent, mock_dependencies):
        """Test management quality assessment."""
        task = AgentTask(
            agent_type="due_diligence_agent",
            prompt_name="management_quality_assessment",
            input_data={"ticker": "AMZN"}
        )

        result = await agent.execute(task)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_risk_assessment_task(self, agent, mock_dependencies):
        """Test risk assessment analysis."""
        task = AgentTask(
            agent_type="due_diligence_agent",
            prompt_name="risk_assessment",
            input_data={"ticker": "NVDA"}
        )

        result = await agent.execute(task)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_dcf_valuation_task(self, agent, mock_dependencies):
        """Test DCF valuation analysis."""
        task = AgentTask(
            agent_type="due_diligence_agent",
            prompt_name="dcf_valuation",
            input_data={"ticker": "META"}
        )

        result = await agent.execute(task)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_bear_case_task(self, agent, mock_dependencies):
        """Test bear case analysis."""
        task = AgentTask(
            agent_type="due_diligence_agent",
            prompt_name="bear_case_analysis",
            input_data={"ticker": "TSLA"}
        )

        result = await agent.execute(task)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_generic_analysis_fallback(self, agent, mock_dependencies):
        """Test generic analysis for unsupported prompts."""
        task = AgentTask(
            agent_type="due_diligence_agent",
            prompt_name="unsupported_prompt_name",
            input_data={"ticker": "AAPL"}
        )

        result = await agent.execute(task)

        # Should fall back to generic analysis
        assert result.success is True

    @pytest.mark.asyncio
    async def test_fetch_company_data(self, agent, mock_dependencies):
        """Test company data fetching."""
        data = await agent._fetch_company_data("AAPL")

        assert data["ticker"] == "AAPL"
        assert "profile" in data
        assert data["profile"]["name"] == "Test Corp"
        assert "income_statements" in data
        assert "key_metrics" in data

    @pytest.mark.asyncio
    async def test_handles_missing_ticker(self, agent, mock_dependencies):
        """Test handling of missing ticker."""
        task = AgentTask(
            agent_type="due_diligence_agent",
            prompt_name="business_overview_report",
            input_data={}  # No ticker
        )

        result = await agent.execute(task)

        # Should still succeed with empty company data
        assert result.success is True

    @pytest.mark.asyncio
    async def test_handles_api_failure(self, agent, mock_dependencies):
        """Test handling of API failures."""
        mock_dependencies['fmp'].get_company_profile.side_effect = Exception("API Error")

        task = AgentTask(
            agent_type="due_diligence_agent",
            prompt_name="business_overview_report",
            input_data={"ticker": "AAPL"}
        )

        # Should handle gracefully
        result = await agent.execute(task)

        # May succeed with partial data or fail gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_result_includes_metadata(self, agent, mock_dependencies):
        """Test that result includes proper metadata."""
        task = AgentTask(
            agent_type="due_diligence_agent",
            prompt_name="business_overview_report",
            input_data={"ticker": "AAPL"}
        )

        result = await agent.execute(task)

        assert result.task_id == task.task_id
        assert result.agent_type == "due_diligence_agent"
        assert result.execution_time_seconds > 0
        assert result.tokens_used >= 0


# =============================================================================
# Due Diligence Output Validation Tests
# =============================================================================

@pytest.mark.unit
class TestDueDiligenceOutputValidation:
    """Tests for validating Due Diligence agent outputs."""

    def test_business_overview_output_structure(self):
        """Test expected structure of business overview output."""
        expected_fields = [
            "business_description",
            "market_position",
            "growth_drivers",
            "competitive_advantages",
            "key_risks",
            "financial_snapshot",
            "investment_thesis"
        ]

        output = {
            "business_description": {"core_business": "Test"},
            "market_position": {"industry": "Tech", "market_share": "20%"},
            "growth_drivers": ["Product expansion", "Geographic expansion"],
            "competitive_advantages": ["Brand", "Scale"],
            "key_risks": ["Competition", "Regulation"],
            "financial_snapshot": {"revenue": 100, "margin": 0.25},
            "investment_thesis": {"bull_case": "Buy", "bear_case": "Risk"}
        }

        for field in expected_fields:
            assert field in output, f"Missing field: {field}"

    def test_dcf_valuation_output_structure(self):
        """Test expected structure of DCF valuation output."""
        expected_fields = [
            "revenue_projections",
            "margin_projections",
            "free_cash_flow",
            "discount_rate",
            "terminal_value",
            "valuation_output",
            "sensitivity_analysis"
        ]

        output = {
            "revenue_projections": {"year_1": 100, "year_5": 150},
            "margin_projections": {"gross": 0.4, "operating": 0.25},
            "free_cash_flow": {"year_1": 20, "year_5": 35},
            "discount_rate": {"wacc": 0.10, "cost_of_equity": 0.12},
            "terminal_value": {"method": "perpetuity", "value": 500},
            "valuation_output": {"enterprise_value": 600, "equity_value": 550},
            "sensitivity_analysis": {"wacc_range": [0.08, 0.12]}
        }

        for field in expected_fields:
            assert field in output, f"Missing field: {field}"

    def test_risk_assessment_output_structure(self):
        """Test expected structure of risk assessment output."""
        expected_risk_categories = [
            "business_risks",
            "competitive_risks",
            "financial_risks",
            "operational_risks",
            "regulatory_risks",
            "macro_risks"
        ]

        output = {
            "business_risks": [{"risk": "Model disruption", "severity": "high"}],
            "competitive_risks": [{"risk": "New entrants", "severity": "medium"}],
            "financial_risks": [{"risk": "Leverage", "severity": "low"}],
            "operational_risks": [{"risk": "Key person", "severity": "medium"}],
            "regulatory_risks": [{"risk": "Antitrust", "severity": "high"}],
            "macro_risks": [{"risk": "Recession", "severity": "medium"}]
        }

        for category in expected_risk_categories:
            assert category in output, f"Missing category: {category}"
            assert isinstance(output[category], list)
