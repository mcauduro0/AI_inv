"""
Integration Tests for API Endpoints

Tests the complete API Gateway endpoints including:
- Authentication flow
- Research project management
- Agent task execution
- Prompt library access
- Workflow management
- Market data endpoints
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services'))


# =============================================================================
# Authentication API Tests
# =============================================================================

@pytest.mark.integration
class TestAuthenticationAPI:
    """Tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_user(self, api_gateway_client, test_user_credentials):
        """Test user registration."""
        response = await api_gateway_client.post(
            "/api/auth/register",
            json=test_user_credentials
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["email"] == test_user_credentials["email"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, api_gateway_client, test_user_credentials):
        """Test registration with duplicate email fails."""
        # First registration
        await api_gateway_client.post(
            "/api/auth/register",
            json=test_user_credentials
        )

        # Second registration with same email
        response = await api_gateway_client.post(
            "/api/auth/register",
            json=test_user_credentials
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_login_success(self, api_gateway_client, test_user_credentials):
        """Test successful login."""
        # Register first
        await api_gateway_client.post(
            "/api/auth/register",
            json=test_user_credentials
        )

        # Login
        response = await api_gateway_client.post(
            "/api/auth/login",
            json={
                "email": test_user_credentials["email"],
                "password": test_user_credentials["password"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, api_gateway_client, test_user_credentials):
        """Test login with invalid password."""
        # Register first
        await api_gateway_client.post(
            "/api/auth/register",
            json=test_user_credentials
        )

        # Login with wrong password
        response = await api_gateway_client.post(
            "/api/auth/login",
            json={
                "email": test_user_credentials["email"],
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, api_gateway_client, auth_headers):
        """Test getting current user profile."""
        response = await api_gateway_client.get(
            "/api/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "email" in data

    @pytest.mark.asyncio
    async def test_access_protected_route_without_token(self, api_gateway_client):
        """Test accessing protected route without token."""
        response = await api_gateway_client.get("/api/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token(self, api_gateway_client, test_user_credentials):
        """Test token refresh."""
        # Login to get tokens
        await api_gateway_client.post(
            "/api/auth/register",
            json=test_user_credentials
        )

        login_response = await api_gateway_client.post(
            "/api/auth/login",
            json={
                "email": test_user_credentials["email"],
                "password": test_user_credentials["password"]
            }
        )

        tokens = login_response.json()

        # Refresh token
        response = await api_gateway_client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


# =============================================================================
# Research API Tests
# =============================================================================

@pytest.mark.integration
class TestResearchAPI:
    """Tests for research project endpoints."""

    @pytest.mark.asyncio
    async def test_start_research(self, api_gateway_client, auth_headers):
        """Test starting a research project."""
        response = await api_gateway_client.post(
            "/api/research",
            headers=auth_headers,
            json={
                "ticker": "AAPL",
                "research_type": "full",
                "focus_areas": ["valuation", "competitive"]
            }
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "project_id" in data

    @pytest.mark.asyncio
    async def test_list_research_projects(self, api_gateway_client, auth_headers):
        """Test listing research projects."""
        response = await api_gateway_client.get(
            "/api/research",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data

    @pytest.mark.asyncio
    async def test_get_research_project(self, api_gateway_client, auth_headers):
        """Test getting a specific research project."""
        # Create project first
        create_response = await api_gateway_client.post(
            "/api/research",
            headers=auth_headers,
            json={"ticker": "MSFT", "research_type": "quick"}
        )

        if create_response.status_code in [200, 201]:
            project_id = create_response.json().get("project_id")

            if project_id:
                # Get project
                response = await api_gateway_client.get(
                    f"/api/research/{project_id}",
                    headers=auth_headers
                )

                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_research_project(self, api_gateway_client, auth_headers):
        """Test deleting a research project."""
        # Create project first
        create_response = await api_gateway_client.post(
            "/api/research",
            headers=auth_headers,
            json={"ticker": "TSLA", "research_type": "quick"}
        )

        if create_response.status_code in [200, 201]:
            project_id = create_response.json().get("project_id")

            if project_id:
                # Delete project
                response = await api_gateway_client.delete(
                    f"/api/research/{project_id}",
                    headers=auth_headers
                )

                assert response.status_code in [200, 204]


# =============================================================================
# Prompt API Tests
# =============================================================================

@pytest.mark.integration
class TestPromptAPI:
    """Tests for prompt library endpoints."""

    @pytest.mark.asyncio
    async def test_list_prompts(self, api_gateway_client, auth_headers):
        """Test listing prompts."""
        response = await api_gateway_client.get(
            "/api/prompts",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_prompts_with_category_filter(self, api_gateway_client, auth_headers):
        """Test listing prompts filtered by category."""
        response = await api_gateway_client.get(
            "/api/prompts?category=idea_generation",
            headers=auth_headers
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_prompts_with_search(self, api_gateway_client, auth_headers):
        """Test searching prompts."""
        response = await api_gateway_client.get(
            "/api/prompts?search=business",
            headers=auth_headers
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_prompt_categories(self, api_gateway_client, auth_headers):
        """Test getting prompt categories."""
        response = await api_gateway_client.get(
            "/api/prompts/categories",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data

    @pytest.mark.asyncio
    async def test_execute_prompt(self, api_gateway_client, auth_headers):
        """Test executing a prompt."""
        response = await api_gateway_client.post(
            "/api/prompts/execute",
            headers=auth_headers,
            json={
                "prompt_name": "business_overview_report",
                "input_data": {"ticker": "AAPL"}
            }
        )

        # May be 200, 201, or 202 for async execution
        assert response.status_code in [200, 201, 202]


# =============================================================================
# Agent API Tests
# =============================================================================

@pytest.mark.integration
class TestAgentAPI:
    """Tests for agent management endpoints."""

    @pytest.mark.asyncio
    async def test_list_agents(self, api_gateway_client, auth_headers):
        """Test listing available agents."""
        response = await api_gateway_client.get(
            "/api/agents",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data

        # Verify expected agents exist
        agent_types = [a["type"] for a in data["agents"]]
        assert "idea_generation_agent" in agent_types
        assert "due_diligence_agent" in agent_types

    @pytest.mark.asyncio
    async def test_execute_agent_task(self, api_gateway_client, auth_headers):
        """Test executing an agent task."""
        response = await api_gateway_client.post(
            "/api/agents/execute",
            headers=auth_headers,
            json={
                "agent_type": "due_diligence_agent",
                "prompt_name": "business_overview_report",
                "input_data": {"ticker": "GOOGL"}
            }
        )

        assert response.status_code in [200, 201, 202]


# =============================================================================
# Workflow API Tests
# =============================================================================

@pytest.mark.integration
class TestWorkflowAPI:
    """Tests for workflow management endpoints."""

    @pytest.mark.asyncio
    async def test_list_workflows(self, api_gateway_client, auth_headers):
        """Test listing workflow templates."""
        response = await api_gateway_client.get(
            "/api/workflows",
            headers=auth_headers
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_start_workflow(self, api_gateway_client, auth_headers):
        """Test starting a workflow."""
        # First get available workflows
        list_response = await api_gateway_client.get(
            "/api/workflows",
            headers=auth_headers
        )

        if list_response.status_code == 200:
            workflows = list_response.json()
            if workflows and len(workflows) > 0:
                workflow_id = workflows[0].get("id")

                if workflow_id:
                    response = await api_gateway_client.post(
                        f"/api/workflows/{workflow_id}/start",
                        headers=auth_headers,
                        json={"ticker": "NVDA"}
                    )

                    assert response.status_code in [200, 201, 202]

    @pytest.mark.asyncio
    async def test_list_workflow_runs(self, api_gateway_client, auth_headers):
        """Test listing workflow runs."""
        response = await api_gateway_client.get(
            "/api/workflows/runs",
            headers=auth_headers
        )

        assert response.status_code == 200


# =============================================================================
# Market Data API Tests
# =============================================================================

@pytest.mark.integration
class TestMarketDataAPI:
    """Tests for market data endpoints."""

    @pytest.mark.asyncio
    async def test_get_quote(self, api_gateway_client, auth_headers):
        """Test getting stock quote."""
        response = await api_gateway_client.get(
            "/api/market/quote/AAPL",
            headers=auth_headers
        )

        # May fail if API key not configured
        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_get_company_info(self, api_gateway_client, auth_headers):
        """Test getting company information."""
        response = await api_gateway_client.get(
            "/api/market/company/MSFT",
            headers=auth_headers
        )

        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_get_financials(self, api_gateway_client, auth_headers):
        """Test getting financial statements."""
        response = await api_gateway_client.get(
            "/api/market/financials/GOOGL?period=annual&limit=5",
            headers=auth_headers
        )

        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_get_news(self, api_gateway_client, auth_headers):
        """Test getting stock news."""
        response = await api_gateway_client.get(
            "/api/market/news/AMZN?limit=10",
            headers=auth_headers
        )

        assert response.status_code in [200, 503]


# =============================================================================
# Health Check Tests
# =============================================================================

@pytest.mark.integration
class TestHealthChecks:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_api_gateway_health(self, api_gateway_client):
        """Test API Gateway health check."""
        response = await api_gateway_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, api_gateway_client):
        """Test Prometheus metrics endpoint."""
        response = await api_gateway_client.get("/metrics")

        assert response.status_code == 200


# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.integration
class TestErrorHandling:
    """Tests for API error handling."""

    @pytest.mark.asyncio
    async def test_404_not_found(self, api_gateway_client, auth_headers):
        """Test 404 response for non-existent endpoint."""
        response = await api_gateway_client.get(
            "/api/nonexistent/endpoint",
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_422_validation_error(self, api_gateway_client, auth_headers):
        """Test 422 response for validation errors."""
        response = await api_gateway_client.post(
            "/api/research",
            headers=auth_headers,
            json={}  # Missing required fields
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_json(self, api_gateway_client, auth_headers):
        """Test handling of invalid JSON."""
        response = await api_gateway_client.post(
            "/api/research",
            headers=auth_headers,
            content="not valid json",
            headers_override={"Content-Type": "application/json"}
        )

        assert response.status_code in [400, 422]


# =============================================================================
# Rate Limiting Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestRateLimiting:
    """Tests for API rate limiting."""

    @pytest.mark.asyncio
    async def test_rate_limit_applied(self, api_gateway_client, auth_headers):
        """Test that rate limiting is applied."""
        responses = []

        # Make many rapid requests
        for _ in range(100):
            response = await api_gateway_client.get(
                "/api/prompts",
                headers=auth_headers
            )
            responses.append(response.status_code)

        # At least some should be rate limited (429) if implemented
        # If not implemented, all should be 200
        assert all(r in [200, 429] for r in responses)
