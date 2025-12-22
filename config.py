"""
Configuration management for Omni-Architect
Handles environment variables, constants, and application settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List
import logging

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('omni_architect.log'),
        logging.StreamHandler()
    ]
)

class Config:
    """Application configuration"""
    
    # Application
    APP_NAME = "Omni-Architect"
    APP_VERSION = "v44.0"
    APP_ICON = "🛡️"
    
    # Async Configuration
    ASYNC_ENABLED = True
    MAX_CONCURRENT_REQUESTS = 3
    ASYNC_TIMEOUT = 120  # seconds
    BATCH_SIZE = 5
    
    # Directories
    BASE_DIR = Path.cwd()
    CACHE_DIR = BASE_DIR / ".cache"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Create directories if they don't exist
    CACHE_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Kubernetes Flavors
    K8S_FLAVORS: List[str] = [
        "Standard (Vanilla)",
        "Minikube (Local VM)",
        "Kind (Docker-in-Docker)",
        "Google (GKE)",
        "AWS (EKS)",
        "Azure (AKS)",
        "IBM (IKS)"
    ]
    
    # Terraform Providers
    TF_PROVIDERS: List[str] = [
        "AWS",
        "GCP",
        "IBM Cloud",
        "Azure",
        "Oracle Cloud"
    ]
    
    # Application file extensions
    APP_EXTS: set = {
        '.c', '.cpp', '.go', '.php', '.js', '.ts', 
        '.java', '.html', '.sh', '.py', '.rb', '.rs'
    }
    
    # AI Provider configurations
    AI_PROVIDERS: List[str] = [
        "Local (Ollama)",
        "IBM watsonx",
        "Google (Gemini)",
        "OpenAI (GPT-4)"
    ]
    
    # API Keys from environment
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    WATSONX_API_KEY: str = os.getenv("WATSONX_API_KEY", "")
    WATSONX_PROJECT_ID: str = os.getenv("WATSONX_PROJECT_ID", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Redis configuration for caching
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    CACHE_TTL: int = 3600  # 1 hour
    
    # Security settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_COMMANDS: List[str] = [
        "ls", "pwd", "cat", "echo", "git", "kubectl", 
        "docker", "terraform", "helm"
    ]
    
    # AI Model parameters
    DEFAULT_MAX_TOKENS: int = 2000
    DEFAULT_TEMPERATURE: float = 0.7
    
    @classmethod
    def get_api_key(cls, provider: str) -> str:
        """Get API key for a specific provider"""
        key_map = {
            "Google (Gemini)": cls.GEMINI_API_KEY,
            "IBM watsonx": cls.WATSONX_API_KEY,
            "OpenAI (GPT-4)": cls.OPENAI_API_KEY
        }
        return key_map.get(provider, "")
    
    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """Validate configuration and return status"""
        return {
            "gemini_configured": bool(cls.GEMINI_API_KEY),
            "watsonx_configured": bool(cls.WATSONX_API_KEY and cls.WATSONX_PROJECT_ID),
            "openai_configured": bool(cls.OPENAI_API_KEY),
            "cache_dir_exists": cls.CACHE_DIR.exists(),
            "logs_dir_exists": cls.LOGS_DIR.exists()
        }

# Create logger instance
logger = logging.getLogger(__name__)

# Made with Bob
