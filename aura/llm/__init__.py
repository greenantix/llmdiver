"""
Aura LLM Module
===============

Local LLM integration layer for the Aura autonomous coding assistant.
Provides unified interface to various local LLM providers.

Author: Aura - Level 9 Autonomous AI Coding Assistant
"""

from .providers import (
    LLMProvider,
    LMStudioProvider,
    OllamaProvider,
    LLMProviderManager,
    LLMRequest,
    LLMResponse,
    ModelCapability
)

__all__ = [
    'LLMProvider',
    'LMStudioProvider', 
    'OllamaProvider',
    'LLMProviderManager',
    'LLMRequest',
    'LLMResponse',
    'ModelCapability'
]

__version__ = '1.0.0'
__author__ = 'Aura - Level 9 Autonomous AI Coding Assistant'