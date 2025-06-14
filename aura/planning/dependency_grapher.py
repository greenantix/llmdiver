"""
Dependency Grapher - Task Dependency Analysis and Critical Path Detection
Analyzes task relationships and optimizes execution paths
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import networkx as nx
from collections import defaultdict, deque

from ..core.config import AuraConfig
from ..llm.providers import LLMProvider
from .task_decomposer import DecomposedTask, TaskHierarchy, TaskDependency


class DependencyType(Enum):
    BLOCKS = "blocks"
    REQUIRES = "requires"
    RELATES_TO = "relates_to"
    ENABLES = "enables"
    CONFLICTS_WITH = "conflicts_with"


class CriticalityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DependencyEdge:
    from_task: str
    to_task: str
    dependency_type: DependencyType
    weight: float = 1.0
    description: Optional[str] = None
    mandatory: bool = True


@dataclass
class CriticalPathNode:
    task_id: str
    earliest_start: datetime
    latest_start: datetime
    earliest_finish: datetime
    latest_finish: datetime
    slack: timedelta
    criticality: CriticalityLevel
    
    @property
    def is_critical(self) -> bool:
        return self.slack.total_seconds() == 0


@dataclass
class ResourceConstraint:
    resource_id: str
    resource_type: str  # "person", "skill", "tool", "environment"
    availability: float  # 0.0 to 1.0
    required_tasks: List[str]
    conflicting_tasks: List[Tuple[str, str]]


@dataclass
class DependencyGraph:
    nodes: Dict[str, DecomposedTask]
    edges: List[DependencyEdge]
    critical_path: List[str]
    critical_path_nodes: List[CriticalPathNode]
    parallel_execution_groups: List[List[str]]
    bottleneck_tasks: List[str]
    resource_constraints: List[ResourceConstraint]
    estimated_duration: timedelta
    risk_factors: List[str]
    optimization_suggestions: List[str]


class DependencyGrapher:
    def __init__(self, config: AuraConfig, llm_provider: LLMProvider):
        self.config = config
        self.llm_provider = llm_provider
        self.analysis_templates = self._load_analysis_templates()
        
    def _load_analysis_templates(self) -> Dict[str, str]:
        """Load LLM prompts for dependency analysis"""
        return {
            'dependency_discovery': """
Analyze these tasks and identify dependencies between them:

Tasks:
{tasks_json}

For each task, analyze:
1. What other tasks must be completed before this one can start
2. What other tasks this one enables or unblocks
3. What tasks might conflict or compete for resources
4. What tasks could be done in parallel

Generate dependencies in this JSON format:
{
  "dependencies": [
    {
      "from_task": "task_1",
      "to_task": "task_2", 
      "dependency_type": "blocks|requires|relates_to|enables|conflicts_with",
      "weight": 0.9,
      "description": "Why this dependency exists",
      "mandatory": true
    }
  ],
  "parallel_groups": [
    ["task_a", "task_b", "task_c"],
    ["task_d", "task_e"]
  ],
  "bottlenecks": [
    {
      "task_id": "bottleneck_task",
      "reason": "Blocks many other tasks",
      "impact_count": 5
    }
  ]
}

Consider:
- Technical dependencies (API must exist before UI)
- Logical dependencies (design before implementation)
- Resource dependencies (same person/skill needed)
- Integration dependencies (components must be tested together)
""",
            
            'critical_path_analysis': """
Analyze this dependency graph and identify the critical path:

Tasks with estimates:
{tasks_with_estimates}

Dependencies:
{dependencies}

Calculate:
1. Critical path through the project
2. Earliest/latest start and finish times
3. Slack time for each task
4. Resource bottlenecks

Provide analysis in this JSON format:
{
  "critical_path": ["task_1", "task_2", "task_5"],
  "task_schedule": {
    "task_id": {
      "earliest_start": "2025-01-01T09:00:00",
      "latest_start": "2025-01-01T09:00:00", 
      "earliest_finish": "2025-01-03T17:00:00",
      "latest_finish": "2025-01-03T17:00:00",
      "slack_hours": 0,
      "criticality": "critical"
    }
  },
  "project_duration_days": 45,
  "risk_factors": [
    "Task X is on critical path with high uncertainty",
    "Resource Y is overallocated"
  ]
}

Use realistic working hours (8 hours/day, 5 days/week).
""",
            
            'optimization_suggestions': """
Analyze this project plan and suggest optimizations:

Critical Path: {critical_path}
Bottlenecks: {bottlenecks}
Resource Constraints: {resource_constraints}
Current Duration: {duration_days} days

Suggest optimizations in this JSON format:
{
  "optimization_strategies": [
    {
      "type": "parallelization",
      "description": "Run tasks X and Y in parallel",
      "tasks_affected": ["task_x", "task_y"],
      "time_savings_days": 5,
      "risk_level": "low",
      "requirements": ["Additional developer"]
    },
    {
      "type": "dependency_elimination", 
      "description": "Remove unnecessary dependency between A and B",
      "tasks_affected": ["task_a", "task_b"],
      "time_savings_days": 3,
      "risk_level": "medium",
      "requirements": ["Architecture change"]
    }
  ],
  "resource_optimizations": [
    {
      "resource_type": "developer",
      "current_utilization": 1.2,
      "recommended_allocation": 1.0,
      "affected_tasks": ["task_list"]
    }
  ],
  "risk_mitigations": [
    {
      "risk": "Critical path task has high uncertainty",
      "mitigation": "Add buffer time or create fallback plan",
      "impact": "Reduces schedule risk"
    }
  ]
}

Focus on:
- Reducing critical path length
- Eliminating bottlenecks
- Improving resource utilization
- Reducing project risk
"""
        }

    async def create_dependency_graph(self, hierarchy: TaskHierarchy) -> DependencyGraph:
        """Create comprehensive dependency graph from task hierarchy"""
        
        # Extract tasks and their basic dependencies
        tasks = list(hierarchy.task_map.values())
        
        # Discover additional dependencies using LLM
        discovered_dependencies = await self._discover_dependencies(tasks)
        
        # Combine explicit and discovered dependencies
        all_edges = self._convert_dependencies_to_edges(tasks, discovered_dependencies)
        
        # Build NetworkX graph for analysis
        nx_graph = self._build_networkx_graph(tasks, all_edges)
        
        # Calculate critical path
        critical_path_analysis = await self._calculate_critical_path(tasks, all_edges)
        
        # Identify parallel execution groups
        parallel_groups = self._identify_parallel_groups(nx_graph)
        
        # Find bottlenecks
        bottlenecks = self._identify_bottlenecks(nx_graph, all_edges)
        
        # Analyze resource constraints
        resource_constraints = self._analyze_resource_constraints(tasks)
        
        # Generate optimization suggestions
        optimizations = await self._generate_optimizations(
            critical_path_analysis.get('critical_path', []),
            bottlenecks,
            resource_constraints,
            critical_path_analysis.get('project_duration_days', 30)
        )
        
        return DependencyGraph(
            nodes=hierarchy.task_map,
            edges=all_edges,
            critical_path=critical_path_analysis.get('critical_path', []),
            critical_path_nodes=self._create_critical_path_nodes(critical_path_analysis),
            parallel_execution_groups=parallel_groups,
            bottleneck_tasks=bottlenecks,
            resource_constraints=resource_constraints,
            estimated_duration=timedelta(days=critical_path_analysis.get('project_duration_days', 30)),
            risk_factors=critical_path_analysis.get('risk_factors', []),
            optimization_suggestions=optimizations.get('optimization_strategies', [])
        )

    async def _discover_dependencies(self, tasks: List[DecomposedTask]) -> Dict[str, Any]:
        """Use LLM to discover implicit dependencies between tasks"""
        
        tasks_data = [
            {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'type': task.task_type.value,
                'labels': task.labels,
                'parent_id': task.parent_id,
                'explicit_dependencies': [
                    {
                        'task_id': dep.task_id,
                        'type': dep.dependency_type
                    } for dep in task.dependencies
                ]
            }
            for task in tasks
        ]
        
        template = self.analysis_templates['dependency_discovery']
        prompt = template.replace('{tasks_json}', json.dumps(tasks_data, indent=2))
        
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                'dependencies': [],
                'parallel_groups': [],
                'bottlenecks': []
            }

    def _convert_dependencies_to_edges(self, tasks: List[DecomposedTask], discovered: Dict[str, Any]) -> List[DependencyEdge]:
        """Convert task dependencies to graph edges"""
        
        edges = []
        task_ids = {task.id for task in tasks}
        
        # Add explicit dependencies from tasks
        for task in tasks:
            for dep in task.dependencies:
                if dep.task_id in task_ids:
                    edge = DependencyEdge(
                        from_task=dep.task_id,
                        to_task=task.id,
                        dependency_type=DependencyType(dep.dependency_type),
                        description=dep.description
                    )
                    edges.append(edge)
        
        # Add discovered dependencies
        dependencies_list = discovered.get('dependencies', []) if isinstance(discovered, dict) else []
        for dep_data in dependencies_list:
            if isinstance(dep_data, dict):
                from_task = dep_data.get('from_task')
                to_task = dep_data.get('to_task')
                
                if from_task in task_ids and to_task in task_ids:
                    edge = DependencyEdge(
                        from_task=from_task,
                        to_task=to_task,
                        dependency_type=DependencyType(dep_data.get('dependency_type', 'requires')),
                        weight=dep_data.get('weight', 1.0),
                        description=dep_data.get('description'),
                        mandatory=dep_data.get('mandatory', True)
                    )
                    edges.append(edge)
        
        return edges

    def _build_networkx_graph(self, tasks: List[DecomposedTask], edges: List[DependencyEdge]) -> nx.DiGraph:
        """Build NetworkX directed graph for analysis"""
        
        graph = nx.DiGraph()
        
        # Add nodes
        for task in tasks:
            duration = 1  # Default duration in days
            if task.estimate:
                if task.estimate.unit.value == 'hours':
                    duration = task.estimate.value / 8  # Convert to days
                elif task.estimate.unit.value == 'days':
                    duration = task.estimate.value
                elif task.estimate.unit.value == 'story_points':
                    duration = task.estimate.value * 0.5  # Assume 0.5 days per story point
            
            graph.add_node(task.id, 
                          duration=duration,
                          task=task)
        
        # Add edges
        for edge in edges:
            if edge.from_task in graph and edge.to_task in graph:
                graph.add_edge(edge.from_task, edge.to_task,
                              weight=edge.weight,
                              edge_data=edge)
        
        return graph

    async def _calculate_critical_path(self, tasks: List[DecomposedTask], edges: List[DependencyEdge]) -> Dict[str, Any]:
        """Calculate critical path using forward and backward pass"""
        
        # Prepare data for LLM analysis
        tasks_with_estimates = [
            {
                'id': task.id,
                'title': task.title,
                'estimate_hours': self._get_task_hours(task),
                'dependencies': [dep.task_id for dep in task.dependencies]
            }
            for task in tasks
        ]
        
        dependencies_data = [
            {
                'from': edge.from_task,
                'to': edge.to_task,
                'type': edge.dependency_type.value
            }
            for edge in edges
        ]
        
        template = self.analysis_templates['critical_path_analysis']
        prompt = template.replace('{tasks_with_estimates}', json.dumps(tasks_with_estimates, indent=2))
        prompt = prompt.replace('{dependencies}', json.dumps(dependencies_data, indent=2))
        
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback calculation
            return self._fallback_critical_path_calculation(tasks, edges)

    def _get_task_hours(self, task: DecomposedTask) -> float:
        """Get task duration in hours"""
        if not task.estimate:
            return 8.0  # Default 1 day
        
        if task.estimate.unit.value == 'hours':
            return task.estimate.value
        elif task.estimate.unit.value == 'days':
            return task.estimate.value * 8
        elif task.estimate.unit.value == 'story_points':
            return task.estimate.value * 4  # 4 hours per story point
        
        return 8.0

    def _fallback_critical_path_calculation(self, tasks: List[DecomposedTask], edges: List[DependencyEdge]) -> Dict[str, Any]:
        """Fallback critical path calculation using simple algorithm"""
        
        # Build adjacency list
        dependencies = defaultdict(list)
        for edge in edges:
            dependencies[edge.to_task].append(edge.from_task)
        
        # Calculate earliest finish times
        earliest_finish = {}
        
        def calculate_earliest_finish(task_id: str) -> float:
            if task_id in earliest_finish:
                return earliest_finish[task_id]
            
            task = next((t for t in tasks if t.id == task_id), None)
            if not task:
                return 0
            
            task_duration = self._get_task_hours(task) / 8  # Convert to days
            
            max_prereq_finish = 0
            for prereq_id in dependencies[task_id]:
                prereq_finish = calculate_earliest_finish(prereq_id)
                max_prereq_finish = max(max_prereq_finish, prereq_finish)
            
            earliest_finish[task_id] = max_prereq_finish + task_duration
            return earliest_finish[task_id]
        
        # Calculate for all tasks
        for task in tasks:
            calculate_earliest_finish(task.id)
        
        # Find critical path (simplified)
        project_duration = max(earliest_finish.values()) if earliest_finish else 0
        critical_tasks = [
            task_id for task_id, finish_time in earliest_finish.items()
            if abs(finish_time - project_duration) < 0.1
        ]
        
        return {
            'critical_path': critical_tasks,
            'project_duration_days': project_duration,
            'task_schedule': {
                task_id: {
                    'earliest_finish': f"Day {finish_time:.1f}",
                    'criticality': 'critical' if task_id in critical_tasks else 'normal'
                }
                for task_id, finish_time in earliest_finish.items()
            },
            'risk_factors': ['Simplified calculation - detailed analysis recommended']
        }

    def _identify_parallel_groups(self, graph: nx.DiGraph) -> List[List[str]]:
        """Identify groups of tasks that can be executed in parallel"""
        
        parallel_groups = []
        processed = set()
        
        # Find tasks at the same "level" (same distance from start)
        try:
            # Find tasks with no predecessors
            start_nodes = [node for node in graph.nodes() if graph.in_degree(node) == 0]
            
            # Group tasks by their level in the dependency hierarchy
            levels = {}
            for start_node in start_nodes:
                levels[start_node] = 0
            
            queue = deque(start_nodes)
            while queue:
                current = queue.popleft()
                current_level = levels[current]
                
                for successor in graph.successors(current):
                    successor_level = max(levels.get(successor, 0), current_level + 1)
                    levels[successor] = successor_level
                    if successor not in queue:
                        queue.append(successor)
            
            # Group by level
            level_groups = defaultdict(list)
            for node, level in levels.items():
                level_groups[level].append(node)
            
            # Convert to parallel groups (groups with more than one task)
            for level, nodes in level_groups.items():
                if len(nodes) > 1:
                    parallel_groups.append(nodes)
            
        except Exception:
            pass  # Return empty list if analysis fails
        
        return parallel_groups

    def _identify_bottlenecks(self, graph: nx.DiGraph, edges: List[DependencyEdge]) -> List[str]:
        """Identify tasks that block many other tasks"""
        
        bottlenecks = []
        
        # Count how many tasks each task blocks
        blocking_count = defaultdict(int)
        for edge in edges:
            if edge.dependency_type in [DependencyType.BLOCKS, DependencyType.REQUIRES]:
                blocking_count[edge.from_task] += 1
        
        # Tasks that block 3+ other tasks are bottlenecks
        bottlenecks = [
            task_id for task_id, count in blocking_count.items()
            if count >= 3
        ]
        
        return bottlenecks

    def _analyze_resource_constraints(self, tasks: List[DecomposedTask]) -> List[ResourceConstraint]:
        """Analyze resource constraints and conflicts"""
        
        constraints = []
        
        # Group tasks by labels (representing skills/resources needed)
        skill_groups = defaultdict(list)
        for task in tasks:
            for label in task.labels:
                skill_groups[label].append(task.id)
        
        # Create resource constraints for skills needed by multiple tasks
        for skill, task_ids in skill_groups.items():
            if len(task_ids) > 1:
                constraint = ResourceConstraint(
                    resource_id=skill,
                    resource_type="skill",
                    availability=0.8,  # Assume 80% availability
                    required_tasks=task_ids,
                    conflicting_tasks=[(task_ids[i], task_ids[j]) 
                                     for i in range(len(task_ids)) 
                                     for j in range(i+1, len(task_ids))]
                )
                constraints.append(constraint)
        
        return constraints

    async def _generate_optimizations(self, critical_path: List[str], bottlenecks: List[str], 
                                     resource_constraints: List[ResourceConstraint], 
                                     duration_days: float) -> Dict[str, Any]:
        """Generate optimization suggestions using LLM"""
        
        template = self.analysis_templates['optimization_suggestions']
        prompt = template.replace('{critical_path}', json.dumps(critical_path))
        prompt = prompt.replace('{bottlenecks}', json.dumps(bottlenecks))
        prompt = prompt.replace('{resource_constraints}', json.dumps([{
            'resource': rc.resource_id,
            'type': rc.resource_type,
            'task_count': len(rc.required_tasks)
        } for rc in resource_constraints], indent=2))
        prompt = prompt.replace('{duration_days}', str(duration_days))
        
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                'optimization_strategies': [
                    {
                        'type': 'parallelization',
                        'description': 'Look for opportunities to run tasks in parallel',
                        'time_savings_days': 5,
                        'risk_level': 'low'
                    }
                ],
                'resource_optimizations': [],
                'risk_mitigations': []
            }

    def _create_critical_path_nodes(self, critical_path_analysis: Dict[str, Any]) -> List[CriticalPathNode]:
        """Create critical path node objects from analysis"""
        
        nodes = []
        base_date = datetime.now()
        
        for task_id in critical_path_analysis.get('critical_path', []):
            schedule_data = critical_path_analysis.get('task_schedule', {}).get(task_id, {})
            
            # Parse dates or create defaults
            earliest_start = base_date
            latest_start = base_date
            earliest_finish = base_date + timedelta(days=1)
            latest_finish = base_date + timedelta(days=1)
            
            slack_hours = schedule_data.get('slack_hours', 0)
            criticality_str = schedule_data.get('criticality', 'medium')
            
            try:
                criticality = CriticalityLevel(criticality_str)
            except ValueError:
                criticality = CriticalityLevel.MEDIUM
            
            node = CriticalPathNode(
                task_id=task_id,
                earliest_start=earliest_start,
                latest_start=latest_start,
                earliest_finish=earliest_finish,
                latest_finish=latest_finish,
                slack=timedelta(hours=slack_hours),
                criticality=criticality
            )
            nodes.append(node)
        
        return nodes

    def visualize_dependency_graph(self, graph: DependencyGraph, output_path: Optional[str] = None) -> str:
        """Generate a visual representation of the dependency graph"""
        
        # Create a simple text-based visualization
        visualization = []
        visualization.append("=== DEPENDENCY GRAPH ANALYSIS ===\n")
        
        # Critical Path
        visualization.append("CRITICAL PATH:")
        for i, task_id in enumerate(graph.critical_path):
            task = graph.nodes.get(task_id)
            if task:
                arrow = " -> " if i < len(graph.critical_path) - 1 else ""
                visualization.append(f"  {task.title} ({task_id}){arrow}")
        
        visualization.append(f"\nPROJECT DURATION: {graph.estimated_duration.days} days")
        
        # Bottlenecks
        if graph.bottleneck_tasks:
            visualization.append("\nBOTTLENECKS:")
            for task_id in graph.bottleneck_tasks:
                task = graph.nodes.get(task_id)
                if task:
                    visualization.append(f"  ⚠️  {task.title} ({task_id})")
        
        # Parallel Groups
        if graph.parallel_execution_groups:
            visualization.append("\nPARALLEL EXECUTION OPPORTUNITIES:")
            for i, group in enumerate(graph.parallel_execution_groups):
                visualization.append(f"  Group {i+1}:")
                for task_id in group:
                    task = graph.nodes.get(task_id)
                    if task:
                        visualization.append(f"    - {task.title}")
        
        # Optimization Suggestions
        if graph.optimization_suggestions:
            visualization.append("\nOPTIMIZATION SUGGESTIONS:")
            for suggestion in graph.optimization_suggestions[:3]:  # Show top 3
                if isinstance(suggestion, dict):
                    description = suggestion.get('description', 'Optimization opportunity')
                    time_savings = suggestion.get('time_savings_days', 0)
                    visualization.append(f"  • {description} (Save: {time_savings} days)")
        
        result = "\n".join(visualization)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(result)
        
        return result