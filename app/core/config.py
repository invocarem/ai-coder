"""
Flask-independent configuration module for both API and MCP server.
Provides configuration loading without any Flask dependencies.
"""
import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from dataclasses import dataclass, field

# Set up logging
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Configuration dataclass
# ----------------------------------------------------------------------
@dataclass
class Settings:
    """Typed configuration loaded from environment variables."""
    # Provider configuration
    AI_PROVIDER: str = field(default_factory=lambda: os.getenv("AI_PROVIDER", "ollama").strip().lower())
    OLLAMA_BASE_URL: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip('/'))
    LLAMACPP_BASE_URL: str = field(default_factory=lambda: os.getenv("LLAMACPP_BASE_URL", "http://localhost:8080").rstrip('/'))
    OPENAI_BASE_URL: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip('/'))
    OPENAI_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    MISTRAL_BASE_URL: str = field(default_factory=lambda: os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1").rstrip('/'))
    MISTRAL_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("MISTRAL_API_KEY"))

    # Model configuration
    DEFAULT_MODEL: str = field(init=False)

    # Request timeout
    REQUEST_TIMEOUT: float = field(default=120.0)

    # Logging configuration
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    VERBOSE: bool = field(default_factory=lambda: os.getenv("VERBOSE", "false").lower() == "true")
    SHOW_INFO: bool = field(default_factory=lambda: os.getenv("SHOW_INFO", "false").lower() == "true")
    STREAM_DEBUG_LOG: Optional[str] = field(default_factory=lambda: os.getenv("STREAM_DEBUG_LOG"))

    # JSON configuration
    JSON_AS_ASCII: bool = field(default_factory=lambda: os.getenv("JSON_AS_ASCII", "false").lower() == "true")
    JSONIFY_MIMETYPE: str = field(default_factory=lambda: os.getenv("JSONIFY_MIMETYPE", "application/json; charset=utf-8"))
    JSON_ENSURE_ASCII: bool = field(default_factory=lambda: os.getenv("JSON_ENSURE_ASCII", "false").lower() == "true")

    # Miscellaneous defaults
    MAX_TOKENS: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "4096")))
    DEFAULT_TEMPERATURE: float = field(default_factory=lambda: float(os.getenv("DEFAULT_TEMPERATURE", "0.1")))
    DEFAULT_TOP_P: float = field(default_factory=lambda: float(os.getenv("DEFAULT_TOP_P", "0.9")))
    API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("API_KEY"))
    CASSANDRA_HOSTS: str = field(default_factory=lambda: os.getenv("CASSANDRA_HOSTS", "127.0.0.1"))
    CASSANDRA_PORT: int = field(default_factory=lambda: int(os.getenv("CASSANDRA_PORT", "9042")))

    # Provider‑specific defaults (filled after init)
    def __post_init__(self):
        # Resolve default model based on provider
        provider_defaults = {
            "ollama": "deepseek-coder:6.7b",
            "openai": "gpt-4o-mini",
            "mistral": "mistral-small-latest",
            "llamacpp": "gpt-oss-120b",
            "llama.cpp": "gpt-oss-120b",
            "llama": "gpt-oss-120b",
        }
        # Environment variable priority list
        priority = ["DEFAULT_MODEL"]
        if self.AI_PROVIDER == "openai":
            priority.extend(["OPENAI_MODEL", "OPENAI_DEFAULT_MODEL"])
        elif self.AI_PROVIDER == "mistral":
            priority.extend(["MISTRAL_MODEL", "MISTRAL_DEFAULT_MODEL"])
        elif self.AI_PROVIDER in ("llamacpp", "llama.cpp", "llama"):
            priority.extend(["LLAMACPP_MODEL", "LLAMACPP_DEFAULT_MODEL"])
        else:
            priority.extend(["OLLAMA_MODEL", "OLLAMA_DEFAULT_MODEL"])

        for key in priority:
            val = os.getenv(key)
            if val:
                self.DEFAULT_MODEL = val
                break
        else:
            self.DEFAULT_MODEL = provider_defaults.get(self.AI_PROVIDER, "deepseek-coder:6.7b")

        # Resolve request timeout
        timeout_keys = {
            "ollama": ["OLLAMA_TIMEOUT", "OLLAMA_REQUEST_TIMEOUT"],
            "openai": ["OPENAI_TIMEOUT", "OPENAI_REQUEST_TIMEOUT"],
            "mistral": ["MISTRAL_TIMEOUT", "MISTRAL_REQUEST_TIMEOUT"],
            "llamacpp": ["LLAMACPP_TIMEOUT", "LLAMACPP_REQUEST_TIMEOUT", "LLAMA_CPP_TIMEOUT"],
            "llama.cpp": ["LLAMACPP_TIMEOUT", "LLAMACPP_REQUEST_TIMEOUT", "LLAMA_CPP_TIMEOUT"],
            "llama": ["LLAMACPP_TIMEOUT", "LLAMACPP_REQUEST_TIMEOUT", "LLAMA_CPP_TIMEOUT"],
        }.get(self.AI_PROVIDER, [])
        for key in timeout_keys:
            val = os.getenv(key)
            if val:
                try:
                    self.REQUEST_TIMEOUT = float(val)
                except ValueError:
                    pass
                break
        # Fallback to generic REQUEST_TIMEOUT
        if self.REQUEST_TIMEOUT == 120.0:
            generic = os.getenv("REQUEST_TIMEOUT")
            if generic:
                try:
                    self.REQUEST_TIMEOUT = float(generic)
                except ValueError:
                    pass

# ----------------------------------------------------------------------
# Logging helper
# ----------------------------------------------------------------------
def setup_logging(cfg: dict) -> None:
    """
    Configure root logging based on configuration dict.
    Handles console level, optional stream file handler and log format.
    """
    verbose = cfg.get("VERBOSE", False)
    show_info = cfg.get("SHOW_INFO", False)

    if verbose:
        level = logging.DEBUG
    elif show_info:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    stream_path = cfg.get("STREAM_DEBUG_LOG") or os.getenv("STREAM_DEBUG_LOG")
    if stream_path:
        logger = logging.getLogger("stream_debug")
        abs_path = os.path.abspath(stream_path)
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename == abs_path
                   for h in logger.handlers):
            fh = logging.FileHandler(abs_path, encoding="utf-8")
            fh.setLevel(logging.INFO)
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(fh)
        logger.setLevel(logging.INFO)
        logger.propagate = False

def load_config(env_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load environment variables from a .env file and return configuration dict.
    
    Args:
        env_path (str, optional): Path to .env file. If None, looks for .env in current directory.
        
    Returns:
        dict: Configuration dictionary with the following keys:
            - AI_PROVIDER: Selected AI provider (ollama, openai, mistral, llamacpp)
            - OLLAMA_BASE_URL: Base URL for Ollama API
            - LLAMACPP_BASE_URL: Base URL for llama.cpp server
            - OPENAI_BASE_URL: Base URL for OpenAI-compatible APIs
            - OPENAI_API_KEY: API key for OpenAI-compatible providers
            - MISTRAL_BASE_URL: Base URL for Mistral API
            - MISTRAL_API_KEY: API key for Mistral provider
            - DEFAULT_MODEL: Default model name to use
            - REQUEST_TIMEOUT: Request timeout in seconds
            - FLASK_ENV: Flask environment (development/production)
            - FLASK_DEBUG: Flask debug mode
            - FLASK_HOST: Flask host to bind to
            - FLASK_PORT: Flask port to bind to
            - VERBOSE: Enable verbose/debug logging (true/false)
            - SHOW_INFO: Enable info-level logging (true/false)
            - JSON_AS_ASCII: JSON encoding ASCII mode (true/false, deprecated)
            - JSONIFY_MIMETYPE: MIME type for JSON responses
            - JSON_ENSURE_ASCII: Ensure ASCII in JSON encoding (true/false)
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
        
        # Provider configuration
        provider = os.getenv("AI_PROVIDER", "ollama").strip().lower()
        cfg["AI_PROVIDER"] = provider if provider else "ollama"
        
        # Provider-specific base URLs and credentials
        cfg["OLLAMA_BASE_URL"] = os.getenv(
            "OLLAMA_BASE_URL", 
            "http://localhost:11434"
        ).rstrip('/')  # Remove trailing slash
        cfg["LLAMACPP_BASE_URL"] = os.getenv(
            "LLAMACPP_BASE_URL",
            "http://localhost:8080"
        ).rstrip('/')
        cfg["OPENAI_BASE_URL"] = os.getenv(
            "OPENAI_BASE_URL",
            "https://api.openai.com/v1"
        ).rstrip('/')
        cfg["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        cfg["MISTRAL_BASE_URL"] = os.getenv(
            "MISTRAL_BASE_URL",
            "https://api.mistral.ai/v1"
        ).rstrip('/')
        cfg["MISTRAL_API_KEY"] = os.getenv("MISTRAL_API_KEY")
        
        # Model Configuration - support multiple environment variable names for compatibility
        model_env_priority = ["DEFAULT_MODEL"]
        if provider == "openai":
            model_env_priority.extend(["OPENAI_MODEL", "OPENAI_DEFAULT_MODEL"])
        elif provider == "mistral":
            model_env_priority.extend(["MISTRAL_MODEL", "MISTRAL_DEFAULT_MODEL"])
        elif provider in ("llamacpp", "llama.cpp", "llama"):
            model_env_priority.extend(["LLAMACPP_MODEL", "LLAMACPP_DEFAULT_MODEL"])
        else:  # ollama or others defaulting to ollama behavior
            model_env_priority.extend(["OLLAMA_MODEL", "OLLAMA_DEFAULT_MODEL"])
        
        provider_default_models = {
            "ollama": "deepseek-coder:6.7b",
            "openai": "gpt-4o-mini",
            "mistral": "mistral-small-latest",
            "llamacpp": "gpt-oss-120b",
            "llama.cpp": "gpt-oss-120b",
            "llama": "gpt-oss-120b"
        }
        
        default_model = None
        for env_key in model_env_priority:
            value = os.getenv(env_key)
            if value:
                default_model = value
                break
        if not default_model:
            default_model = provider_default_models.get(provider, "deepseek-coder:6.7b")
        cfg["DEFAULT_MODEL"] = default_model
        
        # Request Timeout Configuration (provider-specific overrides)
        timeout_keys_by_provider = {
            "ollama": ["OLLAMA_TIMEOUT", "OLLAMA_REQUEST_TIMEOUT"],
            "openai": ["OPENAI_TIMEOUT", "OPENAI_REQUEST_TIMEOUT"],
            "mistral": ["MISTRAL_TIMEOUT", "MISTRAL_REQUEST_TIMEOUT"],
            "llamacpp": ["LLAMACPP_TIMEOUT", "LLAMACPP_REQUEST_TIMEOUT", "LLAMA_CPP_TIMEOUT"],
            "llama.cpp": ["LLAMACPP_TIMEOUT", "LLAMACPP_REQUEST_TIMEOUT", "LLAMA_CPP_TIMEOUT"],
            "llama": ["LLAMACPP_TIMEOUT", "LLAMACPP_REQUEST_TIMEOUT", "LLAMA_CPP_TIMEOUT"]
        }

        timeout_value = None
        timeout_keys = timeout_keys_by_provider.get(provider, [])
        for key in timeout_keys:
            value = os.getenv(key)
            if value:
                timeout_value = value
                break

        if timeout_value is None:
            timeout_value = os.getenv("REQUEST_TIMEOUT")
        if timeout_value is None:
            timeout_value = "120"

        try:
            cfg["REQUEST_TIMEOUT"] = float(timeout_value)
        except (ValueError, TypeError):
            logger.warning("Invalid timeout value (%s), using default 120 seconds", timeout_value)
            cfg["REQUEST_TIMEOUT"] = 120.0
        
        # Flask Configuration (for app/__init__.py only)
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
        cfg["VERBOSE"] = os.getenv("VERBOSE", "false").lower() == "true"
        cfg["SHOW_INFO"] = os.getenv("SHOW_INFO", "false").lower() == "true"
        
        # JSON Configuration
        cfg["JSON_AS_ASCII"] = os.getenv("JSON_AS_ASCII", "false").lower() == "true"
        cfg["JSONIFY_MIMETYPE"] = os.getenv("JSONIFY_MIMETYPE", "application/json; charset=utf-8")
        cfg["JSON_ENSURE_ASCII"] = os.getenv("JSON_ENSURE_ASCII", "false").lower() == "true"
        
        # Optional: Model-specific configurations
        cfg["MAX_TOKENS"] = int(os.getenv("MAX_TOKENS", "4096"))
        cfg["DEFAULT_TEMPERATURE"] = float(os.getenv("DEFAULT_TEMPERATURE", "0.1"))
        cfg["DEFAULT_TOP_P"] = float(os.getenv("DEFAULT_TOP_P", "0.9"))
        cfg["STREAM_DEBUG_LOG"] = os.getenv("STREAM_DEBUG_LOG")

        # Data store configuration
        cfg["CASSANDRA_HOSTS"] = os.getenv("CASSANDRA_HOSTS", "127.0.0.1")
        try:
            cfg["CASSANDRA_PORT"] = int(os.getenv("CASSANDRA_PORT", "9042"))
        except (ValueError, TypeError):
            logger.warning("Invalid CASSANDRA_PORT value, using default 9042")
            cfg["CASSANDRA_PORT"] = 9042
        
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
        "AI_PROVIDER": "ollama",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "LLAMACPP_BASE_URL": "http://localhost:8080",
        "OPENAI_BASE_URL": "https://api.openai.com/v1",
        "OPENAI_API_KEY": None,
        "MISTRAL_BASE_URL": "https://api.mistral.ai/v1",
        "MISTRAL_API_KEY": None,
        "DEFAULT_MODEL": "deepseek-coder:6.7b",
        "REQUEST_TIMEOUT": 120.0,
        "FLASK_ENV": "development",
        "FLASK_DEBUG": True,
        "FLASK_HOST": "0.0.0.0",
        "FLASK_PORT": 5000,
        "LOG_LEVEL": "INFO",
        "VERBOSE": False,
        "SHOW_INFO": False,
        "JSON_AS_ASCII": False,
        "JSONIFY_MIMETYPE": "application/json; charset=utf-8",
        "JSON_ENSURE_ASCII": False,
        "MAX_TOKENS": 4096,
        "DEFAULT_TEMPERATURE": 0.1,
        "DEFAULT_TOP_P": 0.9,
        "API_KEY": None,
        "CASSANDRA_HOSTS": "127.0.0.1",
        "CASSANDRA_PORT": 9042
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
        # Validate provider-specific configuration
        provider = str(cfg.get("AI_PROVIDER", "ollama")).strip().lower()
        
        if provider == "ollama":
            url = cfg.get("OLLAMA_BASE_URL", "")
            if not url.startswith(('http://', 'https://')):
                logger.error("OLLAMA_BASE_URL must start with http:// or https://")
                return False
        elif provider in ("llamacpp", "llama.cpp", "llama"):
            url = cfg.get("LLAMACPP_BASE_URL", "")
            if not url or not url.startswith(('http://', 'https://')):
                logger.error("LLAMACPP_BASE_URL must start with http:// or https://")
                return False
        elif provider == "openai":
            url = cfg.get("OPENAI_BASE_URL", "")
            if not url.startswith(('http://', 'https://')):
                logger.error("OPENAI_BASE_URL must start with http:// or https://")
                return False
            if not cfg.get("OPENAI_API_KEY"):
                logger.error("OPENAI_API_KEY is required when AI_PROVIDER is 'openai'")
                return False
        elif provider == "mistral":
            url = cfg.get("MISTRAL_BASE_URL", "")
            if not url.startswith(('http://', 'https://')):
                logger.error("MISTRAL_BASE_URL must start with http:// or https://")
                return False
            if not cfg.get("MISTRAL_API_KEY"):
                logger.error("MISTRAL_API_KEY is required when AI_PROVIDER is 'mistral'")
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
        "ai_provider": cfg.get("AI_PROVIDER"),
        "ollama_base_url": cfg.get("OLLAMA_BASE_URL"),
        "llamacpp_base_url": cfg.get("LLAMACPP_BASE_URL"),
        "openai_base_url": cfg.get("OPENAI_BASE_URL"),
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
    def llama_cpp_base_url(self) -> str:
        return self._config["LLAMACPP_BASE_URL"]
    
    @property
    def ai_provider(self) -> str:
        return self._config["AI_PROVIDER"]
    
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
