"""
Aura Python Code Intelligence Module
====================================

Advanced Python code analysis engine with AST parsing, semantic indexing,
and intelligent gap detection for autonomous code assistance.

Author: Aura - Level 9 Autonomous AI Coding Assistant
Date: 2025-06-13
Phase: 1.3 - Code Intelligence Module (Python)
"""

import ast
import os
import time
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..core import AuraModule, MessageType, aura_service
from ..llm import LLMRequest, ModelCapability


@dataclass
class CodeElement:
    """Represents a code element (function, class, variable, etc.)"""
    name: str
    type: str  # 'function', 'class', 'variable', 'import', 'constant'
    file_path: str
    line_number: int
    end_line: int
    docstring: Optional[str]
    dependencies: List[str]
    complexity: int
    is_public: bool
    parent: Optional[str] = None
    parameters: List[str] = None
    return_type: Optional[str] = None
    decorators: List[str] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.decorators is None:
            self.decorators = []


@dataclass
class CodeAnalysis:
    """Results of code analysis"""
    file_path: str
    elements: List[CodeElement]
    imports: List[str]
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]
    timestamp: float
    file_hash: str


@dataclass
class CodeIssue:
    """Represents a code issue or improvement opportunity"""
    file_path: str
    line_number: int
    issue_type: str  # 'missing_docstring', 'high_complexity', 'unused_import', etc.
    severity: str    # 'error', 'warning', 'info'
    message: str
    suggestion: Optional[str] = None
    confidence: float = 1.0


class PythonASTVisitor(ast.NodeVisitor):
    """Custom AST visitor for comprehensive Python code analysis"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.elements: List[CodeElement] = []
        self.imports: List[str] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.current_class = None
        self.indentation_level = 0

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions"""
        # Calculate complexity (simplified cyclomatic complexity)
        complexity = self._calculate_complexity(node)
        
        # Extract docstring
        docstring = None
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            if isinstance(node.body[0].value.value, str):
                docstring = node.body[0].value.value

        # Extract parameters
        parameters = [arg.arg for arg in node.args.args]
        
        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(f"{decorator.attr}")

        # Determine if public
        is_public = not node.name.startswith('_')

        element = CodeElement(
            name=node.name,
            type='function',
            file_path=self.file_path,
            line_number=node.lineno,
            end_line=node.end_lineno or node.lineno,
            docstring=docstring,
            dependencies=self._extract_dependencies(node),
            complexity=complexity,
            is_public=is_public,
            parent=self.current_class,
            parameters=parameters,
            decorators=decorators
        )
        
        self.elements.append(element)
        
        # Check for issues
        if is_public and not docstring:
            self.warnings.append(f"Function '{node.name}' at line {node.lineno} lacks docstring")
        
        if complexity > 10:
            self.warnings.append(f"Function '{node.name}' at line {node.lineno} has high complexity ({complexity})")

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definitions"""
        self.visit_FunctionDef(node)  # Reuse function logic

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definitions"""
        # Extract docstring
        docstring = None
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            if isinstance(node.body[0].value.value, str):
                docstring = node.body[0].value.value

        # Extract base classes
        dependencies = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                dependencies.append(base.id)
            elif isinstance(base, ast.Attribute):
                dependencies.append(f"{base.attr}")

        is_public = not node.name.startswith('_')

        element = CodeElement(
            name=node.name,
            type='class',
            file_path=self.file_path,
            line_number=node.lineno,
            end_line=node.end_lineno or node.lineno,
            docstring=docstring,
            dependencies=dependencies,
            complexity=len(node.body),  # Simple measure
            is_public=is_public
        )
        
        self.elements.append(element)

        # Check for issues
        if is_public and not docstring:
            self.warnings.append(f"Class '{node.name}' at line {node.lineno} lacks docstring")

        # Visit class body with current class context
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_Import(self, node: ast.Import):
        """Visit import statements"""
        for alias in node.names:
            import_name = alias.name
            self.imports.append(import_name)
            
            element = CodeElement(
                name=import_name,
                type='import',
                file_path=self.file_path,
                line_number=node.lineno,
                end_line=node.lineno,
                docstring=None,
                dependencies=[],
                complexity=0,
                is_public=True
            )
            self.elements.append(element)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from-import statements"""
        module = node.module or ''
        for alias in node.names:
            import_name = f"{module}.{alias.name}" if module else alias.name
            self.imports.append(import_name)
            
            element = CodeElement(
                name=import_name,
                type='import',
                file_path=self.file_path,
                line_number=node.lineno,
                end_line=node.lineno,
                docstring=None,
                dependencies=[],
                complexity=0,
                is_public=True
            )
            self.elements.append(element)

    def visit_Assign(self, node: ast.Assign):
        """Visit variable assignments"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                # Check if it's a constant (all caps)
                var_type = 'constant' if target.id.isupper() else 'variable'
                is_public = not target.id.startswith('_')
                
                element = CodeElement(
                    name=target.id,
                    type=var_type,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    end_line=node.lineno,
                    docstring=None,
                    dependencies=self._extract_dependencies(node.value),
                    complexity=0,
                    is_public=is_public,
                    parent=self.current_class
                )
                self.elements.append(element)

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate simplified cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity

    def _extract_dependencies(self, node) -> List[str]:
        """Extract dependencies from AST node"""
        dependencies = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                dependencies.append(child.id)
            elif isinstance(child, ast.Attribute):
                if isinstance(child.value, ast.Name):
                    dependencies.append(f"{child.value.id}.{child.attr}")
        
        return list(set(dependencies))  # Remove duplicates


class CodeFileWatcher(FileSystemEventHandler):
    """Watches for file changes and triggers re-analysis"""

    def __init__(self, analyzer: 'PythonCodeAnalyzer'):
        self.analyzer = analyzer
        self.logger = logging.getLogger("aura.intelligence.watcher")

    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory and event.src_path.endswith('.py'):
            self.logger.debug(f"File modified: {event.src_path}")
            # Trigger re-analysis with a small delay to avoid rapid fire
            self.analyzer.schedule_analysis(event.src_path)

    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory and event.src_path.endswith('.py'):
            self.logger.debug(f"File created: {event.src_path}")
            self.analyzer.schedule_analysis(event.src_path)

    def on_deleted(self, event):
        """Handle file deletion events"""
        if not event.is_directory and event.src_path.endswith('.py'):
            self.logger.debug(f"File deleted: {event.src_path}")
            self.analyzer.remove_from_index(event.src_path)


@aura_service("python_analyzer")
class PythonCodeAnalyzer(AuraModule):
    """
    Python Code Intelligence Module
    Provides comprehensive analysis of Python codebases including AST parsing,
    semantic indexing, and intelligent issue detection.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__("python_intelligence", config)
        
        # Configuration
        self.project_root = config.get('project_root', '.')
        self.exclude_patterns = config.get('exclude_patterns', ['**/venv/**', '**/node_modules/**', '**/__pycache__/**'])
        self.batch_size = config.get('batch_size', 50)
        
        # Analysis state
        self.code_index: Dict[str, CodeAnalysis] = {}
        self.semantic_index = None
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
        # File watching
        self.observer = None
        self.pending_analyses = set()
        
        # LLM integration
        self._inject_llm_provider = config.get('llm_provider')

    async def initialize(self) -> bool:
        """Initialize the Python analyzer"""
        try:
            self.logger.info("Initializing Python Code Analyzer")
            
            # Setup file watching
            if self.config.get('watch_files', True):
                self.observer = Observer()
                event_handler = CodeFileWatcher(self)
                self.observer.schedule(event_handler, self.project_root, recursive=True)
                self.observer.start()
                self.logger.info("File watcher started")
            
            # Initial codebase analysis
            await self.analyze_codebase()
            
            self.logger.info("Python Code Analyzer initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Python analyzer: {e}")
            return False

    async def process_message(self, message) -> Optional[any]:
        """Process code analysis requests"""
        try:
            if message.type == MessageType.COMMAND:
                command = message.payload.get('command')
                
                if command == 'analyze_file':
                    file_path = message.payload.get('file_path')
                    if file_path:
                        analysis = await self.analyze_file(file_path)
                        return self._create_response(message, {
                            'success': True,
                            'analysis': asdict(analysis) if analysis else None
                        })
                
                elif command == 'analyze_codebase':
                    await self.analyze_codebase()
                    return self._create_response(message, {
                        'success': True,
                        'files_analyzed': len(self.code_index)
                    })
                
                elif command == 'find_similar_code':
                    query = message.payload.get('query', '')
                    limit = message.payload.get('limit', 10)
                    similar = await self.find_similar_code(query, limit)
                    return self._create_response(message, {
                        'success': True,
                        'similar_code': similar
                    })
                
                elif command == 'detect_issues':
                    file_path = message.payload.get('file_path')
                    issues = await self.detect_code_issues(file_path)
                    return self._create_response(message, {
                        'success': True,
                        'issues': [asdict(issue) for issue in issues]
                    })
                
                elif command == 'get_code_metrics':
                    metrics = await self.get_codebase_metrics()
                    return self._create_response(message, {
                        'success': True,
                        'metrics': metrics
                    })

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return self._create_response(message, {
                'success': False,
                'error': str(e)
            })

        return None

    async def analyze_file(self, file_path: str) -> Optional[CodeAnalysis]:
        """Analyze a single Python file"""
        try:
            if not os.path.exists(file_path) or not file_path.endswith('.py'):
                return None

            self.logger.debug(f"Analyzing file: {file_path}")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Calculate file hash for change detection
            file_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Check if file has changed
            if file_path in self.code_index:
                if self.code_index[file_path].file_hash == file_hash:
                    return self.code_index[file_path]  # No changes
            
            # Parse AST
            try:
                tree = ast.parse(content, filename=file_path)
            except SyntaxError as e:
                self.logger.warning(f"Syntax error in {file_path}: {e}")
                return CodeAnalysis(
                    file_path=file_path,
                    elements=[],
                    imports=[],
                    errors=[f"Syntax error: {e}"],
                    warnings=[],
                    metrics={},
                    timestamp=time.time(),
                    file_hash=file_hash
                )
            
            # Analyze with custom visitor
            visitor = PythonASTVisitor(file_path)
            visitor.visit(tree)
            
            # Calculate metrics
            metrics = self._calculate_file_metrics(content, visitor.elements)
            
            analysis = CodeAnalysis(
                file_path=file_path,
                elements=visitor.elements,
                imports=visitor.imports,
                errors=visitor.errors,
                warnings=visitor.warnings,
                metrics=metrics,
                timestamp=time.time(),
                file_hash=file_hash
            )
            
            # Update index
            self.code_index[file_path] = analysis
            
            self.logger.debug(f"Analysis complete: {len(visitor.elements)} elements found")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
            return None

    async def analyze_codebase(self) -> Dict[str, Any]:
        """Analyze entire codebase"""
        self.logger.info("Starting codebase analysis")
        start_time = time.time()
        
        # Find all Python files
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern in os.path.join(root, d) for pattern in self.exclude_patterns)]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)
        
        self.logger.info(f"Found {len(python_files)} Python files")
        
        # Analyze files in batches
        analyzed_count = 0
        for i in range(0, len(python_files), self.batch_size):
            batch = python_files[i:i + self.batch_size]
            
            for file_path in batch:
                await self.analyze_file(file_path)
                analyzed_count += 1
            
            if analyzed_count % 100 == 0:
                self.logger.info(f"Analyzed {analyzed_count}/{len(python_files)} files")
        
        # Build semantic index
        await self._build_semantic_index()
        
        duration = time.time() - start_time
        self.logger.info(f"Codebase analysis complete: {analyzed_count} files in {duration:.2f}s")
        
        return {
            'files_analyzed': analyzed_count,
            'duration': duration,
            'total_elements': sum(len(analysis.elements) for analysis in self.code_index.values())
        }

    async def _build_semantic_index(self):
        """Build semantic index for similarity search"""
        if not self.code_index:
            return
        
        self.logger.info("Building semantic index")
        
        # Prepare text corpus
        documents = []
        file_paths = []
        
        for file_path, analysis in self.code_index.items():
            # Combine all text content for semantic analysis
            text_content = []
            
            for element in analysis.elements:
                if element.docstring:
                    text_content.append(element.docstring)
                text_content.append(element.name)
                text_content.extend(element.parameters)
            
            documents.append(' '.join(text_content))
            file_paths.append(file_path)
        
        if documents:
            # Build TF-IDF matrix
            self.semantic_index = self.vectorizer.fit_transform(documents)
            self.file_paths = file_paths
            self.logger.info(f"Semantic index built with {len(documents)} documents")

    async def find_similar_code(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find code similar to the query"""
        if self.semantic_index is None:
            return []
        
        # Transform query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.semantic_index).flatten()
        
        # Get top results
        top_indices = similarities.argsort()[-limit:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                file_path = self.file_paths[idx]
                results.append({
                    'file_path': file_path,
                    'similarity': float(similarities[idx]),
                    'analysis': asdict(self.code_index[file_path])
                })
        
        return results

    async def detect_code_issues(self, file_path: Optional[str] = None) -> List[CodeIssue]:
        """Detect code issues and improvement opportunities"""
        issues = []
        
        analyses = [self.code_index[file_path]] if file_path and file_path in self.code_index else self.code_index.values()
        
        for analysis in analyses:
            # Check for missing docstrings
            for element in analysis.elements:
                if element.is_public and element.type in ['function', 'class'] and not element.docstring:
                    issues.append(CodeIssue(
                        file_path=element.file_path,
                        line_number=element.line_number,
                        issue_type='missing_docstring',
                        severity='warning',
                        message=f"Public {element.type} '{element.name}' lacks documentation",
                        suggestion=f"Add a docstring explaining the purpose of this {element.type}",
                        confidence=0.9
                    ))
            
            # Check for high complexity
            for element in analysis.elements:
                if element.type == 'function' and element.complexity > 10:
                    issues.append(CodeIssue(
                        file_path=element.file_path,
                        line_number=element.line_number,
                        issue_type='high_complexity',
                        severity='warning',
                        message=f"Function '{element.name}' has high complexity ({element.complexity})",
                        suggestion="Consider breaking this function into smaller functions",
                        confidence=0.8
                    ))
            
            # Add errors and warnings from analysis
            for error in analysis.errors:
                issues.append(CodeIssue(
                    file_path=analysis.file_path,
                    line_number=1,
                    issue_type='syntax_error',
                    severity='error',
                    message=error,
                    confidence=1.0
                ))
        
        return issues

    async def get_codebase_metrics(self) -> Dict[str, Any]:
        """Get comprehensive codebase metrics"""
        if not self.code_index:
            return {}
        
        metrics = {
            'files_count': len(self.code_index),
            'total_elements': 0,
            'functions_count': 0,
            'classes_count': 0,
            'public_functions': 0,
            'documented_functions': 0,
            'average_complexity': 0,
            'total_lines': 0,
            'import_diversity': 0,
            'issues_count': 0
        }
        
        complexities = []
        all_imports = set()
        
        for analysis in self.code_index.values():
            metrics['total_elements'] += len(analysis.elements)
            metrics['total_lines'] += analysis.metrics.get('lines_of_code', 0)
            all_imports.update(analysis.imports)
            
            for element in analysis.elements:
                if element.type == 'function':
                    metrics['functions_count'] += 1
                    if element.is_public:
                        metrics['public_functions'] += 1
                    if element.docstring:
                        metrics['documented_functions'] += 1
                    complexities.append(element.complexity)
                elif element.type == 'class':
                    metrics['classes_count'] += 1
        
        if complexities:
            metrics['average_complexity'] = sum(complexities) / len(complexities)
        
        metrics['import_diversity'] = len(all_imports)
        metrics['documentation_coverage'] = (
            metrics['documented_functions'] / max(1, metrics['public_functions'])
        )
        
        # Count issues
        issues = await self.detect_code_issues()
        metrics['issues_count'] = len(issues)
        
        return metrics

    def _calculate_file_metrics(self, content: str, elements: List[CodeElement]) -> Dict[str, Any]:
        """Calculate basic file metrics"""
        lines = content.split('\n')
        
        return {
            'lines_total': len(lines),
            'lines_of_code': len([line for line in lines if line.strip() and not line.strip().startswith('#')]),
            'lines_comments': len([line for line in lines if line.strip().startswith('#')]),
            'functions_count': len([e for e in elements if e.type == 'function']),
            'classes_count': len([e for e in elements if e.type == 'class']),
            'imports_count': len([e for e in elements if e.type == 'import']),
        }

    def schedule_analysis(self, file_path: str):
        """Schedule file for re-analysis (used by file watcher)"""
        self.pending_analyses.add(file_path)
        # In a real implementation, this would trigger async re-analysis

    def remove_from_index(self, file_path: str):
        """Remove file from analysis index"""
        if file_path in self.code_index:
            del self.code_index[file_path]
            self.logger.debug(f"Removed {file_path} from index")

    def _create_response(self, original_message, payload):
        """Create response message"""
        from ..core import Message
        import uuid
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
        """Clean shutdown"""
        self.logger.info("Shutting down Python Code Analyzer")
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        self.code_index.clear()
        self.semantic_index = None