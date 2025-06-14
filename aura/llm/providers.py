"""
Aura LLM Provider Module
========================

Implements the abstraction layer for various local LLM providers.
Supports LM Studio, Ollama, and other local inference servers.

Author: Aura - Level 9 Autonomous AI Coding Assistant
Date: 2025-06-13
Phase: 1.2 - Local LLM Integration
"""

import asyncio
import json
import time
import logging
import httpx
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import uuid

from ..core import AuraModule, MessageType, aura_service, aura_singleton


class ModelCapability(Enum):
    """Model capability levels for task optimization"""
    FAST = "fast"           # Quick responses, small context
    MEDIUM = "medium"       # Balanced performance
    LARGE = "large"         # Large context, complex reasoning
    CODING = "coding"       # Code-specialized models


@dataclass
class LLMRequest:
    """Standard LLM request format"""
    prompt: str
    model_preference: ModelCapability = ModelCapability.MEDIUM
    max_tokens: int = 1000
    temperature: float = 0.3
    system_prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    request_id: str = None

    def __post_init__(self):
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())


@dataclass
class LLMResponse:
    """Standard LLM response format"""
    request_id: str
    content: str
    model_used: str
    tokens_used: int
    processing_time: float
    confidence: float = 1.0
    metadata: Dict[str, Any] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LLMProvider(ABC):
    """Abstract base class for all LLM providers"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"aura.llm.{self.__class__.__name__.lower()}")
        self.base_url = config.get('base_url', 'http://localhost:1234')
        self.timeout = config.get('timeout', 60)
        self.retry_attempts = config.get('retry_attempts', 3)
        self.model_mappings = self._get_model_mappings()

    @abstractmethod
    def _get_model_mappings(self) -> Dict[ModelCapability, Dict[str, Any]]:
        """Get model mappings for different capabilities"""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available"""
        pass

    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """Get list of available models"""
        pass

    @abstractmethod
    async def generate_completion(self, request: LLMRequest) -> LLMResponse:
        """Generate completion for the request"""
        pass
    
    async def generate_completion_simple(self, prompt: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """Simple completion method that returns just the text response"""
        request = LLMRequest(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        response = await self.generate_completion(request)
        return response.content

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status"""
        start_time = time.time()
        try:
            is_available = await self.is_available()
            models = await self.get_available_models() if is_available else []
            
            return {
                'provider': self.__class__.__name__,
                'available': is_available,
                'models': models,
                'response_time': time.time() - start_time,
                'base_url': self.base_url
            }
        except Exception as e:
            return {
                'provider': self.__class__.__name__,
                'available': False,
                'error': str(e),
                'response_time': time.time() - start_time,
                'base_url': self.base_url
            }


class LMStudioProvider(LLMProvider):
    """LM Studio provider implementation"""

    def _get_model_mappings(self) -> Dict[ModelCapability, Dict[str, Any]]:
        """LM Studio model capability mappings"""
        return {
            ModelCapability.FAST: {
                'preferred_models': ['phi-3-mini', 'phi-3', 'llama-3.2-1b', 'llama-3.2-3b'],
                'max_tokens': 2048,
                'context_window': 4096,
                'use_case': 'Quick responses, simple classification'
            },
            ModelCapability.MEDIUM: {
                'preferred_models': ['llama-3.1-8b', 'llama-3-8b', 'mistral-7b'],
                'max_tokens': 4096,
                'context_window': 8192,
                'use_case': 'Standard processing, balanced performance'
            },
            ModelCapability.LARGE: {
                'preferred_models': ['llama-3.1-70b', 'llama-2-70b', 'codellama-34b'],
                'max_tokens': 8192,
                'context_window': 32768,
                'use_case': 'Complex reasoning, large context analysis'
            },
            ModelCapability.CODING: {
                'preferred_models': ['codegemma', 'codellama', 'deepseek-coder', 'starcoder'],
                'max_tokens': 4096,
                'context_window': 16384,
                'use_case': 'Code generation, analysis, refactoring'
            }
        }

    async def is_available(self) -> bool:
        """Check if LM Studio server is running"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/v1/models", timeout=5)
                return response.status_code == 200
        except Exception:
            return False

    async def get_available_models(self) -> List[str]:
        """Get currently loaded models from LM Studio"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/v1/models", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    return [model['id'] for model in data.get('data', [])]
        except Exception as e:
            self.logger.warning(f"Could not get available models: {e}")
        return []

    def _detect_model_capability(self, model_id: str) -> ModelCapability:
        """Detect model capability based on model ID"""
        model_lower = model_id.lower()
        
        # Check for coding models first
        if any(term in model_lower for term in ['code', 'coder', 'coding', 'starcoder', 'deepseek-coder']):
            return ModelCapability.CODING
        
        # Check for fast models
        if any(term in model_lower for term in ['phi', 'mini', 'small', '1b', '3b']):
            return ModelCapability.FAST
        
        # Check for large models
        if any(term in model_lower for term in ['70b', '65b', 'large', 'xl']):
            return ModelCapability.LARGE
        
        # Default to medium
        return ModelCapability.MEDIUM

    async def generate_completion(self, request: LLMRequest) -> LLMResponse:
        """Generate completion using LM Studio API"""
        start_time = time.time()
        
        try:
            # Get currently loaded model
            available_models = await self.get_available_models()
            if not available_models:
                return LLMResponse(
                    request_id=request.request_id,
                    content="",
                    model_used="none",
                    tokens_used=0,
                    processing_time=time.time() - start_time,
                    error="No models loaded in LM Studio"
                )

            # Select best available model for the request
            current_model = available_models[0]  # Use first available
            detected_capability = self._detect_model_capability(current_model)
            
            # Adjust parameters based on detected capability
            capability_config = self.model_mappings[detected_capability]
            adjusted_max_tokens = min(request.max_tokens, capability_config['max_tokens'])
            
            # Build messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})

            payload = {
                "model": current_model,
                "messages": messages,
                "max_tokens": adjusted_max_tokens,
                "temperature": request.temperature,
                "stream": False
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    choice = result['choices'][0]
                    
                    return LLMResponse(
                        request_id=request.request_id,
                        content=choice['message']['content'].strip(),
                        model_used=current_model,
                        tokens_used=result.get('usage', {}).get('total_tokens', 0),
                        processing_time=time.time() - start_time,
                        metadata={
                            'detected_capability': detected_capability.value,
                            'adjusted_max_tokens': adjusted_max_tokens,
                            'provider': 'lm_studio'
                        }
                    )
                else:
                    error_msg = f"LM Studio API error: {response.status_code}"
                    return LLMResponse(
                        request_id=request.request_id,
                        content="",
                        model_used=current_model,
                        tokens_used=0,
                        processing_time=time.time() - start_time,
                        error=error_msg
                    )

        except Exception as e:
            return LLMResponse(
                request_id=request.request_id,
                content="",
                model_used="unknown",
                tokens_used=0,
                processing_time=time.time() - start_time,
                error=str(e)
            )


class OllamaProvider(LLMProvider):
    """Ollama provider implementation"""

    def _get_model_mappings(self) -> Dict[ModelCapability, Dict[str, Any]]:
        """Ollama model capability mappings"""
        return {
            ModelCapability.FAST: {
                'preferred_models': ['phi3:mini', 'llama3.2:1b', 'llama3.2:3b'],
                'max_tokens': 2048,
                'context_window': 4096
            },
            ModelCapability.MEDIUM: {
                'preferred_models': ['llama3.1:8b', 'mistral:7b', 'gemma2:9b'],
                'max_tokens': 4096,
                'context_window': 8192
            },
            ModelCapability.LARGE: {
                'preferred_models': ['llama3.1:70b', 'mixtral:8x7b'],
                'max_tokens': 8192,
                'context_window': 32768
            },
            ModelCapability.CODING: {
                'preferred_models': ['codellama:13b', 'deepseek-coder:6.7b', 'starcoder2:7b'],
                'max_tokens': 4096,
                'context_window': 16384
            }
        }

    async def is_available(self) -> bool:
        """Check if Ollama server is running"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=5)
                return response.status_code == 200
        except Exception:
            return False

    async def get_available_models(self) -> List[str]:
        """Get available models from Ollama"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            self.logger.warning(f"Could not get available models: {e}")
        return []

    async def generate_completion(self, request: LLMRequest) -> LLMResponse:
        """Generate completion using Ollama API"""
        start_time = time.time()
        
        try:
            # Get available models and select best match
            available_models = await self.get_available_models()
            if not available_models:
                return LLMResponse(
                    request_id=request.request_id,
                    content="",
                    model_used="none",
                    tokens_used=0,
                    processing_time=time.time() - start_time,
                    error="No models available in Ollama"
                )

            # Select model based on preference
            preferred_models = self.model_mappings[request.model_preference]['preferred_models']
            selected_model = None
            
            for preferred in preferred_models:
                for available in available_models:
                    if preferred in available:
                        selected_model = available
                        break
                if selected_model:
                    break
            
            if not selected_model:
                selected_model = available_models[0]  # Fallback to first available

            # Build prompt with system message if provided
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\n{request.prompt}"

            payload = {
                "model": selected_model,
                "prompt": full_prompt,
                "options": {
                    "num_predict": request.max_tokens,
                    "temperature": request.temperature,
                },
                "stream": False
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    
                    return LLMResponse(
                        request_id=request.request_id,
                        content=result['response'].strip(),
                        model_used=selected_model,
                        tokens_used=result.get('prompt_eval_count', 0) + result.get('eval_count', 0),
                        processing_time=time.time() - start_time,
                        metadata={
                            'provider': 'ollama',
                            'eval_duration': result.get('eval_duration', 0),
                            'prompt_eval_duration': result.get('prompt_eval_duration', 0)
                        }
                    )
                else:
                    error_msg = f"Ollama API error: {response.status_code}"
                    return LLMResponse(
                        request_id=request.request_id,
                        content="",
                        model_used=selected_model,
                        tokens_used=0,
                        processing_time=time.time() - start_time,
                        error=error_msg
                    )

        except Exception as e:
            return LLMResponse(
                request_id=request.request_id,
                content="",
                model_used="unknown",
                tokens_used=0,
                processing_time=time.time() - start_time,
                error=str(e)
            )


@aura_singleton("llm_provider_manager")
class LLMProviderManager(AuraModule):
    """
    LLM Provider Manager Module
    Manages multiple LLM providers and routes requests to the best available provider.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__("llm_provider", config)
        self.providers: Dict[str, LLMProvider] = {}
        self.default_provider = config.get('default_provider', 'lm_studio')
        self.fallback_providers = config.get('fallback_providers', ['ollama'])
        
    async def initialize(self) -> bool:
        """Initialize all configured providers"""
        try:
            self.logger.info("Initializing LLM providers")
            
            # Initialize LM Studio provider
            if 'lm_studio' in self.config.get('providers', ['lm_studio']):
                lm_config = self.config.get('lm_studio', {})
                lm_config.update({'base_url': lm_config.get('base_url', 'http://localhost:1234')})
                self.providers['lm_studio'] = LMStudioProvider(lm_config)
                
            # Initialize Ollama provider  
            if 'ollama' in self.config.get('providers', ['ollama']):
                ollama_config = self.config.get('ollama', {})
                ollama_config.update({'base_url': ollama_config.get('base_url', 'http://localhost:11434')})
                self.providers['ollama'] = OllamaProvider(ollama_config)

            # Test provider availability
            available_providers = []
            for name, provider in self.providers.items():
                if await provider.is_available():
                    available_providers.append(name)
                    self.logger.info(f"Provider {name} is available")
                else:
                    self.logger.warning(f"Provider {name} is not available")

            if not available_providers:
                self.logger.error("No LLM providers are available")
                return False

            self.logger.info(f"Initialized {len(available_providers)} LLM providers: {available_providers}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize LLM providers: {e}")
            return False

    async def process_message(self, message) -> Optional[any]:
        """Process LLM generation requests"""
        try:
            if message.type == MessageType.COMMAND:
                command = message.payload.get('command')
                
                if command == 'generate':
                    # Extract LLM request from payload
                    request_data = message.payload.get('request', {})
                    request = LLMRequest(
                        prompt=request_data.get('prompt', ''),
                        model_preference=ModelCapability(request_data.get('model_preference', 'medium')),
                        max_tokens=request_data.get('max_tokens', 1000),
                        temperature=request_data.get('temperature', 0.3),
                        system_prompt=request_data.get('system_prompt'),
                        context=request_data.get('context'),
                        request_id=request_data.get('request_id')
                    )
                    
                    response = await self.generate_completion(request)
                    
                    return self._create_response(message, {
                        'success': response.error is None,
                        'response': asdict(response)
                    })
                
                elif command == 'health_check':
                    health_status = await self.get_health_status()
                    return self._create_response(message, {
                        'success': True,
                        'health_status': health_status
                    })
                
                elif command == 'available_models':
                    models = await self.get_all_available_models()
                    return self._create_response(message, {
                        'success': True,
                        'available_models': models
                    })

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return self._create_response(message, {
                'success': False,
                'error': str(e)
            })

        return None

    async def generate_completion(self, request: LLMRequest) -> LLMResponse:
        """Generate completion using the best available provider"""
        # Try default provider first
        if self.default_provider in self.providers:
            provider = self.providers[self.default_provider]
            if await provider.is_available():
                self.logger.debug(f"Using default provider: {self.default_provider}")
                return await provider.generate_completion(request)
        
        # Try fallback providers
        for provider_name in self.fallback_providers:
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                if await provider.is_available():
                    self.logger.debug(f"Using fallback provider: {provider_name}")
                    return await provider.generate_completion(request)
        
        # No providers available
        return LLMResponse(
            request_id=request.request_id,
            content="",
            model_used="none",
            tokens_used=0,
            processing_time=0,
            error="No LLM providers available"
        )

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        health_status = {}
        for name, provider in self.providers.items():
            health_status[name] = await provider.health_check()
        return health_status

    async def get_all_available_models(self) -> Dict[str, List[str]]:
        """Get available models from all providers"""
        models = {}
        for name, provider in self.providers.items():
            if await provider.is_available():
                models[name] = await provider.get_available_models()
        return models

    def _create_response(self, original_message, payload):
        """Create response message"""
        from ..core import Message
        return Message(
            id=str(uuid.uuid4()),
            type=MessageType.RESPONSE,
            source=self.module_name,
            target=original_message.source,
            timestamp=time.time(),
            payload=payload,
            correlation_id=original_message.id
        )

    async def shutdown(self) -> None:
        """Clean shutdown of all providers"""
        self.logger.info("Shutting down LLM Provider Manager")
        # Providers don't need explicit shutdown currently
        self.providers.clear()