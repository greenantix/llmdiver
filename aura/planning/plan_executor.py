"""
Plan Executor - Autonomous Execution of Development Plans
Orchestrates the execution of task hierarchies and dependency graphs
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable
import uuid

from ..core.config import AuraConfig
from ..llm.providers import LLMProvider
from .prd_parser import RequirementAnalysis
from .task_decomposer import TaskHierarchy, DecomposedTask, TaskStatus, TaskType
from .dependency_grapher import DependencyGraph


class ExecutionStatus(Enum):
    PLANNED = "planned"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionMode(Enum):
    AUTOMATIC = "automatic"
    SEMI_AUTOMATIC = "semi_automatic"
    MANUAL = "manual"


@dataclass
class ExecutionEvent:
    timestamp: datetime
    event_type: str
    task_id: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionMetrics:
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_in_progress: int = 0
    total_time_spent: timedelta = field(default_factory=lambda: timedelta())
    estimated_remaining: timedelta = field(default_factory=lambda: timedelta())
    velocity: float = 0.0  # tasks per day
    efficiency: float = 0.0  # actual vs estimated time
    
    @property
    def completion_percentage(self) -> float:
        total = self.tasks_completed + self.tasks_failed + self.tasks_in_progress
        return (self.tasks_completed / total * 100) if total > 0 else 0


@dataclass
class ExecutionPlan:
    id: str
    name: str
    description: str
    requirement_analysis: RequirementAnalysis
    task_hierarchy: TaskHierarchy
    dependency_graph: DependencyGraph
    execution_mode: ExecutionMode
    status: ExecutionStatus
    current_task: Optional[str] = None
    execution_queue: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    execution_events: List[ExecutionEvent] = field(default_factory=list)
    metrics: ExecutionMetrics = field(default_factory=ExecutionMetrics)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskExecutor:
    """Interface for executing specific types of tasks"""
    
    async def can_execute(self, task: DecomposedTask) -> bool:
        """Check if this executor can handle the given task"""
        raise NotImplementedError
    
    async def execute_task(self, task: DecomposedTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the task and return results"""
        raise NotImplementedError


class CodeGenerationExecutor(TaskExecutor):
    """Executor for code generation tasks"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
    
    async def can_execute(self, task: DecomposedTask) -> bool:
        return any(label in task.labels for label in ['code', 'implementation', 'coding'])
    
    async def execute_task(self, task: DecomposedTask, context: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder for code generation logic
        return {
            'status': 'completed',
            'files_created': [],
            'files_modified': [],
            'output': f"Code generation completed for {task.title}"
        }


class DocumentationExecutor(TaskExecutor):
    """Executor for documentation tasks"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
    
    async def can_execute(self, task: DecomposedTask) -> bool:
        return any(label in task.labels for label in ['docs', 'documentation', 'readme'])
    
    async def execute_task(self, task: DecomposedTask, context: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder for documentation generation logic
        return {
            'status': 'completed',
            'files_created': [],
            'output': f"Documentation completed for {task.title}"
        }


class TestingExecutor(TaskExecutor):
    """Executor for testing tasks"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
    
    async def can_execute(self, task: DecomposedTask) -> bool:
        return any(label in task.labels for label in ['test', 'testing', 'qa'])
    
    async def execute_task(self, task: DecomposedTask, context: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder for test execution logic
        return {
            'status': 'completed',
            'tests_passed': 0,
            'tests_failed': 0,
            'output': f"Testing completed for {task.title}"
        }


class PlanExecutor:
    def __init__(self, config: AuraConfig, llm_provider: LLMProvider):
        self.config = config
        self.llm_provider = llm_provider
        self.active_plans: Dict[str, ExecutionPlan] = {}
        self.executors: List[TaskExecutor] = [
            CodeGenerationExecutor(llm_provider),
            DocumentationExecutor(llm_provider),
            TestingExecutor(llm_provider)
        ]
        self.execution_callbacks: List[Callable] = []
        
    def register_task_executor(self, executor: TaskExecutor):
        """Register a new task executor"""
        self.executors.append(executor)
    
    def register_execution_callback(self, callback: Callable):
        """Register a callback to be called on execution events"""
        self.execution_callbacks.append(callback)
    
    async def create_execution_plan(
        self,
        name: str,
        description: str,
        requirement_analysis: RequirementAnalysis,
        task_hierarchy: TaskHierarchy,
        dependency_graph: DependencyGraph,
        execution_mode: ExecutionMode = ExecutionMode.SEMI_AUTOMATIC
    ) -> ExecutionPlan:
        """Create a new execution plan"""
        
        plan_id = str(uuid.uuid4())
        
        # Calculate execution queue based on dependency graph
        execution_queue = self._calculate_execution_queue(dependency_graph)
        
        plan = ExecutionPlan(
            id=plan_id,
            name=name,
            description=description,
            requirement_analysis=requirement_analysis,
            task_hierarchy=task_hierarchy,
            dependency_graph=dependency_graph,
            execution_mode=execution_mode,
            status=ExecutionStatus.PLANNED,
            execution_queue=execution_queue
        )
        
        self.active_plans[plan_id] = plan
        
        await self._emit_event(plan, "plan_created", "", f"Execution plan '{name}' created")
        
        return plan
    
    def _calculate_execution_queue(self, dependency_graph: DependencyGraph) -> List[str]:
        """Calculate optimal execution order considering dependencies"""
        
        # Use the execution order from dependency graph analysis
        if dependency_graph.execution_order:
            return dependency_graph.execution_order.copy()
        
        # Fallback: simple topological sort
        queue = []
        remaining_tasks = set(dependency_graph.nodes.keys())
        
        while remaining_tasks:
            # Find tasks with no unmet dependencies
            ready_tasks = []
            for task_id in remaining_tasks:
                dependencies_met = True
                for edge in dependency_graph.edges:
                    if edge.to_task == task_id and edge.from_task in remaining_tasks:
                        dependencies_met = False
                        break
                
                if dependencies_met:
                    ready_tasks.append(task_id)
            
            # Add ready tasks to queue
            if ready_tasks:
                # Sort by priority (critical path tasks first)
                critical_tasks = [t for t in ready_tasks if t in dependency_graph.critical_path]
                non_critical_tasks = [t for t in ready_tasks if t not in dependency_graph.critical_path]
                
                queue.extend(critical_tasks)
                queue.extend(non_critical_tasks)
                
                for task_id in ready_tasks:
                    remaining_tasks.remove(task_id)
            else:
                # Break circular dependencies by adding remaining tasks
                queue.extend(list(remaining_tasks))
                break
        
        return queue
    
    async def start_execution(self, plan_id: str) -> bool:
        """Start executing a plan"""
        
        if plan_id not in self.active_plans:
            return False
        
        plan = self.active_plans[plan_id]
        
        if plan.status != ExecutionStatus.PLANNED:
            return False
        
        plan.status = ExecutionStatus.RUNNING
        plan.started_at = datetime.now()
        
        await self._emit_event(plan, "execution_started", "", f"Execution started for plan '{plan.name}'")
        
        # Start execution in background
        asyncio.create_task(self._execute_plan(plan))
        
        return True
    
    async def _execute_plan(self, plan: ExecutionPlan):
        """Execute a plan according to its execution mode"""
        
        try:
            if plan.execution_mode == ExecutionMode.AUTOMATIC:
                await self._execute_automatic(plan)
            elif plan.execution_mode == ExecutionMode.SEMI_AUTOMATIC:
                await self._execute_semi_automatic(plan)
            else:
                await self._execute_manual(plan)
            
            plan.status = ExecutionStatus.COMPLETED
            plan.completed_at = datetime.now()
            
            await self._emit_event(plan, "execution_completed", "", f"Execution completed for plan '{plan.name}'")
            
        except Exception as e:
            plan.status = ExecutionStatus.FAILED
            await self._emit_event(plan, "execution_failed", "", f"Execution failed: {str(e)}")
    
    async def _execute_automatic(self, plan: ExecutionPlan):
        """Fully automatic execution"""
        
        for task_id in plan.execution_queue:
            if plan.status != ExecutionStatus.RUNNING:
                break
            
            await self._execute_single_task(plan, task_id)
            await asyncio.sleep(0.1)  # Small delay for monitoring
    
    async def _execute_semi_automatic(self, plan: ExecutionPlan):
        """Semi-automatic execution with user confirmation for critical tasks"""
        
        for task_id in plan.execution_queue:
            if plan.status != ExecutionStatus.RUNNING:
                break
            
            task = plan.task_hierarchy.task_map.get(task_id)
            if not task:
                continue
            
            # Check if task requires confirmation
            requires_confirmation = (
                task.priority.value == 'critical' or
                task.task_type == TaskType.EPIC or
                task_id in plan.dependency_graph.critical_path
            )
            
            if requires_confirmation:
                # Wait for user confirmation (in real implementation)
                await self._emit_event(plan, "confirmation_required", task_id, 
                                     f"User confirmation required for {task.title}")
                # For now, auto-approve
                await asyncio.sleep(1)
            
            await self._execute_single_task(plan, task_id)
    
    async def _execute_manual(self, plan: ExecutionPlan):
        """Manual execution - wait for user to trigger each task"""
        
        await self._emit_event(plan, "manual_mode", "", "Plan in manual mode - waiting for user actions")
        
        # In manual mode, tasks are executed only when explicitly triggered
        # This method just sets up the plan for manual execution
        pass
    
    async def _execute_single_task(self, plan: ExecutionPlan, task_id: str) -> bool:
        """Execute a single task"""
        
        task = plan.task_hierarchy.task_map.get(task_id)
        if not task:
            return False
        
        plan.current_task = task_id
        task.status = TaskStatus.IN_PROGRESS
        plan.metrics.tasks_in_progress += 1
        
        await self._emit_event(plan, "task_started", task_id, f"Started executing {task.title}")
        
        start_time = datetime.now()
        
        try:
            # Find appropriate executor
            executor = await self._find_executor(task)
            
            if executor:
                # Execute the task
                context = {
                    'plan': plan,
                    'task': task,
                    'project_root': Path.cwd(),
                    'config': self.config
                }
                
                result = await executor.execute_task(task, context)
                
                # Process results
                if result.get('status') == 'completed':
                    task.status = TaskStatus.DONE
                    plan.completed_tasks.append(task_id)
                    plan.metrics.tasks_completed += 1
                    
                    await self._emit_event(plan, "task_completed", task_id, 
                                         f"Completed {task.title}")
                else:
                    task.status = TaskStatus.BLOCKED
                    plan.failed_tasks.append(task_id)
                    plan.metrics.tasks_failed += 1
                    
                    await self._emit_event(plan, "task_failed", task_id, 
                                         f"Failed {task.title}: {result.get('error', 'Unknown error')}")
            else:
                # No executor found - mark as blocked
                task.status = TaskStatus.BLOCKED
                plan.failed_tasks.append(task_id)
                plan.metrics.tasks_failed += 1
                
                await self._emit_event(plan, "task_skipped", task_id, 
                                     f"No executor available for {task.title}")
            
        except Exception as e:
            task.status = TaskStatus.BLOCKED
            plan.failed_tasks.append(task_id)
            plan.metrics.tasks_failed += 1
            
            await self._emit_event(plan, "task_error", task_id, 
                                 f"Error executing {task.title}: {str(e)}")
        
        finally:
            end_time = datetime.now()
            execution_time = end_time - start_time
            plan.metrics.total_time_spent += execution_time
            plan.metrics.tasks_in_progress -= 1
            
            # Update velocity
            if plan.started_at:
                total_duration = end_time - plan.started_at
                if total_duration.total_seconds() > 0:
                    plan.metrics.velocity = plan.metrics.tasks_completed / (total_duration.days or 1)
            
            plan.current_task = None
        
        return task.status == TaskStatus.DONE
    
    async def _find_executor(self, task: DecomposedTask) -> Optional[TaskExecutor]:
        """Find the appropriate executor for a task"""
        
        for executor in self.executors:
            if await executor.can_execute(task):
                return executor
        
        return None
    
    async def _emit_event(self, plan: ExecutionPlan, event_type: str, task_id: str, description: str):
        """Emit an execution event"""
        
        event = ExecutionEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            task_id=task_id,
            description=description
        )
        
        plan.execution_events.append(event)
        
        # Call registered callbacks
        for callback in self.execution_callbacks:
            try:
                await callback(event, plan)
            except Exception as e:
                print(f"Error in execution callback: {e}")
    
    async def pause_execution(self, plan_id: str) -> bool:
        """Pause execution of a plan"""
        
        if plan_id not in self.active_plans:
            return False
        
        plan = self.active_plans[plan_id]
        
        if plan.status == ExecutionStatus.RUNNING:
            plan.status = ExecutionStatus.PAUSED
            await self._emit_event(plan, "execution_paused", "", "Execution paused")
            return True
        
        return False
    
    async def resume_execution(self, plan_id: str) -> bool:
        """Resume execution of a paused plan"""
        
        if plan_id not in self.active_plans:
            return False
        
        plan = self.active_plans[plan_id]
        
        if plan.status == ExecutionStatus.PAUSED:
            plan.status = ExecutionStatus.RUNNING
            await self._emit_event(plan, "execution_resumed", "", "Execution resumed")
            
            # Continue execution
            asyncio.create_task(self._execute_plan(plan))
            return True
        
        return False
    
    async def cancel_execution(self, plan_id: str) -> bool:
        """Cancel execution of a plan"""
        
        if plan_id not in self.active_plans:
            return False
        
        plan = self.active_plans[plan_id]
        plan.status = ExecutionStatus.CANCELLED
        
        await self._emit_event(plan, "execution_cancelled", "", "Execution cancelled")
        
        return True
    
    def get_plan_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a plan"""
        
        if plan_id not in self.active_plans:
            return None
        
        plan = self.active_plans[plan_id]
        
        return {
            'id': plan.id,
            'name': plan.name,
            'status': plan.status.value,
            'current_task': plan.current_task,
            'progress': plan.metrics.completion_percentage,
            'tasks_completed': plan.metrics.tasks_completed,
            'tasks_failed': plan.metrics.tasks_failed,
            'tasks_remaining': len(plan.execution_queue) - len(plan.completed_tasks) - len(plan.failed_tasks),
            'velocity': plan.metrics.velocity,
            'estimated_completion': self._estimate_completion_time(plan),
            'recent_events': plan.execution_events[-5:]  # Last 5 events
        }
    
    def _estimate_completion_time(self, plan: ExecutionPlan) -> Optional[datetime]:
        """Estimate when the plan will be completed"""
        
        if plan.metrics.velocity <= 0:
            return None
        
        remaining_tasks = len(plan.execution_queue) - len(plan.completed_tasks) - len(plan.failed_tasks)
        
        if remaining_tasks <= 0:
            return datetime.now()
        
        days_remaining = remaining_tasks / plan.metrics.velocity
        return datetime.now() + timedelta(days=days_remaining)
    
    def list_active_plans(self) -> List[Dict[str, Any]]:
        """List all active execution plans"""
        
        return [
            {
                'id': plan.id,
                'name': plan.name,
                'status': plan.status.value,
                'created_at': plan.created_at.isoformat(),
                'progress': plan.metrics.completion_percentage
            }
            for plan in self.active_plans.values()
        ]
    
    async def save_plan(self, plan_id: str, file_path: Path) -> bool:
        """Save an execution plan to file"""
        
        if plan_id not in self.active_plans:
            return False
        
        plan = self.active_plans[plan_id]
        
        # Convert plan to serializable format
        plan_data = {
            'id': plan.id,
            'name': plan.name,
            'description': plan.description,
            'execution_mode': plan.execution_mode.value,
            'status': plan.status.value,
            'created_at': plan.created_at.isoformat(),
            'started_at': plan.started_at.isoformat() if plan.started_at else None,
            'completed_at': plan.completed_at.isoformat() if plan.completed_at else None,
            'execution_queue': plan.execution_queue,
            'completed_tasks': plan.completed_tasks,
            'failed_tasks': plan.failed_tasks,
            'metrics': {
                'tasks_completed': plan.metrics.tasks_completed,
                'tasks_failed': plan.metrics.tasks_failed,
                'completion_percentage': plan.metrics.completion_percentage,
                'velocity': plan.metrics.velocity
            },
            'events': [
                {
                    'timestamp': event.timestamp.isoformat(),
                    'type': event.event_type,
                    'task_id': event.task_id,
                    'description': event.description
                }
                for event in plan.execution_events
            ]
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(plan_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving plan: {e}")
            return False