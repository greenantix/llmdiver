"""
Task Decomposer - Hierarchical Task Breakdown and Decomposition
Transforms epics and user stories into actionable development tasks
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import asyncio

from ..core.config import AuraConfig
from ..llm.providers import LLMProvider
from .prd_parser import Epic, UserStory, RequirementAnalysis, Priority


class TaskType(Enum):
    EPIC = "epic"
    STORY = "story"
    TASK = "task"
    SUBTASK = "subtask"
    BUG = "bug"
    SPIKE = "spike"
    RESEARCH = "research"


class TaskStatus(Enum):
    BACKLOG = "backlog"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    TESTING = "testing"
    DONE = "done"
    BLOCKED = "blocked"


class EstimationUnit(Enum):
    STORY_POINTS = "story_points"
    HOURS = "hours"
    DAYS = "days"


@dataclass
class TaskEstimate:
    value: float
    unit: EstimationUnit
    confidence: float  # 0-1 scale
    complexity_factors: List[str] = field(default_factory=list)


@dataclass
class TaskDependency:
    task_id: str
    dependency_type: str  # "blocks", "requires", "relates_to"
    description: Optional[str] = None


@dataclass
class AcceptanceCriteria:
    id: str
    description: str
    testable: bool = True
    automated: bool = False


@dataclass 
class DecomposedTask:
    id: str
    title: str
    description: str
    task_type: TaskType
    priority: Priority
    status: TaskStatus
    estimate: Optional[TaskEstimate] = None
    parent_id: Optional[str] = None
    dependencies: List[TaskDependency] = field(default_factory=list)
    acceptance_criteria: List[AcceptanceCriteria] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskHierarchy:
    root_tasks: List[DecomposedTask]
    task_map: Dict[str, DecomposedTask]
    dependency_graph: Dict[str, List[str]]
    execution_order: List[str]
    parallel_groups: List[List[str]]
    critical_path: List[str]
    total_estimate: TaskEstimate
    milestone_mapping: Dict[str, List[str]]


class TaskDecomposer:
    def __init__(self, config: AuraConfig, llm_provider: LLMProvider):
        self.config = config
        self.llm_provider = llm_provider
        self.decomposition_templates = self._load_decomposition_templates()
        
    def _load_decomposition_templates(self) -> Dict[str, str]:
        """Load LLM prompts for task decomposition"""
        return {
            'epic_decomposition': """
Decompose this epic into detailed user stories and technical tasks:

Epic: {epic_title}
Description: {epic_description}
Phase: {epic_phase}
Priority: {epic_priority}

Existing User Stories:
{existing_stories}

Generate a comprehensive decomposition in this JSON format:
{
  "user_stories": [
    {
      "id": "story_unique_id",
      "title": "As a [persona], I want [goal] so that [benefit]",
      "description": "Detailed description of the story",
      "priority": "critical|high|medium|low",
      "estimate": {
        "value": 5,
        "unit": "story_points",
        "confidence": 0.8,
        "complexity_factors": ["UI complexity", "API integration"]
      },
      "acceptance_criteria": [
        {
          "id": "ac_1",
          "description": "Specific, testable criterion",
          "testable": true,
          "automated": false
        }
      ],
      "technical_tasks": [
        {
          "id": "task_unique_id",
          "title": "Implement specific functionality",
          "description": "Technical implementation details",
          "task_type": "task",
          "priority": "high",
          "estimate": {
            "value": 2,
            "unit": "days",
            "confidence": 0.9,
            "complexity_factors": ["Database schema changes"]
          },
          "dependencies": [
            {
              "task_id": "other_task_id",
              "dependency_type": "requires",
              "description": "Needs API endpoint"
            }
          ],
          "labels": ["backend", "database", "api"]
        }
      ]
    }
  ],
  "research_spikes": [
    {
      "id": "spike_id",
      "title": "Research technical approach",
      "description": "Investigation needed before implementation",
      "estimate": {
        "value": 3,
        "unit": "days",
        "confidence": 0.7
      }
    }
  ]
}

Guidelines:
- Break down complex functionality into 1-3 day tasks
- Identify technical dependencies clearly
- Include research spikes for unknowns
- Estimate with realistic confidence levels
- Use appropriate labels for categorization
""",
            
            'story_decomposition': """
Decompose this user story into detailed implementation tasks:

User Story: {story_title}
Description: {story_description}
Priority: {story_priority}
Acceptance Criteria: {acceptance_criteria}

Generate detailed tasks in this JSON format:
{
  "implementation_tasks": [
    {
      "id": "task_id",
      "title": "Specific implementation task",
      "description": "Technical details and approach",
      "task_type": "task",
      "priority": "high|medium|low",
      "estimate": {
        "value": 4,
        "unit": "hours",
        "confidence": 0.85,
        "complexity_factors": ["New technology", "Integration complexity"]
      },
      "dependencies": [
        {
          "task_id": "prerequisite_task",
          "dependency_type": "blocks",
          "description": "Must complete X before Y"
        }
      ],
      "labels": ["frontend", "backend", "testing", "documentation"],
      "subtasks": [
        {
          "id": "subtask_id",
          "title": "Atomic work unit",
          "description": "Smallest unit of work",
          "estimate": {
            "value": 1,
            "unit": "hours",
            "confidence": 0.9
          }
        }
      ]
    }
  ],
  "testing_tasks": [
    {
      "id": "test_task_id",
      "title": "Test implementation",
      "description": "Testing approach and coverage",
      "task_type": "task",
      "priority": "high",
      "labels": ["testing", "qa"]
    }
  ],
  "documentation_tasks": [
    {
      "id": "doc_task_id",
      "title": "Update documentation",
      "description": "Documentation updates needed",
      "task_type": "task",
      "priority": "medium",
      "labels": ["documentation"]
    }
  ]
}

Focus on:
- Atomic, implementable tasks (2-8 hours each)
- Clear technical dependencies
- Comprehensive testing coverage
- Documentation requirements
- Realistic effort estimates
""",
            
            'dependency_analysis': """
Analyze these tasks and identify dependencies and execution order:

Tasks:
{tasks_json}

Generate dependency analysis in this JSON format:
{
  "dependency_graph": {
    "task_id": ["dependent_task_1", "dependent_task_2"]
  },
  "execution_order": ["task_1", "task_2", "task_3"],
  "parallel_groups": [
    ["task_a", "task_b"],
    ["task_c", "task_d"]
  ],
  "critical_path": ["task_1", "task_3", "task_5"],
  "blocking_tasks": ["task_1", "task_2"],
  "bottlenecks": [
    {
      "task_id": "bottleneck_task",
      "blocks_count": 5,
      "description": "Blocks 5 other tasks"
    }
  ]
}

Consider:
- Technical dependencies (API before UI)
- Resource dependencies (same skill set)
- Logical dependencies (design before implementation)
- Testing dependencies (implementation before tests)
""",
            
            'estimation_refinement': """
Refine these task estimates based on complexity analysis:

Tasks with estimates:
{tasks_with_estimates}

Project context:
- Team size: {team_size}
- Technology stack: {tech_stack}
- Timeline constraints: {timeline}

Generate refined estimates in this JSON format:
{
  "refined_estimates": {
    "task_id": {
      "original_estimate": {"value": 5, "unit": "story_points"},
      "refined_estimate": {
        "value": 8,
        "unit": "story_points", 
        "confidence": 0.75,
        "complexity_factors": [
          "Integration complexity higher than expected",
          "New technology learning curve"
        ]
      },
      "risk_factors": ["API changes", "Third-party dependency"],
      "assumptions": ["Team has React experience"]
    }
  },
  "total_estimate": {
    "optimistic": {"value": 45, "unit": "days"},
    "realistic": {"value": 60, "unit": "days"},
    "pessimistic": {"value": 80, "unit": "days"}
  }
}

Focus on:
- Historical data and team velocity
- Technology complexity
- Integration challenges
- Risk buffers
"""
        }

    async def decompose_requirements(self, analysis: RequirementAnalysis) -> TaskHierarchy:
        """Decompose requirements analysis into detailed task hierarchy"""
        
        all_tasks = []
        task_map = {}
        
        # Decompose each epic
        for epic in analysis.epics:
            epic_tasks = await self._decompose_epic(epic)
            all_tasks.extend(epic_tasks)
            
            for task in epic_tasks:
                task_map[task.id] = task
        
        # Analyze dependencies
        dependency_info = await self._analyze_task_dependencies(list(task_map.values()))
        
        # Calculate execution order
        execution_order = self._calculate_execution_order(task_map, dependency_info.get('dependency_graph', {}))
        
        # Identify parallel groups
        parallel_groups = dependency_info.get('parallel_groups', [])
        
        # Calculate critical path
        critical_path = dependency_info.get('critical_path', [])
        
        # Calculate total estimate
        total_estimate = self._calculate_total_estimate(list(task_map.values()))
        
        # Create milestone mapping
        milestone_mapping = self._create_milestone_mapping(analysis, list(task_map.values()))
        
        return TaskHierarchy(
            root_tasks=[t for t in all_tasks if not t.parent_id],
            task_map=task_map,
            dependency_graph=dependency_info.get('dependency_graph', {}),
            execution_order=execution_order,
            parallel_groups=parallel_groups,
            critical_path=critical_path,
            total_estimate=total_estimate,
            milestone_mapping=milestone_mapping
        )

    async def _decompose_epic(self, epic: Epic) -> List[DecomposedTask]:
        """Decompose an epic into detailed tasks"""
        
        existing_stories = [
            {
                'id': story.id,
                'title': story.title,
                'description': story.description,
                'acceptance_criteria': story.acceptance_criteria
            }
            for story in epic.user_stories
        ]
        
        template = self.decomposition_templates['epic_decomposition']
        prompt = template.replace('{epic_title}', epic.title)
        prompt = prompt.replace('{epic_description}', epic.description)
        prompt = prompt.replace('{epic_phase}', epic.phase.value)
        prompt = prompt.replace('{epic_priority}', epic.priority.value)
        prompt = prompt.replace('{existing_stories}', json.dumps(existing_stories, indent=2))
        
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            decomposition = json.loads(response)
            return await self._convert_decomposition_to_tasks(epic, decomposition)
        except json.JSONDecodeError:
            # Fallback decomposition
            return await self._fallback_epic_decomposition(epic)

    async def _convert_decomposition_to_tasks(self, epic: Epic, decomposition: Dict[str, Any]) -> List[DecomposedTask]:
        """Convert LLM decomposition result to task objects"""
        
        tasks = []
        
        # Create epic task
        epic_task = DecomposedTask(
            id=epic.id,
            title=epic.title,
            description=epic.description,
            task_type=TaskType.EPIC,
            priority=epic.priority,
            status=TaskStatus.BACKLOG,
            labels=[epic.phase.value],
            metadata={'phase': epic.phase.value}
        )
        tasks.append(epic_task)
        
        # Process user stories
        for story_data in decomposition.get('user_stories', []):
            story_task = DecomposedTask(
                id=story_data.get('id', str(uuid.uuid4())),
                title=story_data.get('title', ''),
                description=story_data.get('description', ''),
                task_type=TaskType.STORY,
                priority=Priority(story_data.get('priority', 'medium')),
                status=TaskStatus.BACKLOG,
                parent_id=epic.id,
                estimate=self._parse_estimate(story_data.get('estimate')),
                acceptance_criteria=self._parse_acceptance_criteria(story_data.get('acceptance_criteria', [])),
                labels=['story']
            )
            tasks.append(story_task)
            
            # Process technical tasks for this story
            for task_data in story_data.get('technical_tasks', []):
                tech_task = DecomposedTask(
                    id=task_data.get('id', str(uuid.uuid4())),
                    title=task_data.get('title', ''),
                    description=task_data.get('description', ''),
                    task_type=TaskType.TASK,
                    priority=Priority(task_data.get('priority', 'medium')),
                    status=TaskStatus.BACKLOG,
                    parent_id=story_task.id,
                    estimate=self._parse_estimate(task_data.get('estimate')),
                    dependencies=self._parse_dependencies(task_data.get('dependencies', [])),
                    labels=task_data.get('labels', [])
                )
                tasks.append(tech_task)
        
        # Process research spikes
        for spike_data in decomposition.get('research_spikes', []):
            spike_task = DecomposedTask(
                id=spike_data.get('id', str(uuid.uuid4())),
                title=spike_data.get('title', ''),
                description=spike_data.get('description', ''),
                task_type=TaskType.SPIKE,
                priority=Priority.HIGH,
                status=TaskStatus.BACKLOG,
                parent_id=epic.id,
                estimate=self._parse_estimate(spike_data.get('estimate')),
                labels=['research', 'spike']
            )
            tasks.append(spike_task)
        
        return tasks

    def _parse_estimate(self, estimate_data: Optional[Dict[str, Any]]) -> Optional[TaskEstimate]:
        """Parse estimate data into TaskEstimate object"""
        
        if not estimate_data:
            return None
        
        return TaskEstimate(
            value=estimate_data.get('value', 0),
            unit=EstimationUnit(estimate_data.get('unit', 'story_points')),
            confidence=estimate_data.get('confidence', 0.5),
            complexity_factors=estimate_data.get('complexity_factors', [])
        )

    def _parse_acceptance_criteria(self, criteria_list: List[Dict[str, Any]]) -> List[AcceptanceCriteria]:
        """Parse acceptance criteria data"""
        
        criteria = []
        for criterion_data in criteria_list:
            criterion = AcceptanceCriteria(
                id=criterion_data.get('id', str(uuid.uuid4())),
                description=criterion_data.get('description', ''),
                testable=criterion_data.get('testable', True),
                automated=criterion_data.get('automated', False)
            )
            criteria.append(criterion)
        
        return criteria

    def _parse_dependencies(self, deps_list: List[Dict[str, Any]]) -> List[TaskDependency]:
        """Parse dependency data"""
        
        dependencies = []
        for dep_data in deps_list:
            dependency = TaskDependency(
                task_id=dep_data.get('task_id', ''),
                dependency_type=dep_data.get('dependency_type', 'requires'),
                description=dep_data.get('description')
            )
            dependencies.append(dependency)
        
        return dependencies

    async def _fallback_epic_decomposition(self, epic: Epic) -> List[DecomposedTask]:
        """Fallback decomposition when LLM parsing fails"""
        
        tasks = []
        
        # Create epic task
        epic_task = DecomposedTask(
            id=epic.id,
            title=epic.title,
            description=epic.description,
            task_type=TaskType.EPIC,
            priority=epic.priority,
            status=TaskStatus.BACKLOG,
            labels=[epic.phase.value]
        )
        tasks.append(epic_task)
        
        # Convert existing user stories
        for story in epic.user_stories:
            story_task = DecomposedTask(
                id=story.id,
                title=story.title,
                description=story.description,
                task_type=TaskType.STORY,
                priority=story.priority,
                status=TaskStatus.BACKLOG,
                parent_id=epic.id,
                estimate=TaskEstimate(
                    value=story.estimated_effort or 5,
                    unit=EstimationUnit.STORY_POINTS,
                    confidence=0.5
                ),
                acceptance_criteria=[
                    AcceptanceCriteria(
                        id=str(uuid.uuid4()),
                        description=criterion
                    ) for criterion in story.acceptance_criteria
                ],
                labels=['story']
            )
            tasks.append(story_task)
        
        return tasks

    async def _analyze_task_dependencies(self, tasks: List[DecomposedTask]) -> Dict[str, Any]:
        """Analyze dependencies between tasks"""
        
        tasks_data = [
            {
                'id': task.id,
                'title': task.title,
                'type': task.task_type.value,
                'dependencies': [
                    {
                        'task_id': dep.task_id,
                        'type': dep.dependency_type
                    } for dep in task.dependencies
                ],
                'labels': task.labels
            }
            for task in tasks
        ]
        
        template = self.decomposition_templates['dependency_analysis']
        prompt = template.replace('{tasks_json}', json.dumps(tasks_data, indent=2))
        
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                'dependency_graph': {},
                'execution_order': [task.id for task in tasks],
                'parallel_groups': [],
                'critical_path': [],
                'blocking_tasks': []
            }

    def _calculate_execution_order(self, task_map: Dict[str, DecomposedTask], dependency_graph: Dict[str, List[str]]) -> List[str]:
        """Calculate optimal execution order using topological sort"""
        
        # Build adjacency list
        adj_list = {}
        in_degree = {}
        
        for task_id in task_map:
            adj_list[task_id] = []
            in_degree[task_id] = 0
        
        for task_id, dependencies in dependency_graph.items():
            for dep_id in dependencies:
                if dep_id in adj_list:
                    adj_list[dep_id].append(task_id)
                    in_degree[task_id] += 1
        
        # Topological sort using Kahn's algorithm
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        execution_order = []
        
        while queue:
            current = queue.pop(0)
            execution_order.append(current)
            
            for neighbor in adj_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return execution_order

    def _calculate_total_estimate(self, tasks: List[DecomposedTask]) -> TaskEstimate:
        """Calculate total project estimate"""
        
        total_story_points = 0
        total_hours = 0
        confidence_scores = []
        
        for task in tasks:
            if task.estimate:
                if task.estimate.unit == EstimationUnit.STORY_POINTS:
                    total_story_points += task.estimate.value
                elif task.estimate.unit == EstimationUnit.HOURS:
                    total_hours += task.estimate.value
                elif task.estimate.unit == EstimationUnit.DAYS:
                    total_hours += task.estimate.value * 8
                
                confidence_scores.append(task.estimate.confidence)
        
        # Convert story points to hours (assuming 1 SP = 4 hours)
        total_hours += total_story_points * 4
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        return TaskEstimate(
            value=total_hours,
            unit=EstimationUnit.HOURS,
            confidence=avg_confidence,
            complexity_factors=['Aggregated estimate']
        )

    def _create_milestone_mapping(self, analysis: RequirementAnalysis, tasks: List[DecomposedTask]) -> Dict[str, List[str]]:
        """Map tasks to project milestones"""
        
        milestones = {}
        
        # Group by phase from original analysis
        for phase_name, epic_ids in analysis.phases.items():
            milestone_tasks = []
            
            for task in tasks:
                if task.task_type == TaskType.EPIC and task.id in epic_ids:
                    milestone_tasks.append(task.id)
                elif task.parent_id in epic_ids:
                    milestone_tasks.append(task.id)
            
            milestones[f"Phase: {phase_name}"] = milestone_tasks
        
        return milestones

    async def refine_estimates(self, hierarchy: TaskHierarchy, context: Dict[str, Any]) -> TaskHierarchy:
        """Refine task estimates based on additional context"""
        
        tasks_with_estimates = [
            {
                'id': task.id,
                'title': task.title,
                'current_estimate': {
                    'value': task.estimate.value if task.estimate else 0,
                    'unit': task.estimate.unit.value if task.estimate else 'story_points',
                    'confidence': task.estimate.confidence if task.estimate else 0.5
                },
                'complexity_factors': task.estimate.complexity_factors if task.estimate else []
            }
            for task in hierarchy.task_map.values()
            if task.estimate
        ]
        
        template = self.decomposition_templates['estimation_refinement']
        prompt = template.replace('{tasks_with_estimates}', json.dumps(tasks_with_estimates, indent=2))
        prompt = prompt.replace('{team_size}', str(context.get('team_size', 'unknown')))
        prompt = prompt.replace('{tech_stack}', str(context.get('tech_stack', 'unknown')))
        prompt = prompt.replace('{timeline}', str(context.get('timeline', 'unknown')))
        
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            refinement_data = json.loads(response)
            
            # Update task estimates
            for task_id, refined_data in refinement_data.get('refined_estimates', {}).items():
                if task_id in hierarchy.task_map:
                    task = hierarchy.task_map[task_id]
                    refined_estimate = refined_data.get('refined_estimate', {})
                    
                    task.estimate = TaskEstimate(
                        value=refined_estimate.get('value', task.estimate.value if task.estimate else 0),
                        unit=EstimationUnit(refined_estimate.get('unit', 'story_points')),
                        confidence=refined_estimate.get('confidence', 0.5),
                        complexity_factors=refined_estimate.get('complexity_factors', [])
                    )
                    
                    # Add risk factors to metadata
                    task.metadata['risk_factors'] = refined_data.get('risk_factors', [])
                    task.metadata['assumptions'] = refined_data.get('assumptions', [])
            
            # Update total estimate
            total_estimate_data = refinement_data.get('total_estimate', {})
            realistic_estimate = total_estimate_data.get('realistic', {})
            
            hierarchy.total_estimate = TaskEstimate(
                value=realistic_estimate.get('value', hierarchy.total_estimate.value),
                unit=EstimationUnit(realistic_estimate.get('unit', 'days')),
                confidence=0.7,
                complexity_factors=['Refined estimate with context']
            )
            
        except json.JSONDecodeError:
            pass  # Keep original estimates if refinement fails
        
        return hierarchy