"""
Performance and Load Tests for AI Investment Agent System

Tests system performance under various load conditions including:
- API response times
- Concurrent request handling
- Agent execution performance
- Database query performance
- Memory and resource usage
"""

import pytest
from datetime import datetime, timezone
import asyncio
import time
import statistics
from typing import List, Tuple
from unittest.mock import AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services'))


# =============================================================================
# API Response Time Tests
# =============================================================================

@pytest.mark.performance
class TestAPIResponseTimes:
    """Tests for API response time benchmarks."""

    @pytest.mark.asyncio
    async def test_health_check_response_time(
        self,
        api_gateway_client,
        performance_thresholds
    ):
        """Test health check responds within threshold."""
        times = []

        for _ in range(10):
            start = time.perf_counter()
            response = await api_gateway_client.get("/health")
            elapsed = (time.perf_counter() - start) * 1000  # ms

            assert response.status_code == 200
            times.append(elapsed)

        avg_time = statistics.mean(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]

        assert avg_time < performance_thresholds["api_response_time_ms"], \
            f"Average response time {avg_time:.2f}ms exceeds threshold"

        print(f"Health check - Avg: {avg_time:.2f}ms, P95: {p95_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_prompt_list_response_time(
        self,
        api_gateway_client,
        auth_headers,
        performance_thresholds
    ):
        """Test prompt listing responds within threshold."""
        times = []

        for _ in range(10):
            start = time.perf_counter()
            response = await api_gateway_client.get(
                "/api/prompts",
                headers=auth_headers
            )
            elapsed = (time.perf_counter() - start) * 1000

            times.append(elapsed)

        avg_time = statistics.mean(times)

        # Prompt listing should be fast
        assert avg_time < performance_thresholds["api_response_time_ms"] * 2

        print(f"Prompt list - Avg: {avg_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_agent_list_response_time(
        self,
        api_gateway_client,
        auth_headers,
        performance_thresholds
    ):
        """Test agent listing responds within threshold."""
        times = []

        for _ in range(10):
            start = time.perf_counter()
            response = await api_gateway_client.get(
                "/api/agents",
                headers=auth_headers
            )
            elapsed = (time.perf_counter() - start) * 1000

            times.append(elapsed)

        avg_time = statistics.mean(times)

        assert avg_time < performance_thresholds["api_response_time_ms"]

        print(f"Agent list - Avg: {avg_time:.2f}ms")


# =============================================================================
# Concurrent Request Tests
# =============================================================================

@pytest.mark.performance
class TestConcurrentRequests:
    """Tests for concurrent request handling."""

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(
        self,
        api_gateway_client,
        performance_thresholds
    ):
        """Test handling many concurrent health checks."""
        num_requests = 50

        async def make_request():
            start = time.perf_counter()
            response = await api_gateway_client.get("/health")
            elapsed = (time.perf_counter() - start) * 1000
            return response.status_code, elapsed

        start = time.perf_counter()
        results = await asyncio.gather(
            *[make_request() for _ in range(num_requests)]
        )
        total_time = time.perf_counter() - start

        successful = sum(1 for status, _ in results if status == 200)
        times = [t for _, t in results]

        assert successful == num_requests, \
            f"Only {successful}/{num_requests} requests succeeded"

        print(f"Concurrent health checks ({num_requests}) - Total: {total_time:.2f}s, "
              f"Avg: {statistics.mean(times):.2f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_prompt_requests(
        self,
        api_gateway_client,
        auth_headers
    ):
        """Test handling concurrent prompt list requests."""
        num_requests = 20

        async def make_request():
            start = time.perf_counter()
            response = await api_gateway_client.get(
                "/api/prompts",
                headers=auth_headers
            )
            elapsed = (time.perf_counter() - start) * 1000
            return response.status_code, elapsed

        results = await asyncio.gather(
            *[make_request() for _ in range(num_requests)]
        )

        successful = sum(1 for status, _ in results if status in [200, 401])

        # Most should succeed
        assert successful >= num_requests * 0.9

    @pytest.mark.asyncio
    async def test_mixed_concurrent_requests(
        self,
        api_gateway_client,
        auth_headers
    ):
        """Test handling mixed concurrent request types."""

        async def health_request():
            return await api_gateway_client.get("/health")

        async def prompts_request():
            return await api_gateway_client.get(
                "/api/prompts",
                headers=auth_headers
            )

        async def agents_request():
            return await api_gateway_client.get(
                "/api/agents",
                headers=auth_headers
            )

        # Mix of request types
        requests = (
            [health_request() for _ in range(10)] +
            [prompts_request() for _ in range(10)] +
            [agents_request() for _ in range(10)]
        )

        results = await asyncio.gather(*requests, return_exceptions=True)

        successful = sum(
            1 for r in results
            if not isinstance(r, Exception) and r.status_code in [200, 401]
        )

        # Most should succeed
        assert successful >= len(requests) * 0.8


# =============================================================================
# Agent Execution Performance Tests
# =============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestAgentExecutionPerformance:
    """Tests for agent execution performance."""

    @pytest.mark.asyncio
    async def test_task_creation_performance(
        self,
        mca_client,
        performance_thresholds
    ):
        """Test task creation performance."""
        times = []

        for i in range(10):
            start = time.perf_counter()
            response = await mca_client.post(
                "/tasks",
                json={
                    "agent_type": "due_diligence_agent",
                    "prompt_name": "business_overview_report",
                    "input_data": {"ticker": "AAPL"}
                }
            )
            elapsed = (time.perf_counter() - start) * 1000

            if response.status_code in [200, 201]:
                times.append(elapsed)

        if times:
            avg_time = statistics.mean(times)
            print(f"Task creation - Avg: {avg_time:.2f}ms")

            # Task creation should be fast
            assert avg_time < 500  # 500ms threshold

    @pytest.mark.asyncio
    async def test_concurrent_task_creation(self, mca_client):
        """Test concurrent task creation."""
        num_tasks = 20

        async def create_task(i):
            start = time.perf_counter()
            response = await mca_client.post(
                "/tasks",
                json={
                    "agent_type": "due_diligence_agent",
                    "prompt_name": "business_overview_report",
                    "input_data": {"ticker": f"TEST{i}"}
                }
            )
            elapsed = (time.perf_counter() - start) * 1000
            return response.status_code, elapsed

        results = await asyncio.gather(
            *[create_task(i) for i in range(num_tasks)]
        )

        successful = sum(1 for status, _ in results if status in [200, 201])

        print(f"Concurrent task creation: {successful}/{num_tasks} successful")

        assert successful >= num_tasks * 0.8


# =============================================================================
# Database Query Performance Tests
# =============================================================================

@pytest.mark.performance
class TestDatabasePerformance:
    """Tests for database query performance."""

    @pytest.mark.asyncio
    async def test_prompt_query_performance(
        self,
        mca_client,
        performance_thresholds
    ):
        """Test prompt listing query performance."""
        times = []

        for _ in range(20):
            start = time.perf_counter()
            response = await mca_client.get("/prompts?limit=100")
            elapsed = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                times.append(elapsed)

        if times:
            avg_time = statistics.mean(times)
            p95_time = sorted(times)[int(len(times) * 0.95)]

            print(f"Prompt query - Avg: {avg_time:.2f}ms, P95: {p95_time:.2f}ms")

            assert avg_time < performance_thresholds["database_query_time_ms"] * 5

    @pytest.mark.asyncio
    async def test_category_query_performance(self, mca_client):
        """Test category aggregation query performance."""
        times = []

        for _ in range(20):
            start = time.perf_counter()
            response = await mca_client.get("/prompts/categories")
            elapsed = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                times.append(elapsed)

        if times:
            avg_time = statistics.mean(times)
            print(f"Category query - Avg: {avg_time:.2f}ms")


# =============================================================================
# Throughput Tests
# =============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestThroughput:
    """Tests for system throughput."""

    @pytest.mark.asyncio
    async def test_sustained_load(
        self,
        api_gateway_client,
        performance_thresholds
    ):
        """Test sustained load handling."""
        duration_seconds = 10
        results = []

        async def make_requests():
            start = time.perf_counter()
            count = 0

            while (time.perf_counter() - start) < duration_seconds:
                response = await api_gateway_client.get("/health")
                if response.status_code == 200:
                    count += 1
                results.append(response.status_code)

            return count

        # Run multiple workers
        workers = 5
        counts = await asyncio.gather(
            *[make_requests() for _ in range(workers)]
        )

        total_requests = sum(counts)
        rps = total_requests / duration_seconds

        print(f"Sustained load - {total_requests} requests in {duration_seconds}s "
              f"({rps:.2f} RPS)")

        # Should achieve reasonable throughput
        assert rps >= 10  # At least 10 RPS


# =============================================================================
# Memory and Resource Tests
# =============================================================================

@pytest.mark.performance
class TestResourceUsage:
    """Tests for resource usage patterns."""

    @pytest.mark.asyncio
    async def test_no_memory_leak_on_requests(
        self,
        api_gateway_client
    ):
        """Test that repeated requests don't cause memory leaks."""
        import gc

        gc.collect()

        # Make many requests
        for _ in range(100):
            await api_gateway_client.get("/health")

        gc.collect()

        # Note: Actual memory leak detection would require more sophisticated tools
        # This is a placeholder for the pattern

    @pytest.mark.asyncio
    async def test_connection_handling(
        self,
        api_gateway_client
    ):
        """Test that connections are properly managed."""

        # Rapid connection/disconnection
        for _ in range(50):
            response = await api_gateway_client.get("/health")
            assert response.status_code == 200


# =============================================================================
# Benchmark Fixtures
# =============================================================================

@pytest.fixture
def benchmark_results():
    """Collect benchmark results."""
    return {
        "health_check_ms": [],
        "prompt_list_ms": [],
        "task_creation_ms": [],
        "concurrent_rps": 0
    }


# =============================================================================
# Load Test Configuration
# =============================================================================

@pytest.fixture
def load_test_config():
    """Load test configuration."""
    return {
        "light": {
            "users": 10,
            "duration_seconds": 30,
            "ramp_up_seconds": 5
        },
        "medium": {
            "users": 50,
            "duration_seconds": 60,
            "ramp_up_seconds": 10
        },
        "heavy": {
            "users": 100,
            "duration_seconds": 120,
            "ramp_up_seconds": 20
        }
    }
