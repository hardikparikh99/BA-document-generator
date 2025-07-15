"""
OpenAI primary service for the CrewAI Multi-Agent Project Documentation System.
This module provides the main LLM functionality with Ollama as fallback.
"""
import logging
import aiohttp
from typing import Dict, List, Optional, Any

from utils.config import get_settings
from .ollama_fallback import OllamaFallback

# Get settings
settings = get_settings()

# Set up logging
logger = logging.getLogger(__name__)

class OpenAIService:
    """
    Service for interacting with OpenAI LLM with Ollama fallback.
    """
    
    def __init__(self):
        """Initialize the OpenAI service."""
        self.api_key = settings.openai_api_key
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = settings.openai_model
        self.fallback_to_ollama = True
        self.ollama_fallback = OllamaFallback()
        
    async def _openai_request(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Make a request to OpenAI API.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            str: The LLM response
            
        Raises:
            Exception: If the API key is missing or the request fails
        """
        if not self.api_key:
            raise Exception("OpenAI API key is missing")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add user prompt
        messages.append({"role": "user", "content": prompt})
        
        # Determine max_tokens based on documentation level
        max_tokens = 2000  # Default
        if system_prompt:
            if "SIMPLE" in system_prompt.upper():
                max_tokens = 1500
            elif "ADVANCED" in system_prompt.upper():
                max_tokens = 6000
            elif "INTERMEDIATE" in system_prompt.upper():
                max_tokens = 3000
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": max_tokens
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {error_text}")
                        raise Exception(f"OpenAI API error: {response.status}")
                    
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error in OpenAI request: {str(e)}")
            raise
    
    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response using OpenAI with fallback to Ollama.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            str: The LLM response
        """
        try:
            # Try OpenAI first
            logger.info("Attempting to use OpenAI for response generation")
            response = await self._openai_request(prompt, system_prompt)
            logger.info("Successfully generated response with OpenAI")
            return response
        except Exception as e:
            logger.warning(f"OpenAI request failed: {str(e)}")
            
            if self.fallback_to_ollama:
                logger.info("Falling back to Ollama")
                try:
                    response = await self.ollama_fallback.generate_response(prompt, system_prompt)
                    logger.info("Successfully generated response with Ollama fallback")
                    return response
                except Exception as fallback_error:
                    logger.error(f"Ollama fallback also failed: {str(fallback_error)}")
                    raise fallback_error
            else:
                logger.error("No fallback available or fallback disabled")
                raise e
    
    async def check_availability(self) -> bool:
        """
        Check if OpenAI API is available.
        
        Returns:
            bool: True if the API is available, False otherwise
        """
        if not self.api_key:
            return False
            
        try:
            # Simple models endpoint to check availability
            url = "https://api.openai.com/v1/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    return response.status == 200
        except Exception:
            return False
