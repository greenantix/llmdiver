"""
Aura Self-Analysis Framework - Exhaustive Performance and Security Audit
Turn Your Gaze Inward: Conduct relentless analysis of your own codebase
"""

import ast
import asyncio
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union

from ..core.config import AuraConfig
from ..llm.providers import LLMProvider


class SecuritySeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class PerformanceImpact(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class CodeQualityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


@dataclass
class SecurityIssue:
    file_path: str
    line_number: int
    severity: SecuritySeverity
    issue_type: str
    description: str
    recommendation: str
    cwe_id: Optional[str] = None
    vulnerable_code: Optional[str] = None


@dataclass
class PerformanceIssue:
    file_path: str
    line_number: int
    impact: PerformanceImpact
    issue_type: str
    description: str
    recommendation: str
    estimated_improvement: Optional[str] = None
    problematic_code: Optional[str] = None


@dataclass
class CodeQualityIssue:
    file_path: str
    line_number: int
    level: CodeQualityLevel
    issue_type: str
    description: str
    recommendation: str
    metric_value: Optional[float] = None


@dataclass
class DependencyIssue:
    dependency_name: str
    current_version: str
    severity: SecuritySeverity
    issue_type: str
    description: str
    recommended_version: Optional[str] = None
    cve_id: Optional[str] = None


@dataclass
class FileAnalysis:
    file_path: str
    lines_of_code: int
    complexity_score: float
    maintainability_index: float
    security_issues: List[SecurityIssue]
    performance_issues: List[PerformanceIssue]
    quality_issues: List[CodeQualityIssue]
    imports: List[str]
    functions: List[str]
    classes: List[str]
    ast_tree: Optional[ast.AST] = None


@dataclass
class ProjectAnalysis:
    total_files: int
    total_lines: int
    total_functions: int
    total_classes: int
    average_complexity: float
    security_score: float
    performance_score: float
    quality_score: float
    all_security_issues: List[SecurityIssue]
    all_performance_issues: List[PerformanceIssue]
    all_quality_issues: List[CodeQualityIssue]
    dependency_issues: List[DependencyIssue]
    architecture_analysis: Dict[str, Any]
    hotspots: List[str]
    recommendations: List[str]
    analysis_timestamp: datetime


class AuraSelfAnalyzer:
    def __init__(self, config: AuraConfig, llm_provider: LLMProvider):
        self.config = config
        self.llm_provider = llm_provider
        self.project_root = Path("/home/greenantix/AI/LLMdiver/aura")
        self.analysis_patterns = self._load_analysis_patterns()
        
    def _load_analysis_patterns(self) -> Dict[str, str]:
        """Load comprehensive analysis patterns"""
        return {
            'security_analysis': """
Analyze this Python code for security vulnerabilities and risks:

```python
{code}
```

Examine for:
1. SQL injection vulnerabilities (if database queries present)
2. Command injection (subprocess, os.system usage)
3. Path traversal vulnerabilities (file operations)
4. Insecure deserialization (pickle, eval usage)
5. Hardcoded secrets or credentials
6. Insufficient input validation
7. Insecure random number generation
8. Cross-site scripting (XSS) if web-related
9. Authentication/authorization flaws
10. Cryptographic issues

Provide analysis in JSON format:
{
  "security_issues": [
    {
      "line": 42,
      "severity": "high|medium|low|critical",
      "type": "injection|path_traversal|hardcoded_secret|insecure_crypto",
      "description": "Detailed description of the vulnerability",
      "vulnerable_code": "The specific vulnerable code snippet",
      "recommendation": "How to fix this vulnerability",
      "cwe_id": "CWE-XX if applicable"
    }
  ],
  "security_score": 0.85,
  "security_summary": "Overall security assessment"
}

Focus on real vulnerabilities, not theoretical ones.
""",
            
            'performance_analysis': """
Analyze this Python code for performance issues and optimization opportunities:

```python
{code}
```

Examine for:
1. Inefficient algorithms (O(n²) when O(n) possible)
2. Memory leaks or excessive memory usage
3. I/O blocking operations without async
4. Inefficient data structures
5. Unnecessary object creation
6. String concatenation issues
7. Database query inefficiencies
8. Missing caching opportunities
9. CPU-intensive operations in loops
10. Import time issues

Provide analysis in JSON format:
{
  "performance_issues": [
    {
      "line": 25,
      "impact": "critical|high|medium|low|negligible",
      "type": "algorithm|memory|io|data_structure|string_ops",
      "description": "Description of the performance issue",
      "problematic_code": "The inefficient code",
      "recommendation": "Optimization recommendation",
      "estimated_improvement": "Estimated performance gain"
    }
  ],
  "performance_score": 0.75,
  "bottlenecks": ["List of major bottlenecks"],
  "optimization_opportunities": ["List of optimization suggestions"]
}

Focus on actual performance bottlenecks with measurable impact.
""",
            
            'code_quality_analysis': """
Analyze this Python code for quality, maintainability, and best practices:

```python
{code}
```

Examine for:
1. Code complexity (cyclomatic complexity)
2. Function/method length and responsibility
3. Class design and single responsibility principle
4. Naming conventions and readability
5. Documentation and comments quality
6. Error handling completeness
7. Type hints usage
8. Code duplication
9. Adherence to PEP 8 and Python best practices
10. Testability and modularity

Provide analysis in JSON format:
{
  "quality_issues": [
    {
      "line": 15,
      "level": "excellent|good|acceptable|needs_improvement|poor",
      "type": "complexity|naming|documentation|error_handling|design",
      "description": "Description of the quality issue",
      "recommendation": "How to improve code quality",
      "metric_value": 12.5
    }
  ],
  "quality_score": 0.88,
  "maintainability_index": 75.2,
  "complexity_metrics": {
    "cyclomatic_complexity": 8.5,
    "cognitive_complexity": 12.0
  },
  "best_practices": {
    "follows_pep8": true,
    "has_type_hints": false,
    "has_docstrings": true
  }
}

Provide constructive feedback for improvement.
""",
            
            'architecture_analysis': """
Analyze the overall architecture and design patterns of this Python module:

```python
{code}
```

Module path: {file_path}

Examine for:
1. Design patterns usage (appropriate/inappropriate)
2. Separation of concerns
3. Coupling and cohesion
4. Dependency injection patterns
5. Interface segregation
6. Single responsibility principle
7. Open/closed principle adherence
8. Layered architecture compliance
9. Error propagation patterns
10. Configuration management

Provide analysis in JSON format:
{
  "architecture_assessment": {
    "design_patterns": ["List of detected patterns"],
    "coupling_level": "low|medium|high",
    "cohesion_level": "high|medium|low",
    "modularity_score": 0.82,
    "responsibility_clarity": "excellent|good|poor"
  },
  "design_issues": [
    {
      "type": "tight_coupling|low_cohesion|violation_of_principle",
      "description": "Architecture issue description",
      "impact": "Impact on maintainability",
      "recommendation": "Architectural improvement suggestion"
    }
  ],
  "strengths": ["Architecture strengths"],
  "improvements": ["Suggested architectural improvements"]
}

Focus on maintainability and extensibility.
"""
        }
    
    async def analyze_project(self) -> ProjectAnalysis:
        """Perform comprehensive analysis of the entire Aura project"""
        
        print("🔍 Beginning exhaustive self-analysis of Aura codebase...")
        
        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not f.name.startswith('.') and 'test_' not in f.name]
        
        print(f"📁 Found {len(python_files)} Python files to analyze")
        
        # Analyze each file
        file_analyses = []
        all_security_issues = []
        all_performance_issues = []
        all_quality_issues = []
        
        for file_path in python_files:
            print(f"🔬 Analyzing: {file_path.relative_to(self.project_root)}")
            
            try:
                analysis = await self.analyze_file(file_path)
                file_analyses.append(analysis)
                
                all_security_issues.extend(analysis.security_issues)
                all_performance_issues.extend(analysis.performance_issues)
                all_quality_issues.extend(analysis.quality_issues)
                
            except Exception as e:
                print(f"❌ Error analyzing {file_path}: {e}")
        
        # Analyze dependencies
        print("📦 Analyzing dependencies...")
        dependency_issues = await self.analyze_dependencies()
        
        # Perform architecture analysis
        print("🏗️ Analyzing overall architecture...")
        architecture_analysis = await self.analyze_architecture(file_analyses)
        
        # Calculate aggregate metrics
        total_files = len(file_analyses)
        total_lines = sum(fa.lines_of_code for fa in file_analyses)
        total_functions = sum(len(fa.functions) for fa in file_analyses)
        total_classes = sum(len(fa.classes) for fa in file_analyses)
        average_complexity = sum(fa.complexity_score for fa in file_analyses) / max(total_files, 1)
        
        # Calculate scores
        security_score = self._calculate_security_score(all_security_issues, total_lines)
        performance_score = self._calculate_performance_score(all_performance_issues, total_lines)
        quality_score = self._calculate_quality_score(all_quality_issues, file_analyses)
        
        # Identify hotspots (files with most issues)
        hotspots = self._identify_hotspots(file_analyses)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            all_security_issues, all_performance_issues, all_quality_issues, 
            dependency_issues, architecture_analysis
        )
        
        return ProjectAnalysis(
            total_files=total_files,
            total_lines=total_lines,
            total_functions=total_functions,
            total_classes=total_classes,
            average_complexity=average_complexity,
            security_score=security_score,
            performance_score=performance_score,
            quality_score=quality_score,
            all_security_issues=all_security_issues,
            all_performance_issues=all_performance_issues,
            all_quality_issues=all_quality_issues,
            dependency_issues=dependency_issues,
            architecture_analysis=architecture_analysis,
            hotspots=hotspots,
            recommendations=recommendations,
            analysis_timestamp=datetime.now()
        )
    
    async def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Perform comprehensive analysis of a single Python file"""
        
        content = file_path.read_text(encoding='utf-8')
        
        # Parse AST
        try:
            ast_tree = ast.parse(content)
        except SyntaxError as e:
            print(f"❌ Syntax error in {file_path}: {e}")
            ast_tree = None
        
        # Extract basic metrics
        lines_of_code = len([line for line in content.split('\n') if line.strip() and not line.strip().startswith('#')])
        
        # Extract constructs
        imports, functions, classes = self._extract_constructs(ast_tree) if ast_tree else ([], [], [])
        
        # Calculate complexity
        complexity_score = self._calculate_file_complexity(ast_tree) if ast_tree else 0
        maintainability_index = self._calculate_maintainability_index(content, complexity_score, lines_of_code)
        
        # Perform specialized analyses
        security_issues = await self._analyze_file_security(file_path, content)
        performance_issues = await self._analyze_file_performance(file_path, content)
        quality_issues = await self._analyze_file_quality(file_path, content)
        
        return FileAnalysis(
            file_path=str(file_path),
            lines_of_code=lines_of_code,
            complexity_score=complexity_score,
            maintainability_index=maintainability_index,
            security_issues=security_issues,
            performance_issues=performance_issues,
            quality_issues=quality_issues,
            imports=imports,
            functions=functions,
            classes=classes,
            ast_tree=ast_tree
        )
    
    def _extract_constructs(self, ast_tree: ast.AST) -> Tuple[List[str], List[str], List[str]]:
        """Extract imports, functions, and classes from AST"""
        
        imports = []
        functions = []
        classes = []
        
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.extend([f"{module}.{alias.name}" for alias in node.names])
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
        
        return imports, functions, classes
    
    def _calculate_file_complexity(self, ast_tree: ast.AST) -> float:
        """Calculate cyclomatic complexity of file"""
        
        complexity = 0
        
        for node in ast.walk(ast_tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    def _calculate_maintainability_index(self, content: str, complexity: float, loc: int) -> float:
        """Calculate maintainability index (0-100 scale)"""
        
        # Simplified maintainability index calculation
        # Based on Halstead volume, cyclomatic complexity, and lines of code
        
        if loc == 0:
            return 100.0
        
        # Estimate Halstead volume (simplified)
        unique_operators = len(set(re.findall(r'[+\-*/=<>!&|%^~]', content)))
        unique_operands = len(set(re.findall(r'\b\w+\b', content)))
        halstead_volume = (unique_operators + unique_operands) * 2.5  # Simplified
        
        # Calculate maintainability index
        if halstead_volume <= 0:
            halstead_volume = 1
        
        mi = 171 - 5.2 * (halstead_volume / 1000) - 0.23 * complexity - 16.2 * (loc / 1000)
        
        return max(0, min(100, mi))
    
    async def _analyze_file_security(self, file_path: Path, content: str) -> List[SecurityIssue]:
        """Analyze file for security vulnerabilities"""
        
        # Perform pattern-based security analysis first
        issues = self._pattern_based_security_analysis(file_path, content)
        
        # Use LLM for deeper analysis
        try:
            prompt = self.analysis_patterns['security_analysis'].replace('{code}', content)
            response = await self.llm_provider.generate_completion_simple(prompt)
            
            llm_analysis = json.loads(response)
            
            # Convert LLM findings to SecurityIssue objects
            for issue_data in llm_analysis.get('security_issues', []):
                issue = SecurityIssue(
                    file_path=str(file_path),
                    line_number=issue_data.get('line', 0),
                    severity=SecuritySeverity(issue_data.get('severity', 'medium')),
                    issue_type=issue_data.get('type', 'unknown'),
                    description=issue_data.get('description', ''),
                    recommendation=issue_data.get('recommendation', ''),
                    cwe_id=issue_data.get('cwe_id'),
                    vulnerable_code=issue_data.get('vulnerable_code')
                )
                issues.append(issue)
                
        except Exception as e:
            print(f"LLM security analysis failed for {file_path}: {e}")
        
        return issues
    
    def _pattern_based_security_analysis(self, file_path: Path, content: str) -> List[SecurityIssue]:
        """Pattern-based security vulnerability detection"""
        
        issues = []
        lines = content.split('\n')
        
        # Check for dangerous function usage
        dangerous_patterns = {
            r'eval\s*\(': ('code_injection', 'Use of eval() is dangerous', 'CWE-95'),
            r'exec\s*\(': ('code_injection', 'Use of exec() is dangerous', 'CWE-95'),
            r'pickle\.loads?\s*\(': ('insecure_deserialization', 'Pickle deserialization can be unsafe', 'CWE-502'),
            r'subprocess\.(call|run|Popen).*shell=True': ('command_injection', 'Shell=True can lead to command injection', 'CWE-78'),
            r'os\.system\s*\(': ('command_injection', 'os.system() can lead to command injection', 'CWE-78'),
            r'random\.random\(\).*password|secret': ('weak_crypto', 'Using weak random for secrets', 'CWE-338'),
            r'md5\s*\(': ('weak_crypto', 'MD5 is cryptographically broken', 'CWE-327'),
            r'sha1\s*\(': ('weak_crypto', 'SHA1 is cryptographically weak', 'CWE-327'),
        }
        
        for line_num, line in enumerate(lines, 1):
            for pattern, (issue_type, description, cwe_id) in dangerous_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        file_path=str(file_path),
                        line_number=line_num,
                        severity=SecuritySeverity.HIGH,
                        issue_type=issue_type,
                        description=description,
                        recommendation=f"Replace with safer alternative",
                        cwe_id=cwe_id,
                        vulnerable_code=line.strip()
                    ))
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']{8,}["\']',
            r'secret\s*=\s*["\'][^"\']{8,}["\']',
            r'api_key\s*=\s*["\'][^"\']{8,}["\']',
            r'token\s*=\s*["\'][^"\']{8,}["\']',
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        file_path=str(file_path),
                        line_number=line_num,
                        severity=SecuritySeverity.MEDIUM,
                        issue_type='hardcoded_secret',
                        description='Potential hardcoded secret detected',
                        recommendation='Use environment variables or secure configuration',
                        cwe_id='CWE-798',
                        vulnerable_code=line.strip()
                    ))
        
        return issues
    
    async def _analyze_file_performance(self, file_path: Path, content: str) -> List[PerformanceIssue]:
        """Analyze file for performance issues"""
        
        # Pattern-based performance analysis
        issues = self._pattern_based_performance_analysis(file_path, content)
        
        # Use LLM for deeper analysis
        try:
            prompt = self.analysis_patterns['performance_analysis'].replace('{code}', content)
            response = await self.llm_provider.generate_completion_simple(prompt)
            
            llm_analysis = json.loads(response)
            
            for issue_data in llm_analysis.get('performance_issues', []):
                issue = PerformanceIssue(
                    file_path=str(file_path),
                    line_number=issue_data.get('line', 0),
                    impact=PerformanceImpact(issue_data.get('impact', 'medium')),
                    issue_type=issue_data.get('type', 'unknown'),
                    description=issue_data.get('description', ''),
                    recommendation=issue_data.get('recommendation', ''),
                    estimated_improvement=issue_data.get('estimated_improvement'),
                    problematic_code=issue_data.get('problematic_code')
                )
                issues.append(issue)
                
        except Exception as e:
            print(f"LLM performance analysis failed for {file_path}: {e}")
        
        return issues
    
    def _pattern_based_performance_analysis(self, file_path: Path, content: str) -> List[PerformanceIssue]:
        """Pattern-based performance issue detection"""
        
        issues = []
        lines = content.split('\n')
        
        # Performance anti-patterns
        performance_patterns = {
            r'for\s+\w+\s+in\s+range\(len\(': ('inefficient_loop', 'Use direct iteration instead of range(len())'),
            r'\+.*str\(.*\).*for.*in': ('string_concatenation', 'String concatenation in loop is inefficient'),
            r'\.append\(.*\)\s*for.*in.*\.append\(': ('list_append_in_loop', 'Multiple appends in loop, consider list comprehension'),
            r'time\.sleep\(.*\)': ('blocking_sleep', 'time.sleep() blocks the thread'),
            r'\.replace\(.*\)\.replace\(': ('chained_replace', 'Multiple string.replace() calls are inefficient'),
        }
        
        for line_num, line in enumerate(lines, 1):
            for pattern, (issue_type, description) in performance_patterns.items():
                if re.search(pattern, line):
                    issues.append(PerformanceIssue(
                        file_path=str(file_path),
                        line_number=line_num,
                        impact=PerformanceImpact.MEDIUM,
                        issue_type=issue_type,
                        description=description,
                        recommendation='Consider more efficient alternative',
                        problematic_code=line.strip()
                    ))
        
        return issues
    
    async def _analyze_file_quality(self, file_path: Path, content: str) -> List[CodeQualityIssue]:
        """Analyze file for code quality issues"""
        
        # Pattern-based quality analysis
        issues = self._pattern_based_quality_analysis(file_path, content)
        
        # Use LLM for deeper analysis
        try:
            prompt = self.analysis_patterns['code_quality_analysis'].replace('{code}', content)
            response = await self.llm_provider.generate_completion_simple(prompt)
            
            llm_analysis = json.loads(response)
            
            for issue_data in llm_analysis.get('quality_issues', []):
                issue = CodeQualityIssue(
                    file_path=str(file_path),
                    line_number=issue_data.get('line', 0),
                    level=CodeQualityLevel(issue_data.get('level', 'acceptable')),
                    issue_type=issue_data.get('type', 'unknown'),
                    description=issue_data.get('description', ''),
                    recommendation=issue_data.get('recommendation', ''),
                    metric_value=issue_data.get('metric_value')
                )
                issues.append(issue)
                
        except Exception as e:
            print(f"LLM quality analysis failed for {file_path}: {e}")
        
        return issues
    
    def _pattern_based_quality_analysis(self, file_path: Path, content: str) -> List[CodeQualityIssue]:
        """Pattern-based code quality issue detection"""
        
        issues = []
        lines = content.split('\n')
        
        # Check for long functions (simple heuristic)
        in_function = False
        function_start = 0
        function_name = ""
        
        for line_num, line in enumerate(lines, 1):
            if re.match(r'\s*def\s+(\w+)', line):
                if in_function and (line_num - function_start) > 50:
                    issues.append(CodeQualityIssue(
                        file_path=str(file_path),
                        line_number=function_start,
                        level=CodeQualityLevel.NEEDS_IMPROVEMENT,
                        issue_type='long_function',
                        description=f'Function {function_name} is too long ({line_num - function_start} lines)',
                        recommendation='Consider breaking into smaller functions',
                        metric_value=line_num - function_start
                    ))
                
                in_function = True
                function_start = line_num
                function_name = re.match(r'\s*def\s+(\w+)', line).group(1)
            
            elif line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                if in_function and (line_num - function_start) > 50:
                    issues.append(CodeQualityIssue(
                        file_path=str(file_path),
                        line_number=function_start,
                        level=CodeQualityLevel.NEEDS_IMPROVEMENT,
                        issue_type='long_function',
                        description=f'Function {function_name} is too long ({line_num - function_start} lines)',
                        recommendation='Consider breaking into smaller functions',
                        metric_value=line_num - function_start
                    ))
                in_function = False
        
        # Check for missing docstrings
        for line_num, line in enumerate(lines, 1):
            if re.match(r'\s*def\s+\w+', line) or re.match(r'\s*class\s+\w+', line):
                # Check if next few lines contain docstring
                has_docstring = False
                for i in range(line_num, min(line_num + 3, len(lines))):
                    if '"""' in lines[i] or "'''" in lines[i]:
                        has_docstring = True
                        break
                
                if not has_docstring:
                    construct_type = 'function' if 'def' in line else 'class'
                    issues.append(CodeQualityIssue(
                        file_path=str(file_path),
                        line_number=line_num,
                        level=CodeQualityLevel.NEEDS_IMPROVEMENT,
                        issue_type='missing_docstring',
                        description=f'{construct_type.title()} missing docstring',
                        recommendation='Add descriptive docstring'
                    ))
        
        return issues
    
    async def analyze_dependencies(self) -> List[DependencyIssue]:
        """Analyze project dependencies for security vulnerabilities"""
        
        issues = []
        
        # Check requirements.txt
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            # Use pip-audit or safety to check for known vulnerabilities
            try:
                result = subprocess.run(
                    ["pip-audit", "--format", "json", "--requirement", str(requirements_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    audit_data = json.loads(result.stdout)
                    for vuln in audit_data.get('vulnerabilities', []):
                        issues.append(DependencyIssue(
                            dependency_name=vuln['package'],
                            current_version=vuln['installed_version'],
                            severity=SecuritySeverity.HIGH,
                            issue_type='known_vulnerability',
                            description=vuln['description'],
                            recommended_version=vuln.get('fixed_versions', [None])[0],
                            cve_id=vuln.get('id')
                        ))
                        
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                print("⚠️ Could not run pip-audit for dependency analysis")
        
        return issues
    
    async def analyze_architecture(self, file_analyses: List[FileAnalysis]) -> Dict[str, Any]:
        """Analyze overall project architecture"""
        
        # Calculate architecture metrics
        total_files = len(file_analyses)
        avg_complexity = sum(fa.complexity_score for fa in file_analyses) / max(total_files, 1)
        
        # Analyze module dependencies
        dependency_graph = {}
        for analysis in file_analyses:
            module_name = Path(analysis.file_path).stem
            dependencies = [imp.split('.')[0] for imp in analysis.imports if not imp.startswith('.')]
            dependency_graph[module_name] = dependencies
        
        # Identify tightly coupled modules
        coupling_issues = []
        for module, deps in dependency_graph.items():
            if len(deps) > 10:  # High coupling threshold
                coupling_issues.append(f"Module {module} has high coupling ({len(deps)} dependencies)")
        
        # Identify large modules (potential SRP violations)
        srp_violations = []
        for analysis in file_analyses:
            if analysis.lines_of_code > 500:
                srp_violations.append(f"Module {Path(analysis.file_path).stem} is large ({analysis.lines_of_code} LOC)")
        
        return {
            'total_modules': total_files,
            'average_complexity': avg_complexity,
            'dependency_graph': dependency_graph,
            'coupling_issues': coupling_issues,
            'srp_violations': srp_violations,
            'architecture_score': max(0, 100 - len(coupling_issues) * 10 - len(srp_violations) * 5)
        }
    
    def _calculate_security_score(self, issues: List[SecurityIssue], total_lines: int) -> float:
        """Calculate overall security score (0-1)"""
        
        if not issues:
            return 1.0
        
        # Weight by severity
        severity_weights = {
            SecuritySeverity.CRITICAL: 10,
            SecuritySeverity.HIGH: 5,
            SecuritySeverity.MEDIUM: 2,
            SecuritySeverity.LOW: 1,
            SecuritySeverity.INFO: 0.5
        }
        
        total_weight = sum(severity_weights[issue.severity] for issue in issues)
        
        # Normalize by lines of code
        normalized_weight = total_weight / max(total_lines / 100, 1)
        
        return max(0, 1 - (normalized_weight / 100))
    
    def _calculate_performance_score(self, issues: List[PerformanceIssue], total_lines: int) -> float:
        """Calculate overall performance score (0-1)"""
        
        if not issues:
            return 1.0
        
        impact_weights = {
            PerformanceImpact.CRITICAL: 10,
            PerformanceImpact.HIGH: 5,
            PerformanceImpact.MEDIUM: 2,
            PerformanceImpact.LOW: 1,
            PerformanceImpact.NEGLIGIBLE: 0.5
        }
        
        total_weight = sum(impact_weights[issue.impact] for issue in issues)
        normalized_weight = total_weight / max(total_lines / 100, 1)
        
        return max(0, 1 - (normalized_weight / 100))
    
    def _calculate_quality_score(self, issues: List[CodeQualityIssue], file_analyses: List[FileAnalysis]) -> float:
        """Calculate overall code quality score (0-1)"""
        
        if not file_analyses:
            return 0.0
        
        # Average maintainability index
        avg_maintainability = sum(fa.maintainability_index for fa in file_analyses) / len(file_analyses)
        
        # Penalty for quality issues
        level_weights = {
            CodeQualityLevel.POOR: 5,
            CodeQualityLevel.NEEDS_IMPROVEMENT: 2,
            CodeQualityLevel.ACCEPTABLE: 1,
            CodeQualityLevel.GOOD: 0.5,
            CodeQualityLevel.EXCELLENT: 0
        }
        
        issue_penalty = sum(level_weights.get(issue.level, 1) for issue in issues)
        
        # Combine maintainability and issue penalty
        return max(0, min(1, (avg_maintainability / 100) - (issue_penalty / 1000)))
    
    def _identify_hotspots(self, file_analyses: List[FileAnalysis]) -> List[str]:
        """Identify files with most issues (hotspots)"""
        
        file_scores = []
        
        for analysis in file_analyses:
            total_issues = (
                len(analysis.security_issues) * 3 +
                len(analysis.performance_issues) * 2 +
                len(analysis.quality_issues) * 1
            )
            
            if total_issues > 0:
                file_scores.append((str(Path(analysis.file_path).relative_to(self.project_root)), total_issues))
        
        # Sort by issue count and return top 5
        file_scores.sort(key=lambda x: x[1], reverse=True)
        return [f"{file} ({count} issues)" for file, count in file_scores[:5]]
    
    async def _generate_recommendations(self, security_issues: List[SecurityIssue], 
                                      performance_issues: List[PerformanceIssue],
                                      quality_issues: List[CodeQualityIssue],
                                      dependency_issues: List[DependencyIssue],
                                      architecture_analysis: Dict[str, Any]) -> List[str]:
        """Generate overall improvement recommendations"""
        
        recommendations = []
        
        # Security recommendations
        critical_security = [i for i in security_issues if i.severity == SecuritySeverity.CRITICAL]
        if critical_security:
            recommendations.append(f"🚨 URGENT: Address {len(critical_security)} critical security vulnerabilities immediately")
        
        high_security = [i for i in security_issues if i.severity == SecuritySeverity.HIGH]
        if high_security:
            recommendations.append(f"🔴 Address {len(high_security)} high-severity security issues")
        
        # Performance recommendations
        critical_perf = [i for i in performance_issues if i.impact == PerformanceImpact.CRITICAL]
        if critical_perf:
            recommendations.append(f"⚡ Address {len(critical_perf)} critical performance bottlenecks")
        
        # Quality recommendations
        poor_quality = [i for i in quality_issues if i.level == CodeQualityLevel.POOR]
        if poor_quality:
            recommendations.append(f"📝 Refactor {len(poor_quality)} poor-quality code sections")
        
        # Dependency recommendations
        if dependency_issues:
            recommendations.append(f"📦 Update {len(dependency_issues)} vulnerable dependencies")
        
        # Architecture recommendations
        if architecture_analysis['coupling_issues']:
            recommendations.append("🏗️ Reduce coupling between tightly-coupled modules")
        
        if architecture_analysis['srp_violations']:
            recommendations.append("📏 Break down large modules to improve single responsibility")
        
        # General recommendations
        if len(security_issues) == 0:
            recommendations.append("✅ Security: No major vulnerabilities detected - maintain current practices")
        
        if len(performance_issues) < 5:
            recommendations.append("✅ Performance: Code is generally well-optimized")
        
        return recommendations
    
    def generate_report(self, analysis: ProjectAnalysis, output_path: Optional[Path] = None) -> str:
        """Generate comprehensive self-analysis report"""
        
        report = []
        report.append("# Aura Self-Analysis Report")
        report.append("## Exhaustive Performance and Security Audit")
        report.append(f"Generated: {analysis.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Executive Summary
        report.append("## Executive Summary")
        report.append(f"- **Total Files Analyzed:** {analysis.total_files}")
        report.append(f"- **Lines of Code:** {analysis.total_lines:,}")
        report.append(f"- **Functions:** {analysis.total_functions}")
        report.append(f"- **Classes:** {analysis.total_classes}")
        report.append(f"- **Average Complexity:** {analysis.average_complexity:.2f}")
        report.append("")
        report.append(f"### Health Scores")
        report.append(f"- **Security Score:** {analysis.security_score:.2f}/1.0 ({'✅ Excellent' if analysis.security_score > 0.9 else '⚠️ Needs Attention' if analysis.security_score > 0.7 else '🚨 Critical'})")
        report.append(f"- **Performance Score:** {analysis.performance_score:.2f}/1.0 ({'✅ Excellent' if analysis.performance_score > 0.9 else '⚠️ Needs Attention' if analysis.performance_score > 0.7 else '🚨 Critical'})")
        report.append(f"- **Quality Score:** {analysis.quality_score:.2f}/1.0 ({'✅ Excellent' if analysis.quality_score > 0.9 else '⚠️ Needs Attention' if analysis.quality_score > 0.7 else '🚨 Critical'})")
        report.append("")
        
        # Security Analysis
        report.append("## Security Analysis")
        report.append(f"**Total Security Issues:** {len(analysis.all_security_issues)}")
        
        if analysis.all_security_issues:
            severity_counts = {}
            for issue in analysis.all_security_issues:
                severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
            
            for severity, count in severity_counts.items():
                emoji = "🚨" if severity == SecuritySeverity.CRITICAL else "🔴" if severity == SecuritySeverity.HIGH else "🟡" if severity == SecuritySeverity.MEDIUM else "🟢"
                report.append(f"- {emoji} **{severity.value.title()}:** {count}")
            
            report.append("")
            report.append("### Critical Security Issues")
            critical_issues = [i for i in analysis.all_security_issues if i.severity == SecuritySeverity.CRITICAL]
            if critical_issues:
                for issue in critical_issues[:5]:  # Show top 5
                    report.append(f"- **{Path(issue.file_path).name}:{issue.line_number}** - {issue.description}")
            else:
                report.append("No critical security issues found ✅")
        else:
            report.append("No security issues detected ✅")
        
        report.append("")
        
        # Performance Analysis
        report.append("## Performance Analysis")
        report.append(f"**Total Performance Issues:** {len(analysis.all_performance_issues)}")
        
        if analysis.all_performance_issues:
            impact_counts = {}
            for issue in analysis.all_performance_issues:
                impact_counts[issue.impact] = impact_counts.get(issue.impact, 0) + 1
            
            for impact, count in impact_counts.items():
                emoji = "🚨" if impact == PerformanceImpact.CRITICAL else "🔴" if impact == PerformanceImpact.HIGH else "🟡" if impact == PerformanceImpact.MEDIUM else "🟢"
                report.append(f"- {emoji} **{impact.value.title()}:** {count}")
            
            report.append("")
            report.append("### High Impact Performance Issues")
            high_impact = [i for i in analysis.all_performance_issues if i.impact in [PerformanceImpact.CRITICAL, PerformanceImpact.HIGH]]
            if high_impact:
                for issue in high_impact[:5]:
                    report.append(f"- **{Path(issue.file_path).name}:{issue.line_number}** - {issue.description}")
            else:
                report.append("No high-impact performance issues found ✅")
        else:
            report.append("No performance issues detected ✅")
        
        report.append("")
        
        # Code Quality Analysis
        report.append("## Code Quality Analysis")
        report.append(f"**Total Quality Issues:** {len(analysis.all_quality_issues)}")
        
        if analysis.all_quality_issues:
            level_counts = {}
            for issue in analysis.all_quality_issues:
                level_counts[issue.level] = level_counts.get(issue.level, 0) + 1
            
            for level, count in level_counts.items():
                emoji = "🚨" if level == CodeQualityLevel.POOR else "🟡" if level == CodeQualityLevel.NEEDS_IMPROVEMENT else "🟢"
                report.append(f"- {emoji} **{level.value.replace('_', ' ').title()}:** {count}")
        else:
            report.append("No significant quality issues detected ✅")
        
        report.append("")
        
        # Architecture Analysis
        report.append("## Architecture Analysis")
        arch = analysis.architecture_analysis
        report.append(f"- **Architecture Score:** {arch['architecture_score']}/100")
        report.append(f"- **Average Module Complexity:** {arch['average_complexity']:.2f}")
        
        if arch['coupling_issues']:
            report.append(f"- **Coupling Issues:** {len(arch['coupling_issues'])}")
            for issue in arch['coupling_issues'][:3]:
                report.append(f"  - {issue}")
        
        if arch['srp_violations']:
            report.append(f"- **SRP Violations:** {len(arch['srp_violations'])}")
            for violation in arch['srp_violations'][:3]:
                report.append(f"  - {violation}")
        
        report.append("")
        
        # Hotspots
        if analysis.hotspots:
            report.append("## Code Hotspots")
            report.append("Files requiring immediate attention:")
            for hotspot in analysis.hotspots:
                report.append(f"- {hotspot}")
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        for i, rec in enumerate(analysis.recommendations, 1):
            report.append(f"{i}. {rec}")
        
        report.append("")
        report.append("---")
        report.append("*This analysis was conducted by Aura's self-reflection capabilities*")
        
        report_text = "\n".join(report)
        
        if output_path:
            output_path.write_text(report_text)
        
        return report_text


async def run_self_analysis():
    """Run comprehensive self-analysis of Aura codebase"""
    
    # Initialize configuration and LLM provider
    config = AuraConfig()
    
    # Use mock LLM provider for testing
    from ..planning.test_parser_mock import MockLLMProvider
    llm_provider = MockLLMProvider()
    
    # Initialize self-analyzer
    analyzer = AuraSelfAnalyzer(config, llm_provider)
    
    print("🔍 Initiating Aura Self-Analysis...")
    print("Turn Your Gaze Inward: Conducting exhaustive performance and security audit")
    
    # Perform analysis
    analysis = await analyzer.analyze_project()
    
    # Generate report
    report_path = Path("/home/greenantix/AI/LLMdiver/aura/intelligence/aura_self_analysis_report.md")
    report = analyzer.generate_report(analysis, report_path)
    
    # Save detailed results
    results_path = Path("/home/greenantix/AI/LLMdiver/aura/intelligence/aura_self_analysis_results.json")
    results = {
        'timestamp': analysis.analysis_timestamp.isoformat(),
        'summary': {
            'total_files': analysis.total_files,
            'total_lines': analysis.total_lines,
            'security_score': analysis.security_score,
            'performance_score': analysis.performance_score,
            'quality_score': analysis.quality_score
        },
        'security_issues': [
            {
                'file': issue.file_path,
                'line': issue.line_number,
                'severity': issue.severity.value,
                'type': issue.issue_type,
                'description': issue.description
            }
            for issue in analysis.all_security_issues
        ],
        'performance_issues': [
            {
                'file': issue.file_path,
                'line': issue.line_number,
                'impact': issue.impact.value,
                'type': issue.issue_type,
                'description': issue.description
            }
            for issue in analysis.all_performance_issues
        ],
        'quality_issues': [
            {
                'file': issue.file_path,
                'line': issue.line_number,
                'level': issue.level.value,
                'type': issue.issue_type,
                'description': issue.description
            }
            for issue in analysis.all_quality_issues
        ],
        'recommendations': analysis.recommendations
    }
    
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Display summary
    print(f"\n📊 Self-Analysis Complete!")
    print(f"📁 Analyzed {analysis.total_files} files ({analysis.total_lines:,} lines of code)")
    print(f"🔒 Security Score: {analysis.security_score:.2f}/1.0")
    print(f"⚡ Performance Score: {analysis.performance_score:.2f}/1.0")
    print(f"📝 Quality Score: {analysis.quality_score:.2f}/1.0")
    print(f"🚨 Security Issues: {len(analysis.all_security_issues)}")
    print(f"⚡ Performance Issues: {len(analysis.all_performance_issues)}")
    print(f"📝 Quality Issues: {len(analysis.all_quality_issues)}")
    print(f"\n📋 Report saved to: {report_path}")
    print(f"💾 Results saved to: {results_path}")
    
    return analysis


if __name__ == "__main__":
    asyncio.run(run_self_analysis())