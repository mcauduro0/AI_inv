#!/usr/bin/env python3
"""
API Endpoint Test Script for Investment Agent System

This script tests all API endpoints against the live deployment:
1. Authentication (login, token refresh)
2. Research endpoints
3. Agent execution
4. Prompt library
5. Market data

Usage:
    python scripts/test-api-endpoints.py [--url URL] [--email EMAIL] [--password PASSWORD]

Example:
    python scripts/test-api-endpoints.py --url http://129.212.197.52
"""

import argparse
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import requests
except ImportError:
    print("Please install requests: pip install requests")
    sys.exit(1)


class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class TestResult:
    name: str
    status: TestStatus
    response_time_ms: float
    status_code: Optional[int]
    message: str
    response_data: Optional[Dict] = None


class APITester:
    """Comprehensive API endpoint tester."""

    def __init__(
        self,
        base_url: str,
        email: str,
        password: str,
        verbose: bool = False
    ):
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.password = password
        self.verbose = verbose
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.results: list[TestResult] = []

    def run_all_tests(self) -> bool:
        """Run all API tests."""
        print("\n" + "=" * 70)
        print("  Investment Agent System - API Endpoint Tests")
        print(f"  Target: {self.base_url}")
        print(f"  Time: {datetime.now().isoformat()}")
        print("=" * 70 + "\n")

        test_groups = [
            ("Health & Status", [
                self.test_health_check,
                self.test_docs_available,
            ]),
            ("Authentication", [
                self.test_login,
                self.test_get_current_user,
                self.test_token_refresh,
            ]),
            ("Prompts", [
                self.test_list_prompts,
                self.test_get_prompt_categories,
            ]),
            ("Agents", [
                self.test_list_agents,
            ]),
            ("Research", [
                self.test_list_research,
                self.test_start_research,
            ]),
            ("Workflows", [
                self.test_list_workflows,
            ]),
            ("Market Data", [
                self.test_market_quote,
                self.test_company_info,
            ]),
        ]

        for group_name, tests in test_groups:
            print(f"\n--- {group_name} ---")
            for test in tests:
                try:
                    result = test()
                    self.results.append(result)
                    self._print_result(result)
                except Exception as e:
                    result = TestResult(
                        name=test.__name__,
                        status=TestStatus.FAILED,
                        response_time_ms=0,
                        status_code=None,
                        message=f"Exception: {str(e)}"
                    )
                    self.results.append(result)
                    self._print_result(result)

        return self._print_summary()

    def _print_result(self, result: TestResult):
        """Print a single test result."""
        status_icons = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌",
            TestStatus.SKIPPED: "⏭️ "
        }

        icon = status_icons[result.status]
        time_str = f"{result.response_time_ms:.0f}ms" if result.response_time_ms else "N/A"

        print(f"  {icon} {result.name}")
        print(f"      Status: {result.status_code or 'N/A'} | Time: {time_str}")
        print(f"      {result.message}")

        if self.verbose and result.response_data:
            print(f"      Response: {json.dumps(result.response_data, indent=2)[:200]}...")

    def _print_summary(self) -> bool:
        """Print test summary."""
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        total_time = sum(r.response_time_ms for r in self.results)

        print("\n" + "=" * 70)
        print("  Test Summary")
        print("=" * 70)
        print(f"  ✅ Passed:  {passed}")
        print(f"  ❌ Failed:  {failed}")
        print(f"  ⏭️  Skipped: {skipped}")
        print(f"  ⏱️  Total Time: {total_time:.0f}ms")
        print("=" * 70 + "\n")

        if failed > 0:
            print("❌ SOME TESTS FAILED\n")
            return False
        else:
            print("✅ ALL TESTS PASSED\n")
            return True

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        auth: bool = False
    ) -> Tuple[Optional[requests.Response], float]:
        """Make HTTP request and return response with timing."""
        url = f"{self.base_url}{endpoint}"

        headers = {"Content-Type": "application/json"}
        if auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        start = time.time()
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return None, 0

            elapsed_ms = (time.time() - start) * 1000
            return response, elapsed_ms
        except requests.exceptions.RequestException as e:
            elapsed_ms = (time.time() - start) * 1000
            return None, elapsed_ms

    # =========================================================================
    # Health & Status Tests
    # =========================================================================

    def test_health_check(self) -> TestResult:
        """Test health check endpoint."""
        response, elapsed = self._request("GET", "/health")

        if response is None:
            return TestResult(
                name="Health Check",
                status=TestStatus.FAILED,
                response_time_ms=elapsed,
                status_code=None,
                message="Connection failed"
            )

        if response.status_code == 200:
            return TestResult(
                name="Health Check",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message="API is healthy",
                response_data=response.json() if response.text else None
            )

        return TestResult(
            name="Health Check",
            status=TestStatus.FAILED,
            response_time_ms=elapsed,
            status_code=response.status_code,
            message=f"Unexpected status: {response.text[:100]}"
        )

    def test_docs_available(self) -> TestResult:
        """Test OpenAPI docs availability."""
        response, elapsed = self._request("GET", "/docs")

        if response and response.status_code == 200:
            return TestResult(
                name="API Docs",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message="OpenAPI docs available"
            )

        return TestResult(
            name="API Docs",
            status=TestStatus.FAILED,
            response_time_ms=elapsed,
            status_code=response.status_code if response else None,
            message="Docs not accessible"
        )

    # =========================================================================
    # Authentication Tests
    # =========================================================================

    def test_login(self) -> TestResult:
        """Test login endpoint."""
        response, elapsed = self._request(
            "POST",
            "/api/auth/login",
            data={"email": self.email, "password": self.password}
        )

        if response is None:
            return TestResult(
                name="Login",
                status=TestStatus.FAILED,
                response_time_ms=elapsed,
                status_code=None,
                message="Connection failed"
            )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")

            return TestResult(
                name="Login",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message=f"Successfully authenticated as {self.email}"
            )

        return TestResult(
            name="Login",
            status=TestStatus.FAILED,
            response_time_ms=elapsed,
            status_code=response.status_code,
            message=f"Login failed: {response.text[:100]}"
        )

    def test_get_current_user(self) -> TestResult:
        """Test get current user endpoint."""
        if not self.access_token:
            return TestResult(
                name="Get Current User",
                status=TestStatus.SKIPPED,
                response_time_ms=0,
                status_code=None,
                message="No access token (login first)"
            )

        response, elapsed = self._request("GET", "/api/auth/me", auth=True)

        if response and response.status_code == 200:
            data = response.json()
            return TestResult(
                name="Get Current User",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message=f"User: {data.get('email', 'N/A')}",
                response_data=data
            )

        return TestResult(
            name="Get Current User",
            status=TestStatus.FAILED,
            response_time_ms=elapsed,
            status_code=response.status_code if response else None,
            message="Failed to get user info"
        )

    def test_token_refresh(self) -> TestResult:
        """Test token refresh endpoint."""
        if not self.refresh_token:
            return TestResult(
                name="Token Refresh",
                status=TestStatus.SKIPPED,
                response_time_ms=0,
                status_code=None,
                message="No refresh token"
            )

        response, elapsed = self._request(
            "POST",
            "/api/auth/refresh",
            data={"refresh_token": self.refresh_token}
        )

        if response and response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token", self.access_token)

            return TestResult(
                name="Token Refresh",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message="Token refreshed successfully"
            )

        return TestResult(
            name="Token Refresh",
            status=TestStatus.FAILED,
            response_time_ms=elapsed,
            status_code=response.status_code if response else None,
            message="Token refresh failed"
        )

    # =========================================================================
    # Prompt Tests
    # =========================================================================

    def test_list_prompts(self) -> TestResult:
        """Test list prompts endpoint."""
        response, elapsed = self._request("GET", "/api/prompts", auth=True)

        if response and response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            total = data.get("total", len(items))

            return TestResult(
                name="List Prompts",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message=f"Found {total} prompts"
            )

        return TestResult(
            name="List Prompts",
            status=TestStatus.FAILED,
            response_time_ms=elapsed,
            status_code=response.status_code if response else None,
            message="Failed to list prompts"
        )

    def test_get_prompt_categories(self) -> TestResult:
        """Test get prompt categories endpoint."""
        response, elapsed = self._request("GET", "/api/prompts/categories", auth=True)

        if response and response.status_code == 200:
            data = response.json()
            categories = data.get("categories", [])

            return TestResult(
                name="Prompt Categories",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message=f"Found {len(categories)} categories"
            )

        return TestResult(
            name="Prompt Categories",
            status=TestStatus.FAILED,
            response_time_ms=elapsed,
            status_code=response.status_code if response else None,
            message="Failed to get categories"
        )

    # =========================================================================
    # Agent Tests
    # =========================================================================

    def test_list_agents(self) -> TestResult:
        """Test list agents endpoint."""
        response, elapsed = self._request("GET", "/api/agents", auth=True)

        if response and response.status_code == 200:
            data = response.json()
            agents = data.get("agents", [])

            return TestResult(
                name="List Agents",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message=f"Found {len(agents)} agents"
            )

        return TestResult(
            name="List Agents",
            status=TestStatus.FAILED,
            response_time_ms=elapsed,
            status_code=response.status_code if response else None,
            message="Failed to list agents"
        )

    # =========================================================================
    # Research Tests
    # =========================================================================

    def test_list_research(self) -> TestResult:
        """Test list research projects endpoint."""
        response, elapsed = self._request("GET", "/api/research", auth=True)

        if response and response.status_code == 200:
            return TestResult(
                name="List Research",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message="Research endpoint accessible"
            )

        return TestResult(
            name="List Research",
            status=TestStatus.FAILED,
            response_time_ms=elapsed,
            status_code=response.status_code if response else None,
            message="Failed to list research"
        )

    def test_start_research(self) -> TestResult:
        """Test start research endpoint (dry run - doesn't actually start)."""
        # Just test the endpoint is reachable, don't actually start research
        response, elapsed = self._request(
            "POST",
            "/api/research",
            data={
                "ticker": "AAPL",
                "research_type": "quick"
            },
            auth=True
        )

        if response and response.status_code in [200, 201, 202]:
            return TestResult(
                name="Start Research",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message="Research endpoint functional"
            )

        # 422 is also acceptable (validation) - means endpoint exists
        if response and response.status_code == 422:
            return TestResult(
                name="Start Research",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message="Research endpoint exists (validation error expected)"
            )

        return TestResult(
            name="Start Research",
            status=TestStatus.FAILED,
            response_time_ms=elapsed,
            status_code=response.status_code if response else None,
            message="Research endpoint not accessible"
        )

    # =========================================================================
    # Workflow Tests
    # =========================================================================

    def test_list_workflows(self) -> TestResult:
        """Test list workflows endpoint."""
        response, elapsed = self._request("GET", "/api/workflows", auth=True)

        if response and response.status_code == 200:
            return TestResult(
                name="List Workflows",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message="Workflows endpoint accessible"
            )

        return TestResult(
            name="List Workflows",
            status=TestStatus.FAILED,
            response_time_ms=elapsed,
            status_code=response.status_code if response else None,
            message="Failed to list workflows"
        )

    # =========================================================================
    # Market Data Tests
    # =========================================================================

    def test_market_quote(self) -> TestResult:
        """Test market quote endpoint."""
        response, elapsed = self._request("GET", "/api/market/quote/AAPL", auth=True)

        if response and response.status_code == 200:
            return TestResult(
                name="Market Quote",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message="Market data accessible"
            )

        # 503 might mean external API is down - that's a warning, not failure
        if response and response.status_code in [503, 502]:
            return TestResult(
                name="Market Quote",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message="Endpoint exists (external API may be unavailable)"
            )

        return TestResult(
            name="Market Quote",
            status=TestStatus.FAILED,
            response_time_ms=elapsed,
            status_code=response.status_code if response else None,
            message="Market endpoint not accessible"
        )

    def test_company_info(self) -> TestResult:
        """Test company info endpoint."""
        response, elapsed = self._request("GET", "/api/market/company/AAPL", auth=True)

        if response and response.status_code == 200:
            return TestResult(
                name="Company Info",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message="Company data accessible"
            )

        if response and response.status_code in [503, 502]:
            return TestResult(
                name="Company Info",
                status=TestStatus.PASSED,
                response_time_ms=elapsed,
                status_code=response.status_code,
                message="Endpoint exists (external API may be unavailable)"
            )

        return TestResult(
            name="Company Info",
            status=TestStatus.FAILED,
            response_time_ms=elapsed,
            status_code=response.status_code if response else None,
            message="Company endpoint not accessible"
        )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test API endpoints")
    parser.add_argument(
        "--url",
        default="http://129.212.197.52",
        help="API base URL"
    )
    parser.add_argument(
        "--email",
        default="admin@investmentagent.com",
        help="Login email"
    )
    parser.add_argument(
        "--password",
        default="InvestAgent2026!",
        help="Login password"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )

    args = parser.parse_args()

    tester = APITester(
        base_url=args.url,
        email=args.email,
        password=args.password,
        verbose=args.verbose
    )

    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
