#!/usr/bin/env python3
"""
Multi-LLM Provider Abstraction for LLMdiver
Supports OpenAI, Anthropic, LM Studio, Ollama, etc.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import requests
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class AnalysisTask:
    task_type: str
    content: str
    context: Dict
    priority: int = 1
    max_tokens: int = 4096
    temperature: float = 0.3

@dataclass
class ProviderResponse:
    content: str
    provider: str
    model: str
    tokens_used: int
    cost_estimate: float
    latency: float
    success: bool
    error: Optional[str] = None

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = self.__class__.__name__.replace('Provider', '').lower()
        
    @abstractmethod
    async def analyze(self, task: AnalysisTask) -> ProviderResponse:
        """Perform analysis using this provider"""
        pass
    
    @abstractmethod
    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for given token count"""
        pass
    
    @abstractmethod
    def get_max_tokens(self) -> int:
        """Get maximum token limit for this provider"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is currently available"""
        pass

class LMStudioProvider(LLMProvider):
    """LM Studio local provider (existing functionality)"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.url = config.get("url", "http://127.0.0.1:1234/v1/chat/completions")
        self.model = config.get("model", "meta-llama-3.1-8b-instruct")
        
    async def analyze(self, task: AnalysisTask) -> ProviderResponse:
        start_time = time.time()
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a principal software architect conducting code analysis."},
                {"role": "user", "content": task.content}
            ],
            "temperature": task.temperature,
            "max_tokens": task.max_tokens,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=payload, timeout=300) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        tokens_used = result.get("usage", {}).get("total_tokens", len(content) // 4)
                        
                        return ProviderResponse(
                            content=content,
                            provider=self.name,
                            model=self.model,
                            tokens_used=tokens_used,
                            cost_estimate=0.0,  # Local model, no cost
                            latency=time.time() - start_time,
                            success=True
                        )
                    else:
                        error_msg = f"LM Studio error: {response.status}"
                        return ProviderResponse(
                            content="",
                            provider=self.name,
                            model=self.model,
                            tokens_used=0,
                            cost_estimate=0.0,
                            latency=time.time() - start_time,
                            success=False,
                            error=error_msg
                        )
        except Exception as e:
            return ProviderResponse(
                content="",
                provider=self.name,
                model=self.model,
                tokens_used=0,
                cost_estimate=0.0,
                latency=time.time() - start_time,
                success=False,
                error=str(e)
            )
    
    def estimate_cost(self, tokens: int) -> float:
        return 0.0  # Local model, no cost
    
    def get_max_tokens(self) -> int:
        return self.config.get("max_tokens", 32768)
    
    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.url.replace('/chat/completions', '/models')}", timeout=5)
            return response.status_code == 200
        except:
            return False

class OpenAIProvider(LLMProvider):
    """OpenAI API provider"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.model = config.get("model", "gpt-4")
        self.url = "https://api.openai.com/v1/chat/completions"
        
        # Pricing per 1K tokens (as of 2024)
        self.pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
        }
    
    async def analyze(self, task: AnalysisTask) -> ProviderResponse:
        if not self.api_key:
            return ProviderResponse(
                content="", provider=self.name, model=self.model,
                tokens_used=0, cost_estimate=0.0, latency=0.0,
                success=False, error="No API key provided"
            )
        
        start_time = time.time()
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a principal software architect conducting code analysis."},
                {"role": "user", "content": task.content}
            ],
            "temperature": task.temperature,
            "max_tokens": task.max_tokens
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=payload, headers=headers, timeout=300) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        usage = result.get("usage", {})
                        tokens_used = usage.get("total_tokens", len(content) // 4)
                        
                        return ProviderResponse(
                            content=content,
                            provider=self.name,
                            model=self.model,
                            tokens_used=tokens_used,
                            cost_estimate=self.estimate_cost(tokens_used),
                            latency=time.time() - start_time,
                            success=True
                        )
                    else:
                        error_data = await response.json()
                        error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status}")
                        return ProviderResponse(
                            content="", provider=self.name, model=self.model,
                            tokens_used=0, cost_estimate=0.0, latency=time.time() - start_time,
                            success=False, error=error_msg
                        )
        except Exception as e:
            return ProviderResponse(
                content="", provider=self.name, model=self.model,
                tokens_used=0, cost_estimate=0.0, latency=time.time() - start_time,
                success=False, error=str(e)
            )
    
    def estimate_cost(self, tokens: int) -> float:
        pricing = self.pricing.get(self.model, self.pricing["gpt-4"])
        # Assume 75% input, 25% output tokens
        input_tokens = int(tokens * 0.75)
        output_tokens = int(tokens * 0.25)
        
        cost = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
        return round(cost, 6)
    
    def get_max_tokens(self) -> int:
        max_tokens_map = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 16385
        }
        return max_tokens_map.get(self.model, 8192)
    
    def is_available(self) -> bool:
        return bool(self.api_key)

class OllamaProvider(LLMProvider):
    """Ollama local provider"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.url = config.get("url", "http://localhost:11434/api/generate")
        self.model = config.get("model", "llama2")
    
    async def analyze(self, task: AnalysisTask) -> ProviderResponse:
        start_time = time.time()
        
        payload = {
            "model": self.model,
            "prompt": task.content,
            "stream": False,
            "options": {
                "temperature": task.temperature,
                "num_predict": task.max_tokens
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=payload, timeout=300) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get("response", "")
                        tokens_used = len(content) // 4  # Rough estimate
                        
                        return ProviderResponse(
                            content=content,
                            provider=self.name,
                            model=self.model,
                            tokens_used=tokens_used,
                            cost_estimate=0.0,  # Local model, no cost
                            latency=time.time() - start_time,
                            success=True
                        )
                    else:
                        return ProviderResponse(
                            content="", provider=self.name, model=self.model,
                            tokens_used=0, cost_estimate=0.0, latency=time.time() - start_time,
                            success=False, error=f"Ollama error: {response.status}"
                        )
        except Exception as e:
            return ProviderResponse(
                content="", provider=self.name, model=self.model,
                tokens_used=0, cost_estimate=0.0, latency=time.time() - start_time,
                success=False, error=str(e)
            )
    
    def estimate_cost(self, tokens: int) -> float:
        return 0.0  # Local model, no cost
    
    def get_max_tokens(self) -> int:
        return self.config.get("max_tokens", 4096)
    
    def is_available(self) -> bool:
        try:
            # Check if Ollama is running
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

class ProviderOrchestrator:
    """Intelligent routing and fallback for multiple LLM providers"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.providers = {}
        self.fallback_chain = []
        self.cost_budget = config.get("cost_budget", 10.0)  # $10 daily budget
        self.daily_spend = 0.0
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured providers"""
        provider_configs = self.config.get("providers", {})
        
        if "lmstudio" in provider_configs:
            self.providers["lmstudio"] = LMStudioProvider(provider_configs["lmstudio"])
        
        if "openai" in provider_configs:
            self.providers["openai"] = OpenAIProvider(provider_configs["openai"])
        
        if "ollama" in provider_configs:
            self.providers["ollama"] = OllamaProvider(provider_configs["ollama"])
        
        # Set fallback chain preference
        self.fallback_chain = self.config.get("fallback_chain", ["lmstudio", "ollama", "openai"])
        
        logger.info(f"Initialized {len(self.providers)} LLM providers: {list(self.providers.keys())}")
    
    async def route_request(self, task: AnalysisTask) -> ProviderResponse:
        """Route request to optimal provider with fallback"""
        
        # Determine optimal provider based on task
        optimal_provider = self._select_optimal_provider(task)
        
        # Try optimal provider first
        if optimal_provider in self.providers:
            response = await self._try_provider(optimal_provider, task)
            if response.success:
                self.daily_spend += response.cost_estimate
                return response
        
        # Try fallback chain
        for provider_name in self.fallback_chain:
            if provider_name == optimal_provider:
                continue  # Already tried
            
            if provider_name in self.providers:
                logger.info(f"Falling back to provider: {provider_name}")
                response = await self._try_provider(provider_name, task)
                if response.success:
                    self.daily_spend += response.cost_estimate
                    return response
        
        # All providers failed
        return ProviderResponse(
            content="", provider="none", model="none",
            tokens_used=0, cost_estimate=0.0, latency=0.0,
            success=False, error="All providers failed"
        )
    
    def _select_optimal_provider(self, task: AnalysisTask) -> str:
        """Select optimal provider based on task characteristics"""
        
        # For security analysis, prefer more capable models
        if task.task_type == "security":
            if "openai" in self.providers and self.daily_spend < self.cost_budget * 0.8:
                return "openai"
        
        # For large tasks, prefer local models to avoid costs
        if len(task.content) > 50000:
            if "lmstudio" in self.providers and self.providers["lmstudio"].is_available():
                return "lmstudio"
            if "ollama" in self.providers and self.providers["ollama"].is_available():
                return "ollama"
        
        # Default: prefer local first, then cloud
        for provider in ["lmstudio", "ollama", "openai"]:
            if provider in self.providers and self.providers[provider].is_available():
                if provider == "openai" and self.daily_spend >= self.cost_budget:
                    continue  # Skip if over budget
                return provider
        
        return "lmstudio"  # Default fallback
    
    async def _try_provider(self, provider_name: str, task: AnalysisTask) -> ProviderResponse:
        """Try a specific provider with error handling"""
        try:
            provider = self.providers[provider_name]
            if not provider.is_available():
                return ProviderResponse(
                    content="", provider=provider_name, model="unknown",
                    tokens_used=0, cost_estimate=0.0, latency=0.0,
                    success=False, error="Provider not available"
                )
            
            return await provider.analyze(task)
        except Exception as e:
            logger.error(f"Provider {provider_name} failed: {e}")
            return ProviderResponse(
                content="", provider=provider_name, model="unknown",
                tokens_used=0, cost_estimate=0.0, latency=0.0,
                success=False, error=str(e)
            )
    
    def get_provider_status(self) -> Dict:
        """Get status of all providers"""
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                "available": provider.is_available(),
                "max_tokens": provider.get_max_tokens(),
                "model": getattr(provider, 'model', 'unknown')
            }
        
        status["orchestrator"] = {
            "daily_spend": self.daily_spend,
            "budget_remaining": self.cost_budget - self.daily_spend,
            "fallback_chain": self.fallback_chain
        }
        
        return status

# Example usage and integration point
async def example_usage():
    """Example of how to use the multi-provider system"""
    
    config = {
        "providers": {
            "lmstudio": {
                "url": "http://127.0.0.1:1234/v1/chat/completions",
                "model": "meta-llama-3.1-8b-instruct"
            },
            "openai": {
                "api_key": "your-openai-api-key",
                "model": "gpt-4"
            },
            "ollama": {
                "url": "http://localhost:11434/api/generate",
                "model": "llama2"
            }
        },
        "fallback_chain": ["lmstudio", "ollama", "openai"],
        "cost_budget": 10.0
    }
    
    orchestrator = ProviderOrchestrator(config)
    
    task = AnalysisTask(
        task_type="security",
        content="Analyze this code for security vulnerabilities: ...",
        context={"file_path": "example.py"},
        max_tokens=2048
    )
    
    response = await orchestrator.route_request(task)
    
    if response.success:
        print(f"Analysis completed using {response.provider}")
        print(f"Cost: ${response.cost_estimate:.4f}")
        print(f"Content: {response.content[:200]}...")
    else:
        print(f"Analysis failed: {response.error}")
    
    # Check provider status
    status = orchestrator.get_provider_status()
    print(f"Provider status: {status}")

if __name__ == "__main__":
    asyncio.run(example_usage())