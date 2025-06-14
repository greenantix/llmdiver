"""
Go AST Analyzer - Deep Analysis of Go Language Constructs
Mastery of Concurrency, Performance, and Go Ecosystem Patterns
"""

import asyncio
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import ast

from ...core.config import AuraConfig
from ...llm.providers import LLMProvider


class GoConstructType(Enum):
    PACKAGE = "package"
    IMPORT = "import"
    FUNCTION = "function"
    METHOD = "method"
    STRUCT = "struct"
    INTERFACE = "interface"
    VARIABLE = "variable"
    CONSTANT = "constant"
    GOROUTINE = "goroutine"
    CHANNEL = "channel"
    SELECT = "select"
    MUTEX = "mutex"
    TYPE_ALIAS = "type_alias"
    DEFER = "defer"
    PANIC = "panic"
    RECOVER = "recover"


class ConcurrencyPattern(Enum):
    WORKER_POOL = "worker_pool"
    FAN_OUT_FAN_IN = "fan_out_fan_in"
    PIPELINE = "pipeline"
    PRODUCER_CONSUMER = "producer_consumer"
    RATE_LIMITER = "rate_limiter"
    TIMEOUT_PATTERN = "timeout_pattern"
    CONTEXT_CANCELLATION = "context_cancellation"
    SYNC_ONCE = "sync_once"
    WAITGROUP = "waitgroup"


class PerformanceFlag(Enum):
    MEMORY_LEAK = "memory_leak"
    GOROUTINE_LEAK = "goroutine_leak"
    BLOCKING_OPERATION = "blocking_operation"
    INEFFICIENT_ALLOCATION = "inefficient_allocation"
    MISSING_CONTEXT = "missing_context"
    UNBUFFERED_CHANNEL = "unbuffered_channel"
    REFLECTION_OVERUSE = "reflection_overuse"
    STRING_CONCATENATION = "string_concatenation"


@dataclass
class GoConstruct:
    name: str
    construct_type: GoConstructType
    start_line: int
    end_line: int
    signature: str
    docstring: Optional[str] = None
    parameters: List[Dict[str, str]] = field(default_factory=list)
    return_types: List[str] = field(default_factory=list)
    receivers: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    concurrency_patterns: List[ConcurrencyPattern] = field(default_factory=list)
    performance_flags: List[PerformanceFlag] = field(default_factory=list)
    complexity_score: float = 0.0
    is_exported: bool = False
    is_generic: bool = False
    generic_constraints: List[str] = field(default_factory=list)


@dataclass
class GoPackageInfo:
    name: str
    path: str
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    internal_dependencies: List[str] = field(default_factory=list)
    external_dependencies: List[str] = field(default_factory=list)
    go_version: Optional[str] = None
    module_path: Optional[str] = None


@dataclass
class ConcurrencyAnalysis:
    goroutine_count: int
    channel_operations: List[Dict[str, Any]]
    mutex_usage: List[Dict[str, Any]]
    waitgroup_usage: List[Dict[str, Any]]
    context_usage: List[Dict[str, Any]]
    detected_patterns: List[ConcurrencyPattern]
    potential_races: List[str]
    deadlock_risks: List[str]
    performance_recommendations: List[str]


@dataclass
class GoFileAnalysis:
    file_path: str
    package_info: GoPackageInfo
    constructs: List[GoConstruct]
    concurrency_analysis: ConcurrencyAnalysis
    performance_analysis: Dict[str, Any]
    security_analysis: Dict[str, Any]
    test_coverage: Dict[str, float]
    complexity_metrics: Dict[str, float]
    recommendations: List[str]
    analysis_timestamp: datetime


class GoASTAnalyzer:
    def __init__(self, config: AuraConfig, llm_provider: LLMProvider):
        self.config = config
        self.llm_provider = llm_provider
        self.analysis_patterns = self._load_analysis_patterns()
        
    def _load_analysis_patterns(self) -> Dict[str, str]:
        """Load Go-specific analysis patterns"""
        return {
            'concurrency_analysis': """
Analyze this Go code for concurrency patterns and potential issues:

```go
{code}
```

Identify:
1. Goroutine usage patterns
2. Channel operations and patterns
3. Mutex and synchronization primitives
4. Context usage for cancellation/timeouts
5. Potential race conditions
6. Deadlock risks
7. Performance bottlenecks in concurrent code

Provide analysis in JSON format:
{
  "goroutine_patterns": [
    {
      "pattern": "worker_pool|fan_out_fan_in|pipeline",
      "location": "line_number",
      "description": "Pattern description",
      "efficiency": "high|medium|low",
      "recommendations": ["recommendation1", "recommendation2"]
    }
  ],
  "concurrency_issues": [
    {
      "type": "race_condition|deadlock|goroutine_leak",
      "location": "line_number", 
      "severity": "high|medium|low",
      "description": "Issue description",
      "fix_suggestion": "How to fix"
    }
  ],
  "performance_insights": [
    {
      "insight": "Performance observation",
      "impact": "high|medium|low",
      "recommendation": "Optimization suggestion"
    }
  ]
}

Focus on Go-specific concurrency best practices and common pitfalls.
""",
            
            'memory_analysis': """
Analyze this Go code for memory usage patterns and potential issues:

```go
{code}
```

Examine:
1. Memory allocation patterns
2. Slice and map usage efficiency
3. String manipulation efficiency
4. Interface{} usage impact
5. Reflection usage
6. Garbage collection pressure
7. Memory leaks potential

Provide analysis in JSON format:
{
  "memory_patterns": [
    {
      "pattern": "Description of memory pattern",
      "location": "line_number",
      "efficiency": "high|medium|low",
      "memory_impact": "high|medium|low",
      "recommendations": ["recommendation1"]
    }
  ],
  "optimization_opportunities": [
    {
      "type": "allocation|gc_pressure|memory_leak",
      "location": "line_number",
      "current_approach": "Current implementation",
      "optimized_approach": "Suggested improvement",
      "impact": "Performance impact description"
    }
  ]
}
""",
            
            'security_analysis': """
Analyze this Go code for security vulnerabilities and best practices:

```go
{code}
```

Check for:
1. Input validation and sanitization
2. SQL injection vulnerabilities
3. XSS prevention
4. CSRF protection
5. Authentication/authorization patterns
6. Cryptographic usage
7. File system access security
8. Network security patterns

Provide security analysis in JSON format:
{
  "security_issues": [
    {
      "type": "injection|xss|auth|crypto|file_access",
      "severity": "critical|high|medium|low",
      "location": "line_number",
      "description": "Security issue description",
      "recommendation": "How to fix",
      "cwe_id": "CWE-XX if applicable"
    }
  ],
  "best_practices": [
    {
      "practice": "Security best practice",
      "implemented": true,
      "location": "line_number",
      "notes": "Implementation notes"
    }
  ]
}
""",
            
            'architecture_analysis': """
Analyze this Go code for architectural patterns and design quality:

```go
{code}
```

Evaluate:
1. Package structure and organization
2. Interface design and usage
3. Dependency injection patterns
4. Error handling strategies
5. Configuration management
6. Logging and observability
7. Testing patterns
8. Clean architecture principles

Provide architectural analysis in JSON format:
{
  "architecture_patterns": [
    {
      "pattern": "dependency_injection|clean_architecture|hexagonal",
      "quality": "excellent|good|needs_improvement",
      "location": "line_number",
      "description": "Pattern implementation",
      "recommendations": ["improvement1"]
    }
  ],
  "design_quality": {
    "cohesion": "high|medium|low",
    "coupling": "low|medium|high", 
    "maintainability": "high|medium|low",
    "testability": "high|medium|low",
    "recommendations": ["design_improvement1"]
  }
}
"""
        }

    async def analyze_go_file(self, file_path: Path) -> GoFileAnalysis:
        """Comprehensive analysis of a Go source file"""
        
        if not file_path.exists():
            raise FileNotFoundError(f"Go file not found: {file_path}")
        
        content = file_path.read_text(encoding='utf-8')
        
        # Parse basic Go constructs
        constructs = await self._parse_go_constructs(content)
        
        # Analyze package information
        package_info = await self._analyze_package_info(file_path, content)
        
        # Perform specialized analyses
        concurrency_analysis = await self._analyze_concurrency(content)
        performance_analysis = await self._analyze_performance(content)
        security_analysis = await self._analyze_security(content)
        
        # Calculate complexity metrics
        complexity_metrics = await self._calculate_complexity_metrics(content, constructs)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            constructs, concurrency_analysis, performance_analysis, security_analysis
        )
        
        # Analyze test coverage (if test files exist)
        test_coverage = await self._analyze_test_coverage(file_path)
        
        return GoFileAnalysis(
            file_path=str(file_path),
            package_info=package_info,
            constructs=constructs,
            concurrency_analysis=concurrency_analysis,
            performance_analysis=performance_analysis,
            security_analysis=security_analysis,
            test_coverage=test_coverage,
            complexity_metrics=complexity_metrics,
            recommendations=recommendations,
            analysis_timestamp=datetime.now()
        )

    async def _parse_go_constructs(self, content: str) -> List[GoConstruct]:
        """Parse Go language constructs using AST-like analysis"""
        
        constructs = []
        lines = content.split('\n')
        
        # Parse package declaration
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Package declaration
            if line.startswith('package '):
                package_name = line.split()[1]
                constructs.append(GoConstruct(
                    name=package_name,
                    construct_type=GoConstructType.PACKAGE,
                    start_line=i + 1,
                    end_line=i + 1,
                    signature=line,
                    is_exported=True
                ))
            
            # Function declarations
            elif re.match(r'func\s+(\w+)', line):
                func_match = re.match(r'func\s+(\w+)\s*\(([^)]*)\)\s*(\([^)]*\))?\s*(\w+)?\s*{?', line)
                if func_match:
                    func_name = func_match.group(1)
                    params = func_match.group(2) or ""
                    returns = func_match.group(3) or func_match.group(4) or ""
                    
                    # Find function end
                    end_line = self._find_function_end(lines, i)
                    
                    # Analyze function complexity and patterns
                    func_content = '\n'.join(lines[i:end_line+1])
                    concurrency_patterns = self._detect_concurrency_patterns(func_content)
                    performance_flags = self._detect_performance_flags(func_content)
                    
                    constructs.append(GoConstruct(
                        name=func_name,
                        construct_type=GoConstructType.FUNCTION,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        signature=line,
                        parameters=self._parse_parameters(params),
                        return_types=self._parse_return_types(returns),
                        concurrency_patterns=concurrency_patterns,
                        performance_flags=performance_flags,
                        complexity_score=self._calculate_function_complexity(func_content),
                        is_exported=func_name[0].isupper()
                    ))
            
            # Method declarations (with receiver)
            elif re.match(r'func\s+\([^)]+\)\s+(\w+)', line):
                method_match = re.match(r'func\s+\(([^)]+)\)\s+(\w+)\s*\(([^)]*)\)\s*(\([^)]*\))?\s*(\w+)?\s*{?', line)
                if method_match:
                    receiver = method_match.group(1)
                    method_name = method_match.group(2)
                    params = method_match.group(3) or ""
                    returns = method_match.group(4) or method_match.group(5) or ""
                    
                    end_line = self._find_function_end(lines, i)
                    func_content = '\n'.join(lines[i:end_line+1])
                    
                    constructs.append(GoConstruct(
                        name=method_name,
                        construct_type=GoConstructType.METHOD,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        signature=line,
                        parameters=self._parse_parameters(params),
                        return_types=self._parse_return_types(returns),
                        receivers=[receiver.strip()],
                        concurrency_patterns=self._detect_concurrency_patterns(func_content),
                        performance_flags=self._detect_performance_flags(func_content),
                        complexity_score=self._calculate_function_complexity(func_content),
                        is_exported=method_name[0].isupper()
                    ))
            
            # Struct declarations
            elif re.match(r'type\s+(\w+)\s+struct', line):
                struct_match = re.match(r'type\s+(\w+)\s+struct', line)
                if struct_match:
                    struct_name = struct_match.group(1)
                    end_line = self._find_struct_end(lines, i)
                    
                    constructs.append(GoConstruct(
                        name=struct_name,
                        construct_type=GoConstructType.STRUCT,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        signature=line,
                        is_exported=struct_name[0].isupper()
                    ))
            
            # Interface declarations
            elif re.match(r'type\s+(\w+)\s+interface', line):
                interface_match = re.match(r'type\s+(\w+)\s+interface', line)
                if interface_match:
                    interface_name = interface_match.group(1)
                    end_line = self._find_interface_end(lines, i)
                    
                    constructs.append(GoConstruct(
                        name=interface_name,
                        construct_type=GoConstructType.INTERFACE,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        signature=line,
                        is_exported=interface_name[0].isupper()
                    ))
        
        return constructs

    def _find_function_end(self, lines: List[str], start_idx: int) -> int:
        """Find the end of a function by matching braces"""
        brace_count = 0
        for i in range(start_idx, len(lines)):
            line = lines[i]
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and '{' in lines[start_idx]:
                return i
        return start_idx

    def _find_struct_end(self, lines: List[str], start_idx: int) -> int:
        """Find the end of a struct declaration"""
        brace_count = 0
        for i in range(start_idx, len(lines)):
            line = lines[i]
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and '{' in line:
                return i
        return start_idx

    def _find_interface_end(self, lines: List[str], start_idx: int) -> int:
        """Find the end of an interface declaration"""
        return self._find_struct_end(lines, start_idx)

    def _parse_parameters(self, params_str: str) -> List[Dict[str, str]]:
        """Parse function parameters"""
        if not params_str.strip():
            return []
        
        params = []
        # Simple parsing - could be enhanced with proper Go parser
        param_parts = params_str.split(',')
        for part in param_parts:
            part = part.strip()
            if part:
                # Handle "name type" or just "type" format
                parts = part.split()
                if len(parts) >= 2:
                    params.append({'name': parts[0], 'type': ' '.join(parts[1:])})
                else:
                    params.append({'name': '', 'type': part})
        
        return params

    def _parse_return_types(self, returns_str: str) -> List[str]:
        """Parse function return types"""
        if not returns_str.strip():
            return []
        
        # Remove parentheses if present
        returns_str = returns_str.strip('()')
        if not returns_str:
            return []
        
        # Split by comma for multiple return values
        return [r.strip() for r in returns_str.split(',') if r.strip()]

    def _detect_concurrency_patterns(self, code: str) -> List[ConcurrencyPattern]:
        """Detect concurrency patterns in Go code"""
        patterns = []
        
        # Worker pool pattern
        if 'for range' in code and 'go func' in code and 'chan' in code:
            patterns.append(ConcurrencyPattern.WORKER_POOL)
        
        # Channel patterns
        if 'select {' in code:
            patterns.append(ConcurrencyPattern.FAN_OUT_FAN_IN)
        
        # Pipeline pattern
        if code.count('chan') > 1 and 'range' in code:
            patterns.append(ConcurrencyPattern.PIPELINE)
        
        # Context usage
        if 'context.' in code and ('Cancel' in code or 'Timeout' in code):
            patterns.append(ConcurrencyPattern.CONTEXT_CANCELLATION)
        
        # WaitGroup usage
        if 'sync.WaitGroup' in code or 'wg.Wait()' in code:
            patterns.append(ConcurrencyPattern.WAITGROUP)
        
        return patterns

    def _detect_performance_flags(self, code: str) -> List[PerformanceFlag]:
        """Detect potential performance issues"""
        flags = []
        
        # String concatenation in loops
        if 'for ' in code and ('+=' in code or '= ' in code and '+' in code):
            if 'string' in code:
                flags.append(PerformanceFlag.STRING_CONCATENATION)
        
        # Unbuffered channels
        if 'make(chan' in code and not re.search(r'make\(chan\s+\w+,\s*\d+\)', code):
            flags.append(PerformanceFlag.UNBUFFERED_CHANNEL)
        
        # Reflection usage
        if 'reflect.' in code:
            flags.append(PerformanceFlag.REFLECTION_OVERUSE)
        
        # Missing context
        if 'http.Get' in code or 'http.Post' in code:
            if 'context.' not in code:
                flags.append(PerformanceFlag.MISSING_CONTEXT)
        
        return flags

    def _calculate_function_complexity(self, code: str) -> float:
        """Calculate cyclomatic complexity for Go function"""
        complexity = 1  # Base complexity
        
        # Count decision points
        complexity += code.count('if ')
        complexity += code.count('for ')
        complexity += code.count('switch ')
        complexity += code.count('case ')
        complexity += code.count('&&')
        complexity += code.count('||')
        complexity += code.count('select {')
        
        # Normalize to 0-1 scale
        return min(complexity / 20.0, 1.0)

    async def _analyze_package_info(self, file_path: Path, content: str) -> GoPackageInfo:
        """Analyze Go package information"""
        
        package_name = ""
        imports = []
        
        lines = content.split('\n')
        in_import_block = False
        
        for line in lines:
            line = line.strip()
            
            # Package declaration
            if line.startswith('package '):
                package_name = line.split()[1]
            
            # Import statements
            elif line.startswith('import ('):
                in_import_block = True
            elif line == ')' and in_import_block:
                in_import_block = False
            elif in_import_block:
                # Clean import line
                import_line = line.strip('"').strip()
                if import_line and not import_line.startswith('//'):
                    imports.append(import_line)
            elif line.startswith('import '):
                # Single import
                import_match = re.search(r'import\s+"([^"]+)"', line)
                if import_match:
                    imports.append(import_match.group(1))
        
        # Determine go.mod info if available
        go_mod_path = file_path.parent
        while go_mod_path != go_mod_path.parent:
            if (go_mod_path / 'go.mod').exists():
                break
            go_mod_path = go_mod_path.parent
        
        module_path = None
        go_version = None
        
        if (go_mod_path / 'go.mod').exists():
            mod_content = (go_mod_path / 'go.mod').read_text()
            mod_match = re.search(r'module\s+(\S+)', mod_content)
            if mod_match:
                module_path = mod_match.group(1)
            
            version_match = re.search(r'go\s+(\d+\.\d+)', mod_content)
            if version_match:
                go_version = version_match.group(1)
        
        return GoPackageInfo(
            name=package_name,
            path=str(file_path.parent),
            imports=imports,
            module_path=module_path,
            go_version=go_version
        )

    async def _analyze_concurrency(self, content: str) -> ConcurrencyAnalysis:
        """Analyze concurrency patterns and issues"""
        
        prompt = self.analysis_patterns['concurrency_analysis'].replace('{code}', content)
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            analysis_data = json.loads(response)
            
            # Extract detected patterns
            detected_patterns = []
            for pattern_info in analysis_data.get('goroutine_patterns', []):
                pattern_name = pattern_info.get('pattern', '')
                if pattern_name:
                    try:
                        detected_patterns.append(ConcurrencyPattern(pattern_name))
                    except ValueError:
                        pass  # Unknown pattern
            
            return ConcurrencyAnalysis(
                goroutine_count=content.count('go '),
                channel_operations=self._extract_channel_operations(content),
                mutex_usage=self._extract_mutex_usage(content),
                waitgroup_usage=self._extract_waitgroup_usage(content),
                context_usage=self._extract_context_usage(content),
                detected_patterns=detected_patterns,
                potential_races=[issue['description'] for issue in analysis_data.get('concurrency_issues', []) if issue.get('type') == 'race_condition'],
                deadlock_risks=[issue['description'] for issue in analysis_data.get('concurrency_issues', []) if issue.get('type') == 'deadlock'],
                performance_recommendations=[insight['recommendation'] for insight in analysis_data.get('performance_insights', [])]
            )
            
        except json.JSONDecodeError:
            # Fallback analysis
            return ConcurrencyAnalysis(
                goroutine_count=content.count('go '),
                channel_operations=[],
                mutex_usage=[],
                waitgroup_usage=[],
                context_usage=[],
                detected_patterns=[],
                potential_races=[],
                deadlock_risks=[],
                performance_recommendations=[]
            )

    def _extract_channel_operations(self, content: str) -> List[Dict[str, Any]]:
        """Extract channel operations from code"""
        operations = []
        
        # Find channel sends
        sends = re.findall(r'(\w+)\s*<-\s*(\w+)', content)
        for send in sends:
            operations.append({
                'type': 'send',
                'channel': send[0],
                'value': send[1]
            })
        
        # Find channel receives
        receives = re.findall(r'(\w+)\s*:?=\s*<-\s*(\w+)', content)
        for receive in receives:
            operations.append({
                'type': 'receive',
                'variable': receive[0],
                'channel': receive[1]
            })
        
        return operations

    def _extract_mutex_usage(self, content: str) -> List[Dict[str, Any]]:
        """Extract mutex usage patterns"""
        usage = []
        
        # Find mutex locks
        locks = re.findall(r'(\w+)\.Lock\(\)', content)
        unlocks = re.findall(r'(\w+)\.Unlock\(\)', content)
        
        for lock in locks:
            usage.append({
                'type': 'lock',
                'mutex': lock
            })
        
        for unlock in unlocks:
            usage.append({
                'type': 'unlock',
                'mutex': unlock
            })
        
        return usage

    def _extract_waitgroup_usage(self, content: str) -> List[Dict[str, Any]]:
        """Extract WaitGroup usage patterns"""
        usage = []
        
        adds = re.findall(r'(\w+)\.Add\((\d+)\)', content)
        dones = re.findall(r'(\w+)\.Done\(\)', content)
        waits = re.findall(r'(\w+)\.Wait\(\)', content)
        
        for add in adds:
            usage.append({
                'type': 'add',
                'waitgroup': add[0],
                'count': int(add[1])
            })
        
        for done in dones:
            usage.append({
                'type': 'done',
                'waitgroup': done
            })
        
        for wait in waits:
            usage.append({
                'type': 'wait',
                'waitgroup': wait
            })
        
        return usage

    def _extract_context_usage(self, content: str) -> List[Dict[str, Any]]:
        """Extract context usage patterns"""
        usage = []
        
        # Find context creation
        contexts = re.findall(r'context\.(\w+)\(', content)
        for ctx in contexts:
            usage.append({
                'type': 'creation',
                'method': ctx
            })
        
        # Find context usage in function parameters
        ctx_params = re.findall(r'func\s+\w+\([^)]*context\.Context[^)]*\)', content)
        usage.extend([{'type': 'parameter'} for _ in ctx_params])
        
        return usage

    async def _analyze_performance(self, content: str) -> Dict[str, Any]:
        """Analyze performance characteristics"""
        
        prompt = self.analysis_patterns['memory_analysis'].replace('{code}', content)
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                'memory_patterns': [],
                'optimization_opportunities': []
            }

    async def _analyze_security(self, content: str) -> Dict[str, Any]:
        """Analyze security aspects"""
        
        prompt = self.analysis_patterns['security_analysis'].replace('{code}', content)
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                'security_issues': [],
                'best_practices': []
            }

    async def _calculate_complexity_metrics(self, content: str, constructs: List[GoConstruct]) -> Dict[str, float]:
        """Calculate various complexity metrics"""
        
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip() and not line.strip().startswith('//')]
        
        metrics = {
            'lines_of_code': len(non_empty_lines),
            'cyclomatic_complexity': sum(construct.complexity_score for construct in constructs if construct.construct_type in [GoConstructType.FUNCTION, GoConstructType.METHOD]),
            'function_count': len([c for c in constructs if c.construct_type == GoConstructType.FUNCTION]),
            'method_count': len([c for c in constructs if c.construct_type == GoConstructType.METHOD]),
            'struct_count': len([c for c in constructs if c.construct_type == GoConstructType.STRUCT]),
            'interface_count': len([c for c in constructs if c.construct_type == GoConstructType.INTERFACE]),
            'exported_symbols': len([c for c in constructs if c.is_exported]),
            'goroutine_density': content.count('go ') / max(len(non_empty_lines), 1),
            'channel_density': content.count('chan ') / max(len(non_empty_lines), 1)
        }
        
        return metrics

    async def _generate_recommendations(self, constructs: List[GoConstruct], concurrency_analysis: ConcurrencyAnalysis, performance_analysis: Dict[str, Any], security_analysis: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        
        recommendations = []
        
        # Concurrency recommendations
        if concurrency_analysis.goroutine_count > 0 and not concurrency_analysis.context_usage:
            recommendations.append("Consider using context.Context for goroutine cancellation and timeout handling")
        
        if len(concurrency_analysis.potential_races) > 0:
            recommendations.append(f"Review and fix {len(concurrency_analysis.potential_races)} potential race conditions")
        
        if len(concurrency_analysis.deadlock_risks) > 0:
            recommendations.append(f"Address {len(concurrency_analysis.deadlock_risks)} potential deadlock risks")
        
        # Performance recommendations
        performance_flags = [flag for construct in constructs for flag in construct.performance_flags]
        if PerformanceFlag.STRING_CONCATENATION in performance_flags:
            recommendations.append("Use strings.Builder for efficient string concatenation in loops")
        
        if PerformanceFlag.UNBUFFERED_CHANNEL in performance_flags:
            recommendations.append("Consider using buffered channels to prevent goroutine blocking")
        
        # Security recommendations
        security_issues = security_analysis.get('security_issues', [])
        high_severity_issues = [issue for issue in security_issues if issue.get('severity') in ['critical', 'high']]
        if high_severity_issues:
            recommendations.append(f"Address {len(high_severity_issues)} high-severity security issues")
        
        # Code quality recommendations
        complex_functions = [c for c in constructs if c.complexity_score > 0.7]
        if complex_functions:
            recommendations.append(f"Refactor {len(complex_functions)} high-complexity functions for better maintainability")
        
        return recommendations

    async def _analyze_test_coverage(self, file_path: Path) -> Dict[str, float]:
        """Analyze test coverage for the Go file"""
        
        # Look for corresponding test file
        test_file_path = file_path.parent / (file_path.stem + '_test.go')
        
        if not test_file_path.exists():
            return {'test_coverage': 0.0, 'test_functions': 0}
        
        test_content = test_file_path.read_text()
        test_functions = len(re.findall(r'func\s+Test\w+', test_content))
        
        # Simple heuristic for coverage estimation
        source_functions = len(re.findall(r'func\s+\w+', file_path.read_text()))
        coverage = min(test_functions / max(source_functions, 1), 1.0)
        
        return {
            'test_coverage': coverage,
            'test_functions': test_functions,
            'source_functions': source_functions
        }

    async def analyze_go_project(self, project_path: Path) -> Dict[str, GoFileAnalysis]:
        """Analyze an entire Go project"""
        
        analyses = {}
        
        # Find all Go files
        go_files = list(project_path.rglob('*.go'))
        
        # Exclude vendor and test files for main analysis
        source_files = [f for f in go_files if 'vendor' not in str(f) and not f.name.endswith('_test.go')]
        
        for go_file in source_files:
            try:
                analysis = await self.analyze_go_file(go_file)
                relative_path = go_file.relative_to(project_path)
                analyses[str(relative_path)] = analysis
            except Exception as e:
                print(f"Error analyzing {go_file}: {e}")
        
        return analyses

    def generate_go_analysis_report(self, analyses: Dict[str, GoFileAnalysis], output_path: Optional[Path] = None) -> str:
        """Generate comprehensive Go analysis report"""
        
        report = []
        report.append("# Go Project Analysis Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary statistics
        total_files = len(analyses)
        total_functions = sum(len([c for c in analysis.constructs if c.construct_type == GoConstructType.FUNCTION]) for analysis in analyses.values())
        total_methods = sum(len([c for c in analysis.constructs if c.construct_type == GoConstructType.METHOD]) for analysis in analyses.values())
        total_structs = sum(len([c for c in analysis.constructs if c.construct_type == GoConstructType.STRUCT]) for analysis in analyses.values())
        total_interfaces = sum(len([c for c in analysis.constructs if c.construct_type == GoConstructType.INTERFACE]) for analysis in analyses.values())
        
        report.append("## Project Summary")
        report.append(f"- **Files analyzed:** {total_files}")
        report.append(f"- **Functions:** {total_functions}")
        report.append(f"- **Methods:** {total_methods}")
        report.append(f"- **Structs:** {total_structs}")
        report.append(f"- **Interfaces:** {total_interfaces}")
        report.append("")
        
        # Concurrency analysis summary
        report.append("## Concurrency Analysis")
        total_goroutines = sum(analysis.concurrency_analysis.goroutine_count for analysis in analyses.values())
        files_with_concurrency = len([a for a in analyses.values() if a.concurrency_analysis.goroutine_count > 0])
        
        report.append(f"- **Total goroutines:** {total_goroutines}")
        report.append(f"- **Files with concurrency:** {files_with_concurrency}")
        report.append("")
        
        # Security and performance issues
        all_security_issues = []
        all_performance_issues = []
        
        for analysis in analyses.values():
            all_security_issues.extend(analysis.security_analysis.get('security_issues', []))
            all_performance_issues.extend([flag.value for construct in analysis.constructs for flag in construct.performance_flags])
        
        report.append("## Issues Summary")
        report.append(f"- **Security issues:** {len(all_security_issues)}")
        report.append(f"- **Performance flags:** {len(all_performance_issues)}")
        report.append("")
        
        # Detailed file analysis
        report.append("## File Analysis Details")
        for file_path, analysis in analyses.items():
            report.append(f"### {file_path}")
            report.append(f"**Package:** {analysis.package_info.name}")
            report.append(f"**Constructs:** {len(analysis.constructs)}")
            report.append(f"**Complexity Score:** {analysis.complexity_metrics.get('cyclomatic_complexity', 0):.2f}")
            
            if analysis.concurrency_analysis.goroutine_count > 0:
                report.append(f"**Goroutines:** {analysis.concurrency_analysis.goroutine_count}")
                report.append(f"**Concurrency Patterns:** {', '.join(p.value for p in analysis.concurrency_analysis.detected_patterns)}")
            
            if analysis.recommendations:
                report.append("**Recommendations:**")
                for rec in analysis.recommendations[:3]:  # Show top 3
                    report.append(f"- {rec}")
            
            report.append("")
        
        report_text = "\n".join(report)
        
        if output_path:
            output_path.write_text(report_text)
        
        return report_text