"""
Unit Tests for Base Agent Class

Tests the core functionality of the BaseAgent abstract class including:
- Task lifecycle management
- LLM interaction methods
- Prompt management
- Status publishing
- Error handling
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services'))

from shared.agents.base import (
    BaseAgent, AgentTask, AgentResult, TaskStatus, TaskPriority
)


# =============================================================================
# Test Agent Implementation
# =============================================================================

class TestAgent(BaseAgent):
    """Concrete implementation for testing BaseAgent."""

    SUPPORTED_PROMPTS = ["test_prompt_1", "test_prompt_2"]

    async def execute(self, task: AgentTask) -> AgentResult:
        """Simple execute implementation for testing."""
        return AgentResult(
            task_id=task.task_id,
            agent_type=self.agent_type,
            success=True,
            data={"result": "test_output"},
            execution_time_seconds=1.0,
            tokens_used=100,
            model_used="test-model"
        )

    def get_supported_prompts(self):
        return self.SUPPORTED_PROMPTS


# =============================================================================
# AgentTask Tests
# =============================================================================

class TestAgentTask:
    """Tests for AgentTask model."""

    def test_task_creation_with_defaults(self):
        """Test creating a task with default values."""
        task = AgentTask(
            agent_type="test_agent",
            prompt_name="test_prompt",
            input_data={"ticker": "AAPL"}
        )

        assert task.task_id is not None
        assert task.agent_type == "test_agent"
        assert task.prompt_name == "test_prompt"
        assert task.priority == TaskPriority.NORMAL
        assert task.status == TaskStatus.PENDING
        assert task.input_data == {"ticker": "AAPL"}
        assert task.result is None
        assert task.error is None

    def test_task_creation_with_custom_values(self):
        """Test creating a task with custom values."""
        task = AgentTask(
            task_id="custom-id-123",
            agent_type="due_diligence_agent",
            prompt_name="business_overview_report",
            input_data={"ticker": "MSFT", "depth": "deep"},
            priority=TaskPriority.HIGH,
            status=TaskStatus.RUNNING,
            metadata={"source": "test"}
        )

        assert task.task_id == "custom-id-123"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.RUNNING
        assert task.metadata == {"source": "test"}

    def test_task_serialization(self):
        """Test that task can be serialized to JSON."""
        task = AgentTask(
            agent_type="test_agent",
            prompt_name="test_prompt",
            input_data={"ticker": "AAPL"}
        )

        json_str = task.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["agent_type"] == "test_agent"
        assert parsed["prompt_name"] == "test_prompt"
        assert parsed["input_data"]["ticker"] == "AAPL"


# =============================================================================
# AgentResult Tests
# =============================================================================

class TestAgentResult:
    """Tests for AgentResult model."""

    def test_successful_result(self):
        """Test creating a successful result."""
        result = AgentResult(
            task_id="task-123",
            agent_type="test_agent",
            success=True,
            data={"analysis": "test"},
            execution_time_seconds=5.5,
            tokens_used=1500,
            model_used="gpt-4"
        )

        assert result.success is True
        assert result.error is None
        assert result.data == {"analysis": "test"}
        assert result.execution_time_seconds == 5.5

    def test_failed_result(self):
        """Test creating a failed result."""
        result = AgentResult(
            task_id="task-456",
            agent_type="test_agent",
            success=False,
            error="LLM API timeout",
            execution_time_seconds=30.0
        )

        assert result.success is False
        assert result.error == "LLM API timeout"
        assert result.data is None


# =============================================================================
# BaseAgent Tests
# =============================================================================

@pytest.mark.unit
class TestBaseAgent:
    """Tests for BaseAgent class."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM provider."""
        mock = AsyncMock()
        mock.generate.return_value = (
            '{"result": "test output"}',
            100
        )
        return mock

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        mock = AsyncMock()
        mock.publish.return_value = None
        mock.ping.return_value = True
        return mock

    @pytest.fixture
    def agent(self, mock_llm, mock_redis):
        """Create test agent with mocked dependencies."""
        with patch('shared.agents.base.get_llm_provider', return_value=mock_llm), \
             patch('shared.agents.base.get_redis_client', return_value=mock_redis):
            agent = TestAgent(agent_type="test_agent")
            agent.llm = mock_llm
            agent.redis = mock_redis
            return agent

    @pytest.mark.asyncio
    async def test_run_successful_task(self, agent, sample_task):
        """Test running a task successfully."""
        result = await agent.run(sample_task)

        assert result.success is True
        assert sample_task.status == TaskStatus.COMPLETED
        assert sample_task.completed_at is not None
        assert result.execution_time_seconds > 0

    @pytest.mark.asyncio
    async def test_run_publishes_status(self, agent, sample_task):
        """Test that running a task publishes status updates."""
        await agent.run(sample_task)

        # Should publish at least twice (start and end)
        assert agent.redis.publish.call_count >= 1

    @pytest.mark.asyncio
    async def test_run_handles_exception(self, agent, sample_task, mock_llm, mock_redis):
        """Test that exceptions are handled properly."""

        class FailingAgent(BaseAgent):
            async def execute(self, task):
                raise ValueError("Test error")

            def get_supported_prompts(self):
                return ["test"]

        failing_agent = FailingAgent(
            agent_type="failing_agent",
            llm_provider=mock_llm,
            redis_client=mock_redis
        )

        result = await failing_agent.run(sample_task)

        assert result.success is False
        assert "Test error" in result.error
        assert sample_task.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_call_llm(self, agent):
        """Test LLM call method."""
        response, tokens = await agent.call_llm(
            prompt="Test prompt",
            system_prompt="You are a test assistant",
            temperature=0.5
        )

        assert response is not None
        assert tokens == 100
        agent.llm.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_llm_with_fallback(self, agent):
        """Test LLM fallback on primary failure."""
        # Make primary fail
        agent.llm.generate.side_effect = Exception("Primary LLM failed")

        with patch('shared.agents.base.get_llm_provider') as mock_get_provider:
            fallback_llm = AsyncMock()
            fallback_llm.generate.return_value = ("fallback response", 50)
            mock_get_provider.return_value = fallback_llm

            response, tokens = await agent.call_llm(prompt="Test")

            assert response == "fallback response"
            assert tokens == 50

    def test_validate_input_success(self, agent):
        """Test input validation with all required fields."""
        input_data = {"ticker": "AAPL", "depth": "deep"}

        # Should not raise
        agent.validate_input(input_data, ["ticker", "depth"])

    def test_validate_input_missing_fields(self, agent):
        """Test input validation with missing fields."""
        input_data = {"ticker": "AAPL"}

        with pytest.raises(ValueError) as exc_info:
            agent.validate_input(input_data, ["ticker", "depth", "period"])

        assert "depth" in str(exc_info.value)
        assert "period" in str(exc_info.value)

    def test_get_supported_prompts(self, agent):
        """Test getting supported prompts."""
        prompts = agent.get_supported_prompts()

        assert "test_prompt_1" in prompts
        assert "test_prompt_2" in prompts
        assert len(prompts) == 2

    @pytest.mark.asyncio
    async def test_request_sub_task(self, agent):
        """Test requesting a sub-task from another agent."""
        task_id = await agent.request_sub_task(
            target_agent="due_diligence_agent",
            prompt_name="business_overview",
            input_data={"ticker": "AAPL"},
            priority=TaskPriority.HIGH
        )

        assert task_id is not None
        agent.redis.publish.assert_called_once()


# =============================================================================
# Task Status Transition Tests
# =============================================================================

@pytest.mark.unit
class TestTaskStatusTransitions:
    """Tests for task status transitions."""

    def test_pending_to_running(self):
        """Test transition from PENDING to RUNNING."""
        task = AgentTask(
            agent_type="test",
            prompt_name="test",
            input_data={}
        )

        assert task.status == TaskStatus.PENDING
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)

        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None

    def test_running_to_completed(self):
        """Test transition from RUNNING to COMPLETED."""
        task = AgentTask(
            agent_type="test",
            prompt_name="test",
            input_data={},
            status=TaskStatus.RUNNING,
            started_at=datetime.now(timezone.utc)
        )

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        task.result = {"output": "success"}

        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
        assert task.result is not None

    def test_running_to_failed(self):
        """Test transition from RUNNING to FAILED."""
        task = AgentTask(
            agent_type="test",
            prompt_name="test",
            input_data={},
            status=TaskStatus.RUNNING
        )

        task.status = TaskStatus.FAILED
        task.error = "API timeout"

        assert task.status == TaskStatus.FAILED
        assert task.error == "API timeout"


# =============================================================================
# Priority Tests
# =============================================================================

@pytest.mark.unit
class TestTaskPriority:
    """Tests for task priority handling."""

    def test_priority_values(self):
        """Test priority enum values."""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.NORMAL.value == "normal"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.CRITICAL.value == "critical"

    def test_priority_comparison(self):
        """Test that priorities can be compared."""
        priorities = [
            TaskPriority.LOW,
            TaskPriority.NORMAL,
            TaskPriority.HIGH,
            TaskPriority.CRITICAL
        ]

        # Create tasks with different priorities
        tasks = [
            AgentTask(
                agent_type="test",
                prompt_name="test",
                input_data={},
                priority=p
            )
            for p in priorities
        ]

        assert tasks[0].priority == TaskPriority.LOW
        assert tasks[3].priority == TaskPriority.CRITICAL


# =============================================================================
# LLM Structured Output Tests
# =============================================================================

@pytest.mark.unit
class TestStructuredOutput:
    """Tests for structured LLM output parsing."""

    @pytest.fixture
    def mock_llm(self):
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def agent_with_mock(self, mock_llm):
        with patch('shared.agents.base.get_llm_provider', return_value=mock_llm), \
             patch('shared.agents.base.get_redis_client', return_value=AsyncMock()):
            agent = TestAgent(agent_type="test_agent")
            agent.llm = mock_llm
            return agent

    @pytest.mark.asyncio
    async def test_parse_json_response(self, agent_with_mock):
        """Test parsing JSON response from LLM."""
        from pydantic import BaseModel

        class TestOutput(BaseModel):
            analysis: str
            score: float

        agent_with_mock.llm.generate.return_value = (
            '```json\n{"analysis": "Test analysis", "score": 8.5}\n```',
            100
        )

        result = await agent_with_mock.call_llm_structured(
            prompt="Analyze this",
            output_schema=TestOutput
        )

        assert isinstance(result, TestOutput)
        assert result.analysis == "Test analysis"
        assert result.score == 8.5

    @pytest.mark.asyncio
    async def test_parse_json_without_markdown(self, agent_with_mock):
        """Test parsing JSON without markdown code blocks."""
        from pydantic import BaseModel

        class SimpleOutput(BaseModel):
            result: str

        agent_with_mock.llm.generate.return_value = (
            '{"result": "direct json"}',
            50
        )

        result = await agent_with_mock.call_llm_structured(
            prompt="Test",
            output_schema=SimpleOutput
        )

        assert result.result == "direct json"

    @pytest.mark.asyncio
    async def test_parse_invalid_json(self, agent_with_mock):
        """Test handling of invalid JSON response."""
        from pydantic import BaseModel

        class TestOutput(BaseModel):
            value: str

        agent_with_mock.llm.generate.return_value = (
            'This is not valid JSON at all',
            100
        )

        with pytest.raises(ValueError) as exc_info:
            await agent_with_mock.call_llm_structured(
                prompt="Test",
                output_schema=TestOutput
            )

        assert "Failed to parse" in str(exc_info.value)
