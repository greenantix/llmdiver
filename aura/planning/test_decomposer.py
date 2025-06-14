"""
Test TaskDecomposer - Empower the Decomposer
"""

import asyncio
import json
from pathlib import Path
import sys

# Add the parent directory to the path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from aura.core.config import AuraConfig
from aura.planning.test_parser_mock import MockLLMProvider
from aura.planning.prd_parser import PRDParser
from aura.planning.task_decomposer import TaskDecomposer
from aura.planning.dependency_grapher import DependencyGrapher


async def test_task_decomposer():
    """Test the TaskDecomposer with parsed requirements"""
    
    # Initialize configuration
    config = AuraConfig()
    
    # Initialize mock LLM provider
    llm_provider = MockLLMProvider()
    
    # Initialize parser and decomposer
    parser = PRDParser(config, llm_provider)
    decomposer = TaskDecomposer(config, llm_provider)
    dependency_grapher = DependencyGrapher(config, llm_provider)
    
    print("🔧 Testing TaskDecomposer...")
    
    try:
        # First, parse the PRD to get requirements
        prd_path = Path("/home/greenantix/AI/LLMdiver/PRD.md")
        analysis = await parser.parse_prd_file(prd_path)
        
        print(f"\n📋 Parsed {len(analysis.epics)} epics from PRD")
        
        # Decompose requirements into detailed task hierarchy
        print("\n🔨 Decomposing requirements into task hierarchy...")
        task_hierarchy = await decomposer.decompose_requirements(analysis)
        
        print("\n✅ Task Decomposition Complete!")
        print(f"Root Tasks: {len(task_hierarchy.root_tasks)}")
        print(f"Total Tasks: {len(task_hierarchy.task_map)}")
        
        # Display task hierarchy
        print("\n📊 Task Hierarchy:")
        for root_task in task_hierarchy.root_tasks:
            _print_task_tree(root_task, task_hierarchy.task_map, 0)
        
        # Display execution order
        print(f"\n⚡ Execution Order ({len(task_hierarchy.execution_order)} tasks):")
        for i, task_id in enumerate(task_hierarchy.execution_order[:10]):  # Show first 10
            task = task_hierarchy.task_map.get(task_id)
            if task:
                print(f"  {i+1}. {task.title} ({task.task_type.value})")
        if len(task_hierarchy.execution_order) > 10:
            print(f"  ... and {len(task_hierarchy.execution_order) - 10} more tasks")
        
        # Display parallel groups
        if task_hierarchy.parallel_groups:
            print(f"\n🔀 Parallel Execution Groups ({len(task_hierarchy.parallel_groups)}):")
            for i, group in enumerate(task_hierarchy.parallel_groups[:3]):  # Show first 3
                print(f"  Group {i+1}: {len(group)} tasks can run in parallel")
                for task_id in group[:3]:  # Show first 3 tasks in group
                    task = task_hierarchy.task_map.get(task_id)
                    if task:
                        print(f"    - {task.title}")
        
        # Display critical path
        if task_hierarchy.critical_path:
            print(f"\n🎯 Critical Path ({len(task_hierarchy.critical_path)} tasks):")
            for task_id in task_hierarchy.critical_path[:5]:  # Show first 5
                task = task_hierarchy.task_map.get(task_id)
                if task:
                    print(f"  → {task.title}")
        
        # Display total estimate
        print(f"\n⏱️ Total Project Estimate:")
        print(f"  Value: {task_hierarchy.total_estimate.value}")
        print(f"  Unit: {task_hierarchy.total_estimate.unit.value}")
        print(f"  Confidence: {task_hierarchy.total_estimate.confidence:.1%}")
        
        # Display milestone mapping
        print(f"\n🏁 Milestone Mapping:")
        for milestone, task_ids in task_hierarchy.milestone_mapping.items():
            print(f"  {milestone}: {len(task_ids)} tasks")
        
        # Create dependency graph
        print("\n🕸️ Creating dependency graph...")
        dependency_graph = await dependency_grapher.create_dependency_graph(task_hierarchy)
        
        print("\n✅ Dependency Analysis Complete!")
        print(f"Dependencies: {len(dependency_graph.edges)}")
        print(f"Critical Path: {len(dependency_graph.critical_path)} tasks")
        print(f"Parallel Groups: {len(dependency_graph.parallel_execution_groups)}")
        print(f"Bottlenecks: {len(dependency_graph.bottleneck_tasks)}")
        print(f"Project Duration: {dependency_graph.estimated_duration.days} days")
        
        # Display optimization suggestions
        if dependency_graph.optimization_suggestions:
            print(f"\n💡 Optimization Suggestions:")
            for suggestion in dependency_graph.optimization_suggestions[:3]:
                if isinstance(suggestion, dict):
                    print(f"  • {suggestion.get('description', 'Optimization opportunity')}")
                    print(f"    Type: {suggestion.get('type', 'unknown')}")
                    print(f"    Time Savings: {suggestion.get('time_savings_days', 0)} days")
        
        # Test estimation refinement
        print("\n🔧 Testing estimate refinement...")
        context = {
            'team_size': 3,
            'tech_stack': 'Python, TypeScript, React',
            'timeline': '6 months'
        }
        
        refined_hierarchy = await decomposer.refine_estimates(task_hierarchy, context)
        
        print(f"Refined Total Estimate: {refined_hierarchy.total_estimate.value} {refined_hierarchy.total_estimate.unit.value}")
        print(f"Refined Confidence: {refined_hierarchy.total_estimate.confidence:.1%}")
        
        # Save results for inspection
        output_file = Path("/home/greenantix/AI/LLMdiver/aura/planning/task_hierarchy.json")
        hierarchy_data = {
            'total_tasks': len(task_hierarchy.task_map),
            'root_tasks': len(task_hierarchy.root_tasks),
            'execution_order': task_hierarchy.execution_order,
            'parallel_groups': task_hierarchy.parallel_groups,
            'critical_path': task_hierarchy.critical_path,
            'total_estimate': {
                'value': task_hierarchy.total_estimate.value,
                'unit': task_hierarchy.total_estimate.unit.value,
                'confidence': task_hierarchy.total_estimate.confidence
            },
            'milestone_mapping': task_hierarchy.milestone_mapping,
            'dependency_graph': {
                'edges_count': len(dependency_graph.edges),
                'critical_path_length': len(dependency_graph.critical_path),
                'parallel_groups_count': len(dependency_graph.parallel_execution_groups),
                'estimated_duration_days': dependency_graph.estimated_duration.days,
                'optimization_suggestions_count': len(dependency_graph.optimization_suggestions)
            },
            'sample_tasks': [
                {
                    'id': task.id,
                    'title': task.title,
                    'type': task.task_type.value,
                    'priority': task.priority.value,
                    'status': task.status.value,
                    'estimate': {
                        'value': task.estimate.value if task.estimate else None,
                        'unit': task.estimate.unit.value if task.estimate else None,
                        'confidence': task.estimate.confidence if task.estimate else None
                    } if task.estimate else None,
                    'dependencies_count': len(task.dependencies),
                    'acceptance_criteria_count': len(task.acceptance_criteria),
                    'labels': task.labels
                }
                for task in list(task_hierarchy.task_map.values())[:10]  # First 10 tasks
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(hierarchy_data, f, indent=2)
        
        print(f"\n💾 Task hierarchy saved to: {output_file}")
        
        print("\n🎉 TaskDecomposer test completed successfully!")
        
        return task_hierarchy, dependency_graph
        
    except Exception as e:
        print(f"❌ Error in task decomposition: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def _print_task_tree(task, task_map, indent=0):
    """Print task hierarchy as a tree"""
    indent_str = "  " * indent
    estimate_str = ""
    if task.estimate:
        estimate_str = f" ({task.estimate.value} {task.estimate.unit.value})"
    
    print(f"{indent_str}- {task.title} [{task.task_type.value}]{estimate_str}")
    
    # Find child tasks
    children = [t for t in task_map.values() if t.parent_id == task.id]
    for child in children:
        _print_task_tree(child, task_map, indent + 1)


if __name__ == "__main__":
    asyncio.run(test_task_decomposer())