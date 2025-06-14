"""
Rust Memory Safety Analyzer - Deep Understanding of Ownership and Lifetimes
Mastery of Zero-Cost Abstractions and Fearless Concurrency
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

from ...core.config import AuraConfig
from ...llm.providers import LLMProvider


class RustConstructType(Enum):
    FUNCTION = "function"
    METHOD = "method"
    STRUCT = "struct"
    ENUM = "enum"
    TRAIT = "trait"
    IMPL_BLOCK = "impl_block"
    MODULE = "module"
    MACRO = "macro"
    CONST = "const"
    STATIC = "static"
    TYPE_ALIAS = "type_alias"
    CLOSURE = "closure"


class OwnershipPattern(Enum):
    OWNED = "owned"
    BORROWED = "borrowed"
    MUTABLE_BORROW = "mutable_borrow"
    MOVE_SEMANTICS = "move_semantics"
    CLONE = "clone"
    COPY = "copy"
    RC_REFCELL = "rc_refcell"
    ARC_MUTEX = "arc_mutex"
    BOX_HEAP = "box_heap"


class LifetimePattern(Enum):
    STATIC = "static"
    EXPLICIT = "explicit"
    ELIDED = "elided"
    HIGHER_RANKED = "higher_ranked"
    ANONYMOUS = "anonymous"


class ConcurrencyPattern(Enum):
    ASYNC_AWAIT = "async_await"
    TOKIO_SPAWN = "tokio_spawn"
    THREAD_SPAWN = "thread_spawn"
    CHANNEL_MPSC = "channel_mpsc"
    CHANNEL_ONESHOT = "channel_oneshot"
    MUTEX_STD = "mutex_std"
    RWLOCK = "rwlock"
    ATOMIC = "atomic"
    RAYON_PARALLEL = "rayon_parallel"


class MemorySafetyFlag(Enum):
    UNSAFE_BLOCK = "unsafe_block"
    RAW_POINTER = "raw_pointer"
    FFI_CALL = "ffi_call"
    TRANSMUTE = "transmute"
    DANGLING_REFERENCE = "dangling_reference"
    DOUBLE_FREE = "double_free"
    USE_AFTER_MOVE = "use_after_move"
    MUTABLE_ALIASING = "mutable_aliasing"


class PerformanceFlag(Enum):
    UNNECESSARY_CLONE = "unnecessary_clone"
    HEAP_ALLOCATION = "heap_allocation"
    RECURSIVE_CALL = "recursive_call"
    LARGE_STACK_OBJECT = "large_stack_object"
    INEFFICIENT_STRING_OPS = "inefficient_string_ops"
    ITERATOR_NOT_CHAINED = "iterator_not_chained"
    COLLECT_UNNECESSARY = "collect_unnecessary"


@dataclass
class RustConstruct:
    name: str
    construct_type: RustConstructType
    start_line: int
    end_line: int
    signature: str
    visibility: str = "private"  # pub, pub(crate), pub(super), private
    docstring: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    lifetimes: List[LifetimePattern] = field(default_factory=list)
    ownership_patterns: List[OwnershipPattern] = field(default_factory=list)
    concurrency_patterns: List[ConcurrencyPattern] = field(default_factory=list)
    memory_safety_flags: List[MemorySafetyFlag] = field(default_factory=list)
    performance_flags: List[PerformanceFlag] = field(default_factory=list)
    complexity_score: float = 0.0
    is_generic: bool = False
    generic_constraints: List[str] = field(default_factory=list)
    derives: List[str] = field(default_factory=list)
    is_async: bool = False
    is_unsafe: bool = False


@dataclass
class OwnershipAnalysis:
    owned_values: List[str]
    borrowed_values: List[str]
    mutable_borrows: List[str]
    moved_values: List[str]
    cloned_values: List[str]
    potential_issues: List[Dict[str, Any]]
    borrowing_violations: List[str]
    lifetime_issues: List[str]
    memory_efficiency_score: float


@dataclass
class ConcurrencyAnalysis:
    async_functions: List[str]
    spawn_points: List[Dict[str, Any]]
    channel_usage: List[Dict[str, Any]]
    shared_state: List[Dict[str, Any]]
    synchronization_primitives: List[str]
    potential_races: List[str]
    deadlock_risks: List[str]
    async_patterns: List[ConcurrencyPattern]
    thread_safety_score: float


@dataclass
class MemorySafetyAnalysis:
    unsafe_blocks: List[Dict[str, Any]]
    raw_pointer_usage: List[str]
    ffi_interactions: List[str]
    transmute_calls: List[str]
    potential_vulnerabilities: List[Dict[str, Any]]
    safety_score: float
    recommendations: List[str]


@dataclass
class RustFileAnalysis:
    file_path: str
    module_info: Dict[str, Any]
    constructs: List[RustConstruct]
    ownership_analysis: OwnershipAnalysis
    concurrency_analysis: ConcurrencyAnalysis
    memory_safety_analysis: MemorySafetyAnalysis
    performance_analysis: Dict[str, Any]
    error_handling_analysis: Dict[str, Any]
    trait_usage: Dict[str, Any]
    macro_usage: List[str]
    complexity_metrics: Dict[str, float]
    recommendations: List[str]
    analysis_timestamp: datetime


class RustMemoryAnalyzer:
    def __init__(self, config: AuraConfig, llm_provider: LLMProvider):
        self.config = config
        self.llm_provider = llm_provider
        self.analysis_patterns = self._load_analysis_patterns()
        
    def _load_analysis_patterns(self) -> Dict[str, str]:
        """Load Rust-specific analysis patterns"""
        return {
            'ownership_analysis': """
Analyze this Rust code for ownership and borrowing patterns:

```rust
{code}
```

Examine:
1. Ownership transfers (moves)
2. Borrowing patterns (&T and &mut T)
3. Lifetime annotations and elision
4. Clone/Copy usage efficiency
5. Reference counting (Rc, Arc) usage
6. Potential borrowing violations
7. Memory efficiency patterns

Provide analysis in JSON format:
{
  "ownership_patterns": [
    {
      "pattern": "owned|borrowed|mutable_borrow|move_semantics",
      "location": "line_number",
      "variable": "variable_name",
      "efficiency": "optimal|acceptable|inefficient",
      "recommendation": "Optimization suggestion"
    }
  ],
  "borrowing_issues": [
    {
      "type": "borrow_checker|lifetime|mutable_aliasing",
      "location": "line_number",
      "description": "Issue description",
      "severity": "error|warning|suggestion",
      "fix": "How to resolve"
    }
  ],
  "memory_efficiency": {
    "score": 0.85,
    "inefficiencies": ["unnecessary clones", "heap allocations"],
    "optimizations": ["Use references instead of clones"]
  }
}

Focus on Rust's unique ownership model and zero-cost abstractions.
""",
            
            'concurrency_analysis': """
Analyze this Rust code for concurrency patterns and thread safety:

```rust
{code}
```

Examine:
1. Async/await usage patterns
2. Thread spawning and management
3. Channel communication (mpsc, oneshot)
4. Shared state management (Arc, Mutex, RwLock)
5. Atomic operations
6. Data race prevention
7. Deadlock potential

Provide analysis in JSON format:
{
  "concurrency_patterns": [
    {
      "pattern": "async_await|thread_spawn|channel_communication",
      "location": "line_number",
      "description": "Pattern description",
      "thread_safety": "safe|unsafe|needs_review",
      "performance_impact": "low|medium|high"
    }
  ],
  "thread_safety_issues": [
    {
      "type": "data_race|deadlock|unsafe_sharing",
      "location": "line_number",
      "severity": "critical|high|medium",
      "description": "Issue description",
      "mitigation": "How to fix"
    }
  ],
  "async_patterns": [
    {
      "pattern": "Description of async pattern",
      "efficiency": "high|medium|low",
      "recommendations": ["improvement suggestions"]
    }
  ]
}
""",
            
            'memory_safety_analysis': """
Analyze this Rust code for memory safety and unsafe usage:

```rust
{code}
```

Examine:
1. Unsafe blocks and their necessity
2. Raw pointer dereferencing
3. FFI (Foreign Function Interface) calls
4. Transmute operations
5. Memory layout assumptions
6. Buffer overflow potential
7. Use-after-free prevention

Provide analysis in JSON format:
{
  "unsafe_analysis": [
    {
      "type": "unsafe_block|raw_pointer|ffi|transmute",
      "location": "line_number",
      "necessity": "required|avoidable|questionable",
      "safety_justification": "Why unsafe is used",
      "risk_level": "low|medium|high|critical",
      "alternatives": ["Safer alternatives if available"]
    }
  ],
  "memory_safety_score": 0.92,
  "vulnerabilities": [
    {
      "type": "buffer_overflow|use_after_free|double_free",
      "location": "line_number",
      "description": "Vulnerability description",
      "impact": "Potential impact",
      "mitigation": "How to fix"
    }
  ]
}
""",
            
            'performance_analysis': """
Analyze this Rust code for performance characteristics:

```rust
{code}
```

Examine:
1. Zero-cost abstractions usage
2. Allocation patterns (stack vs heap)
3. Iterator efficiency
4. String manipulation efficiency
5. Clone/copy overhead
6. Generic specialization
7. Compiler optimization opportunities

Provide analysis in JSON format:
{
  "performance_patterns": [
    {
      "pattern": "Description of performance pattern",
      "location": "line_number",
      "efficiency": "optimal|good|poor",
      "cost": "zero|low|medium|high",
      "optimization": "Suggested improvement"
    }
  ],
  "allocation_analysis": {
    "stack_allocations": 15,
    "heap_allocations": 3,
    "unnecessary_allocations": ["Vec::new() could be avoided"],
    "optimization_opportunities": ["Use iterators instead of collect()"]
  },
  "zero_cost_abstractions": [
    {
      "abstraction": "Iterator|Option|Result|Generic",
      "usage": "optimal|suboptimal",
      "notes": "Usage analysis"
    }
  ]
}
""",
            
            'error_handling_analysis': """
Analyze this Rust code for error handling patterns:

```rust
{code}
```

Examine:
1. Result<T, E> usage patterns
2. Option<T> handling
3. Error propagation (? operator)
4. Panic usage and appropriateness
5. Custom error types
6. Error conversion patterns
7. Recovery strategies

Provide analysis in JSON format:
{
  "error_patterns": [
    {
      "pattern": "result|option|panic|custom_error",
      "location": "line_number",
      "appropriateness": "good|questionable|problematic",
      "description": "Pattern usage description",
      "improvement": "Suggested improvement"
    }
  ],
  "error_handling_quality": {
    "score": 0.88,
    "strengths": ["Good use of Result types"],
    "weaknesses": ["Some unwrap() calls without justification"],
    "recommendations": ["Replace unwrap() with proper error handling"]
  }
}
"""
        }

    async def analyze_rust_file(self, file_path: Path) -> RustFileAnalysis:
        """Comprehensive analysis of a Rust source file"""
        
        if not file_path.exists():
            raise FileNotFoundError(f"Rust file not found: {file_path}")
        
        content = file_path.read_text(encoding='utf-8')
        
        # Parse Rust constructs
        constructs = await self._parse_rust_constructs(content)
        
        # Analyze module information
        module_info = await self._analyze_module_info(file_path, content)
        
        # Perform specialized analyses
        ownership_analysis = await self._analyze_ownership(content)
        concurrency_analysis = await self._analyze_concurrency(content)
        memory_safety_analysis = await self._analyze_memory_safety(content)
        performance_analysis = await self._analyze_performance(content)
        error_handling_analysis = await self._analyze_error_handling(content)
        
        # Analyze trait usage
        trait_usage = await self._analyze_trait_usage(content)
        
        # Analyze macro usage
        macro_usage = self._extract_macro_usage(content)
        
        # Calculate complexity metrics
        complexity_metrics = await self._calculate_complexity_metrics(content, constructs)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            constructs, ownership_analysis, concurrency_analysis, 
            memory_safety_analysis, performance_analysis
        )
        
        return RustFileAnalysis(
            file_path=str(file_path),
            module_info=module_info,
            constructs=constructs,
            ownership_analysis=ownership_analysis,
            concurrency_analysis=concurrency_analysis,
            memory_safety_analysis=memory_safety_analysis,
            performance_analysis=performance_analysis,
            error_handling_analysis=error_handling_analysis,
            trait_usage=trait_usage,
            macro_usage=macro_usage,
            complexity_metrics=complexity_metrics,
            recommendations=recommendations,
            analysis_timestamp=datetime.now()
        )

    async def _parse_rust_constructs(self, content: str) -> List[RustConstruct]:
        """Parse Rust language constructs"""
        
        constructs = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Function definitions
            if re.match(r'(pub\s+)?(async\s+)?(unsafe\s+)?fn\s+(\w+)', line):
                func_match = re.match(r'(pub\s+)?(async\s+)?(unsafe\s+)?fn\s+(\w+)', line)
                if func_match:
                    visibility = "public" if func_match.group(1) else "private"
                    is_async = bool(func_match.group(2))
                    is_unsafe = bool(func_match.group(3))
                    func_name = func_match.group(4)
                    
                    end_line = self._find_block_end(lines, i)
                    func_content = '\n'.join(lines[i:end_line+1])
                    
                    constructs.append(RustConstruct(
                        name=func_name,
                        construct_type=RustConstructType.FUNCTION,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        signature=line,
                        visibility=visibility,
                        is_async=is_async,
                        is_unsafe=is_unsafe,
                        ownership_patterns=self._detect_ownership_patterns(func_content),
                        concurrency_patterns=self._detect_concurrency_patterns(func_content),
                        memory_safety_flags=self._detect_memory_safety_flags(func_content),
                        performance_flags=self._detect_performance_flags(func_content),
                        complexity_score=self._calculate_function_complexity(func_content)
                    ))
            
            # Struct definitions
            elif re.match(r'(pub\s+)?struct\s+(\w+)', line):
                struct_match = re.match(r'(pub\s+)?struct\s+(\w+)', line)
                if struct_match:
                    visibility = "public" if struct_match.group(1) else "private"
                    struct_name = struct_match.group(2)
                    
                    end_line = self._find_block_end(lines, i)
                    
                    # Check for derives
                    derives = self._extract_derives(lines, i)
                    
                    constructs.append(RustConstruct(
                        name=struct_name,
                        construct_type=RustConstructType.STRUCT,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        signature=line,
                        visibility=visibility,
                        derives=derives
                    ))
            
            # Enum definitions
            elif re.match(r'(pub\s+)?enum\s+(\w+)', line):
                enum_match = re.match(r'(pub\s+)?enum\s+(\w+)', line)
                if enum_match:
                    visibility = "public" if enum_match.group(1) else "private"
                    enum_name = enum_match.group(2)
                    
                    end_line = self._find_block_end(lines, i)
                    derives = self._extract_derives(lines, i)
                    
                    constructs.append(RustConstruct(
                        name=enum_name,
                        construct_type=RustConstructType.ENUM,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        signature=line,
                        visibility=visibility,
                        derives=derives
                    ))
            
            # Trait definitions
            elif re.match(r'(pub\s+)?trait\s+(\w+)', line):
                trait_match = re.match(r'(pub\s+)?trait\s+(\w+)', line)
                if trait_match:
                    visibility = "public" if trait_match.group(1) else "private"
                    trait_name = trait_match.group(2)
                    
                    end_line = self._find_block_end(lines, i)
                    
                    constructs.append(RustConstruct(
                        name=trait_name,
                        construct_type=RustConstructType.TRAIT,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        signature=line,
                        visibility=visibility
                    ))
            
            # Impl blocks
            elif re.match(r'impl\s+', line):
                impl_match = re.match(r'impl\s+(?:<[^>]+>\s+)?(\w+)', line)
                if impl_match:
                    impl_target = impl_match.group(1)
                    end_line = self._find_block_end(lines, i)
                    
                    constructs.append(RustConstruct(
                        name=f"impl_{impl_target}",
                        construct_type=RustConstructType.IMPL_BLOCK,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        signature=line
                    ))
        
        return constructs

    def _find_block_end(self, lines: List[str], start_idx: int) -> int:
        """Find the end of a code block by matching braces"""
        brace_count = 0
        for i in range(start_idx, len(lines)):
            line = lines[i]
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and '{' in lines[start_idx]:
                return i
        return start_idx

    def _extract_derives(self, lines: List[str], struct_idx: int) -> List[str]:
        """Extract derive attributes for structs/enums"""
        derives = []
        
        # Look backwards for derive attributes
        for i in range(struct_idx - 1, max(0, struct_idx - 5), -1):
            line = lines[i].strip()
            if line.startswith('#[derive('):
                derive_match = re.search(r'#\[derive\(([^)]+)\)\]', line)
                if derive_match:
                    derive_traits = [trait.strip() for trait in derive_match.group(1).split(',')]
                    derives.extend(derive_traits)
        
        return derives

    def _detect_ownership_patterns(self, code: str) -> List[OwnershipPattern]:
        """Detect ownership and borrowing patterns"""
        patterns = []
        
        # Move semantics
        if 'move |' in code or 'move ||' in code:
            patterns.append(OwnershipPattern.MOVE_SEMANTICS)
        
        # Borrowing patterns
        if '&mut ' in code:
            patterns.append(OwnershipPattern.MUTABLE_BORROW)
        elif '&' in code and '->' in code:
            patterns.append(OwnershipPattern.BORROWED)
        
        # Clone usage
        if '.clone()' in code:
            patterns.append(OwnershipPattern.CLONE)
        
        # Reference counting
        if 'Rc<' in code or 'RefCell<' in code:
            patterns.append(OwnershipPattern.RC_REFCELL)
        
        if 'Arc<' in code and 'Mutex<' in code:
            patterns.append(OwnershipPattern.ARC_MUTEX)
        
        # Box for heap allocation
        if 'Box<' in code or 'Box::new' in code:
            patterns.append(OwnershipPattern.BOX_HEAP)
        
        return patterns

    def _detect_concurrency_patterns(self, code: str) -> List[ConcurrencyPattern]:
        """Detect concurrency patterns"""
        patterns = []
        
        # Async/await
        if 'async ' in code or '.await' in code:
            patterns.append(ConcurrencyPattern.ASYNC_AWAIT)
        
        # Thread spawning
        if 'thread::spawn' in code:
            patterns.append(ConcurrencyPattern.THREAD_SPAWN)
        elif 'tokio::spawn' in code:
            patterns.append(ConcurrencyPattern.TOKIO_SPAWN)
        
        # Channels
        if 'mpsc::' in code:
            patterns.append(ConcurrencyPattern.CHANNEL_MPSC)
        elif 'oneshot::' in code:
            patterns.append(ConcurrencyPattern.CHANNEL_ONESHOT)
        
        # Synchronization primitives
        if 'Mutex<' in code:
            patterns.append(ConcurrencyPattern.MUTEX_STD)
        elif 'RwLock<' in code:
            patterns.append(ConcurrencyPattern.RWLOCK)
        elif 'Atomic' in code:
            patterns.append(ConcurrencyPattern.ATOMIC)
        
        # Parallel processing
        if 'rayon::' in code or '.par_iter()' in code:
            patterns.append(ConcurrencyPattern.RAYON_PARALLEL)
        
        return patterns

    def _detect_memory_safety_flags(self, code: str) -> List[MemorySafetyFlag]:
        """Detect potential memory safety issues"""
        flags = []
        
        # Unsafe blocks
        if 'unsafe {' in code or 'unsafe fn' in code:
            flags.append(MemorySafetyFlag.UNSAFE_BLOCK)
        
        # Raw pointers
        if '*const ' in code or '*mut ' in code:
            flags.append(MemorySafetyFlag.RAW_POINTER)
        
        # FFI calls
        if 'extern "C"' in code or 'extern crate' in code:
            flags.append(MemorySafetyFlag.FFI_CALL)
        
        # Transmute
        if 'transmute' in code:
            flags.append(MemorySafetyFlag.TRANSMUTE)
        
        return flags

    def _detect_performance_flags(self, code: str) -> List[PerformanceFlag]:
        """Detect potential performance issues"""
        flags = []
        
        # Unnecessary clones
        if '.clone()' in code and ('&' in code or 'iter()' in code):
            flags.append(PerformanceFlag.UNNECESSARY_CLONE)
        
        # Heap allocations
        if 'Vec::new()' in code or 'Box::new' in code or 'String::new()' in code:
            flags.append(PerformanceFlag.HEAP_ALLOCATION)
        
        # Inefficient string operations
        if '+' in code and 'String' in code:
            flags.append(PerformanceFlag.INEFFICIENT_STRING_OPS)
        
        # Collect when not needed
        if '.collect()' in code and not any(container in code for container in ['Vec<', 'HashMap<', 'BTreeMap<']):
            flags.append(PerformanceFlag.COLLECT_UNNECESSARY)
        
        return flags

    def _calculate_function_complexity(self, code: str) -> float:
        """Calculate cyclomatic complexity for Rust function"""
        complexity = 1  # Base complexity
        
        # Count decision points
        complexity += code.count('if ')
        complexity += code.count('match ')
        complexity += code.count('while ')
        complexity += code.count('for ')
        complexity += code.count('loop ')
        complexity += code.count(' && ')
        complexity += code.count(' || ')
        complexity += code.count(' => ')  # Match arms
        
        # Normalize to 0-1 scale
        return min(complexity / 25.0, 1.0)

    async def _analyze_module_info(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze Rust module information"""
        
        module_info = {
            'name': file_path.stem,
            'path': str(file_path.parent),
            'uses': [],
            'mods': [],
            'crates': [],
            'features': []
        }
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            
            # Use statements
            if line.startswith('use '):
                use_match = re.search(r'use\s+([^;]+);', line)
                if use_match:
                    module_info['uses'].append(use_match.group(1))
            
            # Module declarations
            elif line.startswith('mod '):
                mod_match = re.search(r'mod\s+(\w+)', line)
                if mod_match:
                    module_info['mods'].append(mod_match.group(1))
            
            # External crate declarations
            elif line.startswith('extern crate'):
                crate_match = re.search(r'extern crate\s+(\w+)', line)
                if crate_match:
                    module_info['crates'].append(crate_match.group(1))
        
        return module_info

    async def _analyze_ownership(self, content: str) -> OwnershipAnalysis:
        """Analyze ownership and borrowing patterns"""
        
        prompt = self.analysis_patterns['ownership_analysis'].replace('{code}', content)
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            analysis_data = json.loads(response)
            
            return OwnershipAnalysis(
                owned_values=self._extract_owned_values(content),
                borrowed_values=self._extract_borrowed_values(content),
                mutable_borrows=self._extract_mutable_borrows(content),
                moved_values=self._extract_moved_values(content),
                cloned_values=self._extract_cloned_values(content),
                potential_issues=analysis_data.get('borrowing_issues', []),
                borrowing_violations=[],
                lifetime_issues=[],
                memory_efficiency_score=analysis_data.get('memory_efficiency', {}).get('score', 0.8)
            )
            
        except json.JSONDecodeError:
            return OwnershipAnalysis(
                owned_values=[],
                borrowed_values=[],
                mutable_borrows=[],
                moved_values=[],
                cloned_values=[],
                potential_issues=[],
                borrowing_violations=[],
                lifetime_issues=[],
                memory_efficiency_score=0.7
            )

    def _extract_owned_values(self, code: str) -> List[str]:
        """Extract owned value patterns"""
        owned = []
        
        # Function parameters without & or &mut
        param_matches = re.findall(r'fn\s+\w+\([^)]*(\w+):\s*([^,&)]+)', code)
        for match in param_matches:
            if not match[1].startswith('&'):
                owned.append(match[0])
        
        return owned

    def _extract_borrowed_values(self, code: str) -> List[str]:
        """Extract borrowed value patterns"""
        borrowed = []
        
        # References (&T)
        borrow_matches = re.findall(r'&(\w+)', code)
        borrowed.extend(borrow_matches)
        
        return borrowed

    def _extract_mutable_borrows(self, code: str) -> List[str]:
        """Extract mutable borrow patterns"""
        mutable_borrows = []
        
        # Mutable references (&mut T)
        mut_borrow_matches = re.findall(r'&mut\s+(\w+)', code)
        mutable_borrows.extend(mut_borrow_matches)
        
        return mutable_borrows

    def _extract_moved_values(self, code: str) -> List[str]:
        """Extract moved value patterns"""
        moved = []
        
        # Move closures
        move_matches = re.findall(r'move\s*\|[^|]*\|\s*{[^}]*(\w+)', code)
        moved.extend(move_matches)
        
        return moved

    def _extract_cloned_values(self, code: str) -> List[str]:
        """Extract cloned value patterns"""
        cloned = []
        
        # Clone method calls
        clone_matches = re.findall(r'(\w+)\.clone\(\)', code)
        cloned.extend(clone_matches)
        
        return cloned

    async def _analyze_concurrency(self, content: str) -> ConcurrencyAnalysis:
        """Analyze concurrency patterns"""
        
        prompt = self.analysis_patterns['concurrency_analysis'].replace('{code}', content)
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            analysis_data = json.loads(response)
            
            return ConcurrencyAnalysis(
                async_functions=self._extract_async_functions(content),
                spawn_points=self._extract_spawn_points(content),
                channel_usage=self._extract_channel_usage(content),
                shared_state=self._extract_shared_state(content),
                synchronization_primitives=self._extract_sync_primitives(content),
                potential_races=analysis_data.get('thread_safety_issues', []),
                deadlock_risks=[],
                async_patterns=self._detect_concurrency_patterns(content),
                thread_safety_score=0.85
            )
            
        except json.JSONDecodeError:
            return ConcurrencyAnalysis(
                async_functions=[],
                spawn_points=[],
                channel_usage=[],
                shared_state=[],
                synchronization_primitives=[],
                potential_races=[],
                deadlock_risks=[],
                async_patterns=[],
                thread_safety_score=0.8
            )

    def _extract_async_functions(self, code: str) -> List[str]:
        """Extract async function names"""
        async_funcs = re.findall(r'async\s+fn\s+(\w+)', code)
        return async_funcs

    def _extract_spawn_points(self, code: str) -> List[Dict[str, Any]]:
        """Extract thread/task spawn points"""
        spawn_points = []
        
        # Thread spawns
        thread_spawns = re.finditer(r'thread::spawn\s*\(', code)
        for match in thread_spawns:
            spawn_points.append({
                'type': 'thread',
                'position': match.start()
            })
        
        # Async spawns
        async_spawns = re.finditer(r'tokio::spawn\s*\(', code)
        for match in async_spawns:
            spawn_points.append({
                'type': 'async_task',
                'position': match.start()
            })
        
        return spawn_points

    def _extract_channel_usage(self, code: str) -> List[Dict[str, Any]]:
        """Extract channel usage patterns"""
        usage = []
        
        # MPSC channels
        if 'mpsc::channel' in code:
            usage.append({'type': 'mpsc', 'pattern': 'multi_producer_single_consumer'})
        
        # Oneshot channels
        if 'oneshot::channel' in code:
            usage.append({'type': 'oneshot', 'pattern': 'single_value'})
        
        return usage

    def _extract_shared_state(self, code: str) -> List[Dict[str, Any]]:
        """Extract shared state patterns"""
        shared_state = []
        
        # Arc patterns
        arc_matches = re.findall(r'Arc<([^>]+)>', code)
        for match in arc_matches:
            shared_state.append({
                'type': 'arc',
                'inner_type': match,
                'thread_safe': True
            })
        
        return shared_state

    def _extract_sync_primitives(self, code: str) -> List[str]:
        """Extract synchronization primitives"""
        primitives = []
        
        if 'Mutex<' in code:
            primitives.append('Mutex')
        if 'RwLock<' in code:
            primitives.append('RwLock')
        if 'Atomic' in code:
            primitives.append('Atomic')
        
        return primitives

    async def _analyze_memory_safety(self, content: str) -> MemorySafetyAnalysis:
        """Analyze memory safety"""
        
        prompt = self.analysis_patterns['memory_safety_analysis'].replace('{code}', content)
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            analysis_data = json.loads(response)
            
            return MemorySafetyAnalysis(
                unsafe_blocks=self._extract_unsafe_blocks(content),
                raw_pointer_usage=self._extract_raw_pointers(content),
                ffi_interactions=self._extract_ffi_calls(content),
                transmute_calls=self._extract_transmute_calls(content),
                potential_vulnerabilities=analysis_data.get('vulnerabilities', []),
                safety_score=analysis_data.get('memory_safety_score', 0.95),
                recommendations=[]
            )
            
        except json.JSONDecodeError:
            return MemorySafetyAnalysis(
                unsafe_blocks=[],
                raw_pointer_usage=[],
                ffi_interactions=[],
                transmute_calls=[],
                potential_vulnerabilities=[],
                safety_score=0.9,
                recommendations=[]
            )

    def _extract_unsafe_blocks(self, code: str) -> List[Dict[str, Any]]:
        """Extract unsafe block information"""
        unsafe_blocks = []
        
        unsafe_matches = re.finditer(r'unsafe\s*{', code)
        for match in unsafe_matches:
            unsafe_blocks.append({
                'type': 'block',
                'position': match.start(),
                'context': 'unsafe block'
            })
        
        return unsafe_blocks

    def _extract_raw_pointers(self, code: str) -> List[str]:
        """Extract raw pointer usage"""
        pointers = []
        
        const_ptrs = re.findall(r'\*const\s+(\w+)', code)
        mut_ptrs = re.findall(r'\*mut\s+(\w+)', code)
        
        pointers.extend([f"*const {ptr}" for ptr in const_ptrs])
        pointers.extend([f"*mut {ptr}" for ptr in mut_ptrs])
        
        return pointers

    def _extract_ffi_calls(self, code: str) -> List[str]:
        """Extract FFI interactions"""
        ffi_calls = []
        
        extern_blocks = re.findall(r'extern\s+"C"\s*{[^}]+}', code)
        ffi_calls.extend(extern_blocks)
        
        return ffi_calls

    def _extract_transmute_calls(self, code: str) -> List[str]:
        """Extract transmute usage"""
        transmutes = re.findall(r'transmute[^;]+;', code)
        return transmutes

    async def _analyze_performance(self, content: str) -> Dict[str, Any]:
        """Analyze performance characteristics"""
        
        prompt = self.analysis_patterns['performance_analysis'].replace('{code}', content)
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                'performance_patterns': [],
                'allocation_analysis': {
                    'stack_allocations': 0,
                    'heap_allocations': 0
                },
                'zero_cost_abstractions': []
            }

    async def _analyze_error_handling(self, content: str) -> Dict[str, Any]:
        """Analyze error handling patterns"""
        
        prompt = self.analysis_patterns['error_handling_analysis'].replace('{code}', content)
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                'error_patterns': [],
                'error_handling_quality': {
                    'score': 0.8,
                    'strengths': [],
                    'weaknesses': []
                }
            }

    async def _analyze_trait_usage(self, content: str) -> Dict[str, Any]:
        """Analyze trait implementation and usage"""
        
        trait_usage = {
            'defined_traits': [],
            'implemented_traits': [],
            'derived_traits': [],
            'trait_objects': []
        }
        
        # Trait definitions
        trait_defs = re.findall(r'trait\s+(\w+)', content)
        trait_usage['defined_traits'] = trait_defs
        
        # Trait implementations
        impl_matches = re.findall(r'impl\s+(\w+)\s+for\s+(\w+)', content)
        trait_usage['implemented_traits'] = [{'trait': match[0], 'type': match[1]} for match in impl_matches]
        
        # Derived traits
        derive_matches = re.findall(r'#\[derive\(([^)]+)\)\]', content)
        for match in derive_matches:
            traits = [t.strip() for t in match.split(',')]
            trait_usage['derived_traits'].extend(traits)
        
        # Trait objects
        trait_obj_matches = re.findall(r'dyn\s+(\w+)', content)
        trait_usage['trait_objects'] = trait_obj_matches
        
        return trait_usage

    def _extract_macro_usage(self, content: str) -> List[str]:
        """Extract macro usage"""
        macros = []
        
        # Macro invocations
        macro_matches = re.findall(r'(\w+)!', content)
        macros.extend(set(macro_matches))  # Remove duplicates
        
        return macros

    async def _calculate_complexity_metrics(self, content: str, constructs: List[RustConstruct]) -> Dict[str, float]:
        """Calculate complexity metrics"""
        
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip() and not line.strip().startswith('//')]
        
        metrics = {
            'lines_of_code': len(non_empty_lines),
            'cyclomatic_complexity': sum(construct.complexity_score for construct in constructs),
            'function_count': len([c for c in constructs if c.construct_type == RustConstructType.FUNCTION]),
            'struct_count': len([c for c in constructs if c.construct_type == RustConstructType.STRUCT]),
            'enum_count': len([c for c in constructs if c.construct_type == RustConstructType.ENUM]),
            'trait_count': len([c for c in constructs if c.construct_type == RustConstructType.TRAIT]),
            'unsafe_density': content.count('unsafe') / max(len(non_empty_lines), 1),
            'async_density': content.count('async') / max(len(non_empty_lines), 1),
            'clone_density': content.count('.clone()') / max(len(non_empty_lines), 1)
        }
        
        return metrics

    async def _generate_recommendations(self, constructs: List[RustConstruct], ownership_analysis: OwnershipAnalysis, concurrency_analysis: ConcurrencyAnalysis, memory_safety_analysis: MemorySafetyAnalysis, performance_analysis: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        
        recommendations = []
        
        # Ownership recommendations
        if ownership_analysis.memory_efficiency_score < 0.8:
            recommendations.append("Review ownership patterns to improve memory efficiency")
        
        if len(ownership_analysis.cloned_values) > 5:
            recommendations.append("Consider reducing clone() usage for better performance")
        
        # Concurrency recommendations
        if concurrency_analysis.async_functions and not concurrency_analysis.spawn_points:
            recommendations.append("Consider using tokio::spawn for CPU-intensive async tasks")
        
        if len(concurrency_analysis.potential_races) > 0:
            recommendations.append(f"Address {len(concurrency_analysis.potential_races)} potential race conditions")
        
        # Memory safety recommendations
        if len(memory_safety_analysis.unsafe_blocks) > 0:
            recommendations.append("Review unsafe blocks and document safety invariants")
        
        if memory_safety_analysis.safety_score < 0.9:
            recommendations.append("Improve memory safety practices")
        
        # Performance recommendations
        perf_flags = [flag for construct in constructs for flag in construct.performance_flags]
        if PerformanceFlag.UNNECESSARY_CLONE in perf_flags:
            recommendations.append("Eliminate unnecessary clone() calls")
        
        if PerformanceFlag.INEFFICIENT_STRING_OPS in perf_flags:
            recommendations.append("Use String::push_str() or format! macro for string concatenation")
        
        return recommendations

    async def analyze_rust_project(self, project_path: Path) -> Dict[str, RustFileAnalysis]:
        """Analyze an entire Rust project"""
        
        analyses = {}
        
        # Find all Rust files
        rust_files = list(project_path.rglob('*.rs'))
        
        # Exclude target directory
        source_files = [f for f in rust_files if 'target' not in str(f)]
        
        for rust_file in source_files:
            try:
                analysis = await self.analyze_rust_file(rust_file)
                relative_path = rust_file.relative_to(project_path)
                analyses[str(relative_path)] = analysis
            except Exception as e:
                print(f"Error analyzing {rust_file}: {e}")
        
        return analyses

    def generate_rust_analysis_report(self, analyses: Dict[str, RustFileAnalysis], output_path: Optional[Path] = None) -> str:
        """Generate comprehensive Rust analysis report"""
        
        report = []
        report.append("# Rust Project Analysis Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary statistics
        total_files = len(analyses)
        total_functions = sum(len([c for c in analysis.constructs if c.construct_type == RustConstructType.FUNCTION]) for analysis in analyses.values())
        total_structs = sum(len([c for c in analysis.constructs if c.construct_type == RustConstructType.STRUCT]) for analysis in analyses.values())
        total_traits = sum(len([c for c in analysis.constructs if c.construct_type == RustConstructType.TRAIT]) for analysis in analyses.values())
        
        report.append("## Project Summary")
        report.append(f"- **Files analyzed:** {total_files}")
        report.append(f"- **Functions:** {total_functions}")
        report.append(f"- **Structs:** {total_structs}")
        report.append(f"- **Traits:** {total_traits}")
        report.append("")
        
        # Memory safety analysis
        total_unsafe_blocks = sum(len(analysis.memory_safety_analysis.unsafe_blocks) for analysis in analyses.values())
        avg_safety_score = sum(analysis.memory_safety_analysis.safety_score for analysis in analyses.values()) / max(total_files, 1)
        
        report.append("## Memory Safety Analysis")
        report.append(f"- **Unsafe blocks:** {total_unsafe_blocks}")
        report.append(f"- **Average safety score:** {avg_safety_score:.2f}")
        report.append("")
        
        # Concurrency analysis
        total_async_functions = sum(len(analysis.concurrency_analysis.async_functions) for analysis in analyses.values())
        files_with_concurrency = len([a for a in analyses.values() if len(a.concurrency_analysis.async_functions) > 0 or len(a.concurrency_analysis.spawn_points) > 0])
        
        report.append("## Concurrency Analysis")
        report.append(f"- **Async functions:** {total_async_functions}")
        report.append(f"- **Files with concurrency:** {files_with_concurrency}")
        report.append("")
        
        # Performance analysis
        all_performance_flags = []
        for analysis in analyses.values():
            all_performance_flags.extend([flag.value for construct in analysis.constructs for flag in construct.performance_flags])
        
        report.append("## Performance Analysis")
        report.append(f"- **Performance flags:** {len(all_performance_flags)}")
        if all_performance_flags:
            flag_counts = {}
            for flag in all_performance_flags:
                flag_counts[flag] = flag_counts.get(flag, 0) + 1
            
            report.append("- **Common issues:**")
            for flag, count in sorted(flag_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
                report.append(f"  - {flag}: {count} instances")
        report.append("")
        
        report_text = "\n".join(report)
        
        if output_path:
            output_path.write_text(report_text)
        
        return report_text