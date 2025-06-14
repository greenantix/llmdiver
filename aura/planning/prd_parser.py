"""
PRD Parser - Semantic Analysis and Requirement Extraction
Transforms natural language requirements into structured, actionable data
"""

import re
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import asyncio

from ..core.config import AuraConfig
from ..llm.providers import LLMProvider


class RequirementType(Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    TECHNICAL = "technical"
    BUSINESS = "business"
    USER_STORY = "user_story"
    EPIC = "epic"
    TASK = "task"


class Priority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Phase(Enum):
    FOUNDATION = "foundation"
    AUTOMATION = "automation"
    ADVANCED = "advanced"
    RELEASE = "release"


@dataclass
class UserStory:
    id: str
    title: str
    description: str
    persona: str
    acceptance_criteria: List[str]
    priority: Priority
    estimated_effort: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class Epic:
    id: str
    title: str
    description: str
    user_stories: List[UserStory]
    phase: Phase
    priority: Priority
    success_metrics: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class TechnicalRequirement:
    id: str
    title: str
    description: str
    category: str
    specifications: Dict[str, Any]
    acceptance_criteria: List[str]
    priority: Priority
    dependencies: List[str] = field(default_factory=list)


@dataclass
class RequirementAnalysis:
    document_version: str
    analysis_timestamp: datetime
    epics: List[Epic]
    technical_requirements: List[TechnicalRequirement]
    user_personas: Dict[str, Dict[str, Any]]
    success_metrics: Dict[str, str]
    dependencies: Dict[str, List[str]]
    phases: Dict[str, List[str]]
    complexity_score: float
    estimated_timeline: Dict[str, int]


class PRDParser:
    def __init__(self, config: AuraConfig, llm_provider: LLMProvider):
        self.config = config
        self.llm_provider = llm_provider
        self.parsing_templates = self._load_parsing_templates()
        
    def _load_parsing_templates(self) -> Dict[str, str]:
        """Load LLM prompts for different parsing tasks"""
        return {
            'epic_extraction': """
Analyze this PRD section and extract epics with their details:

{text}

Extract information in this JSON format:
{
  "epics": [
    {
      "id": "epic_id",
      "title": "Epic Title",
      "description": "Detailed description",
      "phase": "foundation|automation|advanced|release",
      "priority": "critical|high|medium|low",
      "success_metrics": ["metric1", "metric2"],
      "user_stories": [
        {
          "id": "story_id", 
          "title": "Story Title",
          "description": "As a [persona], I want [goal] so that [benefit]",
          "persona": "persona_name",
          "acceptance_criteria": ["criteria1", "criteria2"],
          "priority": "critical|high|medium|low",
          "estimated_effort": 5,
          "tags": ["tag1", "tag2"]
        }
      ]
    }
  ]
}

Focus on:
- Identifying clear epic boundaries
- Extracting user stories in proper format
- Determining priority and effort estimates
- Mapping to appropriate development phases
""",
            
            'technical_requirements': """
Analyze this PRD section for technical requirements and specifications:

{text}

Extract technical requirements in this JSON format:
{
  "technical_requirements": [
    {
      "id": "req_id",
      "title": "Requirement Title",
      "description": "Detailed description",
      "category": "performance|security|architecture|integration",
      "specifications": {
        "response_time": "500ms",
        "throughput": "100k lines in 5 minutes",
        "memory_usage": "2GB max"
      },
      "acceptance_criteria": ["criteria1", "criteria2"],
      "priority": "critical|high|medium|low"
    }
  ]
}

Focus on:
- Performance requirements with specific metrics
- Security and privacy constraints
- Architecture and design specifications
- Integration requirements
""",
            
            'dependency_analysis': """
Analyze the requirements and identify dependencies between components:

{requirements_json}

Generate a dependency analysis in this JSON format:
{
  "dependencies": {
    "epic_id": ["dependent_epic1", "dependent_epic2"],
    "story_id": ["dependent_story1", "dependent_story2"]
  },
  "critical_path": ["epic1", "epic2", "epic3"],
  "parallel_tracks": [
    ["epic1", "epic2"],
    ["epic3", "epic4"]
  ]
}

Focus on:
- Logical dependencies (A must be complete before B)
- Technical dependencies (B requires infrastructure from A)
- Resource dependencies (same team/skill required)
""",
            
            'complexity_estimation': """
Estimate the complexity and timeline for these requirements:

{requirements_json}

Provide estimation in this JSON format:
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

Consider:
- Number of components and integrations
- Technology complexity and maturity
- Team size and expertise assumptions
"""
        }

    async def parse_prd_file(self, prd_path: Path) -> RequirementAnalysis:
        """Parse a complete PRD file into structured requirements"""
        
        if not prd_path.exists():
            raise FileNotFoundError(f"PRD file not found: {prd_path}")
        
        content = prd_path.read_text(encoding='utf-8')
        return await self.parse_prd_content(content)

    async def parse_prd_content(self, content: str) -> RequirementAnalysis:
        """Parse PRD content into structured requirements"""
        
        # Extract document metadata
        version = self._extract_version(content)
        
        # Parse different sections concurrently
        tasks = [
            self._extract_epics(content),
            self._extract_technical_requirements(content),
            self._extract_user_personas(content),
            self._extract_success_metrics(content)
        ]
        
        epics, tech_reqs, personas, metrics = await asyncio.gather(*tasks)
        
        # Analyze dependencies - convert to serializable format
        epics_data = []
        for epic in epics:
            epic_dict = {
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
            epics_data.append(epic_dict)
        
        tech_reqs_data = []
        for req in tech_reqs:
            req_dict = {
                'id': req.id,
                'title': req.title,
                'description': req.description,
                'category': req.category,
                'priority': req.priority.value,
                'specifications': req.specifications,
                'acceptance_criteria': req.acceptance_criteria
            }
            tech_reqs_data.append(req_dict)
        
        all_requirements = {
            'epics': epics_data,
            'technical_requirements': tech_reqs_data
        }
        
        dependencies = await self._analyze_dependencies(all_requirements)
        complexity_data = await self._estimate_complexity(all_requirements)
        
        return RequirementAnalysis(
            document_version=version,
            analysis_timestamp=datetime.now(),
            epics=epics,
            technical_requirements=tech_reqs,
            user_personas=personas,
            success_metrics=metrics,
            dependencies=dependencies.get('dependencies', {}),
            phases=self._group_by_phases(epics),
            complexity_score=complexity_data.get('complexity_analysis', {}).get('overall_score', 0.5),
            estimated_timeline=complexity_data.get('timeline_estimation', {'total_days': 180})
        )

    def _extract_version(self, content: str) -> str:
        """Extract document version from PRD content"""
        version_pattern = r'Version:\s*([^\n]+)'
        match = re.search(version_pattern, content)
        return match.group(1).strip() if match else "unknown"

    async def _extract_epics(self, content: str) -> List[Epic]:
        """Extract epics and user stories from PRD content"""
        
        # Find action plan sections
        action_plan_pattern = r'(Phase \d+:.*?)(?=Phase \d+:|$)'
        phases = re.findall(action_plan_pattern, content, re.DOTALL)
        
        all_epics = []
        
        for phase_content in phases:
            # Extract phase information
            phase_match = re.search(r'Phase (\d+):', phase_content)
            phase_num = int(phase_match.group(1)) if phase_match else 1
            
            phase_mapping = {
                1: Phase.FOUNDATION,
                2: Phase.AUTOMATION, 
                3: Phase.ADVANCED,
                4: Phase.RELEASE
            }
            phase_enum = phase_mapping.get(phase_num, Phase.FOUNDATION)
            
            # Use LLM to extract structured epic data
            template = self.parsing_templates['epic_extraction']
            prompt = template.replace('{text}', phase_content)
            response = await self.llm_provider.generate_completion_simple(prompt)
            
            try:
                parsed_data = json.loads(response)
                for epic_data in parsed_data.get('epics', []):
                    
                    # Convert user stories
                    user_stories = []
                    for story_data in epic_data.get('user_stories', []):
                        user_story = UserStory(
                            id=story_data.get('id', f"story_{len(user_stories)}"),
                            title=story_data.get('title', ''),
                            description=story_data.get('description', ''),
                            persona=story_data.get('persona', 'developer'),
                            acceptance_criteria=story_data.get('acceptance_criteria', []),
                            priority=Priority(story_data.get('priority', 'medium')),
                            estimated_effort=story_data.get('estimated_effort'),
                            tags=story_data.get('tags', [])
                        )
                        user_stories.append(user_story)
                    
                    epic = Epic(
                        id=epic_data.get('id', f"epic_{len(all_epics)}"),
                        title=epic_data.get('title', ''),
                        description=epic_data.get('description', ''),
                        user_stories=user_stories,
                        phase=phase_enum,
                        priority=Priority(epic_data.get('priority', 'medium')),
                        success_metrics=epic_data.get('success_metrics', [])
                    )
                    all_epics.append(epic)
                    
            except json.JSONDecodeError:
                # Fallback parsing for malformed JSON
                epic_sections = re.findall(r'Epic [\d.]+: ([^\n]+)', phase_content)
                for i, epic_title in enumerate(epic_sections):
                    epic = Epic(
                        id=f"epic_{phase_num}_{i+1}",
                        title=epic_title.strip(),
                        description=f"Epic from Phase {phase_num}",
                        user_stories=[],
                        phase=phase_enum,
                        priority=Priority.MEDIUM
                    )
                    all_epics.append(epic)
        
        return all_epics

    async def _extract_technical_requirements(self, content: str) -> List[TechnicalRequirement]:
        """Extract technical requirements from PRD content"""
        
        # Find technical specifications section
        tech_sections = re.findall(
            r'((?:Technical Specifications|Performance Requirements|Security Requirements).*?)(?=\n\d+\.|$)',
            content,
            re.DOTALL
        )
        
        all_tech_reqs = []
        
        for section in tech_sections:
            template = self.parsing_templates['technical_requirements']
            prompt = template.replace('{text}', section)
            response = await self.llm_provider.generate_completion_simple(prompt)
            
            try:
                parsed_data = json.loads(response)
                for req_data in parsed_data.get('technical_requirements', []):
                    tech_req = TechnicalRequirement(
                        id=req_data.get('id', f"tech_req_{len(all_tech_reqs)}"),
                        title=req_data.get('title', ''),
                        description=req_data.get('description', ''),
                        category=req_data.get('category', 'technical'),
                        specifications=req_data.get('specifications', {}),
                        acceptance_criteria=req_data.get('acceptance_criteria', []),
                        priority=Priority(req_data.get('priority', 'medium'))
                    )
                    all_tech_reqs.append(tech_req)
                    
            except json.JSONDecodeError:
                # Fallback parsing
                requirements = re.findall(r'([A-Z][^.]+\.)', section)
                for i, req_text in enumerate(requirements):
                    tech_req = TechnicalRequirement(
                        id=f"tech_req_{len(all_tech_reqs)}",
                        title=req_text.strip()[:50],
                        description=req_text.strip(),
                        category='technical',
                        specifications={},
                        acceptance_criteria=[req_text.strip()],
                        priority=Priority.MEDIUM
                    )
                    all_tech_reqs.append(tech_req)
        
        return all_tech_reqs

    async def _extract_user_personas(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Extract user personas from PRD content"""
        
        personas = {}
        persona_pattern = r'Persona:\s*"([^"]+)",\s*([^\n]+).*?Bio:\s*([^G]+).*?Goals:\s*([^U]+).*?User Stories:\s*(.*?)(?=Persona:|$)'
        
        matches = re.findall(persona_pattern, content, re.DOTALL)
        
        for match in matches:
            name, title, bio, goals, stories = match
            
            # Extract user stories for this persona
            story_list = re.findall(r'"([^"]+)"', stories)
            
            personas[name] = {
                'title': title.strip(),
                'bio': bio.strip(),
                'goals': goals.strip(),
                'user_stories': story_list
            }
        
        return personas

    async def _extract_success_metrics(self, content: str) -> Dict[str, str]:
        """Extract success metrics and KPIs from PRD content"""
        
        metrics = {}
        
        # Look for quantified goals
        metric_patterns = [
            r'(\d+)%\s+([^.]+)\.',
            r'([^:]+):\s*([^.]+(?:reduction|improvement|increase)[^.]*)\.',
            r'(Response Time|Throughput|Resource Usage):\s*([^.]+)\.'
        ]
        
        for pattern in metric_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    key, value = match
                    metrics[key.strip()] = value.strip()
        
        return metrics

    async def _analyze_dependencies(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze dependencies between requirements using LLM"""
        
        template = self.parsing_templates['dependency_analysis']
        prompt = template.replace('{requirements_json}', json.dumps(requirements, indent=2))
        
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                'dependencies': {},
                'critical_path': [],
                'parallel_tracks': []
            }

    async def _estimate_complexity(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate complexity and timeline using LLM"""
        
        template = self.parsing_templates['complexity_estimation']
        prompt = template.replace('{requirements_json}', json.dumps(requirements, indent=2))
        
        response = await self.llm_provider.generate_completion_simple(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                'complexity_analysis': {
                    'overall_score': 0.5,
                    'factors': {}
                },
                'timeline_estimation': {
                    'total_days': 180
                },
                'risk_factors': []
            }

    def _group_by_phases(self, epics: List[Epic]) -> Dict[str, List[str]]:
        """Group epics by development phases"""
        
        phases = {}
        for epic in epics:
            phase_name = epic.phase.value
            if phase_name not in phases:
                phases[phase_name] = []
            phases[phase_name].append(epic.id)
        
        return phases

    async def validate_requirements(self, analysis: RequirementAnalysis) -> Dict[str, List[str]]:
        """Validate requirements for completeness and consistency"""
        
        issues = {
            'missing_acceptance_criteria': [],
            'orphaned_dependencies': [],
            'priority_conflicts': [],
            'timeline_inconsistencies': []
        }
        
        # Check for missing acceptance criteria
        for epic in analysis.epics:
            for story in epic.user_stories:
                if not story.acceptance_criteria:
                    issues['missing_acceptance_criteria'].append(story.id)
        
        # Check for orphaned dependencies
        all_ids = {epic.id for epic in analysis.epics}
        all_ids.update({story.id for epic in analysis.epics for story in epic.user_stories})
        
        for deps in analysis.dependencies.values():
            for dep in deps:
                if dep not in all_ids:
                    issues['orphaned_dependencies'].append(dep)
        
        return issues