"""
Logging configuration for the CrewAI Multi-Agent Project Documentation System.
This module sets up a consistent logging format across the application.
"""
import os
import logging
import sys
from datetime import datetime
from .config import get_settings

def setup_logger(name=None):
    """
    Set up and configure a logger.
    
    Args:
        name: Optional name for the logger. If None, returns the root logger.
        
    Returns:
        logging.Logger: Configured logger instance
    """
    settings = get_settings()
    
    # Get logger
    logger = logging.getLogger(name)
    
    # Skip if logger is already configured
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create file handler
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add formatter to handlers
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Propagate to root logger
    logger.propagate = False
    
    return logger

def get_agent_logger(agent_name):
    """
    Get a logger specifically for an agent.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        logging.Logger: Logger for the agent
    """
    return setup_logger(f"agent.{agent_name}")
