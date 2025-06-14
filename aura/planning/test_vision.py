"""
Test Vision Integration - Integrate Vision into Planning Architecture
"""

import asyncio
import json
from pathlib import Path
import sys
import tempfile

# Add the parent directory to the path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from aura.core.config import AuraConfig
from aura.planning.test_parser_mock import MockLLMProvider
from aura.planning.prd_parser import PRDParser
from aura.planning.task_decomposer import TaskDecomposer
from aura.planning.vision_integration import VisionPlanningIntegrator, VisualContentType, VisualAnalysis


async def test_vision_integration():
    """Test vision integration with planning system"""
    
    # Initialize configuration
    config = AuraConfig()
    
    # Initialize mock LLM provider
    llm_provider = MockLLMProvider()
    
    # Initialize components
    parser = PRDParser(config, llm_provider)
    decomposer = TaskDecomposer(config, llm_provider)
    vision_integrator = VisionPlanningIntegrator(config, llm_provider)
    
    print("👁️ Testing Vision Integration with Planning Architecture...")
    
    try:
        # Step 1: Parse existing requirements
        prd_path = Path("/home/greenantix/AI/LLMdiver/PRD.md")
        analysis = await parser.parse_prd_file(prd_path)
        
        print(f"\n📋 Parsed {len(analysis.epics)} epics from PRD")
        
        # Step 2: Create mock visual assets for testing
        mock_visuals = await create_mock_visual_assets()
        
        print(f"\n🖼️ Created {len(mock_visuals)} mock visual assets")
        
        # Step 3: Analyze visual requirements
        visual_analyses = []
        for visual_path, content_type in mock_visuals:
            print(f"   Analyzing: {visual_path} ({content_type.value})")
            
            analysis_result = await vision_integrator.analyze_visual_requirement(
                visual_path, 
                content_type,
                context={'source': 'test', 'purpose': 'planning_enhancement'}
            )
            visual_analyses.append(analysis_result)
        
        print(f"\n✅ Visual Analysis Complete!")
        print(f"   Total visual elements identified: {sum(len(va.visual_elements) for va in visual_analyses)}")
        print(f"   Total user stories suggested: {sum(len(va.suggested_user_stories) for va in visual_analyses)}")
        
        # Step 4: Enhance requirements with visual insights
        print("\n🔄 Enhancing requirements with visual insights...")
        enhanced_analysis = await vision_integrator.enhance_requirements_with_visuals(analysis, visual_analyses)
        
        print(f"   Original epics: {len(analysis.epics)}")
        print(f"   Enhanced epics: {len(enhanced_analysis.epics)}")
        print(f"   Original user stories: {sum(len(epic.user_stories) for epic in analysis.epics)}")
        print(f"   Enhanced user stories: {sum(len(epic.user_stories) for epic in enhanced_analysis.epics)}")
        
        # Step 5: Decompose enhanced requirements
        print("\n🔨 Decomposing enhanced requirements...")
        task_hierarchy = await decomposer.decompose_requirements(enhanced_analysis)
        
        print(f"   Tasks generated: {len(task_hierarchy.task_map)}")
        
        # Step 6: Enhance tasks with visual context
        print("\n👁️ Enhancing tasks with visual context...")
        enhanced_hierarchy = await vision_integrator.enhance_tasks_with_visual_context(task_hierarchy, visual_analyses)
        
        print(f"   Original tasks: {len(task_hierarchy.task_map)}")
        print(f"   Enhanced tasks: {len(enhanced_hierarchy.task_map)}")
        
        # Step 7: Display enhanced planning results
        print("\n📊 Enhanced Planning Results:")
        
        # Show visual-enhanced tasks
        visual_tasks = [t for t in enhanced_hierarchy.task_map.values() if 'visual' in t.labels]
        print(f"\n🎨 Visual-Enhanced Tasks ({len(visual_tasks)}):")
        for task in visual_tasks[:5]:  # Show first 5
            print(f"   • {task.title}")
            print(f"     Labels: {', '.join(task.labels)}")
            if task.estimate:
                print(f"     Estimate: {task.estimate.value} {task.estimate.unit.value}")
        
        # Show visual analysis details
        print(f"\n🔍 Visual Analysis Details:")
        for i, va in enumerate(visual_analyses, 1):
            print(f"\n   Analysis {i}: {Path(va.image_path).name}")
            print(f"     Type: {va.content_type.value}")
            print(f"     Complexity: {va.complexity.value}")
            print(f"     Confidence: {va.confidence_score:.1%}")
            print(f"     Elements: {len(va.visual_elements)}")
            print(f"     Technical Requirements: {len(va.technical_requirements)}")
            
            # Show sample elements
            if va.visual_elements:
                print(f"     Sample Elements:")
                for element in va.visual_elements[:3]:  # Show first 3
                    print(f"       - {element.element_id} ({element.element_type}): {element.description[:50]}...")
        
        # Step 8: Generate visual planning report
        print(f"\n📄 Generating visual planning report...")
        report_path = Path("/home/greenantix/AI/LLMdiver/aura/planning/visual_planning_report.md")
        report = vision_integrator.create_visual_planning_report(visual_analyses, report_path)
        
        print(f"   Report saved to: {report_path}")
        print(f"   Report length: {len(report)} characters")
        
        # Step 9: Test screenshot analysis (mock)
        print(f"\n📸 Testing screenshot analysis...")
        sample_task = list(enhanced_hierarchy.task_map.values())[0]
        mock_screenshot = "/tmp/mock_screenshot.png"
        
        # Create mock screenshot file
        Path(mock_screenshot).touch()
        
        enhanced_task = await vision_integrator.analyze_screenshot_for_task_enhancement(
            mock_screenshot, 
            sample_task
        )
        
        print(f"   Task enhancement complete")
        print(f"   Original description length: {len(sample_task.description)}")
        print(f"   Enhanced description length: {len(enhanced_task.description)}")
        print(f"   Original criteria: {len(sample_task.acceptance_criteria)}")
        print(f"   Enhanced criteria: {len(enhanced_task.acceptance_criteria)}")
        
        # Step 10: Save comprehensive results
        output_file = Path("/home/greenantix/AI/LLMdiver/aura/planning/vision_integration_results.json")
        results = {
            'timestamp': enhanced_analysis.analysis_timestamp.isoformat(),
            'original_epics': len(analysis.epics),
            'enhanced_epics': len(enhanced_analysis.epics),
            'original_tasks': len(task_hierarchy.task_map),
            'enhanced_tasks': len(enhanced_hierarchy.task_map),
            'visual_analyses': len(visual_analyses),
            'total_visual_elements': sum(len(va.visual_elements) for va in visual_analyses),
            'total_suggested_stories': sum(len(va.suggested_user_stories) for va in visual_analyses),
            'visual_enhanced_tasks': len([t for t in enhanced_hierarchy.task_map.values() if 'visual' in t.labels]),
            'confidence_scores': [va.confidence_score for va in visual_analyses],
            'complexity_distribution': {
                complexity.value: len([va for va in visual_analyses if va.complexity == complexity])
                for complexity in [va.complexity for va in visual_analyses]
            },
            'content_type_distribution': {
                content_type.value: len([va for va in visual_analyses if va.content_type == content_type])
                for content_type in [va.content_type for va in visual_analyses]
            },
            'sample_enhanced_tasks': [
                {
                    'id': task.id,
                    'title': task.title,
                    'labels': task.labels,
                    'estimate': {
                        'value': task.estimate.value if task.estimate else None,
                        'unit': task.estimate.unit.value if task.estimate else None
                    } if task.estimate else None,
                    'acceptance_criteria_count': len(task.acceptance_criteria),
                    'visual_enhanced': 'visual' in task.labels
                }
                for task in list(enhanced_hierarchy.task_map.values())[:10]
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        print("\n🎉 Vision Integration test completed successfully!")
        print("\n📈 Integration Summary:")
        print(f"   • Enhanced {len(enhanced_analysis.epics)} epics with visual requirements")
        print(f"   • Generated {len(enhanced_hierarchy.task_map)} tasks (including {len([t for t in enhanced_hierarchy.task_map.values() if 'visual' in t.labels])} visual tasks)")
        print(f"   • Analyzed {len(visual_analyses)} visual assets")
        print(f"   • Identified {sum(len(va.visual_elements) for va in visual_analyses)} visual elements")
        print(f"   • Average confidence score: {sum(va.confidence_score for va in visual_analyses) / len(visual_analyses):.1%}")
        
        return enhanced_hierarchy, visual_analyses
        
    except Exception as e:
        print(f"❌ Error in vision integration: {e}")
        import traceback
        traceback.print_exc()
        return None, None


async def create_mock_visual_assets():
    """Create mock visual assets for testing"""
    
    mock_assets = []
    
    # Create temporary mock files
    temp_dir = Path("/tmp/aura_vision_test")
    temp_dir.mkdir(exist_ok=True)
    
    # Mock UI Mockup
    ui_mockup = temp_dir / "dashboard_mockup.png"
    ui_mockup.touch()
    mock_assets.append((str(ui_mockup), VisualContentType.UI_MOCKUP))
    
    # Mock Architecture Diagram
    arch_diagram = temp_dir / "system_architecture.png"
    arch_diagram.touch()
    mock_assets.append((str(arch_diagram), VisualContentType.ARCHITECTURE_DIAGRAM))
    
    # Mock Wireframe
    wireframe = temp_dir / "user_flow_wireframe.png"
    wireframe.touch()
    mock_assets.append((str(wireframe), VisualContentType.WIREFRAME))
    
    return mock_assets


if __name__ == "__main__":
    asyncio.run(test_vision_integration())