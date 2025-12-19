"""
AI Provider abstraction layer
Supports multiple LLM providers with unified interface
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import requests
import ollama

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, model: str, config: Optional[Dict[str, Any]] = None):
        self.model = model
        self.config = config or {}
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate provider configuration"""
        pass

class OllamaProvider(AIProvider):
    """Local Ollama provider"""
    
    def validate_config(self) -> bool:
        try:
            ollama.list()
            return True
        except:
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        try:
            max_tokens = kwargs.get('max_tokens', 2000)
            temperature = kwargs.get('temperature', 0.7)
            
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'num_predict': max_tokens,
                    'temperature': temperature
                }
            )
            return response['response']
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise

class GeminiProvider(AIProvider):
    """Google Gemini provider"""
    
    def __init__(self, model: str, config: Dict[str, Any]):
        super().__init__(model, config)
        self.api_key = config.get('api_key', '')
    
    def validate_config(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)
    
    def generate(self, prompt: str, **kwargs) -> str:
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise

class WatsonXProvider(AIProvider):
    """IBM watsonx provider"""
    
    def __init__(self, model: str, config: Dict[str, Any]):
        super().__init__(model, config)
        self.api_key = config.get('api_key', '')
        self.project_id = config.get('project_id', '')
    
    def validate_config(self) -> bool:
        return bool(self.api_key and self.project_id)
    
    def _get_token(self) -> Optional[str]:
        """Get IBM Cloud IAM token"""
        url = "https://iam.cloud.ibm.com/identity/token"
        data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={self.api_key}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        try:
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            return response.json().get("access_token")
        except Exception as e:
            logger.error(f"Failed to get watsonx token: {e}")
            return None
    
    def generate(self, prompt: str, **kwargs) -> str:
        try:
            token = self._get_token()
            if not token:
                raise ValueError("Failed to obtain authentication token")
            
            url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            max_tokens = kwargs.get('max_tokens', 2000)
            temperature = kwargs.get('temperature', 0.7)
            
            body = {
                "input": f"<s>[INST] {prompt} [/INST]",
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature
                },
                "project_id": self.project_id
            }
            
            response = requests.post(url, headers=headers, json=body, timeout=60)
            response.raise_for_status()
            
            return response.json()['results'][0]['generated_text']
        except Exception as e:
            logger.error(f"WatsonX generation error: {e}")
            raise

class OpenAIProvider(AIProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, model: str, config: Dict[str, Any]):
        super().__init__(model, config)
        self.api_key = config.get('api_key', '')
    
    def validate_config(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)
    
    def generate(self, prompt: str, **kwargs) -> str:
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            max_tokens = kwargs.get('max_tokens', 2000)
            temperature = kwargs.get('temperature', 0.7)
            
            response = client.chat.completions.create(
                model=self.model or "gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert DevOps architect."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise

class AIProviderFactory:
    """Factory for creating AI provider instances"""
    
    @staticmethod
    def create_provider(provider_name: str, model: str, config: Dict[str, Any]) -> AIProvider:
        """Create appropriate provider instance"""
        providers = {
            "Local (Ollama)": OllamaProvider,
            "Google (Gemini)": GeminiProvider,
            "IBM watsonx": WatsonXProvider,
            "OpenAI (GPT-4)": OpenAIProvider
        }
        
        provider_class = providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        return provider_class(model, config)

# Made with Bob
