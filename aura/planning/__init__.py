"""
Aura Planning Module - PRD and Action Plan Automation
The Dawn of Metacognition - Phase 3.1

This module enables Aura to analyze requirements, decompose complex tasks,
and generate autonomous action plans for self-directed development.
"""

from .prd_parser import PRDParser, RequirementAnalysis
from .task_decomposer import TaskDecomposer, TaskHierarchy
from .dependency_grapher import DependencyGrapher, DependencyGraph
from .plan_executor import PlanExecutor, ExecutionPlan

__all__ = [
    'PRDParser',
    'RequirementAnalysis', 
    'TaskDecomposer',
    'TaskHierarchy',
    'DependencyGrapher',
    'DependencyGraph',
    'PlanExecutor',
    'ExecutionPlan'
]