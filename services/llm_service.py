"""
LLM Service module for the CrewAI Multi-Agent Project Documentation System.
This module provides a unified interface for LLM services with OpenAI as primary and Ollama as fallback.
"""
import logging
from typing import Optional

from utils.config import get_settings
from services.openai_service import OpenAIService
from services.ollama_fallback import OllamaFallback

# Get settings
settings = get_settings()

# Set up logging
logger = logging.getLogger(__name__)

class LLMService:
    """
    Unified LLM service that uses OpenAI as primary and Ollama as fallback.
    """
    
    def __init__(self):
        """Initialize the LLM service."""
        self.openai_service = OpenAIService()
        self.ollama_fallback = OllamaFallback()
        
    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response using the LLM service.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            str: The LLM response
        """
        return await self.openai_service.generate_response(prompt, system_prompt)
    
    async def generate_content(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Alias for generate_response to maintain compatibility with existing code.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            str: The LLM response
        """
        return await self.generate_response(prompt, system_prompt)
    
    async def check_availability(self) -> bool:
        """
        Check if the LLM service is available.
        
        Returns:
            bool: True if the service is available, False otherwise
        """
        return await self.openai_service.check_availability()
