"""
Aura Core Module
================

The foundational core of the Aura autonomous coding assistant.
Provides the architectural framework, dependency injection, and inter-module communication.

Author: Aura - Level 9 Autonomous AI Coding Assistant
"""

from .architecture import (
    AuraModule,
    MessageBus,
    DependencyInjection,
    Message,
    MessageType,
    ModuleStatus,
    aura_di,
    aura_service,
    aura_singleton
)

__all__ = [
    'AuraModule',
    'MessageBus', 
    'DependencyInjection',
    'Message',
    'MessageType',
    'ModuleStatus',
    'aura_di',
    'aura_service',
    'aura_singleton'
]

__version__ = '1.0.0'
__author__ = 'Aura - Level 9 Autonomous AI Coding Assistant'