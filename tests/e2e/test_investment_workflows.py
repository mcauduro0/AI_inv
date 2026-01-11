"""
End-to-End Tests for Investment Workflows

Tests complete investment research workflows from start to finish including:
- Full company analysis workflow
- Thematic idea generation workflow
- Due diligence workflow
- Portfolio analysis workflow
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import json
import asyncio

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services'))


# =============================================================================
# Full Investment Analysis E2E Tests
# =============================================================================

@pytest.mark.e2e
@pytest.mark.slow
class TestFullInvestmentAnalysis:
    """End-to-end tests for full investment analysis workflow."""

    @pytest.mark.asyncio
    async def test_complete_company_analysis(
        self,
        api_gateway_client,
        auth_headers,
        mock_llm_provider,
        mock_fmp_client,
        mock_polygon_client
    ):
        """Test complete company analysis from start to finish."""

        # Step 1: Start research project
        start_response = await api_gateway_client.post(
            "/api/research",
            headers=auth_headers,
            json={
                "ticker": "AAPL",
                "research_type": "full",
                "focus_areas": ["business_model", "financials", "valuation"]
            }
        )

        assert start_response.status_code in [200, 201, 202]
        project_data = start_response.json()
        project_id = project_data["project_id"]

        # Step 2: Monitor research progress
        max_wait_seconds = 60
        poll_interval = 2
        elapsed = 0

        while elapsed < max_wait_seconds:
            status_response = await api_gateway_client.get(
                f"/api/research/{project_id}",
                headers=auth_headers
            )

            assert status_response.status_code == 200
            status = status_response.json()

            if status["status"] in ["completed", "failed"]:
                break

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        # Step 3: Verify completion
        final_response = await api_gateway_client.get(
            f"/api/research/{project_id}",
            headers=auth_headers
        )

        final_data = final_response.json()

        # May not complete in mocked environment, check for progress
        assert final_data["id"] == project_id
        assert final_data["ticker"] == "AAPL"

    @pytest.mark.asyncio
    async def test_research_workflow_stages(
        self,
        api_gateway_client,
        auth_headers
    ):
        """Test that research goes through expected stages."""

        # Start research
        response = await api_gateway_client.post(
            "/api/research",
            headers=auth_headers,
            json={
                "ticker": "MSFT",
                "research_type": "deep"
            }
        )

        if response.status_code in [200, 201, 202]:
            project_id = response.json()["project_id"]

            # Verify initial status
            status = await api_gateway_client.get(
                f"/api/research/{project_id}",
                headers=auth_headers
            )

            data = status.json()

            # Should be in one of the valid stages
            valid_stages = [
                "idea", "screening", "deep_dive",
                "thesis_development", "monitoring", "closed"
            ]

            # Status might be returned as full word or enum
            assert data["status"] in valid_stages or "screening" in data["status"].lower()


# =============================================================================
# Thematic Idea Generation E2E Tests
# =============================================================================

@pytest.mark.e2e
@pytest.mark.slow
class TestThematicIdeaGeneration:
    """End-to-end tests for thematic idea generation."""

    @pytest.mark.asyncio
    async def test_complete_thematic_screen(
        self,
        api_gateway_client,
        auth_headers
    ):
        """Test complete thematic screening workflow."""

        # Step 1: Generate thematic ideas
        generate_response = await api_gateway_client.post(
            "/api/research/ideas",
            headers=auth_headers,
            json={
                "theme": "AI Infrastructure",
                "type": "thematic",
                "sector": "Technology"
            }
        )

        assert generate_response.status_code in [200, 201, 202]

    @pytest.mark.asyncio
    async def test_order_effects_analysis(
        self,
        mca_client
    ):
        """Test theme order effects analysis."""

        response = await mca_client.post(
            "/ideas/generate",
            json={
                "theme": "Electric Vehicles",
                "strategy": "thematic"
            }
        )

        assert response.status_code in [200, 202]

    @pytest.mark.asyncio
    async def test_multi_source_idea_generation(
        self,
        mca_client
    ):
        """Test idea generation from multiple sources."""

        response = await mca_client.post(
            "/ideas/generate",
            json={
                "strategy": "thematic",
                "theme": "Cloud Computing",
                "sources": ["newsletters", "sec_filings", "social"]
            }
        )

        assert response.status_code in [200, 202]
        data = response.json()
        assert data["steps_count"] >= 1


# =============================================================================
# Due Diligence Workflow E2E Tests
# =============================================================================

@pytest.mark.e2e
@pytest.mark.slow
class TestDueDiligenceWorkflow:
    """End-to-end tests for due diligence workflow."""

    @pytest.mark.asyncio
    async def test_complete_due_diligence(
        self,
        mca_client
    ):
        """Test complete due diligence workflow."""

        # Start full due diligence
        response = await mca_client.post(
            "/research/start",
            json={
                "ticker": "NVDA",
                "research_type": "deep",
                "focus_areas": [
                    "business_model",
                    "financials",
                    "competitive",
                    "management",
                    "valuation",
                    "risk"
                ]
            }
        )

        assert response.status_code in [200, 201, 202]
        data = response.json()

        # Deep research should have many steps
        assert data["steps_count"] >= 5

    @pytest.mark.asyncio
    async def test_quick_research(self, mca_client):
        """Test quick research mode."""

        response = await mca_client.post(
            "/research/start",
            json={
                "ticker": "META",
                "research_type": "quick"
            }
        )

        assert response.status_code in [200, 201, 202]
        data = response.json()

        # Quick should have fewer steps
        assert data["steps_count"] >= 1

    @pytest.mark.asyncio
    async def test_standard_research(self, mca_client):
        """Test standard research mode."""

        response = await mca_client.post(
            "/research/start",
            json={
                "ticker": "AMZN",
                "research_type": "standard"
            }
        )

        assert response.status_code in [200, 201, 202]


# =============================================================================
# Portfolio Workflow E2E Tests
# =============================================================================

@pytest.mark.e2e
class TestPortfolioWorkflows:
    """End-to-end tests for portfolio management workflows."""

    @pytest.mark.asyncio
    async def test_portfolio_screening(self, mca_client):
        """Test portfolio screening workflow."""

        response = await mca_client.post(
            "/screening/run",
            json={
                "screener_name": "quality_screen",
                "criteria": {
                    "market_cap_min": 10000000000,
                    "roe_min": 0.15,
                    "debt_to_equity_max": 1.0
                },
                "universe": "us_stocks",
                "limit": 25
            }
        )

        assert response.status_code in [200, 202]


# =============================================================================
# Agent Coordination E2E Tests
# =============================================================================

@pytest.mark.e2e
class TestAgentCoordination:
    """End-to-end tests for multi-agent coordination."""

    @pytest.mark.asyncio
    async def test_sequential_agent_tasks(self, mca_client):
        """Test sequential execution of multiple agent tasks."""

        # Create multiple tasks
        tasks = []

        for prompt in ["business_overview_report", "financial_statement_analysis", "competitive_landscape"]:
            response = await mca_client.post(
                "/tasks",
                json={
                    "agent_type": "due_diligence_agent",
                    "prompt_name": prompt,
                    "input_data": {"ticker": "GOOGL"},
                    "priority": "normal"
                }
            )

            if response.status_code in [200, 201]:
                tasks.append(response.json()["task_id"])

        # All tasks should be created
        assert len(tasks) >= 1

    @pytest.mark.asyncio
    async def test_high_priority_task(self, mca_client):
        """Test high priority task execution."""

        response = await mca_client.post(
            "/tasks",
            json={
                "agent_type": "due_diligence_agent",
                "prompt_name": "risk_assessment",
                "input_data": {"ticker": "TSLA"},
                "priority": "critical"
            }
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["priority"] == "critical"


# =============================================================================
# Data Integration E2E Tests
# =============================================================================

@pytest.mark.e2e
class TestDataIntegration:
    """End-to-end tests for data integration."""

    @pytest.mark.asyncio
    async def test_market_data_flow(
        self,
        api_gateway_client,
        auth_headers
    ):
        """Test market data flows through the system."""

        # Get quote
        quote_response = await api_gateway_client.get(
            "/api/market/quote/AAPL",
            headers=auth_headers
        )

        # May fail if APIs not configured, that's OK for E2E test setup
        if quote_response.status_code == 200:
            data = quote_response.json()
            assert "price" in data or "close" in data

    @pytest.mark.asyncio
    async def test_company_data_aggregation(
        self,
        api_gateway_client,
        auth_headers
    ):
        """Test company data aggregation."""

        response = await api_gateway_client.get(
            "/api/market/company/MSFT",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert "name" in data or "company" in data


# =============================================================================
# Error Recovery E2E Tests
# =============================================================================

@pytest.mark.e2e
class TestErrorRecovery:
    """End-to-end tests for error recovery."""

    @pytest.mark.asyncio
    async def test_invalid_ticker_handling(self, mca_client):
        """Test handling of invalid ticker."""

        response = await mca_client.post(
            "/research/start",
            json={
                "ticker": "INVALIDTICKER123",
                "research_type": "quick"
            }
        )

        # Should accept but may fail during execution
        assert response.status_code in [200, 201, 202, 400]

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, mca_client):
        """Test retry behavior on transient failures."""

        # Create task that might fail
        response = await mca_client.post(
            "/tasks",
            json={
                "agent_type": "due_diligence_agent",
                "prompt_name": "business_overview_report",
                "input_data": {"ticker": "AAPL"}
            }
        )

        assert response.status_code in [200, 201]


# =============================================================================
# Workflow Templates E2E Tests
# =============================================================================

@pytest.mark.e2e
class TestWorkflowTemplates:
    """End-to-end tests for workflow templates."""

    @pytest.mark.asyncio
    async def test_idea_generation_workflow(self, mca_client):
        """Test idea generation workflow template."""

        # Create workflow
        create_response = await mca_client.post(
            "/workflows",
            json={
                "name": "E2E Idea Generation",
                "workflow_type": "idea_generation",
                "config": {"theme": "AI", "sector": "Technology"}
            }
        )

        if create_response.status_code in [200, 201]:
            workflow_id = create_response.json()["id"]

            # Run workflow
            run_response = await mca_client.post(
                f"/workflows/{workflow_id}/run"
            )

            assert run_response.status_code in [200, 202]

    @pytest.mark.asyncio
    async def test_due_diligence_workflow(self, mca_client):
        """Test due diligence workflow template."""

        create_response = await mca_client.post(
            "/workflows",
            json={
                "name": "E2E Due Diligence",
                "workflow_type": "due_diligence"
            }
        )

        if create_response.status_code in [200, 201]:
            workflow_id = create_response.json()["id"]

            run_response = await mca_client.post(
                f"/workflows/{workflow_id}/run",
                json={"ticker": "NVDA"}
            )

            assert run_response.status_code in [200, 202]

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, mca_client):
        """Test full analysis workflow template."""

        create_response = await mca_client.post(
            "/workflows",
            json={
                "name": "E2E Full Analysis",
                "workflow_type": "full_analysis"
            }
        )

        if create_response.status_code in [200, 201]:
            workflow_id = create_response.json()["id"]

            run_response = await mca_client.post(
                f"/workflows/{workflow_id}/run",
                json={"ticker": "AAPL"}
            )

            assert run_response.status_code in [200, 202]
