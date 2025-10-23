# app/config.py
import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

def load_config(env_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load environment variables from a .env file and return configuration dict.
    
    Args:
        env_path (str, optional): Path to .env file. If None, looks for .env in current directory.
        
    Returns:
        dict: Configuration dictionary with the following keys:
            - OLLAMA_BASE_URL: Base URL for Ollama API
            - DEFAULT_MODEL: Default model name to use
            - REQUEST_TIMEOUT: Request timeout in seconds
            - FLASK_ENV: Flask environment (development/production)
            - FLASK_DEBUG: Flask debug mode
            - FLASK_HOST: Flask host to bind to
            - FLASK_PORT: Flask port to bind to
    """
    try:
        # Load environment variables
        if env_path:
            if os.path.exists(env_path):
                load_dotenv(env_path)
                logger.info(f"Loaded environment from {env_path}")
            else:
                logger.warning(f"Environment file {env_path} not found, using default locations")
        else:
            # Try to load from default locations
            load_dotenv()
            logger.info("Loaded environment from default locations")
        
        # Build configuration dictionary
        cfg = {}
        
        # Ollama Configuration
        cfg["OLLAMA_BASE_URL"] = os.getenv(
            "OLLAMA_BASE_URL", 
            "http://localhost:11434"
        ).rstrip('/')  # Remove trailing slash
        
        # Model Configuration - support multiple environment variable names for compatibility
        cfg["DEFAULT_MODEL"] = os.getenv(
            "OLLAMA_MODEL", 
            os.getenv("OLLAMA_DEFAULT_MODEL", "deepseek-coder:6.7b")
        )
        
        # Request Timeout Configuration
        try:
            cfg["REQUEST_TIMEOUT"] = float(os.getenv(
                "OLLAMA_TIMEOUT", 
                os.getenv("OLLAMA_REQUEST_TIMEOUT", "120")
            ))
        except (ValueError, TypeError):
            logger.warning("Invalid timeout value, using default 120 seconds")
            cfg["REQUEST_TIMEOUT"] = 120.0
        
        # Flask Configuration
        cfg["FLASK_ENV"] = os.getenv("FLASK_ENV", "development")
        cfg["FLASK_DEBUG"] = os.getenv("FLASK_DEBUG", "true").lower() == "true"
        cfg["FLASK_HOST"] = os.getenv("FLASK_HOST", "0.0.0.0")
        
        try:
            cfg["FLASK_PORT"] = int(os.getenv("FLASK_PORT", "5000"))
        except (ValueError, TypeError):
            logger.warning("Invalid port value, using default 5000")
            cfg["FLASK_PORT"] = 5000
        
        # Logging Configuration
        cfg["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Optional: Model-specific configurations
        cfg["MAX_TOKENS"] = int(os.getenv("MAX_TOKENS", "4096"))
        cfg["DEFAULT_TEMPERATURE"] = float(os.getenv("DEFAULT_TEMPERATURE", "0.1"))
        cfg["DEFAULT_TOP_P"] = float(os.getenv("DEFAULT_TOP_P", "0.9"))
        
        # Security (if needed in future)
        cfg["API_KEY"] = os.getenv("API_KEY")  # Optional API key for authentication
        
        logger.info("Configuration loaded successfully")
        logger.debug(f"Configuration: { {k: v for k, v in cfg.items() if k != 'API_KEY'} }")
        
        return cfg
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        # Return safe defaults
        return get_default_config()

def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration as fallback.
    
    Returns:
        dict: Default configuration values
    """
    return {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "DEFAULT_MODEL": "deepseek-coder:6.7b",
        "REQUEST_TIMEOUT": 120.0,
        "FLASK_ENV": "development",
        "FLASK_DEBUG": True,
        "FLASK_HOST": "0.0.0.0",
        "FLASK_PORT": 5000,
        "LOG_LEVEL": "INFO",
        "MAX_TOKENS": 4096,
        "DEFAULT_TEMPERATURE": 0.1,
        "DEFAULT_TOP_P": 0.9,
        "API_KEY": None
    }

def validate_config(cfg: Dict[str, Any]) -> bool:
    """
    Validate configuration values.
    
    Args:
        cfg (dict): Configuration dictionary to validate
        
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    try:
        # Validate Ollama URL format
        url = cfg.get("OLLAMA_BASE_URL", "")
        if not url.startswith(('http://', 'https://')):
            logger.error("OLLAMA_BASE_URL must start with http:// or https://")
            return False
        
        # Validate timeout
        timeout = cfg.get("REQUEST_TIMEOUT", 0)
        if timeout <= 0:
            logger.error("REQUEST_TIMEOUT must be positive")
            return False
        
        # Validate port
        port = cfg.get("FLASK_PORT", 0)
        if not (1 <= port <= 65535):
            logger.error("FLASK_PORT must be between 1 and 65535")
            return False
        
        # Validate model name (basic check)
        model = cfg.get("DEFAULT_MODEL", "")
        if not model or not isinstance(model, str):
            logger.error("DEFAULT_MODEL must be a non-empty string")
            return False
        
        logger.info("Configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False

def get_config_summary(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a safe summary of configuration (excluding sensitive data).
    
    Args:
        cfg (dict): Full configuration dictionary
        
    Returns:
        dict: Safe configuration summary
    """
    return {
        "ollama_base_url": cfg.get("OLLAMA_BASE_URL"),
        "default_model": cfg.get("DEFAULT_MODEL"),
        "request_timeout": cfg.get("REQUEST_TIMEOUT"),
        "flask_env": cfg.get("FLASK_ENV"),
        "flask_debug": cfg.get("FLASK_DEBUG"),
        "flask_host": cfg.get("FLASK_HOST"),
        "flask_port": cfg.get("FLASK_PORT"),
        "max_tokens": cfg.get("MAX_TOKENS"),
        "default_temperature": cfg.get("DEFAULT_TEMPERATURE"),
        "default_top_p": cfg.get("DEFAULT_TOP_P")
    }

# Optional: Configuration class for more advanced usage
class Config:
    """Configuration class for type-safe access to settings"""
    
    def __init__(self, env_path: Optional[str] = None):
        self._config = load_config(env_path)
        if not validate_config(self._config):
            logger.warning("Configuration validation failed, using defaults")
            self._config = get_default_config()
    
    @property
    def ollama_base_url(self) -> str:
        return self._config["OLLAMA_BASE_URL"]
    
    @property
    def default_model(self) -> str:
        return self._config["DEFAULT_MODEL"]
    
    @property
    def request_timeout(self) -> float:
        return self._config["REQUEST_TIMEOUT"]
    
    @property
    def flask_env(self) -> str:
        return self._config["FLASK_ENV"]
    
    @property
    def flask_debug(self) -> bool:
        return self._config["FLASK_DEBUG"]
    
    @property
    def flask_host(self) -> str:
        return self._config["FLASK_HOST"]
    
    @property
    def flask_port(self) -> int:
        return self._config["FLASK_PORT"]
    
    @property
    def max_tokens(self) -> int:
        return self._config["MAX_TOKENS"]
    
    @property
    def default_temperature(self) -> float:
        return self._config["DEFAULT_TEMPERATURE"]
    
    @property
    def default_top_p(self) -> float:
        return self._config["DEFAULT_TOP_P"]
    
    @property
    def api_key(self) -> Optional[str]:
        return self._config.get("API_KEY")
    
    def get_summary(self) -> Dict[str, Any]:
        return get_config_summary(self._config)
    
    def __getitem__(self, key: str) -> Any:
        return self._config[key]
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)