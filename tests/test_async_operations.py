"""
Unit tests for async AI operations
Tests async providers, cache, and helpers
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from providers.async_ai_provider import (
    AsyncAIProvider,
    AsyncOllamaProvider,
    AsyncGeminiProvider,
    AsyncWatsonXProvider,
    AsyncOpenAIProvider,
    AsyncAIProviderFactory
)
from utils.async_cache_manager import AsyncCacheManager
from utils.async_helpers import run_async, async_to_sync, AsyncBatchProcessor

# Test Async Cache Manager
class TestAsyncCacheManager:
    """Test async cache manager functionality"""
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """Test setting and getting cache values"""
        cache = AsyncCacheManager(use_redis=False)
        
        prompt = "Test prompt"
        provider = "Test Provider"
        model = "test-model"
        response = "Test response"
        
        # Set cache
        await cache.set(prompt, provider, model, response)
        
        # Get cache
        cached = await cache.get(prompt, provider, model)
        assert cached == response
    
    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """Test cache miss returns None"""
        cache = AsyncCacheManager(use_redis=False)
        
        cached = await cache.get("nonexistent", "provider", "model")
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache expiration"""
        cache = AsyncCacheManager(use_redis=False)
        
        # Set with very short TTL
        await cache.set("prompt", "provider", "model", "response", ttl=0)
        
        # Wait a bit
        await asyncio.sleep(0.1)
        
        # Should be expired
        cached = await cache.get("prompt", "provider", "model")
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_batch_operations(self):
        """Test batch get and set operations"""
        cache = AsyncCacheManager(use_redis=False)
        
        # Batch set
        items = [
            ("prompt1", "provider", "model", "response1", 3600),
            ("prompt2", "provider", "model", "response2", 3600),
            ("prompt3", "provider", "model", "response3", 3600)
        ]
        await cache.batch_set(items)
        
        # Batch get
        requests = [
            ("prompt1", "provider", "model"),
            ("prompt2", "provider", "model"),
            ("prompt3", "provider", "model")
        ]
        results = await cache.batch_get(requests)
        
        assert results[0] == "response1"
        assert results[1] == "response2"
        assert results[2] == "response3"
    
    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """Test clearing cache"""
        cache = AsyncCacheManager(use_redis=False)
        
        await cache.set("prompt", "provider", "model", "response")
        await cache.clear()
        
        cached = await cache.get("prompt", "provider", "model")
        assert cached is None

# Test Async Providers
class TestAsyncProviders:
    """Test async AI provider functionality"""
    
    def test_provider_factory(self):
        """Test provider factory creates correct instances"""
        config = {'api_key': 'test_key'}
        
        # Test Ollama
        provider = AsyncAIProviderFactory.create_provider("Local (Ollama)", "test-model", {})
        assert isinstance(provider, AsyncOllamaProvider)
        
        # Test Gemini
        provider = AsyncAIProviderFactory.create_provider("Google (Gemini)", "gemini-1.5-flash", config)
        assert isinstance(provider, AsyncGeminiProvider)
        
        # Test WatsonX
        config_wx = {'api_key': 'test_key', 'project_id': 'test_project'}
        provider = AsyncAIProviderFactory.create_provider("IBM watsonx", "test-model", config_wx)
        assert isinstance(provider, AsyncWatsonXProvider)
        
        # Test OpenAI
        provider = AsyncAIProviderFactory.create_provider("OpenAI (GPT-4)", "gpt-4o", config)
        assert isinstance(provider, AsyncOpenAIProvider)
    
    def test_invalid_provider(self):
        """Test factory raises error for invalid provider"""
        with pytest.raises(ValueError):
            AsyncAIProviderFactory.create_provider("Invalid Provider", "model", {})
    
    @pytest.mark.asyncio
    async def test_gemini_validation(self):
        """Test Gemini provider validation"""
        # Valid config
        provider = AsyncGeminiProvider("gemini-1.5-flash", {'api_key': 'test_key_12345'})
        assert await provider.validate_config() == True
        
        # Invalid config
        provider = AsyncGeminiProvider("gemini-1.5-flash", {'api_key': ''})
        assert await provider.validate_config() == False
    
    @pytest.mark.asyncio
    async def test_watsonx_validation(self):
        """Test WatsonX provider validation"""
        # Valid config
        config = {'api_key': 'test_key', 'project_id': 'test_project'}
        provider = AsyncWatsonXProvider("test-model", config)
        assert await provider.validate_config() == True
        
        # Invalid config
        provider = AsyncWatsonXProvider("test-model", {'api_key': ''})
        assert await provider.validate_config() == False
    
    @pytest.mark.asyncio
    async def test_openai_validation(self):
        """Test OpenAI provider validation"""
        # Valid config
        provider = AsyncOpenAIProvider("gpt-4o", {'api_key': 'test_key_12345'})
        assert await provider.validate_config() == True
        
        # Invalid config
        provider = AsyncOpenAIProvider("gpt-4o", {'api_key': ''})
        assert await provider.validate_config() == False

# Test Async Helpers
class TestAsyncHelpers:
    """Test async helper utilities"""
    
    def test_run_async(self):
        """Test run_async helper"""
        async def async_function():
            await asyncio.sleep(0.1)
            return "result"
        
        result = run_async(async_function())
        assert result == "result"
    
    def test_async_to_sync_decorator(self):
        """Test async_to_sync decorator"""
        @async_to_sync
        async def async_function(value):
            await asyncio.sleep(0.1)
            return value * 2
        
        result = async_function(5)
        assert result == 10
    
    @pytest.mark.asyncio
    async def test_batch_processor(self):
        """Test async batch processor"""
        processor = AsyncBatchProcessor(max_concurrent=2)
        
        async def process_item(item):
            await asyncio.sleep(0.1)
            return item * 2
        
        items = [1, 2, 3, 4, 5]
        results = await processor.process_batch(items, process_item)
        
        assert len(results) == 5
        assert all(isinstance(r, int) for r in results)
        assert results == [2, 4, 6, 8, 10]
    
    @pytest.mark.asyncio
    async def test_batch_processor_with_errors(self):
        """Test batch processor handles errors"""
        processor = AsyncBatchProcessor(max_concurrent=2)
        
        async def process_item(item):
            if item == 3:
                raise ValueError("Test error")
            return item * 2
        
        items = [1, 2, 3, 4, 5]
        results = await processor.process_batch(items, process_item)
        
        assert len(results) == 5
        assert isinstance(results[2], ValueError)  # Error at index 2

# Test Integration
class TestAsyncIntegration:
    """Test integration of async components"""
    
    @pytest.mark.asyncio
    async def test_provider_with_cache(self):
        """Test provider integration with cache"""
        cache = AsyncCacheManager(use_redis=False)
        
        # Mock provider
        class MockProvider(AsyncAIProvider):
            async def validate_config(self):
                return True
            
            async def generate(self, prompt, **kwargs):
                await asyncio.sleep(0.1)
                return f"Generated: {prompt}"
        
        provider = MockProvider("test-model", {})
        prompt = "Test prompt"
        
        # First call - cache miss
        response1 = await provider.generate(prompt)
        await cache.set(prompt, "Mock", "test-model", response1)
        
        # Second call - cache hit
        cached = await cache.get(prompt, "Mock", "test-model")
        
        assert response1 == cached
        assert cached == "Generated: Test prompt"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test concurrent request processing"""
        async def mock_request(delay):
            await asyncio.sleep(delay)
            return f"Result after {delay}s"
        
        # Process 3 requests concurrently
        tasks = [
            mock_request(0.1),
            mock_request(0.1),
            mock_request(0.1)
        ]
        
        import time
        start = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start
        
        # Should take ~0.1s (concurrent) not ~0.3s (sequential)
        assert duration < 0.2
        assert len(results) == 3

# Performance Tests
class TestAsyncPerformance:
    """Test async performance improvements"""
    
    @pytest.mark.asyncio
    async def test_concurrent_vs_sequential(self):
        """Compare concurrent vs sequential execution"""
        async def mock_task(duration):
            await asyncio.sleep(duration)
            return "done"
        
        # Sequential
        import time
        start = time.time()
        for _ in range(3):
            await mock_task(0.1)
        sequential_time = time.time() - start
        
        # Concurrent
        start = time.time()
        await asyncio.gather(*[mock_task(0.1) for _ in range(3)])
        concurrent_time = time.time() - start
        
        # Concurrent should be significantly faster
        assert concurrent_time < sequential_time
        assert concurrent_time < 0.2  # Should be ~0.1s
        assert sequential_time > 0.3  # Should be ~0.3s

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob