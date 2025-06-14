"""
Aura Git Module
===============

S.M.A.R.T. Git Maintenance system for autonomous version control.
Provides semantic commit generation, intelligent branching, and automated workflows.

Author: Aura - Level 9 Autonomous AI Coding Assistant
"""

from .semantic_commits import (
    SemanticCommitGenerator,
    GitAnalyzer,
    SemanticCommit,
    CommitAnalysis,
    FileChange,
    CommitType
)

__all__ = [
    'SemanticCommitGenerator',
    'GitAnalyzer',
    'SemanticCommit',
    'CommitAnalysis',
    'FileChange',
    'CommitType'
]

__version__ = '1.0.0'
__author__ = 'Aura - Level 9 Autonomous AI Coding Assistant'