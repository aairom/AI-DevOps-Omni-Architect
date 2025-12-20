"""
Multi-Model Ensemble Provider
Combines multiple AI models for improved accuracy and reliability
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from collections import Counter
import json

from .async_ai_provider import AsyncAIProvider, AsyncAIProviderFactory

logger = logging.getLogger(__name__)

class EnsembleStrategy:
    """Base class for ensemble strategies"""
    
    @staticmethod
    def combine(responses: List[str], weights: Optional[List[float]] = None) -> str:
        """Combine multiple responses into one"""
        raise NotImplementedError

class VotingStrategy(EnsembleStrategy):
    """Majority voting strategy"""
    
    @staticmethod
    def combine(responses: List[str], weights: Optional[List[float]] = None) -> str:
        """Return most common response"""
        if not responses:
            return ""
        
        # Simple majority vote
        counter = Counter(responses)
        most_common = counter.most_common(1)[0][0]
        return most_common

class WeightedAverageStrategy(EnsembleStrategy):
    """Weighted average strategy for numeric responses"""
    
    @staticmethod
    def combine(responses: List[str], weights: Optional[List[float]] = None) -> str:
        """Combine responses with weights"""
        if not responses:
            return ""
        
        if weights is None:
            weights = [1.0 / len(responses)] * len(responses)
        
        # For text responses, use weighted voting
        response_weights = {}
        for response, weight in zip(responses, weights):
            response_weights[response] = response_weights.get(response, 0) + weight
        
        # Return response with highest weight
        best_response = max(response_weights.items(), key=lambda x: x[1])[0]
        return best_response

class ConsensusStrategy(EnsembleStrategy):
    """Consensus strategy - requires agreement"""
    
    @staticmethod
    def combine(responses: List[str], weights: Optional[List[float]] = None) -> str:
        """Return response only if there's consensus"""
        if not responses:
            return ""
        
        # Check if all responses are similar (simple check)
        unique_responses = set(responses)
        
        if len(unique_responses) == 1:
            return responses[0]
        
        # If no consensus, return the longest response (most detailed)
        return max(responses, key=len)

class BestOfNStrategy(EnsembleStrategy):
    """Best of N strategy - select best response based on criteria"""
    
    @staticmethod
    def combine(responses: List[str], weights: Optional[List[float]] = None) -> str:
        """Select best response based on length and quality indicators"""
        if not responses:
            return ""
        
        # Score responses based on multiple criteria
        scores = []
        for response in responses:
            score = 0
            # Longer responses often more detailed
            score += len(response) * 0.3
            # Responses with code blocks
            score += response.count("```") * 100
            # Responses with file markers
            score += response.count("---FILE:") * 200
            # Responses with structure
            score += response.count("\n") * 2
            
            scores.append(score)
        
        # Return response with highest score
        best_idx = scores.index(max(scores))
        return responses[best_idx]

class EnsembleProvider:
    """
    Multi-model ensemble provider
    Combines multiple AI models for improved results
    """
    
    def __init__(
        self,
        providers: List[Dict[str, Any]],
        strategy: str = "best_of_n",
        weights: Optional[List[float]] = None
    ):
        """
        Initialize ensemble provider
        
        Args:
            providers: List of provider configs [{"name": "...", "model": "...", "config": {...}}]
            strategy: Ensemble strategy ("voting", "weighted", "consensus", "best_of_n")
            weights: Optional weights for each provider
        """
        self.provider_configs = providers
        self.providers: List[AsyncAIProvider] = []
        self.weights = weights
        
        # Initialize strategy
        strategies = {
            "voting": VotingStrategy,
            "weighted": WeightedAverageStrategy,
            "consensus": ConsensusStrategy,
            "best_of_n": BestOfNStrategy
        }
        
        self.strategy = strategies.get(strategy, BestOfNStrategy)()
        
        # Create provider instances
        for provider_config in providers:
            try:
                provider = AsyncAIProviderFactory.create_provider(
                    provider_config["name"],
                    provider_config["model"],
                    provider_config.get("config", {})
                )
                self.providers.append(provider)
                logger.info(f"Added provider to ensemble: {provider_config['name']}")
            except Exception as e:
                logger.error(f"Failed to create provider {provider_config['name']}: {e}")
    
    async def validate_config(self) -> bool:
        """Validate all providers"""
        if not self.providers:
            return False
        
        validations = await asyncio.gather(
            *[provider.validate_config() for provider in self.providers],
            return_exceptions=True
        )
        
        # At least one provider must be valid
        return any(v is True for v in validations)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate response using ensemble of models
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
        
        Returns:
            Combined response from ensemble
        """
        if not self.providers:
            raise ValueError("No providers available in ensemble")
        
        # Generate responses from all providers concurrently
        tasks = [
            provider.generate(prompt, **kwargs)
            for provider in self.providers
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_responses = [
            r for r in responses
            if isinstance(r, str) and r and not r.startswith("❌")
        ]
        
        if not valid_responses:
            # All providers failed
            error_msgs = [str(r) for r in responses if isinstance(r, Exception)]
            return f"❌ All ensemble providers failed: {'; '.join(error_msgs[:3])}"
        
        # Log ensemble results
        logger.info(f"Ensemble generated {len(valid_responses)}/{len(self.providers)} valid responses")
        
        # Combine responses using strategy
        combined = self.strategy.combine(valid_responses, self.weights)
        
        return combined
    
    async def generate_with_metadata(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate response with metadata about ensemble
        
        Returns:
            Dict with 'response', 'individual_responses', 'strategy', 'providers_used'
        """
        if not self.providers:
            raise ValueError("No providers available in ensemble")
        
        # Generate responses from all providers concurrently
        tasks = [
            provider.generate(prompt, **kwargs)
            for provider in self.providers
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Separate valid and error responses
        individual_responses = []
        for i, response in enumerate(responses):
            provider_name = self.provider_configs[i]["name"]
            if isinstance(response, str) and response and not response.startswith("❌"):
                individual_responses.append({
                    "provider": provider_name,
                    "response": response,
                    "status": "success"
                })
            else:
                individual_responses.append({
                    "provider": provider_name,
                    "response": str(response),
                    "status": "error"
                })
        
        # Get valid responses
        valid_responses = [
            r["response"] for r in individual_responses
            if r["status"] == "success"
        ]
        
        if not valid_responses:
            return {
                "response": "❌ All ensemble providers failed",
                "individual_responses": individual_responses,
                "strategy": self.strategy.__class__.__name__,
                "providers_used": 0,
                "total_providers": len(self.providers)
            }
        
        # Combine responses
        combined = self.strategy.combine(valid_responses, self.weights)
        
        return {
            "response": combined,
            "individual_responses": individual_responses,
            "strategy": self.strategy.__class__.__name__,
            "providers_used": len(valid_responses),
            "total_providers": len(self.providers)
        }
    
    def get_provider_info(self) -> List[Dict[str, str]]:
        """Get information about ensemble providers"""
        return [
            {
                "name": config["name"],
                "model": config["model"],
                "status": "active" if i < len(self.providers) else "failed"
            }
            for i, config in enumerate(self.provider_configs)
        ]

# Predefined ensemble configurations
ENSEMBLE_PRESETS = {
    "balanced": {
        "providers": [
            {"name": "OpenAI (GPT-4)", "model": "gpt-4o"},
            {"name": "Google (Gemini)", "model": "gemini-1.5-flash"},
            {"name": "IBM watsonx", "model": "meta-llama/llama-3-70b-instruct"}
        ],
        "strategy": "best_of_n",
        "description": "Balanced ensemble with major providers"
    },
    "fast": {
        "providers": [
            {"name": "Google (Gemini)", "model": "gemini-1.5-flash"},
            {"name": "Local (Ollama)", "model": "llama2"}
        ],
        "strategy": "best_of_n",
        "description": "Fast ensemble with quick models"
    },
    "quality": {
        "providers": [
            {"name": "OpenAI (GPT-4)", "model": "gpt-4o"},
            {"name": "OpenAI (GPT-4)", "model": "gpt-4-turbo"},
            {"name": "Google (Gemini)", "model": "gemini-1.5-flash"}
        ],
        "strategy": "consensus",
        "description": "High-quality ensemble with consensus"
    },
    "diverse": {
        "providers": [
            {"name": "OpenAI (GPT-4)", "model": "gpt-4o"},
            {"name": "Google (Gemini)", "model": "gemini-1.5-flash"},
            {"name": "IBM watsonx", "model": "meta-llama/llama-3-70b-instruct"},
            {"name": "Local (Ollama)", "model": "llama2"}
        ],
        "strategy": "voting",
        "description": "Diverse ensemble with voting"
    }
}

def create_ensemble_from_preset(
    preset: str,
    api_keys: Dict[str, str]
) -> EnsembleProvider:
    """
    Create ensemble from preset configuration
    
    Args:
        preset: Preset name ("balanced", "fast", "quality", "diverse")
        api_keys: Dict of API keys for providers
    
    Returns:
        Configured EnsembleProvider
    """
    if preset not in ENSEMBLE_PRESETS:
        raise ValueError(f"Unknown preset: {preset}")
    
    config = ENSEMBLE_PRESETS[preset]
    
    # Add API keys to provider configs
    providers = []
    for provider_config in config["providers"]:
        provider_with_keys = provider_config.copy()
        
        # Add appropriate API key
        if "OpenAI" in provider_config["name"]:
            provider_with_keys["config"] = {"api_key": api_keys.get("openai", "")}
        elif "Gemini" in provider_config["name"]:
            provider_with_keys["config"] = {"api_key": api_keys.get("gemini", "")}
        elif "watsonx" in provider_config["name"]:
            provider_with_keys["config"] = {
                "api_key": api_keys.get("watsonx_api", ""),
                "project_id": api_keys.get("watsonx_project", "")
            }
        else:
            provider_with_keys["config"] = {}
        
        providers.append(provider_with_keys)
    
    return EnsembleProvider(
        providers=providers,
        strategy=config["strategy"]
    )

# Made with Bob