"""
Integration Tests for Master Control Agent

Tests the central orchestration service including:
- Workflow management
- Task routing
- Research project coordination
- Prompt execution
- Agent status tracking
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services'))


# =============================================================================
# MCA Health and Status Tests
# =============================================================================

@pytest.mark.integration
class TestMCAHealth:
    """Tests for MCA health and status."""

    @pytest.mark.asyncio
    async def test_health_check(self, mca_client):
        """Test MCA health check endpoint."""
        response = await mca_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["service"] == "master-control-agent"


# =============================================================================
# Workflow Management Tests
# =============================================================================

@pytest.mark.integration
class TestMCAWorkflows:
    """Tests for MCA workflow management."""

    @pytest.mark.asyncio
    async def test_create_workflow(self, mca_client):
        """Test creating a new workflow."""
        response = await mca_client.post(
            "/workflows",
            json={
                "name": "Test Research Workflow",
                "workflow_type": "full_analysis",
                "description": "Full company analysis workflow",
                "config": {"depth": "deep"}
            }
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["name"] == "Test Research Workflow"

    @pytest.mark.asyncio
    async def test_list_workflows(self, mca_client):
        """Test listing workflows."""
        response = await mca_client.get("/workflows")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_run_workflow(self, mca_client):
        """Test running a workflow."""
        # Create workflow first
        create_response = await mca_client.post(
            "/workflows",
            json={
                "name": "Test Run Workflow",
                "workflow_type": "due_diligence"
            }
        )

        if create_response.status_code in [200, 201]:
            workflow_id = create_response.json()["id"]

            # Run workflow
            response = await mca_client.post(
                f"/workflows/{workflow_id}/run",
                json={"ticker": "AAPL"}
            )

            assert response.status_code in [200, 202]
            data = response.json()
            assert "run_id" in data


# =============================================================================
# Task Management Tests
# =============================================================================

@pytest.mark.integration
class TestMCATasks:
    """Tests for MCA task management."""

    @pytest.mark.asyncio
    async def test_create_task(self, mca_client):
        """Test creating an agent task."""
        response = await mca_client.post(
            "/tasks",
            json={
                "agent_type": "due_diligence_agent",
                "prompt_name": "business_overview_report",
                "input_data": {"ticker": "MSFT"},
                "priority": "normal"
            }
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "task_id" in data
        assert data["agent_type"] == "due_diligence_agent"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_task_status(self, mca_client):
        """Test getting task status."""
        # Create task first
        create_response = await mca_client.post(
            "/tasks",
            json={
                "agent_type": "idea_generation_agent",
                "prompt_name": "thematic_candidate_screen",
                "input_data": {"theme": "AI"}
            }
        )

        if create_response.status_code in [200, 201]:
            task_id = create_response.json()["task_id"]

            # Get status
            response = await mca_client.get(f"/tasks/{task_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == task_id

    @pytest.mark.asyncio
    async def test_list_tasks(self, mca_client):
        """Test listing tasks."""
        response = await mca_client.get("/tasks")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_tasks_by_agent(self, mca_client):
        """Test filtering tasks by agent type."""
        response = await mca_client.get(
            "/tasks?agent_type=due_diligence_agent"
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_tasks_by_status(self, mca_client):
        """Test filtering tasks by status."""
        response = await mca_client.get("/tasks?status=pending")

        assert response.status_code == 200


# =============================================================================
# Research Management Tests
# =============================================================================

@pytest.mark.integration
class TestMCAResearch:
    """Tests for MCA research project management."""

    @pytest.mark.asyncio
    async def test_start_research(self, mca_client):
        """Test starting a research project."""
        response = await mca_client.post(
            "/research/start",
            json={
                "ticker": "GOOGL",
                "research_type": "full",
                "focus_areas": ["valuation", "competitive"],
                "custom_questions": ["What are the AI revenue drivers?"]
            }
        )

        assert response.status_code in [200, 201, 202]
        data = response.json()
        assert "project_id" in data
        assert data["ticker"] == "GOOGL"

    @pytest.mark.asyncio
    async def test_get_research_status(self, mca_client):
        """Test getting research project status."""
        # Start research first
        start_response = await mca_client.post(
            "/research/start",
            json={"ticker": "AMZN", "research_type": "quick"}
        )

        if start_response.status_code in [200, 201, 202]:
            project_id = start_response.json()["project_id"]

            # Get status
            response = await mca_client.get(f"/research/{project_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == project_id


# =============================================================================
# Screening Tests
# =============================================================================

@pytest.mark.integration
class TestMCAScreening:
    """Tests for MCA stock screening."""

    @pytest.mark.asyncio
    async def test_run_screening(self, mca_client):
        """Test running a stock screening workflow."""
        response = await mca_client.post(
            "/screening/run",
            json={
                "screener_name": "value_screen",
                "criteria": {
                    "pe_ratio_max": 20,
                    "market_cap_min": 10000000000,
                    "revenue_growth_min": 0.1
                },
                "universe": "us_stocks",
                "limit": 50
            }
        )

        assert response.status_code in [200, 202]


# =============================================================================
# Idea Generation Tests
# =============================================================================

@pytest.mark.integration
class TestMCAIdeaGeneration:
    """Tests for MCA idea generation."""

    @pytest.mark.asyncio
    async def test_generate_thematic_ideas(self, mca_client):
        """Test generating thematic investment ideas."""
        response = await mca_client.post(
            "/ideas/generate",
            json={
                "theme": "AI Infrastructure",
                "sector": "Technology",
                "strategy": "thematic"
            }
        )

        assert response.status_code in [200, 202]
        data = response.json()
        assert "strategy" in data
        assert data["strategy"] == "thematic"

    @pytest.mark.asyncio
    async def test_generate_contrarian_ideas(self, mca_client):
        """Test generating contrarian investment ideas."""
        response = await mca_client.post(
            "/ideas/generate",
            json={
                "strategy": "contrarian"
            }
        )

        assert response.status_code in [200, 202]

    @pytest.mark.asyncio
    async def test_generate_ideas_with_sources(self, mca_client):
        """Test generating ideas from specific sources."""
        response = await mca_client.post(
            "/ideas/generate",
            json={
                "strategy": "thematic",
                "theme": "Cloud Computing",
                "sources": ["newsletters", "sec_filings", "social"]
            }
        )

        assert response.status_code in [200, 202]


# =============================================================================
# Prompt Library Tests
# =============================================================================

@pytest.mark.integration
class TestMCAPrompts:
    """Tests for MCA prompt library."""

    @pytest.mark.asyncio
    async def test_list_prompts(self, mca_client):
        """Test listing prompts."""
        response = await mca_client.get("/prompts")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_prompts_by_category(self, mca_client):
        """Test listing prompts by category."""
        response = await mca_client.get("/prompts?category=due_diligence")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_prompts(self, mca_client):
        """Test searching prompts."""
        response = await mca_client.get("/prompts?search=valuation")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_prompt_categories(self, mca_client):
        """Test getting prompt categories."""
        response = await mca_client.get("/prompts/categories")

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data


# =============================================================================
# Agent Discovery Tests
# =============================================================================

@pytest.mark.integration
class TestMCAAgentDiscovery:
    """Tests for MCA agent discovery."""

    @pytest.mark.asyncio
    async def test_list_agents(self, mca_client):
        """Test listing available agents."""
        response = await mca_client.get("/agents")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data

        # Verify expected agents
        agent_types = [a["type"] for a in data["agents"]]
        expected_agents = [
            "idea_generation_agent",
            "business_model_agent",
            "industry_agent",
            "financial_agent",
            "valuation_agent",
            "risk_agent",
            "management_agent",
            "macro_agent",
            "thesis_agent"
        ]

        for expected in expected_agents:
            assert expected in agent_types, f"Missing agent: {expected}"

    @pytest.mark.asyncio
    async def test_agent_prompts_listed(self, mca_client):
        """Test that agent prompts are listed."""
        response = await mca_client.get("/agents")

        data = response.json()
        for agent in data["agents"]:
            assert "prompts" in agent
            assert len(agent["prompts"]) > 0


# =============================================================================
# Metrics Tests
# =============================================================================

@pytest.mark.integration
class TestMCAMetrics:
    """Tests for MCA metrics."""

    @pytest.mark.asyncio
    async def test_get_task_metrics(self, mca_client):
        """Test getting task metrics."""
        response = await mca_client.get("/metrics/tasks?days=7")

        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert data["period_days"] == 7


# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.integration
class TestMCAErrorHandling:
    """Tests for MCA error handling."""

    @pytest.mark.asyncio
    async def test_task_not_found(self, mca_client):
        """Test 404 for non-existent task."""
        response = await mca_client.get("/tasks/nonexistent-task-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_workflow_not_found(self, mca_client):
        """Test 404 for non-existent workflow."""
        response = await mca_client.post(
            "/workflows/00000000-0000-0000-0000-000000000000/run"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_task_creation(self, mca_client):
        """Test validation error for invalid task."""
        response = await mca_client.post(
            "/tasks",
            json={"invalid": "data"}
        )

        assert response.status_code == 422
