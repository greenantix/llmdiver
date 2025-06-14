"""
Test script for PRDParser - Animate the Parser
"""

import asyncio
import json
from pathlib import Path
import sys
import os

# Add the parent directory to the path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from aura.core.config import AuraConfig
from aura.llm.providers import LLMProvider, LMStudioProvider
from aura.planning.prd_parser import PRDParser


async def test_prd_parser():
    """Test the PRDParser with the actual PRD.md file"""
    
    # Initialize configuration
    config = AuraConfig()
    
    # Initialize LLM provider (LM Studio)
    llm_provider = LMStudioProvider({
        'base_url': "http://localhost:1234",
        'model_name': "meta-llama-3.1-8b-instruct",
        'timeout': 30
    })
    
    # Initialize parser
    parser = PRDParser(config, llm_provider)
    
    # Parse the PRD file
    prd_path = Path("/home/greenantix/AI/LLMdiver/PRD.md")
    
    print("🔍 Parsing PRD.md file...")
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
            
            for story in epic.user_stories[:2]:  # Show first 2 stories
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
        
        # Save analysis to file for inspection
        output_file = Path("/home/greenantix/AI/LLMdiver/aura/planning/prd_analysis.json")
        analysis_dict = {
            'document_version': analysis.document_version,
            'analysis_timestamp': analysis.analysis_timestamp.isoformat(),
            'epics': [
                {
                    'id': epic.id,
                    'title': epic.title,
                    'description': epic.description,
                    'phase': epic.phase.value,
                    'priority': epic.priority.value,
                    'user_stories': [
                        {
                            'id': story.id,
                            'title': story.title,
                            'description': story.description,
                            'persona': story.persona,
                            'priority': story.priority.value,
                            'acceptance_criteria': story.acceptance_criteria
                        }
                        for story in epic.user_stories
                    ]
                }
                for epic in analysis.epics
            ],
            'technical_requirements': [
                {
                    'id': req.id,
                    'title': req.title,
                    'description': req.description,
                    'category': req.category,
                    'priority': req.priority.value,
                    'specifications': req.specifications,
                    'acceptance_criteria': req.acceptance_criteria
                }
                for req in analysis.technical_requirements
            ],
            'user_personas': analysis.user_personas,
            'success_metrics': analysis.success_metrics,
            'dependencies': analysis.dependencies,
            'phases': analysis.phases,
            'complexity_score': analysis.complexity_score,
            'estimated_timeline': analysis.estimated_timeline
        }
        
        with open(output_file, 'w') as f:
            json.dump(analysis_dict, f, indent=2)
        
        print(f"\n💾 Analysis saved to: {output_file}")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error parsing PRD: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_prd_parser())