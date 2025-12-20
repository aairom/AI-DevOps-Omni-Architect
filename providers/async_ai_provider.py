"""
Async AI Provider abstraction layer
Supports asynchronous operations for all LLM providers
"""
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import aiohttp
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class AsyncAIProvider(ABC):
    """Abstract base class for async AI providers"""
    
    def __init__(self, model: str, config: Optional[Dict[str, Any]] = None):
        self.model = model
        self.config = config or {}
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt asynchronously"""
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate provider configuration asynchronously"""
        pass
    
    async def batch_generate(self, prompts: list[str], **kwargs) -> list[str]:
        """Generate responses for multiple prompts concurrently"""
        tasks = [self.generate(prompt, **kwargs) for prompt in prompts]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)

class AsyncOllamaProvider(AsyncAIProvider):
    """Async Local Ollama provider"""
    
    async def validate_config(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:11434/api/tags", timeout=aiohttp.ClientTimeout(total=2)) as response:
                    return response.status == 200
        except:
            return False
    
    async def generate(self, prompt: str, **kwargs) -> str:
        try:
            max_tokens = kwargs.get('max_tokens', 2000)
            temperature = kwargs.get('temperature', 0.7)
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '')
                    else:
                        raise Exception(f"Ollama API error: {response.status}")
        except Exception as e:
            logger.error(f"Async Ollama generation error: {e}")
            raise

class AsyncGeminiProvider(AsyncAIProvider):
    """Async Google Gemini provider"""
    
    def __init__(self, model: str, config: Dict[str, Any]):
        super().__init__(model, config)
        self.api_key = config.get('api_key', '')
    
    async def validate_config(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        try:
            # Use thread pool for CPU-bound operations
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self._executor,
                self._sync_generate,
                prompt,
                kwargs
            )
        except Exception as e:
            logger.error(f"Async Gemini generation error: {e}")
            raise
    
    def _sync_generate(self, prompt: str, kwargs: dict) -> str:
        """Synchronous generation wrapped for async"""
        import google.generativeai as genai
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text

class AsyncWatsonXProvider(AsyncAIProvider):
    """Async IBM watsonx provider"""
    
    def __init__(self, model: str, config: Dict[str, Any]):
        super().__init__(model, config)
        self.api_key = config.get('api_key', '')
        self.project_id = config.get('project_id', '')
        self._token_cache = None
        self._token_expiry = None
    
    async def validate_config(self) -> bool:
        return bool(self.api_key and self.project_id)
    
    async def _get_token(self) -> Optional[str]:
        """Get IBM Cloud IAM token asynchronously"""
        # Check cache
        if self._token_cache and self._token_expiry:
            import time
            if time.time() < self._token_expiry:
                return self._token_cache
        
        url = "https://iam.cloud.ibm.com/identity/token"
        data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={self.api_key}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        result = await response.json()
                        token = result.get("access_token")
                        # Cache token for 50 minutes (expires in 60)
                        import time
                        self._token_cache = token
                        self._token_expiry = time.time() + 3000
                        return token
                    else:
                        logger.error(f"Failed to get watsonx token: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Failed to get watsonx token: {e}")
            return None
    
    async def generate(self, prompt: str, **kwargs) -> str:
        try:
            token = await self._get_token()
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
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=body, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['results'][0]['generated_text']
                    else:
                        error_text = await response.text()
                        raise Exception(f"WatsonX API error: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Async WatsonX generation error: {e}")
            raise

class AsyncOpenAIProvider(AsyncAIProvider):
    """Async OpenAI GPT provider"""
    
    def __init__(self, model: str, config: Dict[str, Any]):
        super().__init__(model, config)
        self.api_key = config.get('api_key', '')
    
    async def validate_config(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        try:
            # Use thread pool for OpenAI SDK (not fully async)
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self._executor,
                self._sync_generate,
                prompt,
                kwargs
            )
        except Exception as e:
            logger.error(f"Async OpenAI generation error: {e}")
            raise
    
    def _sync_generate(self, prompt: str, kwargs: dict) -> str:
        """Synchronous generation wrapped for async"""
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

class AsyncAIProviderFactory:
    """Factory for creating async AI provider instances"""
    
    @staticmethod
    def create_provider(provider_name: str, model: str, config: Dict[str, Any]) -> AsyncAIProvider:
        """Create appropriate async provider instance"""
        providers = {
            "Local (Ollama)": AsyncOllamaProvider,
            "Google (Gemini)": AsyncGeminiProvider,
            "IBM watsonx": AsyncWatsonXProvider,
            "OpenAI (GPT-4)": AsyncOpenAIProvider
        }
        
        provider_class = providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        return provider_class(model, config)

# Made with Bob