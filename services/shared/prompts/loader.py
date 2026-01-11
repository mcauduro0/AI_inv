# =============================================================================
# Prompt Loader Service
# =============================================================================
# Loads and manages prompt templates from the database
# =============================================================================

import re
from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)


class PromptLoader:
    """
    Loads prompt templates from the database and renders them with variables.
    """
    
    def __init__(self, prompt_repo):
        """Initialize with a PromptTemplateRepository instance."""
        self.prompt_repo = prompt_repo
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def get_prompt(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a prompt template by name.
        
        Returns dict with:
        - name: str
        - category: str
        - subcategory: str
        - description: str
        - template: str
        - variables: dict
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name]
        
        # Fetch from database
        prompt = await self.prompt_repo.get_by_name(name)
        
        if prompt:
            prompt_data = {
                "name": prompt.name,
                "category": prompt.category,
                "subcategory": prompt.subcategory,
                "description": prompt.description,
                "template": prompt.template,
                "variables": prompt.variables or {}
            }
            self._cache[name] = prompt_data
            return prompt_data
        
        return None
    
    async def get_prompts_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all prompts in a category."""
        prompts = await self.prompt_repo.get_by_category(category)
        return [
            {
                "name": p.name,
                "category": p.category,
                "subcategory": p.subcategory,
                "description": p.description,
                "template": p.template,
                "variables": p.variables or {}
            }
            for p in prompts
        ]
    
    async def render_prompt(
        self,
        name: str,
        variables: Dict[str, Any],
        additional_context: str = ""
    ) -> Optional[str]:
        """
        Render a prompt template with the given variables.
        
        Args:
            name: The prompt template name
            variables: Dict of variable values to substitute
            additional_context: Extra context to append to the prompt
        
        Returns:
            Rendered prompt string or None if template not found
        """
        prompt_data = await self.get_prompt(name)
        
        if not prompt_data:
            logger.warning(f"Prompt template not found: {name}")
            return None
        
        template = prompt_data["template"]
        
        # Replace {{variable}} placeholders with actual values
        for var_name, var_value in variables.items():
            placeholder = "{{" + var_name + "}}"
            
            # Convert complex types to string representation
            if isinstance(var_value, (dict, list)):
                import json
                var_value = json.dumps(var_value, indent=2)
            else:
                var_value = str(var_value)
            
            template = template.replace(placeholder, var_value)
        
        # Add additional context if provided
        if additional_context:
            template = f"{template}\n\n{additional_context}"
        
        return template
    
    async def list_all_prompts(self) -> List[Dict[str, str]]:
        """List all available prompts (name, category, description)."""
        prompts = await self.prompt_repo.get_all()
        return [
            {
                "name": p.name,
                "category": p.category,
                "description": p.description
            }
            for p in prompts
        ]
    
    def clear_cache(self):
        """Clear the prompt cache."""
        self._cache.clear()


def render_template(template: str, variables: Dict[str, Any]) -> str:
    """
    Render a template string with variables.
    
    This is a standalone function for use without database access.
    """
    import json
    
    for var_name, var_value in variables.items():
        placeholder = "{{" + var_name + "}}"
        
        if isinstance(var_value, (dict, list)):
            var_value = json.dumps(var_value, indent=2)
        else:
            var_value = str(var_value)
        
        template = template.replace(placeholder, var_value)
    
    return template
