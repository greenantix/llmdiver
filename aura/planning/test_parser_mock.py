"""
Test PRDParser with Mock LLM Provider
"""

import asyncio
import json
from pathlib import Path
import sys

# Add the parent directory to the path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from aura.core.config import AuraConfig
from aura.llm.providers import LLMProvider, LLMRequest, LLMResponse
from aura.planning.prd_parser import PRDParser


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing"""
    
    def __init__(self):
        super().__init__({'base_url': 'mock', 'timeout': 10})
    
    def _get_model_mappings(self):
        return {}
    
    async def is_available(self) -> bool:
        return True
    
    async def get_available_models(self):
        return ['mock-model']
    
    async def generate_completion(self, request: LLMRequest) -> LLMResponse:
        # Mock response based on prompt content
        content = ""
        
        if "epic_decomposition" in request.prompt.lower() or ("decompose this epic" in request.prompt.lower()):
            content = '''
{
  "user_stories": [
    {
      "id": "story_arch_1",
      "title": "As a developer, I want a message bus so that modules can communicate",
      "description": "Implement ZeroMQ message bus for inter-module communication",
      "priority": "high",
      "estimate": {
        "value": 5,
        "unit": "story_points",
        "confidence": 0.8,
        "complexity_factors": ["ZeroMQ integration", "Message routing"]
      },
      "acceptance_criteria": [
        {
          "id": "ac_1",
          "description": "Message bus can route messages between modules",
          "testable": true,
          "automated": true
        }
      ],
      "technical_tasks": [
        {
          "id": "task_zmq_setup",
          "title": "Set up ZeroMQ infrastructure",
          "description": "Configure ZeroMQ sockets and connection patterns",
          "task_type": "task",
          "priority": "high",
          "estimate": {
            "value": 2,
            "unit": "days",
            "confidence": 0.9,
            "complexity_factors": ["ZeroMQ configuration"]
          },
          "dependencies": [],
          "labels": ["backend", "infrastructure", "zmq"]
        },
        {
          "id": "task_message_routing",
          "title": "Implement message routing logic",
          "description": "Create message routing and subscription system",
          "task_type": "task", 
          "priority": "high",
          "estimate": {
            "value": 3,
            "unit": "days",
            "confidence": 0.8,
            "complexity_factors": ["Message patterns", "Error handling"]
          },
          "dependencies": [
            {
              "task_id": "task_zmq_setup",
              "dependency_type": "requires",
              "description": "Need ZeroMQ setup first"
            }
          ],
          "labels": ["backend", "messaging", "routing"]
        }
      ]
    }
  ],
  "research_spikes": [
    {
      "id": "spike_zmq_patterns",
      "title": "Research ZeroMQ message patterns",
      "description": "Investigate best ZeroMQ patterns for microservices communication",
      "estimate": {
        "value": 1,
        "unit": "days",
        "confidence": 0.7
      }
    }
  ]
}
'''
        elif "story_decomposition" in request.prompt.lower():
            content = '''
{
  "implementation_tasks": [
    {
      "id": "impl_story_core",
      "title": "Implement core story functionality",
      "description": "Core implementation logic for the user story",
      "task_type": "task",
      "priority": "high",
      "estimate": {
        "value": 6,
        "unit": "hours",
        "confidence": 0.85,
        "complexity_factors": ["Business logic complexity"]
      },
      "dependencies": [],
      "labels": ["implementation", "core"],
      "subtasks": [
        {
          "id": "subtask_models",
          "title": "Create data models",
          "description": "Define data structures and models",
          "estimate": {
            "value": 2,
            "unit": "hours",
            "confidence": 0.9
          }
        },
        {
          "id": "subtask_logic",
          "title": "Implement business logic",
          "description": "Core business logic implementation",
          "estimate": {
            "value": 4,
            "unit": "hours",
            "confidence": 0.8
          }
        }
      ]
    }
  ],
  "testing_tasks": [
    {
      "id": "test_story",
      "title": "Test story implementation",
      "description": "Unit and integration tests for the story",
      "task_type": "task",
      "priority": "high",
      "labels": ["testing", "qa"]
    }
  ],
  "documentation_tasks": [
    {
      "id": "doc_story",
      "title": "Document story implementation",
      "description": "API documentation and usage examples",
      "task_type": "task",
      "priority": "medium",
      "labels": ["documentation"]
    }
  ]
}
'''
        elif "dependency_analysis" in request.prompt.lower():
            content = '''
{
  "dependency_graph": {
    "task_zmq_setup": [],
    "task_message_routing": ["task_zmq_setup"],
    "task_api_contracts": ["task_zmq_setup"]
  },
  "execution_order": ["task_zmq_setup", "task_message_routing", "task_api_contracts"],
  "parallel_groups": [
    ["task_message_routing", "task_api_contracts"]
  ],
  "critical_path": ["task_zmq_setup", "task_message_routing"],
  "blocking_tasks": ["task_zmq_setup"],
  "bottlenecks": [
    {
      "task_id": "task_zmq_setup",
      "blocks_count": 2,
      "description": "Blocks message routing and API tasks"
    }
  ]
}
'''
        elif "estimation_refinement" in request.prompt.lower():
            content = '''
{
  "refined_estimates": {
    "task_zmq_setup": {
      "original_estimate": {"value": 2, "unit": "days"},
      "refined_estimate": {
        "value": 3,
        "unit": "days",
        "confidence": 0.8,
        "complexity_factors": [
          "ZeroMQ learning curve",
          "Configuration complexity"
        ]
      },
      "risk_factors": ["New technology", "Integration challenges"],
      "assumptions": ["Team has basic networking experience"]
    }
  },
  "total_estimate": {
    "optimistic": {"value": 30, "unit": "days"},
    "realistic": {"value": 45, "unit": "days"},
    "pessimistic": {"value": 60, "unit": "days"}
  }
}
'''
        elif "optimization" in request.prompt.lower():
            content = '''
{
  "optimization_strategies": [
    {
      "type": "parallelization",
      "description": "Run UI and API development in parallel",
      "tasks_affected": ["task_ui", "task_api"],
      "time_savings_days": 5,
      "risk_level": "low",
      "requirements": ["Frontend and backend developers"]
    },
    {
      "type": "dependency_elimination",
      "description": "Remove unnecessary dependency between testing tasks",
      "tasks_affected": ["task_test_a", "task_test_b"],
      "time_savings_days": 2,
      "risk_level": "medium",
      "requirements": ["Independent test environments"]
    }
  ],
  "resource_optimizations": [
    {
      "resource_type": "developer",
      "current_utilization": 1.1,
      "recommended_allocation": 1.0,
      "affected_tasks": ["task_complex_feature"]
    }
  ],
  "risk_mitigations": [
    {
      "risk": "Critical path task has high uncertainty",
      "mitigation": "Add buffer time and create fallback plan",
      "impact": "Reduces schedule risk by 20%"
    }
  ]
}
'''
        elif "epics" in request.prompt.lower():
            content = '''
{
  "epics": [
    {
      "id": "epic_1_1",
      "title": "Core System Architecture",
      "description": "Design and implement the microservices-inspired architecture",
      "phase": "foundation",
      "priority": "critical",
      "success_metrics": ["Architecture documented", "Message bus functional"],
      "user_stories": [
        {
          "id": "story_1_1_1",
          "title": "As a developer, I want a robust architecture so that the system is reliable",
          "description": "Design the microservices-inspired architecture",
          "persona": "developer",
          "acceptance_criteria": ["API contracts defined", "Message bus implemented"],
          "priority": "high",
          "estimated_effort": 8,
          "tags": ["architecture", "core"]
        }
      ]
    }
  ]
}
'''
        elif "technical_requirements" in request.prompt.lower():
            content = '''
{
  "technical_requirements": [
    {
      "id": "tech_req_1",
      "title": "Response Time Requirements",
      "description": "The AI should respond to interactive prompts in under 500ms",
      "category": "performance",
      "specifications": {
        "response_time": "500ms",
        "throughput": "100k lines in 5 minutes",
        "memory_usage": "2GB max"
      },
      "acceptance_criteria": ["Response time measured", "Performance benchmarks met"],
      "priority": "high"
    }
  ]
}
'''
        elif "dependencies" in request.prompt.lower():
            content = '''
{
  "dependencies": {
    "epic_1_1": ["epic_1_2"]
  },
  "critical_path": ["epic_1_1", "epic_1_2"],
  "parallel_tracks": [
    ["epic_2_1", "epic_2_2"]
  ]
}
'''
        elif "complexity" in request.prompt.lower():
            content = '''
{
  "complexity_analysis": {
    "overall_score": 0.75,
    "factors": {
      "technical_complexity": 0.8,
      "integration_complexity": 0.7,
      "domain_complexity": 0.6
    }
  },
  "timeline_estimation": {
    "phase_1": 90,
    "phase_2": 60, 
    "phase_3": 90,
    "total_days": 240
  },
  "risk_factors": [
    "LLM API integration complexity",
    "Multi-language AST parsing challenges"
  ]
}
'''
        else:
            content = '{"message": "Mock response"}'
        
        return LLMResponse(
            request_id=request.request_id,
            content=content,
            model_used='mock-model',
            tokens_used=100,
            processing_time=0.1
        )


async def test_prd_parser_mock():
    """Test the PRDParser with mock LLM provider"""
    
    # Initialize configuration
    config = AuraConfig()
    
    # Initialize mock LLM provider
    llm_provider = MockLLMProvider()
    
    # Initialize parser
    parser = PRDParser(config, llm_provider)
    
    # Parse the PRD file
    prd_path = Path("/home/greenantix/AI/LLMdiver/PRD.md")
    
    print("🔍 Testing PRDParser with mock LLM...")
    print(f"File path: {prd_path}")
    print(f"File exists: {prd_path.exists()}")
    
    try:
        # Parse the PRD
        analysis = await parser.parse_prd_file(prd_path)
        
        print("\n✅ PRD Analysis Complete!")
        print(f"Document Version: {analysis.document_version}")
        print(f"Analysis Timestamp: {analysis.analysis_timestamp}")
        print(f"Number of Epics: {len(analysis.epics)}")
        print(f"Number of Technical Requirements: {len(analysis.technical_requirements)}")
        print(f"Number of User Personas: {len(analysis.user_personas)}")
        print(f"Complexity Score: {analysis.complexity_score}")
        print(f"Estimated Timeline: {analysis.estimated_timeline}")
        
        # Display epics
        print("\n📋 Epics Found:")
        for epic in analysis.epics:
            print(f"  - {epic.id}: {epic.title}")
            print(f"    Phase: {epic.phase.value}")
            print(f"    Priority: {epic.priority.value}")
            print(f"    User Stories: {len(epic.user_stories)}")
            
            for story in epic.user_stories:
                print(f"      * {story.id}: {story.title}")
        
        # Display technical requirements
        print("\n⚙️ Technical Requirements:")
        for req in analysis.technical_requirements:
            print(f"  - {req.id}: {req.title}")
            print(f"    Category: {req.category}")
            print(f"    Priority: {req.priority.value}")
        
        # Display user personas
        print("\n👥 User Personas:")
        for persona_name, persona_data in analysis.user_personas.items():
            print(f"  - {persona_name}: {persona_data.get('title', 'N/A')}")
        
        # Display dependencies
        print("\n🔗 Dependencies:")
        for item_id, deps in analysis.dependencies.items():
            if deps:
                print(f"  - {item_id}: {deps}")
        
        # Display phases
        print("\n📅 Phases:")
        for phase_name, epic_ids in analysis.phases.items():
            print(f"  - {phase_name}: {len(epic_ids)} epics")
        
        print("\n🎉 PRDParser test completed successfully!")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error parsing PRD: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_prd_parser_mock())