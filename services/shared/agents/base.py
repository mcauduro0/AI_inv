# =============================================================================
# Base Agent Class
# =============================================================================
# Abstract base class for all specialized investment agents
# =============================================================================

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, TypeVar
from enum import Enum

import structlog
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from shared.config.settings import settings
from shared.llm.provider import LLMProvider, get_llm_provider
from shared.clients.redis_client import RedisClient, get_redis_client
from shared.db.repository import Repository

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class TaskStatus(str, Enum):
    """Status of an agent task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Priority levels for tasks."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AgentTask(BaseModel):
    """Represents a task assigned to an agent."""
    
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: str
    prompt_name: str
    input_data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class AgentResult(BaseModel):
    """Result from an agent task execution."""
    
    task_id: str
    agent_type: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_seconds: float
    tokens_used: int = 0
    model_used: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BaseAgent(ABC):
    """
    Abstract base class for all investment agents.
    
    Provides common functionality for:
    - LLM interaction with fallback support
    - Task management and status tracking
    - Knowledge base integration
    - Structured output parsing
    - Error handling and retries
    """
    
    def __init__(
        self,
        agent_type: str,
        llm_provider: Optional[LLMProvider] = None,
        redis_client: Optional[RedisClient] = None,
        repository: Optional[Repository] = None,
    ):
        self.agent_type = agent_type
        self.llm = llm_provider or get_llm_provider()
        self.redis = redis_client or get_redis_client()
        self.repository = repository
        self.logger = structlog.get_logger(agent_type)
        self._prompts: Dict[str, str] = {}
        
    # =========================================================================
    # Abstract Methods (must be implemented by subclasses)
    # =========================================================================
    
    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResult:
        """
        Execute the main task logic.
        
        Args:
            task: The task to execute
            
        Returns:
            AgentResult with the execution outcome
        """
        pass
    
    @abstractmethod
    def get_supported_prompts(self) -> List[str]:
        """Return list of prompt names this agent supports."""
        pass
    
    # =========================================================================
    # Core Methods
    # =========================================================================
    
    async def run(self, task: AgentTask) -> AgentResult:
        """
        Main entry point for running a task with full lifecycle management.
        
        Handles:
        - Status updates
        - Timing
        - Error handling
        - Result persistence
        """
        start_time = datetime.now(timezone.utc)
        task.status = TaskStatus.RUNNING
        task.started_at = start_time
        
        self.logger.info(
            "Starting task execution",
            task_id=task.task_id,
            prompt_name=task.prompt_name
        )
        
        try:
            # Publish status update
            await self._publish_status(task)
            
            # Execute the task
            result = await self.execute(task)
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            task.result = result.data
            
            self.logger.info(
                "Task completed successfully",
                task_id=task.task_id,
                execution_time=result.execution_time_seconds
            )
            
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now(timezone.utc)
            task.error = str(e)
            
            self.logger.error(
                "Task execution failed",
                task_id=task.task_id,
                error=str(e),
                exc_info=True
            )
            
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=False,
                error=str(e),
                execution_time_seconds=(
                    datetime.now(timezone.utc) - start_time
                ).total_seconds()
            )
        finally:
            # Always publish final status
            await self._publish_status(task)
    
    # =========================================================================
    # LLM Interaction Methods
    # =========================================================================
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Type[T]] = None,
    ) -> tuple[str, int]:
        """
        Call the LLM with automatic fallback support.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            model: Specific model to use (defaults to provider default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            response_format: Optional Pydantic model for structured output
            
        Returns:
            Tuple of (response_text, tokens_used)
        """
        try:
            response, tokens = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format
            )
            return response, tokens
            
        except Exception as e:
            self.logger.warning(
                "Primary LLM failed, attempting fallback",
                error=str(e)
            )
            # Fallback to secondary provider
            fallback_llm = get_llm_provider(provider=settings.llm.fallback_provider)
            response, tokens = await fallback_llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response, tokens
    
    async def call_llm_structured(
        self,
        prompt: str,
        output_schema: Type[T],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
    ) -> T:
        """
        Call LLM and parse response into a structured Pydantic model.
        
        Args:
            prompt: The user prompt
            output_schema: Pydantic model class for the expected output
            system_prompt: Optional system prompt
            model: Specific model to use
            temperature: Lower temperature for more deterministic output
            
        Returns:
            Parsed Pydantic model instance
        """
        # Add schema instructions to prompt
        schema_json = output_schema.model_json_schema()
        enhanced_prompt = f"""{prompt}

Please respond with a valid JSON object that matches this schema:
```json
{json.dumps(schema_json, indent=2)}
```

Respond ONLY with the JSON object, no additional text."""

        response, _ = await self.call_llm(
            prompt=enhanced_prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature
        )
        
        # Parse and validate response
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            
            data = json.loads(json_str.strip())
            return output_schema.model_validate(data)
            
        except Exception as e:
            self.logger.error(
                "Failed to parse structured response",
                error=str(e),
                response=response[:500]
            )
            raise ValueError(f"Failed to parse LLM response: {e}")
    
    # =========================================================================
    # Prompt Management
    # =========================================================================
    
    def load_prompt(self, prompt_name: str) -> str:
        """
        Load a prompt template by name.
        
        Args:
            prompt_name: Name of the prompt to load
            
        Returns:
            The prompt template string
        """
        if prompt_name in self._prompts:
            return self._prompts[prompt_name]
        
        # Load from prompts directory
        import os
        prompt_path = os.path.join(
            settings.agent.prompts_directory,
            self.agent_type,
            f"{prompt_name}.md"
        )
        
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")
        
        with open(prompt_path, "r") as f:
            prompt = f.read()
        
        self._prompts[prompt_name] = prompt
        return prompt
    
    def render_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Load and render a prompt template with variables.
        
        Args:
            prompt_name: Name of the prompt to load
            **kwargs: Variables to substitute in the template
            
        Returns:
            Rendered prompt string
        """
        template = self.load_prompt(prompt_name)
        
        # Simple variable substitution using {variable_name} syntax
        for key, value in kwargs.items():
            template = template.replace(f"{{{key}}}", str(value))
        
        return template
    
    # =========================================================================
    # Knowledge Base Integration
    # =========================================================================
    
    async def search_knowledge_base(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the vector knowledge base for relevant context.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of relevant documents with scores
        """
        # This would integrate with Pinecone or similar
        # Placeholder implementation
        self.logger.debug(
            "Searching knowledge base",
            query=query[:100],
            top_k=top_k
        )
        return []
    
    async def store_in_knowledge_base(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Store content in the vector knowledge base.
        
        Args:
            content: Text content to store
            metadata: Associated metadata
            
        Returns:
            ID of the stored document
        """
        # This would integrate with Pinecone or similar
        # Placeholder implementation
        doc_id = str(uuid.uuid4())
        self.logger.debug(
            "Storing in knowledge base",
            doc_id=doc_id,
            content_length=len(content)
        )
        return doc_id
    
    # =========================================================================
    # Communication Methods
    # =========================================================================
    
    async def _publish_status(self, task: AgentTask) -> None:
        """Publish task status update to Redis."""
        channel = f"{settings.redis.channel_prefix}:status:{self.agent_type}"
        await self.redis.publish(channel, task.model_dump_json())
    
    async def request_sub_task(
        self,
        target_agent: str,
        prompt_name: str,
        input_data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """
        Request another agent to perform a sub-task.
        
        Args:
            target_agent: Type of agent to handle the task
            prompt_name: Name of the prompt to execute
            input_data: Input data for the task
            priority: Task priority
            
        Returns:
            Task ID of the created sub-task
        """
        task = AgentTask(
            agent_type=target_agent,
            prompt_name=prompt_name,
            input_data=input_data,
            priority=priority
        )
        
        channel = f"{settings.redis.channel_prefix}:tasks:{target_agent}"
        await self.redis.publish(channel, task.model_dump_json())
        
        self.logger.info(
            "Requested sub-task",
            task_id=task.task_id,
            target_agent=target_agent,
            prompt_name=prompt_name
        )
        
        return task.task_id
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def validate_input(
        self,
        input_data: Dict[str, Any],
        required_fields: List[str]
    ) -> None:
        """
        Validate that required fields are present in input data.
        
        Args:
            input_data: The input data to validate
            required_fields: List of required field names
            
        Raises:
            ValueError: If required fields are missing
        """
        missing = [f for f in required_fields if f not in input_data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
