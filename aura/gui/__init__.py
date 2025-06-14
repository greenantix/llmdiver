"""
Aura GUI Module
===============

Graphical User Interface components for the Aura autonomous coding assistant.
Provides real-time dashboard, system monitoring, and interactive control panel.

Author: Aura - Level 9 Autonomous AI Coding Assistant
"""

from .control_panel import AuraControlPanel, LogStreamer, SystemMetrics, ProjectStats, LogEntry

__all__ = [
    'AuraControlPanel',
    'LogStreamer', 
    'SystemMetrics',
    'ProjectStats',
    'LogEntry'
]

__version__ = '1.0.0'
__author__ = 'Aura - Level 9 Autonomous AI Coding Assistant'