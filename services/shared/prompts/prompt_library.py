"""
Prompt Library Service
Manages loading, caching, and retrieval of prompts from the database.
"""
import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncpg
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class PromptCategory(str, Enum):
    """Prompt categories matching the database schema."""
    IDEA_GENERATION = "idea_generation"
    DUE_DILIGENCE = "due_diligence"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    MACRO = "macro"
    ALTERNATIVE_DATA = "alternative_data"
    BUSINESS_UNDERSTANDING = "business_understanding"
    RISK_IDENTIFICATION = "risk_identification"
    REPORT_GENERATION = "report_generation"
    OTHER = "other"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"
    GEMINI = "gemini"


@dataclass
class Prompt:
    """Represents a prompt from the library."""
    id: str
    name: str
    category: PromptCategory
    subcategory: str
    description: str
    system_prompt: str
    user_prompt_template: str
    output_format: str
    required_data_sources: List[str]
    llm_provider: LLMProvider
    model: str
    temperature: float
    max_tokens: int
    tags: List[str]
    version: str
    is_active: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def render(self, **kwargs) -> str:
        """Render the user prompt template with provided variables."""
        template = self.user_prompt_template
        for key, value in kwargs.items():
            placeholder = "{{" + key + "}}"
            template = template.replace(placeholder, str(value))
        return template
    
    def get_full_prompt(self, **kwargs) -> Dict[str, str]:
        """Get the complete prompt with system and user messages."""
        return {
            "system": self.system_prompt,
            "user": self.render(**kwargs)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert prompt to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "subcategory": self.subcategory,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "output_format": self.output_format,
            "required_data_sources": self.required_data_sources,
            "llm_provider": self.llm_provider.value,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tags": self.tags,
            "version": self.version,
            "is_active": self.is_active,
            "metadata": self.metadata
        }


class PromptLibrary:
    """
    Manages the prompt library with database persistence and caching.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self._pool: Optional[asyncpg.Pool] = None
        self._cache: Dict[str, Prompt] = {}
        self._category_index: Dict[PromptCategory, List[str]] = {}
        self._tag_index: Dict[str, List[str]] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize the prompt library and load prompts."""
        if self._initialized:
            return
        
        try:
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10
            )
            await self._load_prompts()
            self._initialized = True
            logger.info(f"Prompt library initialized with {len(self._cache)} prompts")
        except Exception as e:
            logger.error(f"Failed to initialize prompt library: {e}")
            # Fall back to loading from file
            await self._load_prompts_from_file()
            self._initialized = True
    
    async def _load_prompts(self):
        """Load all active prompts from the database."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name, category, subcategory, description,
                       system_prompt, user_prompt_template, output_format,
                       required_data_sources, llm_provider, model,
                       temperature, max_tokens, tags, version, is_active,
                       metadata
                FROM prompts
                WHERE is_active = true
                ORDER BY category, name
            """)
            
            for row in rows:
                prompt = Prompt(
                    id=row['id'],
                    name=row['name'],
                    category=PromptCategory(row['category']),
                    subcategory=row['subcategory'],
                    description=row['description'],
                    system_prompt=row['system_prompt'],
                    user_prompt_template=row['user_prompt_template'],
                    output_format=row['output_format'],
                    required_data_sources=row['required_data_sources'],
                    llm_provider=LLMProvider(row['llm_provider']),
                    model=row['model'],
                    temperature=row['temperature'],
                    max_tokens=row['max_tokens'],
                    tags=row['tags'],
                    version=row['version'],
                    is_active=row['is_active'],
                    metadata=row['metadata'] or {}
                )
                self._cache[prompt.id] = prompt
                self._index_prompt(prompt)
    
    async def _load_prompts_from_file(self):
        """Fallback: Load prompts from JSON file."""
        prompts_file = os.path.join(
            os.path.dirname(__file__),
            "prompts_library.json"
        )
        
        if os.path.exists(prompts_file):
            with open(prompts_file, 'r') as f:
                prompts_data = json.load(f)
                
            for data in prompts_data:
                prompt = Prompt(
                    id=data['id'],
                    name=data['name'],
                    category=PromptCategory(data['category']),
                    subcategory=data['subcategory'],
                    description=data['description'],
                    system_prompt=data['system_prompt'],
                    user_prompt_template=data['user_prompt_template'],
                    output_format=data['output_format'],
                    required_data_sources=data['required_data_sources'],
                    llm_provider=LLMProvider(data['llm_provider']),
                    model=data['model'],
                    temperature=data['temperature'],
                    max_tokens=data['max_tokens'],
                    tags=data['tags'],
                    version=data['version'],
                    is_active=data['is_active'],
                    metadata=data.get('metadata', {})
                )
                self._cache[prompt.id] = prompt
                self._index_prompt(prompt)
            
            logger.info(f"Loaded {len(self._cache)} prompts from file")
    
    def _index_prompt(self, prompt: Prompt):
        """Index a prompt for fast retrieval."""
        # Category index
        if prompt.category not in self._category_index:
            self._category_index[prompt.category] = []
        self._category_index[prompt.category].append(prompt.id)
        
        # Tag index
        for tag in prompt.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            self._tag_index[tag].append(prompt.id)
    
    def get(self, prompt_id: str) -> Optional[Prompt]:
        """Get a prompt by ID."""
        return self._cache.get(prompt_id)
    
    def get_by_name(self, name: str) -> Optional[Prompt]:
        """Get a prompt by name."""
        for prompt in self._cache.values():
            if prompt.name.lower() == name.lower():
                return prompt
        return None
    
    def get_by_category(self, category: PromptCategory) -> List[Prompt]:
        """Get all prompts in a category."""
        prompt_ids = self._category_index.get(category, [])
        return [self._cache[pid] for pid in prompt_ids]
    
    def get_by_tag(self, tag: str) -> List[Prompt]:
        """Get all prompts with a specific tag."""
        prompt_ids = self._tag_index.get(tag, [])
        return [self._cache[pid] for pid in prompt_ids]
    
    def get_by_subcategory(self, category: PromptCategory, subcategory: str) -> List[Prompt]:
        """Get prompts by category and subcategory."""
        return [
            p for p in self.get_by_category(category)
            if p.subcategory == subcategory
        ]
    
    def search(self, query: str) -> List[Prompt]:
        """Search prompts by name, description, or tags."""
        query = query.lower()
        results = []
        
        for prompt in self._cache.values():
            if (query in prompt.name.lower() or
                query in prompt.description.lower() or
                any(query in tag.lower() for tag in prompt.tags)):
                results.append(prompt)
        
        return results
    
    def get_all(self) -> List[Prompt]:
        """Get all prompts."""
        return list(self._cache.values())
    
    def get_categories(self) -> List[PromptCategory]:
        """Get all available categories."""
        return list(self._category_index.keys())
    
    def get_tags(self) -> List[str]:
        """Get all available tags."""
        return list(self._tag_index.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
        return {
            "total_prompts": len(self._cache),
            "categories": {
                cat.value: len(ids) 
                for cat, ids in self._category_index.items()
            },
            "total_tags": len(self._tag_index),
            "providers": self._count_by_provider()
        }
    
    def _count_by_provider(self) -> Dict[str, int]:
        """Count prompts by LLM provider."""
        counts = {}
        for prompt in self._cache.values():
            provider = prompt.llm_provider.value
            counts[provider] = counts.get(provider, 0) + 1
        return counts
    
    async def close(self):
        """Close database connections."""
        if self._pool:
            await self._pool.close()


# Global prompt library instance
_prompt_library: Optional[PromptLibrary] = None


async def get_prompt_library() -> PromptLibrary:
    """Get or create the global prompt library instance."""
    global _prompt_library
    
    if _prompt_library is None:
        _prompt_library = PromptLibrary()
        await _prompt_library.initialize()
    
    return _prompt_library


# Agent-specific prompt mappings
AGENT_PROMPT_MAPPINGS = {
    "idea_generation_agent": [
        "ig-001", "ig-002", "ig-003", "ig-004", "ig-005",
        "ig-006", "ig-007", "ig-008", "ig-009", "ig-010",
        "ig-011", "ig-012", "ig-013", "ig-014", "ig-015",
        "ig-016", "ig-017", "ig-018", "ig-019", "ig-020"
    ],
    "due_diligence_agent": [
        "dd-001", "dd-002", "dd-003", "dd-004", "dd-005",
        "dd-006", "dd-007", "dd-008", "dd-009", "dd-010",
        "bus-001", "bus-002", "bus-003"
    ],
    "portfolio_management_agent": [
        "pm-001", "pm-002", "pm-003"
    ],
    "macro_agent": [
        "mac-001", "mac-002", "mac-003"
    ],
    "risk_agent": [
        "risk-001", "risk-002", "dd-005"
    ],
    "report_generation_agent": [
        "rpt-001", "rpt-002"
    ],
    "alternative_data_agent": [
        "alt-001", "alt-002"
    ]
}


def get_agent_prompts(agent_name: str) -> List[str]:
    """Get the list of prompt IDs assigned to an agent."""
    return AGENT_PROMPT_MAPPINGS.get(agent_name, [])
