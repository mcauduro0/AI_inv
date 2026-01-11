#!/usr/bin/env python3
"""
Pre-Deployment Validation Script for Investment Agent System

This script performs comprehensive validation checks before deployment:
1. Python syntax validation
2. Import verification
3. Configuration validation
4. Prompt library validation
5. Database schema validation
6. Docker configuration check

Usage:
    python scripts/validate-before-deploy.py [--verbose] [--fix]
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ValidationStatus(Enum):
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"


@dataclass
class ValidationResult:
    name: str
    status: ValidationStatus
    message: str
    details: Optional[List[str]] = None


class PreDeploymentValidator:
    """Comprehensive pre-deployment validation."""

    def __init__(self, project_root: Path, verbose: bool = False):
        self.project_root = project_root
        self.verbose = verbose
        self.results: List[ValidationResult] = []

    def run_all_validations(self) -> bool:
        """Run all validation checks."""
        print("\n" + "=" * 60)
        print("  Investment Agent System - Pre-Deployment Validation")
        print("=" * 60 + "\n")

        validations = [
            ("Python Syntax", self.validate_python_syntax),
            ("Python Imports", self.validate_python_imports),
            ("Environment Config", self.validate_environment_config),
            ("Prompt Library", self.validate_prompt_library),
            ("Database Models", self.validate_database_models),
            ("Docker Files", self.validate_docker_files),
            ("Kubernetes Manifests", self.validate_kubernetes_manifests),
            ("API Routes", self.validate_api_routes),
            ("Agent Definitions", self.validate_agent_definitions),
            ("Security Config", self.validate_security_config),
        ]

        for name, validator in validations:
            print(f"Checking: {name}...")
            try:
                result = validator()
                self.results.append(result)
                self._print_result(result)
            except Exception as e:
                result = ValidationResult(
                    name=name,
                    status=ValidationStatus.FAILED,
                    message=f"Validation error: {str(e)}"
                )
                self.results.append(result)
                self._print_result(result)

        return self._print_summary()

    def _print_result(self, result: ValidationResult):
        """Print a single validation result."""
        status_icons = {
            ValidationStatus.PASSED: "✅",
            ValidationStatus.WARNING: "⚠️ ",
            ValidationStatus.FAILED: "❌"
        }

        icon = status_icons[result.status]
        print(f"  {icon} {result.name}: {result.message}")

        if self.verbose and result.details:
            for detail in result.details[:5]:  # Limit to 5 details
                print(f"      - {detail}")

    def _print_summary(self) -> bool:
        """Print validation summary."""
        passed = sum(1 for r in self.results if r.status == ValidationStatus.PASSED)
        warnings = sum(1 for r in self.results if r.status == ValidationStatus.WARNING)
        failed = sum(1 for r in self.results if r.status == ValidationStatus.FAILED)

        print("\n" + "=" * 60)
        print("  Validation Summary")
        print("=" * 60)
        print(f"  ✅ Passed:   {passed}")
        print(f"  ⚠️  Warnings: {warnings}")
        print(f"  ❌ Failed:   {failed}")
        print("=" * 60 + "\n")

        if failed > 0:
            print("❌ VALIDATION FAILED - Fix errors before deploying\n")
            return False
        elif warnings > 0:
            print("⚠️  VALIDATION PASSED WITH WARNINGS\n")
            return True
        else:
            print("✅ ALL VALIDATIONS PASSED - Ready for deployment\n")
            return True

    # =========================================================================
    # Validation Methods
    # =========================================================================

    def validate_python_syntax(self) -> ValidationResult:
        """Validate Python syntax for all .py files."""
        errors = []
        checked = 0

        services_dir = self.project_root / "services"
        for py_file in services_dir.rglob("*.py"):
            checked += 1
            try:
                with open(py_file, 'r') as f:
                    source = f.read()
                compile(source, str(py_file), 'exec')
            except SyntaxError as e:
                errors.append(f"{py_file.relative_to(self.project_root)}: Line {e.lineno} - {e.msg}")

        if errors:
            return ValidationResult(
                name="Python Syntax",
                status=ValidationStatus.FAILED,
                message=f"{len(errors)} syntax errors found",
                details=errors
            )

        return ValidationResult(
            name="Python Syntax",
            status=ValidationStatus.PASSED,
            message=f"All {checked} Python files valid"
        )

    def validate_python_imports(self) -> ValidationResult:
        """Check for common import issues."""
        warnings = []
        checked = 0

        services_dir = self.project_root / "services"
        for py_file in services_dir.rglob("*.py"):
            checked += 1
            with open(py_file, 'r') as f:
                content = f.read()

            # Check for problematic imports
            if "import *" in content:
                warnings.append(f"{py_file.relative_to(self.project_root)}: Uses 'import *'")

            if "sys.path.insert" in content and "__init__" not in str(py_file):
                # This is actually used in the services, so just note it
                pass

        if warnings:
            return ValidationResult(
                name="Python Imports",
                status=ValidationStatus.WARNING,
                message=f"{len(warnings)} import warnings",
                details=warnings
            )

        return ValidationResult(
            name="Python Imports",
            status=ValidationStatus.PASSED,
            message=f"Import structure OK"
        )

    def validate_environment_config(self) -> ValidationResult:
        """Validate environment configuration."""
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"

        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "JWT_SECRET",
            "OPENAI_API_KEY",
        ]

        missing = []
        found = set()

        # Check .env file
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        var = line.split('=')[0].strip()
                        found.add(var)

        for var in required_vars:
            if var not in found and var not in os.environ:
                missing.append(var)

        if missing:
            return ValidationResult(
                name="Environment Config",
                status=ValidationStatus.WARNING,
                message=f"{len(missing)} vars may need configuration",
                details=missing
            )

        return ValidationResult(
            name="Environment Config",
            status=ValidationStatus.PASSED,
            message="Environment configuration OK"
        )

    def validate_prompt_library(self) -> ValidationResult:
        """Validate prompt library structure."""
        sql_file = self.project_root / "sql" / "init" / "003_seed_complete_prompts.sql"

        if not sql_file.exists():
            return ValidationResult(
                name="Prompt Library",
                status=ValidationStatus.WARNING,
                message="Prompt seed file not found"
            )

        with open(sql_file, 'r') as f:
            content = f.read()

        # Count prompts
        prompt_count = content.count("gen_random_uuid()")

        if prompt_count < 100:
            return ValidationResult(
                name="Prompt Library",
                status=ValidationStatus.WARNING,
                message=f"Only {prompt_count} prompts found (expected 118+)"
            )

        return ValidationResult(
            name="Prompt Library",
            status=ValidationStatus.PASSED,
            message=f"{prompt_count} prompts defined"
        )

    def validate_database_models(self) -> ValidationResult:
        """Validate database model definitions."""
        models_file = self.project_root / "services" / "shared" / "db" / "models.py"

        if not models_file.exists():
            return ValidationResult(
                name="Database Models",
                status=ValidationStatus.FAILED,
                message="models.py not found"
            )

        with open(models_file, 'r') as f:
            content = f.read()

        required_models = [
            "User",
            "ResearchProject",
            "Workflow",
            "WorkflowRun",
            "AgentTask",
            "PromptTemplate"
        ]

        missing = [m for m in required_models if f"class {m}" not in content]

        if missing:
            return ValidationResult(
                name="Database Models",
                status=ValidationStatus.FAILED,
                message=f"Missing models: {', '.join(missing)}",
                details=missing
            )

        return ValidationResult(
            name="Database Models",
            status=ValidationStatus.PASSED,
            message="All required models defined"
        )

    def validate_docker_files(self) -> ValidationResult:
        """Validate Dockerfile existence and structure."""
        required_dockerfiles = [
            "services/api-gateway/Dockerfile",
            "services/auth-service/Dockerfile",
            "services/master-control-agent/Dockerfile",
            "frontend/Dockerfile"
        ]

        missing = []
        for dockerfile in required_dockerfiles:
            if not (self.project_root / dockerfile).exists():
                missing.append(dockerfile)

        if missing:
            return ValidationResult(
                name="Docker Files",
                status=ValidationStatus.FAILED,
                message=f"{len(missing)} Dockerfiles missing",
                details=missing
            )

        return ValidationResult(
            name="Docker Files",
            status=ValidationStatus.PASSED,
            message="All Dockerfiles present"
        )

    def validate_kubernetes_manifests(self) -> ValidationResult:
        """Validate Kubernetes manifest files."""
        k8s_dir = self.project_root / "k8s"

        if not k8s_dir.exists():
            return ValidationResult(
                name="Kubernetes Manifests",
                status=ValidationStatus.WARNING,
                message="k8s directory not found"
            )

        yaml_files = list(k8s_dir.rglob("*.yaml"))

        if len(yaml_files) < 5:
            return ValidationResult(
                name="Kubernetes Manifests",
                status=ValidationStatus.WARNING,
                message=f"Only {len(yaml_files)} manifests found"
            )

        return ValidationResult(
            name="Kubernetes Manifests",
            status=ValidationStatus.PASSED,
            message=f"{len(yaml_files)} manifests found"
        )

    def validate_api_routes(self) -> ValidationResult:
        """Validate API route definitions."""
        api_gateway = self.project_root / "services" / "api-gateway" / "app" / "main.py"

        if not api_gateway.exists():
            return ValidationResult(
                name="API Routes",
                status=ValidationStatus.FAILED,
                message="API Gateway main.py not found"
            )

        with open(api_gateway, 'r') as f:
            content = f.read()

        required_routes = [
            "/api/auth/login",
            "/api/auth/register",
            "/api/research",
            "/api/prompts",
            "/api/agents",
            "/health"
        ]

        missing = [r for r in required_routes if r not in content]

        if missing:
            return ValidationResult(
                name="API Routes",
                status=ValidationStatus.WARNING,
                message=f"{len(missing)} routes may be missing",
                details=missing
            )

        return ValidationResult(
            name="API Routes",
            status=ValidationStatus.PASSED,
            message="Core API routes defined"
        )

    def validate_agent_definitions(self) -> ValidationResult:
        """Validate agent definitions."""
        agents_dir = self.project_root / "services" / "agents"

        if not agents_dir.exists():
            return ValidationResult(
                name="Agent Definitions",
                status=ValidationStatus.FAILED,
                message="Agents directory not found"
            )

        expected_agents = [
            "idea-generation",
            "due-diligence",
            "macro-analysis",
            "risk-analysis",
            "sentiment-analysis",
            "portfolio-management"
        ]

        found = []
        missing = []

        for agent in expected_agents:
            agent_dir = agents_dir / agent
            if agent_dir.exists() and (agent_dir / "app" / "main.py").exists():
                found.append(agent)
            else:
                missing.append(agent)

        if missing:
            return ValidationResult(
                name="Agent Definitions",
                status=ValidationStatus.WARNING,
                message=f"{len(missing)} agents incomplete",
                details=missing
            )

        return ValidationResult(
            name="Agent Definitions",
            status=ValidationStatus.PASSED,
            message=f"{len(found)} agents configured"
        )

    def validate_security_config(self) -> ValidationResult:
        """Validate security configurations."""
        warnings = []

        # Check for hardcoded secrets
        services_dir = self.project_root / "services"
        for py_file in services_dir.rglob("*.py"):
            with open(py_file, 'r') as f:
                content = f.read()

            # Simple pattern checks
            if re.search(r'password\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
                if "example" not in str(py_file).lower() and "test" not in str(py_file).lower():
                    warnings.append(f"{py_file.relative_to(self.project_root)}: Possible hardcoded password")

        # Check CORS configuration
        api_gateway = self.project_root / "services" / "api-gateway" / "app" / "main.py"
        if api_gateway.exists():
            with open(api_gateway, 'r') as f:
                content = f.read()
            if 'allow_origins=["*"]' in content:
                warnings.append("API Gateway: CORS allows all origins (OK for dev, restrict for prod)")

        if warnings:
            return ValidationResult(
                name="Security Config",
                status=ValidationStatus.WARNING,
                message=f"{len(warnings)} security notes",
                details=warnings
            )

        return ValidationResult(
            name="Security Config",
            status=ValidationStatus.PASSED,
            message="No critical security issues found"
        )


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Pre-deployment validation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix issues (not implemented)")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    validator = PreDeploymentValidator(project_root, verbose=args.verbose)

    success = validator.run_all_validations()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
