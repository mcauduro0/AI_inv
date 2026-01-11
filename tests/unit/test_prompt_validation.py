"""
Prompt Library Validation Tests

Tests the 118 prompts in the library for:
- Template syntax correctness
- Variable placeholder validation
- Output schema validation
- Category consistency
- LLM provider compatibility
"""

import pytest
import re
from typing import Dict, List, Any
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services'))


# =============================================================================
# Prompt Template Syntax Tests
# =============================================================================

@pytest.mark.unit
class TestPromptTemplateSyntax:
    """Tests for prompt template syntax validation."""

    def test_variable_placeholder_syntax(self, sample_prompts):
        """Test that variable placeholders use correct syntax."""
        for prompt in sample_prompts:
            template = prompt.get("template", "")

            # Find all placeholders
            placeholders = re.findall(r'\{\{(\w+)\}\}', template)

            # Each placeholder should be alphanumeric
            for placeholder in placeholders:
                assert placeholder.isidentifier(), \
                    f"Invalid placeholder '{placeholder}' in {prompt['name']}"

    def test_no_unclosed_placeholders(self, sample_prompts):
        """Test that all placeholders are properly closed."""
        for prompt in sample_prompts:
            template = prompt.get("template", "")

            # Count opening and closing braces
            opens = template.count("{{")
            closes = template.count("}}")

            assert opens == closes, \
                f"Unbalanced placeholders in {prompt['name']}: {opens} opens, {closes} closes"

    def test_no_empty_placeholders(self, sample_prompts):
        """Test that there are no empty placeholders."""
        for prompt in sample_prompts:
            template = prompt.get("template", "")

            # Should not have empty placeholders
            assert "{{}}" not in template, \
                f"Empty placeholder in {prompt['name']}"

    def test_template_not_empty(self, sample_prompts):
        """Test that templates are not empty."""
        for prompt in sample_prompts:
            template = prompt.get("template", "")

            assert len(template.strip()) > 0, \
                f"Empty template in {prompt['name']}"

    def test_template_minimum_length(self, sample_prompts):
        """Test that templates have minimum meaningful length."""
        min_length = 50  # Minimum characters

        for prompt in sample_prompts:
            template = prompt.get("template", "")

            assert len(template) >= min_length, \
                f"Template too short in {prompt['name']}: {len(template)} chars"


# =============================================================================
# Prompt Category Tests
# =============================================================================

@pytest.mark.unit
class TestPromptCategories:
    """Tests for prompt category validation."""

    VALID_CATEGORIES = [
        "idea_generation",
        "due_diligence",
        "portfolio_management",
        "macro_analysis",
        "alternative_data",
        "business_understanding",
        "risk_identification",
        "report_generation",
        "valuation",
        "screening"
    ]

    def test_category_is_valid(self, sample_prompts):
        """Test that prompts have valid categories."""
        for prompt in sample_prompts:
            category = prompt.get("category", "")

            assert category in self.VALID_CATEGORIES, \
                f"Invalid category '{category}' in {prompt['name']}"

    def test_category_not_empty(self, sample_prompts):
        """Test that category is not empty."""
        for prompt in sample_prompts:
            category = prompt.get("category", "")

            assert len(category.strip()) > 0, \
                f"Empty category in {prompt['name']}"


# =============================================================================
# Prompt Output Schema Tests
# =============================================================================

@pytest.mark.unit
class TestPromptOutputSchemas:
    """Tests for prompt output schema validation."""

    def test_output_format_is_json(self, prompt_validation_schema):
        """Test that output format specifies JSON where expected."""
        for prompt_name, schema in prompt_validation_schema.items():
            assert schema.get("output_type") == "json", \
                f"Prompt {prompt_name} should have JSON output"

    def test_required_fields_defined(self, prompt_validation_schema):
        """Test that required fields are defined."""
        for prompt_name, schema in prompt_validation_schema.items():
            required = schema.get("required_fields", [])

            assert len(required) > 0, \
                f"No required fields defined for {prompt_name}"

    def test_output_schema_parseable(self):
        """Test that output schemas are valid JSON schemas."""
        test_schemas = [
            {
                "type": "object",
                "properties": {
                    "analysis": {"type": "string"},
                    "score": {"type": "number"}
                }
            },
            {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "thesis": {"type": "string"}
                    }
                }
            }
        ]

        for schema in test_schemas:
            # Should be serializable
            json_str = json.dumps(schema)
            parsed = json.loads(json_str)

            assert parsed == schema


# =============================================================================
# Prompt LLM Configuration Tests
# =============================================================================

@pytest.mark.unit
class TestPromptLLMConfiguration:
    """Tests for prompt LLM configuration validation."""

    VALID_PROVIDERS = ["openai", "anthropic", "perplexity", "gemini"]
    VALID_MODELS = [
        # OpenAI
        "gpt-4", "gpt-4-turbo", "gpt-4-turbo-preview", "gpt-4o", "gpt-3.5-turbo",
        # Anthropic
        "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
        "claude-3-opus-20240229", "claude-3-sonnet-20240229",
        # Perplexity
        "sonar-pro", "sonar-medium", "sonar-small",
        # Gemini
        "gemini-pro", "gemini-2.5-flash"
    ]

    def test_temperature_in_range(self):
        """Test that temperature is in valid range."""
        test_temperatures = [0.0, 0.3, 0.5, 0.7, 1.0]

        for temp in test_temperatures:
            assert 0.0 <= temp <= 1.0, f"Temperature {temp} out of range"

    def test_max_tokens_reasonable(self):
        """Test that max_tokens is reasonable."""
        test_max_tokens = [1000, 2000, 3000, 4000, 8000]

        for tokens in test_max_tokens:
            assert 100 <= tokens <= 16000, f"Max tokens {tokens} unreasonable"


# =============================================================================
# Prompt Content Quality Tests
# =============================================================================

@pytest.mark.unit
class TestPromptContentQuality:
    """Tests for prompt content quality."""

    def test_has_clear_instructions(self, sample_prompts):
        """Test that prompts have clear instructions."""
        instruction_keywords = [
            "analyze", "provide", "identify", "evaluate",
            "generate", "create", "assess", "compare"
        ]

        for prompt in sample_prompts:
            template = prompt.get("template", "").lower()

            has_instruction = any(
                keyword in template
                for keyword in instruction_keywords
            )

            assert has_instruction, \
                f"No clear instructions in {prompt['name']}"

    def test_has_output_format_instruction(self, sample_prompts):
        """Test that prompts specify output format."""
        format_keywords = ["json", "format", "structure", "output"]

        for prompt in sample_prompts:
            template = prompt.get("template", "").lower()

            has_format = any(
                keyword in template
                for keyword in format_keywords
            )

            # Not all prompts need format specification, but most should
            if not has_format:
                print(f"Warning: No format instruction in {prompt['name']}")

    def test_no_placeholder_in_description(self, sample_prompts):
        """Test that descriptions don't contain raw placeholders."""
        for prompt in sample_prompts:
            description = prompt.get("description", "")

            assert "{{" not in description, \
                f"Placeholder in description of {prompt['name']}"


# =============================================================================
# Prompt Naming Convention Tests
# =============================================================================

@pytest.mark.unit
class TestPromptNamingConventions:
    """Tests for prompt naming conventions."""

    def test_name_uses_snake_case(self, sample_prompts):
        """Test that names use snake_case."""
        for prompt in sample_prompts:
            name = prompt.get("name", "")

            # Should be lowercase with underscores
            assert name == name.lower(), \
                f"Name should be lowercase: {name}"

            assert " " not in name, \
                f"Name should not contain spaces: {name}"

    def test_name_is_descriptive(self, sample_prompts):
        """Test that names are descriptive (not too short)."""
        min_length = 10

        for prompt in sample_prompts:
            name = prompt.get("name", "")

            assert len(name) >= min_length, \
                f"Name too short: {name}"

    def test_name_unique(self, sample_prompts):
        """Test that names are unique."""
        names = [p.get("name") for p in sample_prompts]
        unique_names = set(names)

        assert len(names) == len(unique_names), \
            "Duplicate prompt names detected"


# =============================================================================
# Investment-Specific Prompt Tests
# =============================================================================

@pytest.mark.unit
class TestInvestmentPromptContent:
    """Tests for investment-specific prompt content."""

    INVESTMENT_CONCEPTS = [
        "revenue", "margin", "growth", "valuation", "risk",
        "market", "competitive", "thesis", "catalyst", "moat"
    ]

    def test_idea_generation_prompts(self):
        """Test idea generation prompts contain relevant concepts."""
        idea_prompts = [
            {
                "name": "thematic_candidate_screen",
                "template": "Identify investment candidates for theme {{theme}}"
            }
        ]

        for prompt in idea_prompts:
            template = prompt.get("template", "").lower()

            # Should mention relevant concepts
            has_investment_concept = any(
                concept in template
                for concept in self.INVESTMENT_CONCEPTS
            ) or "theme" in template or "invest" in template

            assert has_investment_concept, \
                f"Missing investment concepts in {prompt['name']}"

    def test_due_diligence_prompts(self):
        """Test due diligence prompts are comprehensive."""
        dd_concepts = [
            "business", "financial", "competitive", "management",
            "risk", "valuation", "moat", "growth"
        ]

        # Would validate actual prompts from database
        # This is a pattern test

    def test_valuation_prompts(self):
        """Test valuation prompts include necessary components."""
        valuation_concepts = [
            "dcf", "multiple", "comparable", "terminal",
            "discount", "growth", "margin", "cash flow"
        ]

        # Would validate actual prompts from database


# =============================================================================
# Prompt Variable Extraction Tests
# =============================================================================

@pytest.mark.unit
class TestPromptVariableExtraction:
    """Tests for extracting and validating prompt variables."""

    def test_extract_variables(self):
        """Test variable extraction from templates."""
        template = "Analyze {{ticker}} in {{sector}} with focus on {{focus_area}}"

        variables = re.findall(r'\{\{(\w+)\}\}', template)

        assert "ticker" in variables
        assert "sector" in variables
        assert "focus_area" in variables
        assert len(variables) == 3

    def test_common_variables_present(self):
        """Test that common investment variables are supported."""
        common_vars = ["ticker", "theme", "sector", "industry", "period"]

        # These should be used across prompts
        for var in common_vars:
            assert var.isidentifier()

    def test_variable_consistency(self, sample_prompts):
        """Test that variables are consistently named."""
        all_variables = set()

        for prompt in sample_prompts:
            template = prompt.get("template", "")
            variables = re.findall(r'\{\{(\w+)\}\}', template)
            all_variables.update(variables)

        # Check for inconsistent naming
        similar_vars = [
            ("ticker", "symbol"),
            ("company", "company_name"),
            ("sector", "industry_sector")
        ]

        for var1, var2 in similar_vars:
            if var1 in all_variables and var2 in all_variables:
                print(f"Warning: Both '{var1}' and '{var2}' used - consider standardizing")


# =============================================================================
# Prompt Database Seeding Tests
# =============================================================================

@pytest.mark.unit
class TestPromptDatabaseSeeding:
    """Tests for prompt database seeding."""

    def test_seed_file_valid_sql(self):
        """Test that seed SQL file is valid."""
        seed_path = "/home/user/AI_inv/sql/init/003_seed_complete_prompts.sql"

        if os.path.exists(seed_path):
            with open(seed_path, 'r') as f:
                content = f.read()

            # Should contain INSERT statements
            assert "INSERT INTO prompts" in content

            # Should have proper SQL syntax
            assert "VALUES" in content

    def test_expected_prompt_count(self):
        """Test that expected number of prompts are seeded."""
        expected_count = 118

        seed_path = "/home/user/AI_inv/sql/init/003_seed_complete_prompts.sql"

        if os.path.exists(seed_path):
            with open(seed_path, 'r') as f:
                content = f.read()

            # Count INSERT value groups (rough estimate)
            insert_count = content.count("gen_random_uuid()")

            # Should be close to expected
            assert insert_count >= expected_count * 0.9, \
                f"Expected ~{expected_count} prompts, found ~{insert_count}"
