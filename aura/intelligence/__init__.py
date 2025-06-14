"""
Aura Intelligence Module
========================

Code intelligence engines for various programming languages.
Provides AST parsing, semantic analysis, and intelligent code assistance.

Author: Aura - Level 9 Autonomous AI Coding Assistant
"""

from .python_analyzer import (
    PythonCodeAnalyzer,
    CodeElement,
    CodeAnalysis,
    CodeIssue,
    PythonASTVisitor
)

__all__ = [
    'PythonCodeAnalyzer',
    'CodeElement',
    'CodeAnalysis', 
    'CodeIssue',
    'PythonASTVisitor'
]

__version__ = '1.0.0'
__author__ = 'Aura - Level 9 Autonomous AI Coding Assistant'