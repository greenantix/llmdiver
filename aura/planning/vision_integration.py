"""
Vision Integration - Visual Analysis for Planning and Requirements
Integrates visual understanding with planning and task decomposition
"""

import asyncio
import base64
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import tempfile
import subprocess

from ..core.config import AuraConfig
from ..llm.providers import LLMProvider, LLMRequest, LLMResponse
from .prd_parser import RequirementAnalysis, Epic, UserStory
from .task_decomposer import TaskHierarchy, DecomposedTask, TaskType, Priority


class VisualContentType(Enum):
    UI_MOCKUP = "ui_mockup"
    WIREFRAME = "wireframe"
    ARCHITECTURE_DIAGRAM = "architecture_diagram"
    FLOWCHART = "flowchart"
    USER_JOURNEY = "user_journey"
    SCREENSHOT = "screenshot"
    DESIGN_ASSET = "design_asset"
    TECHNICAL_DIAGRAM = "technical_diagram"


class AnalysisComplexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


@dataclass
class VisualElement:
    element_id: str
    element_type: str  # "button", "input", "text", "image", "container", etc.
    description: str
    position: Dict[str, float]  # x, y, width, height
    properties: Dict[str, Any] = field(default_factory=dict)
    interactions: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)


@dataclass
class VisualAnalysis:
    image_path: str
    content_type: VisualContentType
    complexity: AnalysisComplexity
    analysis_timestamp: datetime
    overall_description: str
    visual_elements: List[VisualElement]
    user_flows: List[Dict[str, Any]]
    technical_requirements: List[str]
    implementation_notes: List[str]
    suggested_user_stories: List[Dict[str, Any]]
    estimated_effort: Dict[str, float]
    accessibility_notes: List[str]
    responsive_considerations: List[str]
    confidence_score: float


@dataclass
class ScreenshotContext:
    purpose: str  # "requirement_clarification", "bug_report", "feature_request", "design_feedback"
    description: str
    related_tasks: List[str] = field(default_factory=list)
    annotations: List[Dict[str, Any]] = field(default_factory=list)


class VisionLLMProvider(LLMProvider):
    """Enhanced LLM Provider with vision capabilities"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.vision_model = config.get('vision_model', 'google/gemma-3-4b')
        self.vision_endpoint = config.get('vision_endpoint', 'http://localhost:1235')  # Separate endpoint for vision
    
    def _get_model_mappings(self):
        return {}
    
    async def is_available(self) -> bool:
        return True
    
    async def get_available_models(self):
        return [self.vision_model]
    
    async def analyze_image(self, image_path: str, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Analyze image using vision model"""
        
        try:
            # Read and encode image
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Prepare vision request (this would be adapted based on actual vision model API)
            payload = {
                'model': self.vision_model,
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': prompt},
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:image/jpeg;base64,{image_data}'
                                }
                            }
                        ]
                    }
                ],
                'max_tokens': 4096,
                'temperature': 0.3
            }
            
            # For now, return a mock response since we don't have the actual vision model setup
            return await self._mock_vision_analysis(image_path, prompt, context)
            
        except Exception as e:
            return f"Error analyzing image: {str(e)}"
    
    async def _mock_vision_analysis(self, image_path: str, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Mock vision analysis for testing"""
        
        if "ui mockup" in prompt.lower() or "interface" in prompt.lower():
            return """
{
  "content_type": "ui_mockup",
  "complexity": "medium",
  "overall_description": "Modern web application interface with navigation bar, sidebar, and main content area. Features a dashboard-style layout with cards and data visualization components.",
  "visual_elements": [
    {
      "element_id": "nav_bar",
      "element_type": "navigation",
      "description": "Top navigation bar with logo, menu items, and user profile",
      "position": {"x": 0, "y": 0, "width": 100, "height": 8},
      "properties": {"background": "dark", "fixed": true},
      "interactions": ["click", "hover"],
      "relationships": ["contains_menu_items"]
    },
    {
      "element_id": "sidebar",
      "element_type": "navigation",
      "description": "Left sidebar with menu navigation",
      "position": {"x": 0, "y": 8, "width": 20, "height": 92},
      "properties": {"collapsible": true, "background": "light"},
      "interactions": ["click", "expand", "collapse"],
      "relationships": ["connects_to_main_content"]
    },
    {
      "element_id": "main_content",
      "element_type": "container",
      "description": "Main content area with dashboard cards",
      "position": {"x": 20, "y": 8, "width": 80, "height": 92},
      "properties": {"scrollable": true, "responsive": true},
      "interactions": ["scroll", "click"],
      "relationships": ["contains_dashboard_cards"]
    }
  ],
  "user_flows": [
    {
      "flow_id": "main_navigation",
      "description": "User navigates through main sections using sidebar",
      "steps": ["click_sidebar_item", "load_content", "display_results"],
      "complexity": "simple"
    }
  ],
  "technical_requirements": [
    "Responsive design for mobile and desktop",
    "Navigation state management",
    "Component-based architecture",
    "Data visualization library integration"
  ],
  "implementation_notes": [
    "Use React/Vue components for modularity",
    "Implement responsive grid system",
    "Add loading states for async operations",
    "Consider accessibility for navigation"
  ],
  "suggested_user_stories": [
    {
      "title": "As a user, I want to navigate between sections so that I can access different features",
      "priority": "high",
      "complexity": "medium",
      "acceptance_criteria": [
        "Sidebar navigation works on all devices",
        "Active section is clearly indicated",
        "Navigation is accessible via keyboard"
      ]
    },
    {
      "title": "As a user, I want to see a dashboard overview so that I can quickly understand the system status",
      "priority": "high",
      "complexity": "high",
      "acceptance_criteria": [
        "Dashboard cards display real-time data",
        "Layout adapts to different screen sizes",
        "Loading states are shown during data fetch"
      ]
    }
  ],
  "estimated_effort": {
    "frontend_development": 15,
    "backend_api": 8,
    "testing": 5,
    "design_refinement": 3
  },
  "accessibility_notes": [
    "Ensure keyboard navigation works",
    "Add ARIA labels for screen readers",
    "Maintain sufficient color contrast",
    "Test with screen reader software"
  ],
  "responsive_considerations": [
    "Sidebar should collapse on mobile",
    "Touch targets should be at least 44px",
    "Content should reflow gracefully",
    "Consider swipe gestures for mobile navigation"
  ],
  "confidence_score": 0.85
}
"""
        elif "diagram" in prompt.lower() or "architecture" in prompt.lower():
            return """
{
  "content_type": "architecture_diagram",
  "complexity": "complex",
  "overall_description": "System architecture diagram showing microservices with message queue, databases, and external integrations",
  "visual_elements": [
    {
      "element_id": "api_gateway",
      "element_type": "service",
      "description": "API Gateway handling external requests",
      "position": {"x": 10, "y": 20, "width": 15, "height": 10},
      "properties": {"type": "gateway", "scalable": true},
      "interactions": ["receives_requests", "routes_traffic"],
      "relationships": ["connects_to_services"]
    },
    {
      "element_id": "message_queue",
      "element_type": "infrastructure",
      "description": "Message queue for async communication",
      "position": {"x": 50, "y": 30, "width": 20, "height": 15},
      "properties": {"type": "rabbitmq", "persistent": true},
      "interactions": ["publishes", "subscribes"],
      "relationships": ["connects_services"]
    }
  ],
  "technical_requirements": [
    "Implement API Gateway with rate limiting",
    "Set up message queue with persistence",
    "Configure service discovery",
    "Implement health checks for all services"
  ],
  "implementation_notes": [
    "Use Docker containers for deployment",
    "Implement circuit breaker pattern",
    "Add monitoring and logging",
    "Plan for horizontal scaling"
  ],
  "suggested_user_stories": [
    {
      "title": "As a system administrator, I want to monitor service health so that I can ensure system reliability",
      "priority": "high",
      "complexity": "medium"
    }
  ],
  "estimated_effort": {
    "infrastructure_setup": 20,
    "service_implementation": 35,
    "testing_integration": 15,
    "documentation": 5
  },
  "confidence_score": 0.90
}
"""
        else:
            return """
{
  "content_type": "screenshot",
  "complexity": "simple",
  "overall_description": "Application screenshot showing current state of the interface",
  "visual_elements": [
    {
      "element_id": "main_view",
      "element_type": "container",
      "description": "Main application view with content",
      "position": {"x": 0, "y": 0, "width": 100, "height": 100}
    }
  ],
  "technical_requirements": [
    "Analyze current implementation",
    "Identify areas for improvement"
  ],
  "implementation_notes": [
    "Review code structure",
    "Check for optimization opportunities"
  ],
  "suggested_user_stories": [],
  "estimated_effort": {
    "analysis": 2,
    "documentation": 1
  },
  "confidence_score": 0.70
}
"""


class VisionPlanningIntegrator:
    def __init__(self, config: AuraConfig, llm_provider: LLMProvider):
        self.config = config
        self.llm_provider = llm_provider
        self.vision_provider = VisionLLMProvider(config.to_dict().get('vision', {}))
        self.analysis_templates = self._load_analysis_templates()
        
    def _load_analysis_templates(self) -> Dict[str, str]:
        """Load vision analysis templates"""
        return {
            'ui_analysis': """
Analyze this UI mockup or interface design image and extract detailed information for development planning.

Focus on:
1. Visual elements and their layout
2. User interaction patterns
3. Technical implementation requirements
4. Responsive design considerations
5. Accessibility requirements
6. Suggested user stories and tasks

Provide analysis in the specified JSON format with:
- Element identification and positioning
- User flow descriptions
- Technical requirements
- Implementation notes
- User story suggestions
- Effort estimates
- Accessibility and responsive considerations

Be thorough and specific in identifying all interactive elements, their relationships, and implementation complexity.
""",
            
            'architecture_analysis': """
Analyze this architecture or technical diagram to understand system design and implementation requirements.

Focus on:
1. System components and their relationships
2. Data flow and communication patterns
3. Infrastructure requirements
4. Integration points
5. Scalability considerations
6. Implementation complexity

Extract information about:
- Services and their responsibilities
- Communication protocols
- Data storage requirements
- External dependencies
- Deployment considerations
- Technical challenges

Provide structured analysis for planning development tasks.
""",
            
            'requirements_extraction': """
Analyze this visual requirement (screenshot, mockup, or diagram) and extract actionable development requirements.

Generate:
1. User stories derived from visual elements
2. Technical tasks for implementation
3. Acceptance criteria based on visual specifications
4. Effort estimates for different aspects
5. Dependencies and implementation order
6. Quality considerations (performance, accessibility, etc.)

Format the output to integrate with existing planning and task decomposition systems.
""",
            
            'task_enhancement': """
Based on this visual context, enhance the existing task with additional implementation details.

Original task: {task_description}

Analyze the visual content and provide:
1. More specific acceptance criteria
2. Additional implementation details
3. UI/UX considerations
4. Technical specifications
5. Test scenarios
6. Refined effort estimates

Consider how the visual requirements impact the scope and complexity of the original task.
"""
        }

    async def analyze_visual_requirement(self, image_path: str, content_type: VisualContentType, context: Optional[Dict[str, Any]] = None) -> VisualAnalysis:
        """Analyze visual requirement and extract planning information"""
        
        # Select appropriate analysis template
        if content_type in [VisualContentType.UI_MOCKUP, VisualContentType.WIREFRAME, VisualContentType.SCREENSHOT]:
            template = self.analysis_templates['ui_analysis']
        elif content_type in [VisualContentType.ARCHITECTURE_DIAGRAM, VisualContentType.TECHNICAL_DIAGRAM]:
            template = self.analysis_templates['architecture_analysis']
        else:
            template = self.analysis_templates['requirements_extraction']
        
        # Analyze image with vision model
        analysis_response = await self.vision_provider.analyze_image(image_path, template, context)
        
        try:
            analysis_data = json.loads(analysis_response)
            
            # Convert to VisualAnalysis object
            visual_elements = [
                VisualElement(
                    element_id=elem.get('element_id', ''),
                    element_type=elem.get('element_type', ''),
                    description=elem.get('description', ''),
                    position=elem.get('position', {}),
                    properties=elem.get('properties', {}),
                    interactions=elem.get('interactions', []),
                    relationships=elem.get('relationships', [])
                )
                for elem in analysis_data.get('visual_elements', [])
            ]
            
            return VisualAnalysis(
                image_path=image_path,
                content_type=VisualContentType(analysis_data.get('content_type', content_type.value)),
                complexity=AnalysisComplexity(analysis_data.get('complexity', 'medium')),
                analysis_timestamp=datetime.now(),
                overall_description=analysis_data.get('overall_description', ''),
                visual_elements=visual_elements,
                user_flows=analysis_data.get('user_flows', []),
                technical_requirements=analysis_data.get('technical_requirements', []),
                implementation_notes=analysis_data.get('implementation_notes', []),
                suggested_user_stories=analysis_data.get('suggested_user_stories', []),
                estimated_effort=analysis_data.get('estimated_effort', {}),
                accessibility_notes=analysis_data.get('accessibility_notes', []),
                responsive_considerations=analysis_data.get('responsive_considerations', []),
                confidence_score=analysis_data.get('confidence_score', 0.7)
            )
            
        except json.JSONDecodeError:
            # Fallback analysis
            return self._create_fallback_analysis(image_path, content_type, analysis_response)

    def _create_fallback_analysis(self, image_path: str, content_type: VisualContentType, raw_response: str) -> VisualAnalysis:
        """Create fallback analysis when JSON parsing fails"""
        
        return VisualAnalysis(
            image_path=image_path,
            content_type=content_type,
            complexity=AnalysisComplexity.MEDIUM,
            analysis_timestamp=datetime.now(),
            overall_description=raw_response[:200] + "..." if len(raw_response) > 200 else raw_response,
            visual_elements=[],
            user_flows=[],
            technical_requirements=["Visual analysis available - see description"],
            implementation_notes=["Manual review recommended"],
            suggested_user_stories=[],
            estimated_effort={'analysis_review': 2},
            accessibility_notes=[],
            responsive_considerations=[],
            confidence_score=0.5
        )

    async def enhance_requirements_with_visuals(self, analysis: RequirementAnalysis, visual_analyses: List[VisualAnalysis]) -> RequirementAnalysis:
        """Enhance existing requirements analysis with visual insights"""
        
        enhanced_epics = []
        
        for epic in analysis.epics:
            enhanced_epic = await self._enhance_epic_with_visuals(epic, visual_analyses)
            enhanced_epics.append(enhanced_epic)
        
        # Add new technical requirements from visual analysis
        enhanced_tech_reqs = list(analysis.technical_requirements)
        for visual_analysis in visual_analyses:
            for tech_req in visual_analysis.technical_requirements:
                # Create new technical requirement objects
                pass  # Implementation would create new TechnicalRequirement objects
        
        # Create enhanced analysis
        enhanced_analysis = RequirementAnalysis(
            document_version=analysis.document_version,
            analysis_timestamp=datetime.now(),
            epics=enhanced_epics,
            technical_requirements=enhanced_tech_reqs,
            user_personas=analysis.user_personas,
            success_metrics=analysis.success_metrics,
            dependencies=analysis.dependencies,
            phases=analysis.phases,
            complexity_score=min(analysis.complexity_score + 0.1, 1.0),  # Slightly increase complexity
            estimated_timeline=analysis.estimated_timeline
        )
        
        return enhanced_analysis

    async def _enhance_epic_with_visuals(self, epic: Epic, visual_analyses: List[VisualAnalysis]) -> Epic:
        """Enhance an epic with visual requirements"""
        
        enhanced_user_stories = list(epic.user_stories)
        
        # Add user stories from visual analysis
        for visual_analysis in visual_analyses:
            for suggested_story in visual_analysis.suggested_user_stories:
                # Create new user story from visual suggestion
                new_story = UserStory(
                    id=f"visual_{len(enhanced_user_stories)}",
                    title=suggested_story.get('title', ''),
                    description=suggested_story.get('description', ''),
                    persona='user',  # Default persona
                    acceptance_criteria=suggested_story.get('acceptance_criteria', []),
                    priority=Priority(suggested_story.get('priority', 'medium')),
                    estimated_effort=suggested_story.get('estimated_effort'),
                    tags=['visual', 'ui']
                )
                enhanced_user_stories.append(new_story)
        
        # Create enhanced epic
        enhanced_epic = Epic(
            id=epic.id,
            title=epic.title,
            description=epic.description,
            user_stories=enhanced_user_stories,
            phase=epic.phase,
            priority=epic.priority,
            success_metrics=epic.success_metrics,
            dependencies=epic.dependencies
        )
        
        return enhanced_epic

    async def enhance_tasks_with_visual_context(self, task_hierarchy: TaskHierarchy, visual_analyses: List[VisualAnalysis]) -> TaskHierarchy:
        """Enhance task hierarchy with visual context and additional tasks"""
        
        enhanced_task_map = dict(task_hierarchy.task_map)
        
        # Enhance existing tasks with visual context
        for task_id, task in task_hierarchy.task_map.items():
            if any(label in ['ui', 'frontend', 'interface'] for label in task.labels):
                enhanced_task = await self._enhance_task_with_visual_context(task, visual_analyses)
                enhanced_task_map[task_id] = enhanced_task
        
        # Add new tasks derived from visual analysis
        for visual_analysis in visual_analyses:
            new_tasks = await self._create_tasks_from_visual_analysis(visual_analysis)
            for new_task in new_tasks:
                enhanced_task_map[new_task.id] = new_task
        
        # Create enhanced hierarchy
        enhanced_hierarchy = TaskHierarchy(
            root_tasks=[t for t in enhanced_task_map.values() if not t.parent_id],
            task_map=enhanced_task_map,
            dependency_graph=task_hierarchy.dependency_graph,
            execution_order=task_hierarchy.execution_order,
            parallel_groups=task_hierarchy.parallel_groups,
            critical_path=task_hierarchy.critical_path,
            total_estimate=task_hierarchy.total_estimate,
            milestone_mapping=task_hierarchy.milestone_mapping
        )
        
        return enhanced_hierarchy

    async def _enhance_task_with_visual_context(self, task: DecomposedTask, visual_analyses: List[VisualAnalysis]) -> DecomposedTask:
        """Enhance a single task with visual context"""
        
        # Find relevant visual analyses for this task
        relevant_visuals = [va for va in visual_analyses if self._is_visual_relevant_to_task(task, va)]
        
        if not relevant_visuals:
            return task
        
        # Enhance task description and acceptance criteria
        enhanced_description = task.description
        enhanced_criteria = list(task.acceptance_criteria)
        
        for visual in relevant_visuals:
            # Add visual-specific implementation notes to description
            if visual.implementation_notes:
                enhanced_description += "\n\nVisual Implementation Notes:\n"
                enhanced_description += "\n".join(f"- {note}" for note in visual.implementation_notes)
            
            # Add visual-specific acceptance criteria
            for element in visual.visual_elements:
                if element.element_type in ['button', 'input', 'form']:
                    from .task_decomposer import AcceptanceCriteria
                    criterion = AcceptanceCriteria(
                        id=f"visual_{element.element_id}",
                        description=f"Implement {element.element_type}: {element.description}",
                        testable=True,
                        automated=False
                    )
                    enhanced_criteria.append(criterion)
        
        # Create enhanced task
        enhanced_task = DecomposedTask(
            id=task.id,
            title=task.title,
            description=enhanced_description,
            task_type=task.task_type,
            priority=task.priority,
            status=task.status,
            estimate=task.estimate,
            parent_id=task.parent_id,
            dependencies=task.dependencies,
            acceptance_criteria=enhanced_criteria,
            labels=task.labels + ['visual-enhanced'],
            assignee=task.assignee,
            created_at=task.created_at,
            updated_at=datetime.now(),
            metadata=task.metadata
        )
        
        return enhanced_task

    def _is_visual_relevant_to_task(self, task: DecomposedTask, visual_analysis: VisualAnalysis) -> bool:
        """Determine if a visual analysis is relevant to a specific task"""
        
        # Check if task involves UI/frontend work
        ui_keywords = ['ui', 'frontend', 'interface', 'component', 'page', 'view']
        task_is_ui = any(keyword in task.title.lower() or keyword in task.description.lower() for keyword in ui_keywords)
        
        # Check if visual analysis is UI-related
        visual_is_ui = visual_analysis.content_type in [VisualContentType.UI_MOCKUP, VisualContentType.WIREFRAME, VisualContentType.SCREENSHOT]
        
        return task_is_ui and visual_is_ui

    async def _create_tasks_from_visual_analysis(self, visual_analysis: VisualAnalysis) -> List[DecomposedTask]:
        """Create new tasks based on visual analysis"""
        
        tasks = []
        
        # Create tasks for complex visual elements
        for element in visual_analysis.visual_elements:
            if element.element_type in ['form', 'dashboard', 'navigation', 'modal']:
                from .task_decomposer import TaskEstimate, EstimationUnit, AcceptanceCriteria
                
                task = DecomposedTask(
                    id=f"visual_task_{element.element_id}",
                    title=f"Implement {element.element_type}: {element.description}",
                    description=f"Create {element.element_type} component based on visual design\n\nElement details:\n- Type: {element.element_type}\n- Description: {element.description}\n- Properties: {element.properties}",
                    task_type=TaskType.TASK,
                    priority=Priority.MEDIUM,
                    status=task.status if 'task' in locals() else TaskStatus.BACKLOG,
                    estimate=TaskEstimate(
                        value=self._estimate_element_effort(element),
                        unit=EstimationUnit.HOURS,
                        confidence=0.7,
                        complexity_factors=[f"Visual {element.element_type} implementation"]
                    ),
                    acceptance_criteria=[
                        AcceptanceCriteria(
                            id=f"ac_visual_{element.element_id}",
                            description=f"{element.element_type} matches visual design specifications",
                            testable=True,
                            automated=False
                        )
                    ],
                    labels=['visual', 'ui', element.element_type],
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    metadata={'visual_analysis': visual_analysis.image_path, 'element_id': element.element_id}
                )
                tasks.append(task)
        
        # Create accessibility task if notes are present
        if visual_analysis.accessibility_notes:
            from .task_decomposer import TaskEstimate, EstimationUnit, AcceptanceCriteria
            
            accessibility_task = DecomposedTask(
                id=f"visual_accessibility_{hash(visual_analysis.image_path)}",
                title="Implement accessibility requirements from visual design",
                description=f"Ensure accessibility compliance based on visual design analysis\n\nRequirements:\n" + "\n".join(f"- {note}" for note in visual_analysis.accessibility_notes),
                task_type=TaskType.TASK,
                priority=Priority.HIGH,
                status=task.status if 'task' in locals() else TaskStatus.BACKLOG,
                estimate=TaskEstimate(
                    value=4,
                    unit=EstimationUnit.HOURS,
                    confidence=0.8,
                    complexity_factors=["Accessibility compliance", "Screen reader testing"]
                ),
                acceptance_criteria=[
                    AcceptanceCriteria(
                        id=f"ac_a11y_{hash(visual_analysis.image_path)}",
                        description="Interface meets WCAG 2.1 AA standards",
                        testable=True,
                        automated=True
                    )
                ],
                labels=['accessibility', 'visual', 'compliance'],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={'visual_analysis': visual_analysis.image_path}
            )
            tasks.append(accessibility_task)
        
        return tasks

    def _estimate_element_effort(self, element: VisualElement) -> float:
        """Estimate implementation effort for a visual element"""
        
        base_effort = {
            'button': 1,
            'input': 2,
            'form': 8,
            'navigation': 6,
            'modal': 4,
            'dashboard': 12,
            'table': 6,
            'chart': 8,
            'container': 3
        }
        
        effort = base_effort.get(element.element_type, 4)
        
        # Adjust based on interactions
        if len(element.interactions) > 2:
            effort *= 1.5
        
        # Adjust based on properties complexity
        if len(element.properties) > 3:
            effort *= 1.3
        
        return effort

    async def take_screenshot(self, purpose: str, description: str) -> Optional[str]:
        """Take a screenshot for analysis (placeholder implementation)"""
        
        try:
            # This would be implemented to actually take screenshots
            # For now, return a placeholder path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"/tmp/aura_screenshot_{timestamp}.png"
            
            # Placeholder: In real implementation, this would use a screenshot tool
            # like scrot, gnome-screenshot, or a browser automation tool
            print(f"Would take screenshot for: {purpose}")
            print(f"Description: {description}")
            print(f"Would save to: {screenshot_path}")
            
            return screenshot_path
            
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            return None

    async def analyze_screenshot_for_task_enhancement(self, screenshot_path: str, task: DecomposedTask) -> DecomposedTask:
        """Analyze a screenshot to enhance task requirements"""
        
        template = self.analysis_templates['task_enhancement']
        prompt = template.replace('{task_description}', f"{task.title}\n{task.description}")
        
        analysis_response = await self.vision_provider.analyze_image(screenshot_path, prompt)
        
        try:
            enhancement_data = json.loads(analysis_response)
            
            # Enhance task with visual insights
            enhanced_description = task.description + "\n\nVisual Context Enhancements:\n"
            enhanced_description += enhancement_data.get('implementation_details', '')
            
            # Add visual-specific acceptance criteria
            enhanced_criteria = list(task.acceptance_criteria)
            for criterion_text in enhancement_data.get('acceptance_criteria', []):
                from .task_decomposer import AcceptanceCriteria
                criterion = AcceptanceCriteria(
                    id=f"visual_enhanced_{len(enhanced_criteria)}",
                    description=criterion_text,
                    testable=True,
                    automated=False
                )
                enhanced_criteria.append(criterion)
            
            # Update estimate if provided
            enhanced_estimate = task.estimate
            if enhancement_data.get('effort_estimate'):
                from .task_decomposer import TaskEstimate, EstimationUnit
                enhanced_estimate = TaskEstimate(
                    value=enhancement_data['effort_estimate'],
                    unit=EstimationUnit.HOURS,
                    confidence=0.75,
                    complexity_factors=enhancement_data.get('complexity_factors', [])
                )
            
            # Create enhanced task
            enhanced_task = DecomposedTask(
                id=task.id,
                title=task.title,
                description=enhanced_description,
                task_type=task.task_type,
                priority=task.priority,
                status=task.status,
                estimate=enhanced_estimate,
                parent_id=task.parent_id,
                dependencies=task.dependencies,
                acceptance_criteria=enhanced_criteria,
                labels=task.labels + ['visual-enhanced'],
                assignee=task.assignee,
                created_at=task.created_at,
                updated_at=datetime.now(),
                metadata={**task.metadata, 'visual_context': screenshot_path}
            )
            
            return enhanced_task
            
        except json.JSONDecodeError:
            # Return original task if enhancement fails
            return task

    def create_visual_planning_report(self, visual_analyses: List[VisualAnalysis], output_path: Optional[Path] = None) -> str:
        """Create a comprehensive report of visual planning analysis"""
        
        report = []
        report.append("# Visual Planning Analysis Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append("## Summary")
        report.append(f"- Analyzed {len(visual_analyses)} visual assets")
        
        total_elements = sum(len(va.visual_elements) for va in visual_analyses)
        total_user_stories = sum(len(va.suggested_user_stories) for va in visual_analyses)
        
        report.append(f"- Identified {total_elements} visual elements")
        report.append(f"- Generated {total_user_stories} user stories")
        report.append("")
        
        # Detailed analysis for each visual
        for i, analysis in enumerate(visual_analyses, 1):
            report.append(f"## Analysis {i}: {Path(analysis.image_path).name}")
            report.append(f"**Type:** {analysis.content_type.value}")
            report.append(f"**Complexity:** {analysis.complexity.value}")
            report.append(f"**Confidence:** {analysis.confidence_score:.1%}")
            report.append("")
            report.append(f"**Description:** {analysis.overall_description}")
            report.append("")
            
            if analysis.visual_elements:
                report.append("### Visual Elements")
                for element in analysis.visual_elements:
                    report.append(f"- **{element.element_id}** ({element.element_type}): {element.description}")
                report.append("")
            
            if analysis.technical_requirements:
                report.append("### Technical Requirements")
                for req in analysis.technical_requirements:
                    report.append(f"- {req}")
                report.append("")
            
            if analysis.suggested_user_stories:
                report.append("### Suggested User Stories")
                for story in analysis.suggested_user_stories:
                    report.append(f"- **{story.get('title', 'Untitled')}** (Priority: {story.get('priority', 'medium')})")
                    if story.get('acceptance_criteria'):
                        for criteria in story['acceptance_criteria']:
                            report.append(f"  - {criteria}")
                report.append("")
            
            if analysis.estimated_effort:
                report.append("### Effort Estimates")
                for category, effort in analysis.estimated_effort.items():
                    report.append(f"- {category}: {effort} hours")
                report.append("")
        
        report_text = "\n".join(report)
        
        if output_path:
            output_path.write_text(report_text)
        
        return report_text