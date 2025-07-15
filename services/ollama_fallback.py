"""
Ollama fallback service for the CrewAI Multi-Agent Project Documentation System.
This module provides fallback functionality when OpenAI is unavailable.
"""
import logging
import aiohttp
from typing import Dict, List, Optional, Any

from utils.config import get_settings

# Get settings
settings = get_settings()

# Set up logging
logger = logging.getLogger(__name__)

class OllamaFallback:
    """
    Fallback service for Ollama when OpenAI is unavailable.
    """
    
    def __init__(self):
        """Initialize the Ollama fallback service."""
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        
    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response using Ollama API.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            str: The LLM response
            
        Raises:
            Exception: If the request fails
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.2,  # Lower temperature for more deterministic outputs
            "num_predict": 4096,  # Increase token limit for longer outputs
            "options": {
                "num_ctx": 8192  # Increase context window
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama API error: {error_text}")
                        raise Exception(f"Ollama API error: {response.status}")
                    
                    result = await response.json()
                    return result.get("response", "")
        except Exception as e:
            logger.error(f"Error in Ollama request: {str(e)}")
            raise
    
    async def check_availability(self) -> bool:
        """
        Check if Ollama is available.
        
        Returns:
            bool: True if Ollama is available, False otherwise
        """
        try:
            url = f"{self.base_url}/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def get_available_models(self) -> List[str]:
        """
        Get a list of available models from Ollama.
        
        Returns:
            List[str]: List of available model names
        """
        try:
            url = f"{self.base_url}/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return []
                    
                    result = await response.json()
                    models = [model.get("name") for model in result.get("models", [])]
                    return models
        except Exception as e:
            logger.error(f"Error getting available models: {str(e)}")
            return []
    
    async def is_model_available(self, model_name: Optional[str] = None) -> bool:
        """
        Check if a specific model is available.
        
        Args:
            model_name: Name of the model to check. If None, checks the default model.
            
        Returns:
            bool: True if the model is available, False otherwise
        """
        model_to_check = model_name or self.model
        available_models = await self.get_available_models()
        return model_to_check in available_models
