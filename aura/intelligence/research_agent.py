"""
Research Agent Framework - Continuous Learning and Discovery
Become the Toolmaker: Build agents that learn, discover, and evolve
"""

import asyncio
import json
import re
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from urllib.parse import urlparse, urljoin
import hashlib

from ..core.config import AuraConfig
from ..llm.providers import LLMProvider


class ResearchType(Enum):
    LIBRARY_DISCOVERY = "library_discovery"
    SECURITY_ADVISORY = "security_advisory"
    ARCHITECTURE_PATTERN = "architecture_pattern"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    LANGUAGE_FEATURE = "language_feature"
    FRAMEWORK_UPDATE = "framework_update"
    BEST_PRACTICE = "best_practice"
    VULNERABILITY_SCAN = "vulnerability_scan"


class ResearchPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


class ResearchStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


@dataclass
class ResearchQuery:
    id: str
    query_type: ResearchType
    priority: ResearchPriority
    description: str
    keywords: List[str]
    target_languages: List[str] = field(default_factory=list)
    target_domains: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: ResearchStatus = ResearchStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ResearchResult:
    query_id: str
    source_url: Optional[str]
    title: str
    summary: str
    content: str
    relevance_score: float
    confidence_score: float
    tags: List[str]
    discovered_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LibraryInfo:
    name: str
    version: str
    description: str
    github_url: Optional[str]
    documentation_url: Optional[str]
    popularity_score: float
    maintenance_score: float
    security_score: float
    compatibility: Dict[str, str]  # language/framework compatibility
    use_cases: List[str]
    alternatives: List[str] = field(default_factory=list)


@dataclass
class SecurityAdvisory:
    id: str
    severity: str
    title: str
    description: str
    affected_packages: List[str]
    affected_versions: List[str]
    fixed_versions: List[str]
    published_date: datetime
    cve_id: Optional[str] = None
    references: List[str] = field(default_factory=list)


@dataclass
class ArchitecturePattern:
    name: str
    category: str
    description: str
    use_cases: List[str]
    advantages: List[str]
    disadvantages: List[str]
    implementation_examples: List[str]
    related_patterns: List[str] = field(default_factory=list)
    complexity_level: str = "medium"


class ResearchAgent:
    def __init__(self, config: AuraConfig, llm_provider: LLMProvider):
        self.config = config
        self.llm_provider = llm_provider
        self.research_history: List[ResearchResult] = []
        self.pending_queries: List[ResearchQuery] = []
        self.knowledge_base: Dict[str, Any] = {}
        self.last_scan_time: Dict[ResearchType, datetime] = {}
        self.research_patterns = self._load_research_patterns()
        
    def _load_research_patterns(self) -> Dict[str, str]:
        """Load research and analysis patterns"""
        return {
            'library_analysis': """
Analyze this library/package information and provide structured insights:

Library: {library_name}
Description: {description}
GitHub: {github_url}
Documentation: {documentation_url}

Provide analysis in JSON format:
{{
  "library_assessment": {{
    "popularity_score": 0.85,
    "maintenance_score": 0.92,
    "security_score": 0.88,
    "learning_curve": "moderate",
    "production_readiness": "excellent"
  }},
  "use_cases": [
    "Web API development",
    "Microservices architecture",
    "Real-time applications"
  ],
  "advantages": [
    "High performance",
    "Excellent documentation",
    "Active community"
  ],
  "disadvantages": [
    "Steep learning curve",
    "Large bundle size"
  ],
  "compatibility": {{
    "python": ">=3.8",
    "frameworks": ["FastAPI", "Django", "Flask"]
  }},
  "alternatives": [
    "Alternative library 1",
    "Alternative library 2"
  ],
  "recommendation": "Highly recommended for production use in modern Python applications"
}}

Focus on practical assessment for real-world usage.
""",
            
            'security_analysis': """
Analyze this security advisory and provide actionable insights:

Advisory Title: {title}
Severity: {severity}
Description: {description}
Affected Packages: {packages}

Provide analysis in JSON format:
{{
  "risk_assessment": {{
    "severity_level": "high|medium|low|critical",
    "exploit_likelihood": "high|medium|low",
    "impact_scope": "application|system|data",
    "urgency": "immediate|urgent|moderate|low"
  }},
  "affected_systems": [
    "List of potentially affected systems/components"
  ],
  "mitigation_steps": [
    "Immediate actions to take",
    "Long-term security improvements"
  ],
  "detection_methods": [
    "How to detect if you're affected",
    "Monitoring recommendations"
  ],
  "remediation": {{
    "quick_fix": "Immediate remediation steps",
    "proper_fix": "Comprehensive solution",
    "prevention": "How to prevent similar issues"
  }}
}}

Focus on actionable intelligence for immediate response.
""",
            
            'pattern_analysis': """
Analyze this architectural pattern and provide implementation guidance:

Pattern Name: {pattern_name}
Context: {context}
Description: {description}

Provide analysis in JSON format:
{{
  "pattern_assessment": {{
    "complexity_level": "beginner|intermediate|advanced|expert",
    "implementation_effort": "low|medium|high|very_high",
    "maintenance_overhead": "low|medium|high",
    "performance_impact": "positive|neutral|negative",
    "scalability": "excellent|good|limited|poor"
  }},
  "implementation_guide": {{
    "prerequisites": ["Required knowledge/tools"],
    "key_components": ["Essential components to implement"],
    "implementation_steps": ["Step-by-step implementation"],
    "common_pitfalls": ["Mistakes to avoid"],
    "testing_strategy": ["How to validate implementation"]
  }},
  "use_cases": [
    "Ideal scenarios for this pattern",
    "When NOT to use this pattern"
  ],
  "related_patterns": [
    "Complementary patterns",
    "Alternative patterns"
  ],
  "real_world_examples": [
    "Industry examples",
    "Open source implementations"
  ]
}}

Focus on practical implementation guidance.
""",
            
            'discovery_synthesis': """
Synthesize multiple research findings and identify patterns:

Research Topics: {topics}
Findings: {findings}

Provide synthesis in JSON format:
{{
  "emerging_trends": [
    "Key trends identified across findings",
    "Technology directions",
    "Industry shifts"
  ],
  "knowledge_gaps": [
    "Areas needing further research",
    "Unexplored opportunities"
  ],
  "actionable_insights": [
    "Immediate actions based on findings",
    "Strategic recommendations",
    "Technology adoption suggestions"
  ],
  "risk_factors": [
    "Potential risks identified",
    "Mitigation strategies"
  ],
  "innovation_opportunities": [
    "New possibilities discovered",
    "Combination opportunities",
    "Competitive advantages"
  ]
}}

Focus on strategic insights and future planning.
"""
        }
    
    async def start_continuous_research(self):
        """Start continuous research and learning process"""
        
        print("🔬 Initializing Research Agent Framework...")
        print("🧠 Continuous learning and discovery system activated")
        
        # Initialize research queries
        await self._initialize_research_queries()
        
        # Start research loops
        research_tasks = [
            asyncio.create_task(self._security_research_loop()),
            asyncio.create_task(self._library_discovery_loop()),
            asyncio.create_task(self._pattern_research_loop()),
            asyncio.create_task(self._knowledge_synthesis_loop())
        ]
        
        print("🚀 Research Agent Framework is running...")
        
        # Run research tasks concurrently
        await asyncio.gather(*research_tasks, return_exceptions=True)
    
    async def _initialize_research_queries(self):
        """Initialize priority research queries"""
        
        priority_queries = [
            ResearchQuery(
                id="security-scan-daily",
                query_type=ResearchType.SECURITY_ADVISORY,
                priority=ResearchPriority.CRITICAL,
                description="Daily security advisory scan for Python ecosystem",
                keywords=["python", "security", "vulnerability", "CVE"],
                target_languages=["python"],
                target_domains=["security.org", "cve.mitre.org", "github.com/advisories"]
            ),
            ResearchQuery(
                id="library-discovery-weekly",
                query_type=ResearchType.LIBRARY_DISCOVERY,
                priority=ResearchPriority.HIGH,
                description="Weekly discovery of new Python libraries and frameworks",
                keywords=["python", "library", "framework", "new", "trending"],
                target_languages=["python"],
                target_domains=["pypi.org", "github.com", "reddit.com/r/python"]
            ),
            ResearchQuery(
                id="architecture-patterns-monthly",
                query_type=ResearchType.ARCHITECTURE_PATTERN,
                priority=ResearchPriority.MEDIUM,
                description="Monthly research on emerging architecture patterns",
                keywords=["architecture", "pattern", "microservices", "cloud", "scalability"],
                target_domains=["martinfowler.com", "dzone.com", "infoq.com"]
            ),
            ResearchQuery(
                id="performance-optimization-weekly",
                query_type=ResearchType.PERFORMANCE_OPTIMIZATION,
                priority=ResearchPriority.HIGH,
                description="Weekly performance optimization research",
                keywords=["python", "performance", "optimization", "profiling", "memory"],
                target_languages=["python"],
                target_domains=["stackoverflow.com", "realpython.com", "pythonspeed.com"]
            ),
            ResearchQuery(
                id="ai-ml-developments-daily",
                query_type=ResearchType.LANGUAGE_FEATURE,
                priority=ResearchPriority.HIGH,
                description="Daily AI/ML development tracking",
                keywords=["artificial intelligence", "machine learning", "LLM", "AI agents"],
                target_domains=["arxiv.org", "papers.nips.cc", "openai.com", "anthropic.com"]
            )
        ]
        
        self.pending_queries.extend(priority_queries)
        print(f"📋 Initialized {len(priority_queries)} priority research queries")
    
    async def _security_research_loop(self):
        """Continuous security research and monitoring"""
        
        while True:
            try:
                print("🔒 Conducting security research scan...")
                
                # Simulate security advisory research
                advisories = await self._research_security_advisories()
                
                for advisory in advisories:
                    await self._process_security_advisory(advisory)
                
                # Update last scan time
                self.last_scan_time[ResearchType.SECURITY_ADVISORY] = datetime.now()
                
                print(f"🔒 Security scan complete. Found {len(advisories)} advisories.")
                
                # Wait 24 hours for next security scan
                await asyncio.sleep(24 * 3600)
                
            except Exception as e:
                print(f"❌ Security research error: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour
    
    async def _library_discovery_loop(self):
        """Continuous library and framework discovery"""
        
        while True:
            try:
                print("📚 Conducting library discovery research...")
                
                # Simulate library discovery
                libraries = await self._discover_new_libraries()
                
                for library in libraries:
                    await self._analyze_library(library)
                
                self.last_scan_time[ResearchType.LIBRARY_DISCOVERY] = datetime.now()
                
                print(f"📚 Library discovery complete. Analyzed {len(libraries)} libraries.")
                
                # Wait 7 days for next library discovery
                await asyncio.sleep(7 * 24 * 3600)
                
            except Exception as e:
                print(f"❌ Library discovery error: {e}")
                await asyncio.sleep(24 * 3600)  # Retry in 24 hours
    
    async def _pattern_research_loop(self):
        """Continuous architecture pattern research"""
        
        while True:
            try:
                print("🏗️ Conducting architecture pattern research...")
                
                # Simulate pattern research
                patterns = await self._research_architecture_patterns()
                
                for pattern in patterns:
                    await self._analyze_architecture_pattern(pattern)
                
                self.last_scan_time[ResearchType.ARCHITECTURE_PATTERN] = datetime.now()
                
                print(f"🏗️ Pattern research complete. Analyzed {len(patterns)} patterns.")
                
                # Wait 30 days for next pattern research
                await asyncio.sleep(30 * 24 * 3600)
                
            except Exception as e:
                print(f"❌ Pattern research error: {e}")
                await asyncio.sleep(7 * 24 * 3600)  # Retry in 7 days
    
    async def _knowledge_synthesis_loop(self):
        """Continuous knowledge synthesis and insight generation"""
        
        while True:
            try:
                print("🧠 Conducting knowledge synthesis...")
                
                # Synthesize recent research findings
                insights = await self._synthesize_knowledge()
                
                # Update knowledge base
                await self._update_knowledge_base(insights)
                
                print(f"🧠 Knowledge synthesis complete. Generated {len(insights)} insights.")
                
                # Wait 3 days for next synthesis
                await asyncio.sleep(3 * 24 * 3600)
                
            except Exception as e:
                print(f"❌ Knowledge synthesis error: {e}")
                await asyncio.sleep(24 * 3600)  # Retry in 24 hours
    
    async def _research_security_advisories(self) -> List[SecurityAdvisory]:
        """Research and collect security advisories"""
        
        # Simulate security advisory discovery
        advisories = [
            SecurityAdvisory(
                id="CVE-2024-001",
                severity="HIGH",
                title="Remote Code Execution in Popular Python Library",
                description="A critical vulnerability allowing remote code execution through unsafe deserialization",
                affected_packages=["vulnerable-lib"],
                affected_versions=["< 2.1.0"],
                fixed_versions=["2.1.0"],
                published_date=datetime.now(),
                cve_id="CVE-2024-001",
                references=["https://github.com/example/advisory"]
            ),
            SecurityAdvisory(
                id="GHSA-2024-001",
                severity="MEDIUM",
                title="Information Disclosure in Web Framework",
                description="Sensitive information may be leaked through error messages",
                affected_packages=["web-framework"],
                affected_versions=["1.0.0 - 1.2.3"],
                fixed_versions=["1.2.4"],
                published_date=datetime.now(),
                references=["https://github.com/example/security"]
            )
        ]
        
        return advisories
    
    async def _process_security_advisory(self, advisory: SecurityAdvisory):
        """Process and analyze security advisory"""
        
        # Analyze advisory with LLM
        prompt = self.research_patterns['security_analysis'].format(
            title=advisory.title,
            severity=advisory.severity,
            description=advisory.description,
            packages=", ".join(advisory.affected_packages)
        )
        
        try:
            response = await self.llm_provider.generate_completion_simple(prompt)
            analysis = json.loads(response)
            
            # Store analysis in knowledge base
            advisory_key = f"security_advisory_{advisory.id}"
            self.knowledge_base[advisory_key] = {
                'advisory': advisory,
                'analysis': analysis,
                'processed_at': datetime.now().isoformat()
            }
            
            # Create research result
            result = ResearchResult(
                query_id="security-scan-daily",
                source_url=advisory.references[0] if advisory.references else None,
                title=advisory.title,
                summary=f"Security advisory: {advisory.severity} severity",
                content=advisory.description,
                relevance_score=0.9,
                confidence_score=0.95,
                tags=["security", "vulnerability", advisory.severity.lower()],
                metadata={"cve_id": advisory.cve_id, "affected_packages": advisory.affected_packages}
            )
            
            self.research_history.append(result)
            
        except Exception as e:
            print(f"❌ Error processing security advisory {advisory.id}: {e}")
    
    async def _discover_new_libraries(self) -> List[LibraryInfo]:
        """Discover new and trending libraries"""
        
        # Simulate library discovery
        libraries = [
            LibraryInfo(
                name="aura-ai",
                version="1.0.0",
                description="Advanced AI agent framework for autonomous development",
                github_url="https://github.com/example/aura-ai",
                documentation_url="https://aura-ai.readthedocs.io",
                popularity_score=0.95,
                maintenance_score=0.92,
                security_score=0.88,
                compatibility={"python": ">=3.8", "frameworks": ["asyncio", "aiohttp"]},
                use_cases=["AI agents", "automation", "code analysis"]
            ),
            LibraryInfo(
                name="fastmemory",
                version="2.1.0",
                description="High-performance memory management for Python applications",
                github_url="https://github.com/example/fastmemory",
                documentation_url="https://fastmemory.dev",
                popularity_score=0.78,
                maintenance_score=0.85,
                security_score=0.91,
                compatibility={"python": ">=3.9", "frameworks": ["numpy", "pandas"]},
                use_cases=["data processing", "scientific computing", "performance optimization"]
            )
        ]
        
        return libraries
    
    async def _analyze_library(self, library: LibraryInfo):
        """Analyze discovered library"""
        
        prompt = self.research_patterns['library_analysis'].format(
            library_name=library.name,
            description=library.description,
            github_url=library.github_url or "Not available",
            documentation_url=library.documentation_url or "Not available"
        )
        
        try:
            response = await self.llm_provider.generate_completion_simple(prompt)
            analysis = json.loads(response)
            
            # Store analysis in knowledge base
            library_key = f"library_{library.name}"
            self.knowledge_base[library_key] = {
                'library': library,
                'analysis': analysis,
                'discovered_at': datetime.now().isoformat()
            }
            
            # Create research result
            result = ResearchResult(
                query_id="library-discovery-weekly",
                source_url=library.github_url,
                title=f"Library Analysis: {library.name}",
                summary=f"Analysis of {library.name} - {library.description}",
                content=json.dumps(analysis, indent=2),
                relevance_score=library.popularity_score,
                confidence_score=0.85,
                tags=["library", "discovery"] + library.use_cases,
                metadata={"version": library.version, "compatibility": library.compatibility}
            )
            
            self.research_history.append(result)
            
        except Exception as e:
            print(f"❌ Error analyzing library {library.name}: {e}")
    
    async def _research_architecture_patterns(self) -> List[ArchitecturePattern]:
        """Research emerging architecture patterns"""
        
        # Simulate pattern discovery
        patterns = [
            ArchitecturePattern(
                name="Event-Driven Microservices",
                category="Distributed Systems",
                description="Microservices architecture using event-driven communication",
                use_cases=["Scalable web applications", "Real-time data processing", "IoT systems"],
                advantages=["Loose coupling", "Scalability", "Fault tolerance"],
                disadvantages=["Complexity", "Eventual consistency challenges", "Debugging difficulty"],
                implementation_examples=["Event sourcing", "CQRS", "Message queues"],
                related_patterns=["CQRS", "Event Sourcing", "Saga Pattern"],
                complexity_level="advanced"
            ),
            ArchitecturePattern(
                name="AI-First Architecture",
                category="Artificial Intelligence",
                description="Architecture pattern that integrates AI as a core component",
                use_cases=["Intelligent applications", "Adaptive systems", "Autonomous agents"],
                advantages=["Intelligent behavior", "Adaptability", "Automation"],
                disadvantages=["Resource intensive", "Unpredictability", "Model dependencies"],
                implementation_examples=["LLM integration", "ML pipelines", "Agent frameworks"],
                related_patterns=["Microservices", "Event-Driven", "Pipe and Filter"],
                complexity_level="expert"
            )
        ]
        
        return patterns
    
    async def _analyze_architecture_pattern(self, pattern: ArchitecturePattern):
        """Analyze architecture pattern"""
        
        prompt = self.research_patterns['pattern_analysis'].format(
            pattern_name=pattern.name,
            context=pattern.category,
            description=pattern.description
        )
        
        try:
            response = await self.llm_provider.generate_completion_simple(prompt)
            analysis = json.loads(response)
            
            # Store analysis in knowledge base
            pattern_key = f"pattern_{pattern.name.lower().replace(' ', '_')}"
            self.knowledge_base[pattern_key] = {
                'pattern': pattern,
                'analysis': analysis,
                'researched_at': datetime.now().isoformat()
            }
            
            # Create research result
            result = ResearchResult(
                query_id="architecture-patterns-monthly",
                source_url=None,
                title=f"Architecture Pattern: {pattern.name}",
                summary=f"Analysis of {pattern.name} pattern in {pattern.category}",
                content=json.dumps(analysis, indent=2),
                relevance_score=0.8,
                confidence_score=0.9,
                tags=["architecture", "pattern", pattern.category.lower()],
                metadata={"complexity": pattern.complexity_level, "category": pattern.category}
            )
            
            self.research_history.append(result)
            
        except Exception as e:
            print(f"❌ Error analyzing pattern {pattern.name}: {e}")
    
    async def _synthesize_knowledge(self) -> List[Dict[str, Any]]:
        """Synthesize recent research findings into actionable insights"""
        
        # Get recent research results (last 7 days)
        recent_results = [
            r for r in self.research_history 
            if (datetime.now() - r.discovered_at).days <= 7
        ]
        
        if not recent_results:
            return []
        
        # Group findings by type
        topics = list(set(tag for result in recent_results for tag in result.tags))
        findings = [f"{r.title}: {r.summary}" for r in recent_results[:10]]  # Last 10 findings
        
        prompt = self.research_patterns['discovery_synthesis'].format(
            topics=", ".join(topics),
            findings="\n".join(findings)
        )
        
        try:
            response = await self.llm_provider.generate_completion_simple(prompt)
            synthesis = json.loads(response)
            
            # Create insights from synthesis
            insights = [
                {
                    'type': 'emerging_trends',
                    'content': synthesis.get('emerging_trends', []),
                    'generated_at': datetime.now().isoformat()
                },
                {
                    'type': 'actionable_insights',
                    'content': synthesis.get('actionable_insights', []),
                    'generated_at': datetime.now().isoformat()
                },
                {
                    'type': 'innovation_opportunities',
                    'content': synthesis.get('innovation_opportunities', []),
                    'generated_at': datetime.now().isoformat()
                }
            ]
            
            return insights
            
        except Exception as e:
            print(f"❌ Error synthesizing knowledge: {e}")
            return []
    
    async def _update_knowledge_base(self, insights: List[Dict[str, Any]]):
        """Update knowledge base with new insights"""
        
        timestamp = datetime.now().isoformat()
        
        for insight in insights:
            key = f"insight_{insight['type']}_{timestamp}"
            self.knowledge_base[key] = insight
        
        # Cleanup old insights (keep last 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        
        keys_to_remove = [
            key for key, value in self.knowledge_base.items()
            if key.startswith('insight_') and 
            datetime.fromisoformat(value.get('generated_at', '2020-01-01')) < cutoff_date
        ]
        
        for key in keys_to_remove:
            del self.knowledge_base[key]
    
    def query_knowledge_base(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query the knowledge base for specific information"""
        
        results = []
        query_lower = query.lower()
        
        for key, value in self.knowledge_base.items():
            # Check if category matches
            if category and not key.startswith(category.lower()):
                continue
            
            # Check if query terms match
            try:
                content_str = json.dumps(value, default=str).lower()
            except (TypeError, ValueError):
                content_str = str(value).lower()
            
            if query_lower in content_str:
                results.append({
                    'key': key,
                    'relevance': content_str.count(query_lower),
                    'data': value
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        
        return results[:10]  # Return top 10 results
    
    def get_research_summary(self) -> Dict[str, Any]:
        """Get comprehensive research summary"""
        
        total_results = len(self.research_history)
        recent_results = len([r for r in self.research_history if (datetime.now() - r.discovered_at).days <= 7])
        
        # Categorize research by type
        by_category = {}
        for result in self.research_history:
            for tag in result.tags:
                by_category[tag] = by_category.get(tag, 0) + 1
        
        # Get latest insights
        latest_insights = [
            value for key, value in self.knowledge_base.items()
            if key.startswith('insight_')
        ]
        latest_insights.sort(key=lambda x: x['generated_at'], reverse=True)
        
        return {
            'total_research_results': total_results,
            'recent_results_7_days': recent_results,
            'research_categories': by_category,
            'knowledge_base_size': len(self.knowledge_base),
            'latest_insights': latest_insights[:5],
            'last_scan_times': {
                research_type.value: scan_time.isoformat() if scan_time else None
                for research_type, scan_time in self.last_scan_time.items()
            }
        }
    
    async def save_research_state(self, filepath: Path):
        """Save research state to file"""
        
        state = {
            'research_history': [
                {
                    'query_id': r.query_id,
                    'source_url': r.source_url,
                    'title': r.title,
                    'summary': r.summary,
                    'content': r.content,
                    'relevance_score': r.relevance_score,
                    'confidence_score': r.confidence_score,
                    'tags': r.tags,
                    'discovered_at': r.discovered_at.isoformat(),
                    'metadata': r.metadata
                }
                for r in self.research_history
            ],
            'knowledge_base': self.knowledge_base,
            'last_scan_times': {
                research_type.value: scan_time.isoformat() if scan_time else None
                for research_type, scan_time in self.last_scan_time.items()
            },
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        print(f"💾 Research state saved to {filepath}")
    
    async def load_research_state(self, filepath: Path):
        """Load research state from file"""
        
        if not filepath.exists():
            print(f"⚠️ Research state file not found: {filepath}")
            return
        
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        # Restore research history
        self.research_history = [
            ResearchResult(
                query_id=r['query_id'],
                source_url=r['source_url'],
                title=r['title'],
                summary=r['summary'],
                content=r['content'],
                relevance_score=r['relevance_score'],
                confidence_score=r['confidence_score'],
                tags=r['tags'],
                discovered_at=datetime.fromisoformat(r['discovered_at']),
                metadata=r['metadata']
            )
            for r in state.get('research_history', [])
        ]
        
        # Restore knowledge base
        self.knowledge_base = state.get('knowledge_base', {})
        
        # Restore scan times
        last_scan_times = state.get('last_scan_times', {})
        for research_type_str, scan_time_str in last_scan_times.items():
            if scan_time_str:
                research_type = ResearchType(research_type_str)
                self.last_scan_time[research_type] = datetime.fromisoformat(scan_time_str)
        
        print(f"📥 Research state loaded from {filepath}")
        print(f"📊 Loaded {len(self.research_history)} research results")
        print(f"🧠 Loaded knowledge base with {len(self.knowledge_base)} entries")


async def run_research_agent_demo():
    """Run research agent demonstration"""
    
    # Initialize configuration and LLM provider
    config = AuraConfig()
    
    # Use mock LLM provider for testing
    from ..planning.test_parser_mock import MockLLMProvider
    llm_provider = MockLLMProvider()
    
    # Initialize research agent
    agent = ResearchAgent(config, llm_provider)
    
    print("🔬 Research Agent Framework Demo")
    print("Demonstrating continuous learning capabilities...")
    
    # Initialize research queries
    await agent._initialize_research_queries()
    
    # Simulate research cycles
    print("\n🔒 Simulating security research...")
    advisories = await agent._research_security_advisories()
    for advisory in advisories:
        await agent._process_security_advisory(advisory)
    
    print("\n📚 Simulating library discovery...")
    libraries = await agent._discover_new_libraries()
    for library in libraries:
        await agent._analyze_library(library)
    
    print("\n🏗️ Simulating pattern research...")
    patterns = await agent._research_architecture_patterns()
    for pattern in patterns:
        await agent._analyze_architecture_pattern(pattern)
    
    print("\n🧠 Simulating knowledge synthesis...")
    insights = await agent._synthesize_knowledge()
    await agent._update_knowledge_base(insights)
    
    # Generate research summary
    summary = agent.get_research_summary()
    
    print("\n📊 Research Agent Summary:")
    print(f"📋 Total research results: {summary['total_research_results']}")
    print(f"🧠 Knowledge base entries: {summary['knowledge_base_size']}")
    print(f"💡 Latest insights: {len(summary['latest_insights'])}")
    
    print("\n🔍 Research categories discovered:")
    for category, count in summary['research_categories'].items():
        print(f"   • {category}: {count} results")
    
    # Test knowledge base query
    print("\n🔎 Testing knowledge base queries...")
    security_results = agent.query_knowledge_base("security", "security")
    print(f"   Security query returned {len(security_results)} results")
    
    library_results = agent.query_knowledge_base("python", "library")
    print(f"   Library query returned {len(library_results)} results")
    
    # Save research state
    state_file = Path("/home/greenantix/AI/LLMdiver/aura/intelligence/research_agent_state.json")
    await agent.save_research_state(state_file)
    
    print("\n🎉 Research Agent Framework demonstration complete!")
    print("🚀 Continuous learning capabilities established")
    
    return agent


if __name__ == "__main__":
    asyncio.run(run_research_agent_demo())