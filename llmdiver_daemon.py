#!/usr/bin/env python3
"""
LLMdiver Background Daemon
Monitors repositories, runs analysis, and automates git operations
"""
# Test trigger for enhanced LLM analysis with improved prompts

import os
import sys
import time
import json
import subprocess
import threading
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import signal

import git
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
import hashlib
import shutil
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

try:
    import sentence_transformers
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import llama_cpp
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

class LLMdiverConfig:
    def __init__(self, config_path: str = "config/llmdiver.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            "daemon": {
                "enabled": True,
                "port": 8080,
                "host": "localhost",
                "log_level": "INFO",
                "watch_debounce": 5,
                "max_concurrent_analyses": 3
            },
            "repositories": [
                {
                    "name": "GMAILspambot",
                    "path": "/home/greenantix/AI/GMAILspambot",
                    "auto_commit": True,
                    "auto_push": False,
                    "analysis_triggers": ["*.py", "*.js", "*.sh"],
                    "commit_threshold": 10
                }
            ],
            "git_automation": {
                "enabled": True,
                "commit_message_template": "🤖 LLMdiver: {summary}\n\n{details}",
                "auto_push": False,
                "documentation_update": True,
                "branch_protection": ["main", "master"]
            },
            "llm_integration": {
                "model": "meta-llama-3.1-8b-instruct",
                "url": "http://127.0.0.1:1234/v1/chat/completions",
                "temperature": 0.3,
                "max_tokens": 4096
            },
            "repomix": {
                "style": "markdown",
                "compress": True,
                "remove_comments": True,
                "include_patterns": ["*.py", "*.js", "*.ts"],
                "ignore_patterns": ["*.md", "*.log"],
                "use_gitignore": False
            },
            "semantic_search": {
                "enabled": True,
                "embedding_model": "tfidf",  # Options: tfidf, sentence_transformers, llama_cpp
                "model_path": "",  # Path to GGUF file for llama_cpp
                "model_name": "all-MiniLM-L6-v2",  # For sentence_transformers
                "similarity_threshold": 0.1,
                "max_similar_blocks": 5
            }
        }
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            logging.warning(f"Config file not found: {self.config_path}, using defaults")
            return default_config
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in config: {e}")
            return default_config

class RepoWatcher(FileSystemEventHandler):
    def __init__(self, daemon, repo_config):
        self.daemon = daemon
        self.repo_config = repo_config
        self.last_trigger = 0
        self.debounce_time = daemon.config.config["daemon"]["watch_debounce"]
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Check if file matches trigger patterns
        file_path = Path(event.src_path)
        triggers = self.repo_config["analysis_triggers"]
        
        if not any(file_path.match(pattern) for pattern in triggers):
            return
            
        # Debounce rapid changes
        current_time = time.time()
        if current_time - self.last_trigger < self.debounce_time:
            return
            
        self.last_trigger = current_time
        logging.info(f"File change detected: {file_path}")
        
        # Schedule analysis
        self.daemon.schedule_analysis(self.repo_config)

class LLMStudioClient:
    def __init__(self, config):
        self.config = config
        self.url = config["llm_integration"]["url"]
        self.model = config["llm_integration"]["model"]
        self.specialized_prompts = self._load_specialized_prompts()
    
    def chunk_text(self, text: str, chunk_size: int = 16000) -> List[str]:
        """Split text into chunks that fit within context window"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks

    def _load_specialized_prompts(self) -> Dict:
        """Load specialized prompt templates for different analysis types"""
        return {
            "dependency": """You are a dependency security expert analyzing package and configuration changes. Focus specifically on security, compatibility, and maintenance implications.

**DEPENDENCY ANALYSIS PRIORITY FRAMEWORK:**
- CRITICAL: Security vulnerabilities, known exploits, malicious packages
- HIGH: Breaking changes, version conflicts, deprecated packages
- MEDIUM: Performance impact, bundle size increases, maintenance burden
- LOW: Minor version updates, documentation improvements

**REQUIRED OUTPUT FORMAT:**

## Executive Summary
[2-3 sentences: Security risk assessment, compatibility concerns, immediate actions needed]

## Security Assessment (Priority: CRITICAL)
[Known vulnerabilities, suspicious packages, security advisories - include CVE numbers and severity scores]

## Compatibility & Breaking Changes (Priority: HIGH)
[Version conflicts, API changes, migration requirements - include specific version numbers]

## Performance & Bundle Impact (Priority: MEDIUM)
[Size increases, loading performance, runtime impact - provide metrics where possible]

## Maintenance Recommendations (Priority: LOW)
[Update strategies, alternative packages, long-term dependency health]

**ANALYSIS REQUIREMENTS:**
- Check against known vulnerability databases
- Assess package popularity and maintenance status
- Evaluate licensing compatibility
- Consider supply chain security risks""",

            "security": """You are a cybersecurity expert conducting a focused security audit. Prioritize identifying vulnerabilities, attack vectors, and security weaknesses.

**SECURITY ANALYSIS PRIORITY FRAMEWORK:**
- CRITICAL: Remote code execution, privilege escalation, data exposure
- HIGH: Authentication bypasses, injection vulnerabilities, access control flaws
- MEDIUM: Information disclosure, CSRF, weak cryptography
- LOW: Security headers, timing attacks, information leakage

**REQUIRED OUTPUT FORMAT:**

## Executive Summary
[2-3 sentences: Most critical vulnerabilities found, attack surface assessment, immediate security actions]

## Critical Vulnerabilities (Priority: CRITICAL)
[Remote exploits, privilege escalation, data breaches - include attack scenarios and file:line references]

## Authentication & Authorization Issues (Priority: HIGH)
[Access control flaws, session management, privilege boundaries - provide exploit examples]

## Input Validation & Injection Risks (Priority: MEDIUM)
[SQL injection, XSS, command injection, deserialization - include vulnerable code snippets]

## Security Configuration & Headers (Priority: LOW)
[Missing headers, weak configurations, information disclosure - provide configuration fixes]

**ANALYSIS REQUIREMENTS:**
- Include OWASP Top 10 assessment
- Provide proof-of-concept exploit code where applicable
- Reference security standards and best practices
- Assess impact and likelihood for each finding""",

            "ui": """You are a frontend architecture expert analyzing user interface and user experience code. Focus on component design, state management, and user interaction patterns.

**UI/UX ANALYSIS PRIORITY FRAMEWORK:**
- CRITICAL: Accessibility violations, security in client-side code, data exposure
- HIGH: Performance bottlenecks, broken user flows, state management issues
- MEDIUM: Component reusability, design consistency, responsive design
- LOW: Code organization, naming conventions, minor UX improvements

**REQUIRED OUTPUT FORMAT:**

## Executive Summary
[2-3 sentences: UI architecture health, critical UX issues, performance concerns]

## Accessibility & Standards Compliance (Priority: CRITICAL)
[WCAG violations, keyboard navigation, screen reader compatibility - include specific fixes]

## Performance & User Experience (Priority: HIGH)
[Rendering bottlenecks, loading times, interaction delays - provide performance metrics]

## Component Architecture & State (Priority: MEDIUM)
[Component reusability, state management patterns, data flow - suggest architectural improvements]

## Design System & Consistency (Priority: LOW)
[Style consistency, responsive design, visual hierarchy - recommend design improvements]

**ANALYSIS REQUIREMENTS:**
- Assess against WCAG 2.1 guidelines
- Evaluate mobile responsiveness
- Check for performance anti-patterns
- Review state management architecture""",

            "data": """You are a data architecture expert analyzing database schemas, data access patterns, and information management. Focus on data integrity, performance, and security.

**DATA ANALYSIS PRIORITY FRAMEWORK:**
- CRITICAL: Data corruption risks, security vulnerabilities, privacy violations
- HIGH: Performance bottlenecks, scalability issues, data consistency problems
- MEDIUM: Query optimization, indexing strategies, schema design
- LOW: Documentation, naming conventions, minor optimizations

**REQUIRED OUTPUT FORMAT:**

## Executive Summary
[2-3 sentences: Data architecture health, critical data risks, performance assessment]

## Data Security & Privacy (Priority: CRITICAL)
[Data exposure, encryption gaps, privacy violations - include data flow analysis]

## Performance & Scalability (Priority: HIGH)
[Query performance, indexing issues, bottlenecks - provide optimization recommendations]

## Schema Design & Integrity (Priority: MEDIUM)
[Normalization issues, constraint violations, relationship problems - suggest schema improvements]

## Query Optimization & Maintenance (Priority: LOW)
[Inefficient queries, missing indexes, maintenance procedures - provide specific optimizations]

**ANALYSIS REQUIREMENTS:**
- Assess data classification and sensitivity
- Evaluate backup and recovery procedures
- Check for SQL injection vulnerabilities
- Review data access patterns and permissions""",

            "config": """You are a DevOps and configuration expert analyzing infrastructure, deployment, and configuration files. Focus on security, reliability, and operational excellence.

**CONFIGURATION ANALYSIS PRIORITY FRAMEWORK:**
- CRITICAL: Security misconfigurations, exposed secrets, production risks
- HIGH: Reliability issues, deployment problems, monitoring gaps
- MEDIUM: Performance tuning, resource optimization, maintenance procedures
- LOW: Documentation, naming consistency, minor improvements

**REQUIRED OUTPUT FORMAT:**

## Executive Summary
[2-3 sentences: Infrastructure security, deployment reliability, operational readiness]

## Security Configuration (Priority: CRITICAL)
[Exposed secrets, insecure defaults, access controls - include immediate remediation steps]

## Deployment & Reliability (Priority: HIGH)
[Deployment risks, single points of failure, rollback procedures - provide reliability improvements]

## Performance & Resources (Priority: MEDIUM)
[Resource allocation, scaling configuration, monitoring setup - suggest optimizations]

## Operational Excellence (Priority: LOW)
[Documentation, naming conventions, maintenance procedures - recommend process improvements]

**ANALYSIS REQUIREMENTS:**
- Check for exposed API keys and secrets
- Evaluate infrastructure as code practices
- Assess monitoring and alerting configuration
- Review disaster recovery procedures""",

            "general": """You are a principal software architect and security expert conducting a comprehensive code review for maintainability, security, and performance. Your analysis will be used by development teams to prioritize technical improvements.

**ANALYSIS PRIORITY FRAMEWORK:**
- CRITICAL: Security vulnerabilities, data leaks, system crashes
- HIGH: Performance bottlenecks, architectural violations, breaking changes
- MEDIUM: Code maintainability issues, technical debt, missing tests
- LOW: Style inconsistencies, minor optimizations, documentation gaps

**REQUIRED OUTPUT FORMAT:**

## Executive Summary
[3-4 sentence overview of codebase health, most critical findings, and recommended immediate actions]

## Critical Issues (Priority: CRITICAL)
[Security vulnerabilities, potential crashes, data exposure risks - include code snippets and file:line references]

## High Priority Concerns (Priority: HIGH)  
[Performance bottlenecks, architectural problems, breaking changes - include specific examples]

## Technical Debt & TODOs (Priority: MEDIUM)
[TODO/FIXME items, mock implementations, maintainability issues - provide file locations]

## Dead Code & Optimization (Priority: LOW)
[Unused functions, redundant code, minor optimizations - include removal suggestions]

## Actionable Recommendations
[Specific, prioritized action items with estimated impact and effort]

**ANALYSIS REQUIREMENTS:**
- Provide file:line references for all findings
- Include relevant code snippets for context
- Prioritize findings by business impact and security risk
- Focus on actionable recommendations, not theoretical issues
- Consider the project's architecture and technology stack"""
        }

    def _detect_analysis_type(self, repo_config: Dict, manifest_analysis: str, file_changes: List[str] = None) -> str:
        """Detect the type of analysis needed based on changes and context"""
        
        # Check for dependency changes
        if manifest_analysis and manifest_analysis.strip():
            return "dependency"
        
        # Check file changes if provided
        if file_changes:
            security_files = [f for f in file_changes if any(keyword in f.lower() for keyword in 
                            ['auth', 'login', 'password', 'token', 'security', 'crypto', 'encrypt'])]
            ui_files = [f for f in file_changes if any(ext in f.lower() for ext in 
                       ['.jsx', '.tsx', '.vue', '.html', '.css', '.scss', '.sass'])]
            config_files = [f for f in file_changes if any(keyword in f.lower() for keyword in 
                          ['config', 'env', 'docker', 'kubernetes', 'terraform', '.yml', '.yaml', '.ini'])]
            data_files = [f for f in file_changes if any(keyword in f.lower() for keyword in 
                         ['model', 'schema', 'migration', 'database', 'sql', 'query'])]
            
            if security_files:
                return "security"
            elif ui_files and len(ui_files) > len(file_changes) * 0.5:  # Majority UI files
                return "ui"
            elif config_files:
                return "config"
            elif data_files:
                return "data"
        
        return "general"

    def analyze_repo_summary(self, summary_text: str, analysis_type: str = "general") -> str:
        """Send repo summary to LM Studio for analysis with auto-chunking"""
        system_prompt = self.specialized_prompts.get(analysis_type, self.specialized_prompts["general"])

        # Check if chunking is enabled and needed
        enable_chunking = self.config["llm_integration"].get("enable_chunking", False)
        chunk_size = self.config["llm_integration"].get("chunk_size", 16000)
        
        if enable_chunking and len(summary_text) > chunk_size:
            logging.info(f"Large repository detected ({len(summary_text)} chars), using chunking...")
            chunks = self.chunk_text(summary_text, chunk_size)
            all_analyses = []
            
            for i, chunk in enumerate(chunks):
                logging.info(f"Analyzing chunk {i+1}/{len(chunks)}")
                chunk_prompt = f"Analyze this repository section ({i+1}/{len(chunks)}):\n\n{chunk}"
                
                analysis = self._send_single_request(system_prompt, chunk_prompt)
                if analysis.startswith("Analysis failed:") or analysis.startswith("LM Studio API error:"):
                    return analysis  # Return error immediately
                
                all_analyses.append(f"## Chunk {i+1}/{len(chunks)} Analysis\n{analysis}")
            
            # Combine analyses
            combined = "\n\n".join(all_analyses)
            
            # Send combined analysis for final summary
            final_prompt = f"Summarize and consolidate these code audit findings:\n\n{combined}"
            return self._send_single_request(
                "You are consolidating multiple code audit reports. Combine similar findings and prioritize the most critical issues.",
                final_prompt
            )
        else:
            # Single request for small repositories
            return self._send_single_request(system_prompt, f"Analyze this repository:\n\n{summary_text}")
    
    def _send_single_request(self, system_prompt: str, user_prompt: str) -> str:
        """Send a single request to LM Studio"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.config["llm_integration"]["temperature"],
            "max_tokens": self.config["llm_integration"]["max_tokens"],
            "stream": False
        }
        
        try:
            response = requests.post(self.url, json=payload, timeout=300)  # 5 minutes
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            logging.error("LM Studio API timeout")
            return "Analysis timed out: Request took too long"
        except requests.exceptions.HTTPError as e:
            error_text = ""
            try:
                error_data = e.response.json()
                error_text = error_data.get("error", e.response.text)
            except:
                error_text = e.response.text
            logging.error(f"LM Studio HTTP error: {e.response.status_code} - {error_text}")
            return f"LM Studio API error: {e.response.status_code} - {error_text}"
        except Exception as e:
            logging.error(f"LM Studio API error: {e}")
            return f"Analysis failed: {e}"

class GitAutomation:
    def __init__(self, config):
        self.config = config
        self.git_config = config["git_automation"]
    
    def analyze_changes(self, repo_path: str) -> Dict:
        """Analyze git changes in repository"""
        try:
            repo = git.Repo(repo_path)
            
            # Get modified files
            modified_files = [item.a_path for item in repo.index.diff(None)]
            untracked_files = repo.untracked_files
            
            # Get change stats
            total_changes = len(modified_files) + len(untracked_files)
            
            return {
                "modified_files": modified_files,
                "untracked_files": list(untracked_files),
                "total_changes": total_changes,
                "repo": repo
            }
        except Exception as e:
            logging.error(f"Git analysis error: {e}")
            return {"error": str(e)}
    
    def generate_commit_message(self, analysis: str, changes: Dict) -> str:
        """Generate intelligent commit message from analysis"""
        # Extract key points from analysis
        lines = analysis.split('\n')
        critical_issues = []
        todos = []
        improvements = []
        
        current_section = ""
        for line in lines:
            line = line.strip()
            if line.startswith("## Critical Issues"):
                current_section = "critical"
            elif line.startswith("## TODO"):
                current_section = "todos"
            elif line.startswith("## Architectural"):
                current_section = "improvements"
            elif line.startswith("-") or line.startswith("*"):
                if current_section == "critical" and len(critical_issues) < 3:
                    critical_issues.append(line[1:].strip())
                elif current_section == "todos" and len(todos) < 3:
                    todos.append(line[1:].strip())
                elif current_section == "improvements" and len(improvements) < 2:
                    improvements.append(line[1:].strip())
        
        # Create summary
        summary_parts = []
        if critical_issues:
            summary_parts.append(f"Fix critical issues ({len(critical_issues)})")
        if todos:
            summary_parts.append(f"Address TODOs ({len(todos)})")
        if improvements:
            summary_parts.append(f"Implement improvements ({len(improvements)})")
        
        summary = ", ".join(summary_parts) if summary_parts else "Update codebase"
        
        # Create detailed message
        details = []
        if critical_issues:
            details.append("Critical Issues:")
            details.extend(f"- {issue}" for issue in critical_issues[:3])
        if todos:
            details.append("\nTODOs Addressed:")
            details.extend(f"- {todo}" for todo in todos[:3])
        if changes.get("modified_files"):
            details.append(f"\nModified files: {len(changes['modified_files'])}")
        if changes.get("untracked_files"):
            details.append(f"New files: {len(changes['untracked_files'])}")
        
        details_text = "\n".join(details)
        
        return self.git_config["commit_message_template"].format(
            summary=summary,
            details=details_text
        )
    
    def auto_commit(self, repo_path: str, analysis: str) -> bool:
        """Automatically commit changes with generated message"""
        try:
            changes = self.analyze_changes(repo_path)
            if changes.get("error"):
                return False
                
            if changes["total_changes"] == 0:
                logging.info("No changes to commit")
                return True
                
            repo = changes["repo"]
            
            # Stage all changes
            repo.git.add('--all')
            
            # Generate and make commit
            message = self.generate_commit_message(analysis, changes)
            repo.index.commit(message)
            
            logging.info(f"Auto-committed {changes['total_changes']} changes")
            
            # Auto-push if enabled
            if self.git_config.get("auto_push", False):
                try:
                    origin = repo.remote('origin')
                    origin.push()
                    logging.info("Auto-pushed to remote")
                except Exception as e:
                    logging.warning(f"Auto-push failed: {e}")
            
            return True
            
        except Exception as e:
            logging.error(f"Auto-commit failed: {e}")
            return False

class ManifestAnalyzer:
    """Analyzes project manifests for dependencies and changes"""
    
    def __init__(self, config):
        self.config = config.get("manifest_analysis", {})
        self.manifest_files = self.config.get("manifest_files", [])
        self.manifests_cache = {}
    
    def find_manifests(self, repo_path: str) -> List[str]:
        """Find all manifest files in repository"""
        manifests = []
        repo_path = Path(repo_path)
        
        for manifest_file in self.manifest_files:
            manifest_path = repo_path / manifest_file
            if manifest_path.exists():
                manifests.append(str(manifest_path))
        
        return manifests
    
    def analyze_manifest(self, manifest_path: str) -> Dict:
        """Analyze a single manifest file"""
        manifest_path = Path(manifest_path)
        
        try:
            with open(manifest_path, 'r') as f:
                content = f.read()
            
            # Calculate content hash for change detection
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            analysis = {
                "file": str(manifest_path),
                "type": manifest_path.name,
                "hash": content_hash,
                "dependencies": [],
                "dev_dependencies": [],
                "security_issues": [],
                "outdated_packages": []
            }
            
            # Parse based on manifest type
            if manifest_path.name == "package.json":
                analysis.update(self._analyze_package_json(content))
            elif manifest_path.name == "requirements.txt":
                analysis.update(self._analyze_requirements_txt(content))
            elif manifest_path.name == "Cargo.toml":
                analysis.update(self._analyze_cargo_toml(content))
            
            return analysis
            
        except Exception as e:
            logging.error(f"Failed to analyze manifest {manifest_path}: {e}")
            return {"error": str(e)}
    
    def _analyze_package_json(self, content: str) -> Dict:
        """Analyze package.json file"""
        try:
            data = json.loads(content)
            dependencies = list(data.get("dependencies", {}).keys())
            dev_dependencies = list(data.get("devDependencies", {}).keys())
            
            return {
                "dependencies": dependencies,
                "dev_dependencies": dev_dependencies,
                "scripts": list(data.get("scripts", {}).keys()),
                "engines": data.get("engines", {})
            }
        except json.JSONDecodeError:
            return {"error": "Invalid JSON"}
    
    def _analyze_requirements_txt(self, content: str) -> Dict:
        """Analyze requirements.txt file"""
        dependencies = []
        for line in content.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (before version specifiers)
                package = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                dependencies.append(package)
        
        return {"dependencies": dependencies}
    
    def _analyze_cargo_toml(self, content: str) -> Dict:
        """Analyze Cargo.toml file"""
        dependencies = []
        dev_dependencies = []
        
        # Simple parsing - could be enhanced with proper TOML parser
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('[dependencies]'):
                current_section = "dependencies"
            elif line.startswith('[dev-dependencies]'):
                current_section = "dev_dependencies"
            elif line.startswith('['):
                current_section = None
            elif '=' in line and current_section:
                package = line.split('=')[0].strip()
                if current_section == "dependencies":
                    dependencies.append(package)
                elif current_section == "dev_dependencies":
                    dev_dependencies.append(package)
        
        return {
            "dependencies": dependencies,
            "dev_dependencies": dev_dependencies
        }
    
    def check_manifest_changes(self, repo_path: str) -> List[Dict]:
        """Check for changes in manifest files"""
        manifests = self.find_manifests(repo_path)
        changes = []
        
        for manifest_path in manifests:
            analysis = self.analyze_manifest(manifest_path)
            if "error" in analysis:
                continue
                
            # Check against cached version
            cache_key = manifest_path
            if cache_key in self.manifests_cache:
                cached_analysis = self.manifests_cache[cache_key]
                if cached_analysis["hash"] != analysis["hash"]:
                    changes.append({
                        "file": manifest_path,
                        "type": "modified",
                        "old_dependencies": cached_analysis.get("dependencies", []),
                        "new_dependencies": analysis.get("dependencies", []),
                        "added_deps": list(set(analysis.get("dependencies", [])) - set(cached_analysis.get("dependencies", []))),
                        "removed_deps": list(set(cached_analysis.get("dependencies", [])) - set(analysis.get("dependencies", [])))
                    })
            else:
                changes.append({
                    "file": manifest_path,
                    "type": "new",
                    "dependencies": analysis.get("dependencies", [])
                })
            
            # Update cache
            self.manifests_cache[cache_key] = analysis
        
        return changes

class MultiProjectManager:
    """Manages multiple projects for analysis"""
    
    def __init__(self, config):
        self.config = config.get("multi_project", {})
        self.projects_root = Path(self.config.get("projects_root", "/home/greenantix/AI"))
        self.discovery_patterns = self.config.get("discovery_patterns", [".git"])
        self.exclude_paths = self.config.get("exclude_paths", [])
    
    def discover_projects(self) -> List[Dict]:
        """Automatically discover projects in the projects root"""
        if not self.config.get("auto_discover", False):
            return []
        
        projects = []
        
        try:
            for item in self.projects_root.iterdir():
                if not item.is_dir():
                    continue
                    
                # Skip excluded paths
                if any(exclude in str(item) for exclude in self.exclude_paths):
                    continue
                
                # Check for discovery patterns
                for pattern in self.discovery_patterns:
                    pattern_path = item / pattern
                    if pattern_path.exists():
                        project_config = {
                            "name": item.name,
                            "path": str(item),
                            "auto_commit": False,  # Conservative default
                            "auto_push": False,
                            "analysis_triggers": ["*.py", "*.js", "*.ts", "*.sh", "*.md"],
                            "commit_threshold": 5,
                            "discovered": True
                        }
                        projects.append(project_config)
                        break
            
        except Exception as e:
            logging.error(f"Failed to discover projects: {e}")
        
        return projects
    
    def get_project_manifest_info(self, project_path: str) -> Dict:
        """Get manifest information for a project"""
        manifest_analyzer = ManifestAnalyzer({"manifest_analysis": {"manifest_files": ["package.json", "requirements.txt", "Cargo.toml"]}})
        manifests = manifest_analyzer.find_manifests(project_path)
        
        info = {
            "project_path": project_path,
            "manifests": [],
            "primary_language": "unknown",
            "framework": "unknown"
        }
        
        for manifest_path in manifests:
            analysis = manifest_analyzer.analyze_manifest(manifest_path)
            if "error" not in analysis:
                info["manifests"].append(analysis)
                
                # Determine primary language/framework
                if "package.json" in manifest_path:
                    info["primary_language"] = "javascript"
                elif "requirements.txt" in manifest_path or "pyproject.toml" in manifest_path:
                    info["primary_language"] = "python"
                elif "Cargo.toml" in manifest_path:
                    info["primary_language"] = "rust"
        
        return info

class CodePreprocessor:
    """Preprocesses code before sending to LLM for better analysis"""
    
    def __init__(self):
        self.language_patterns = {
            'python': {
                'imports': r'^(import|from)\s+',
                'classes': r'^class\s+\w+',
                'functions': r'^def\s+\w+',
                'comments': r'^\s*#',
                'docstrings': r'^\s*""".*?"""',
                'decorators': r'^\s*@\w+'
            },
            'javascript': {
                'imports': r'^(import|require|const.*=.*require)',
                'classes': r'^class\s+\w+',
                'functions': r'^(function\s+\w+|const\s+\w+\s*=.*=>|\w+:\s*function)',
                'comments': r'^\s*//',
                'exports': r'^(export|module\.exports)'
            },
            'typescript': {
                'imports': r'^import',
                'interfaces': r'^interface\s+\w+',
                'classes': r'^class\s+\w+',
                'functions': r'^(function\s+\w+|const\s+\w+\s*=)',
                'types': r'^type\s+\w+',
                'comments': r'^\s*//'
            }
        }
    
    def preprocess_repomix_output(self, repomix_content: str) -> Dict:
        """Parse and categorize repomix output for better LLM analysis"""
        
        structured_data = {
            'project_overview': {},
            'files': [],
            'architecture_summary': {},
            'code_metrics': {}
        }
        
        # Parse file sections from repomix output
        file_sections = self._extract_file_sections(repomix_content)
        
        # Process each file
        for file_info in file_sections:
            processed_file = self._analyze_file_content(file_info)
            structured_data['files'].append(processed_file)
        
        # Generate architecture summary
        structured_data['architecture_summary'] = self._generate_architecture_summary(structured_data['files'])
        
        # Calculate metrics
        structured_data['code_metrics'] = self._calculate_code_metrics(structured_data['files'])
        
        return structured_data
    
    def _extract_file_sections(self, content: str) -> List[Dict]:
        """Extract individual file sections from repomix output"""
        files = []
        
        # Split by file markers
        file_pattern = r'## File: (.+?)\n```(\w+)?\n(.*?)\n```'
        matches = re.findall(file_pattern, content, re.DOTALL)
        
        for file_path, language, file_content in matches:
            files.append({
                'path': file_path.strip(),
                'language': language.lower() if language else self._detect_language(file_path),
                'content': file_content.strip(),
                'size': len(file_content)
            })
        
        return files
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.sh': 'bash',
            '.rs': 'rust',
            '.go': 'go',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c'
        }
        
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
        
        return 'unknown'
    
    def _analyze_file_content(self, file_info: Dict) -> Dict:
        """Analyze individual file content and categorize code blocks"""
        
        language = file_info['language']
        content = file_info['content']
        lines = content.split('\n')
        
        analysis = {
            'path': file_info['path'],
            'language': language,
            'size': file_info['size'],
            'line_count': len(lines),
            'code_blocks': {
                'imports': [],
                'classes': [],
                'functions': [],
                'comments': [],
                'other': []
            },
            'complexity_indicators': {
                'nested_blocks': 0,
                'long_functions': 0,
                'todo_count': 0
            }
        }
        
        if language in self.language_patterns:
            patterns = self.language_patterns[language]
            
            current_block = None
            current_block_lines = []
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                
                # Check for TODO/FIXME
                if 'TODO' in line_stripped or 'FIXME' in line_stripped:
                    analysis['complexity_indicators']['todo_count'] += 1
                
                # Categorize code blocks
                block_type = self._categorize_line(line, patterns)
                
                if block_type:
                    # Save previous block
                    if current_block and current_block_lines:
                        analysis['code_blocks'][current_block].append({
                            'start_line': i - len(current_block_lines) + 1,
                            'end_line': i,
                            'content': '\n'.join(current_block_lines[:3])  # First 3 lines for context
                        })
                    
                    # Start new block
                    current_block = block_type
                    current_block_lines = [line]
                elif current_block:
                    current_block_lines.append(line)
                    
                    # Check for long functions
                    if current_block == 'functions' and len(current_block_lines) > 50:
                        analysis['complexity_indicators']['long_functions'] += 1
        
        return analysis
    
    def _categorize_line(self, line: str, patterns: Dict) -> str:
        """Categorize a line of code based on language patterns"""
        
        for category, pattern in patterns.items():
            if re.match(pattern, line.strip()):
                return category
        
        return None
    
    def _generate_architecture_summary(self, files: List[Dict]) -> Dict:
        """Generate high-level architecture summary"""
        
        summary = {
            'languages': {},
            'file_types': {},
            'total_files': len(files),
            'total_lines': 0,
            'complexity_hotspots': []
        }
        
        for file_info in files:
            lang = file_info['language']
            summary['languages'][lang] = summary['languages'].get(lang, 0) + 1
            summary['total_lines'] += file_info['line_count']
            
            # Identify complexity hotspots
            if (file_info['complexity_indicators']['long_functions'] > 0 or 
                file_info['complexity_indicators']['todo_count'] > 5):
                summary['complexity_hotspots'].append({
                    'file': file_info['path'],
                    'issues': file_info['complexity_indicators']
                })
        
        return summary
    
    def _calculate_code_metrics(self, files: List[Dict]) -> Dict:
        """Calculate overall code quality metrics"""
        
        metrics = {
            'total_functions': 0,
            'total_classes': 0,
            'total_todos': 0,
            'avg_file_size': 0,
            'language_distribution': {}
        }
        
        if not files:
            return metrics
        
        for file_info in files:
            metrics['total_functions'] += len(file_info['code_blocks']['functions'])
            metrics['total_classes'] += len(file_info['code_blocks']['classes'])
            metrics['total_todos'] += file_info['complexity_indicators']['todo_count']
            
            lang = file_info['language']
            metrics['language_distribution'][lang] = metrics['language_distribution'].get(lang, 0) + 1
        
        metrics['avg_file_size'] = sum(f['size'] for f in files) / len(files)
        
        return metrics
    
    def format_for_llm(self, structured_data: Dict) -> str:
        """Format preprocessed data for LLM consumption"""
        
        output = []
        
        # Add architecture overview
        arch = structured_data['architecture_summary']
        output.append("# Codebase Architecture Overview")
        output.append(f"- **Total Files**: {arch['total_files']}")
        output.append(f"- **Total Lines**: {arch['total_lines']}")
        output.append(f"- **Languages**: {', '.join(arch['languages'].keys())}")
        
        if arch['complexity_hotspots']:
            output.append("\n## ⚠️ Complexity Hotspots")
            for hotspot in arch['complexity_hotspots'][:5]:  # Top 5
                output.append(f"- **{hotspot['file']}**: {hotspot['issues']}")
        
        # Add file summaries
        output.append("\n# File Analysis Summary")
        
        for file_info in structured_data['files'][:10]:  # Top 10 files
            output.append(f"\n## 📁 {file_info['path']}")
            output.append(f"- **Language**: {file_info['language']}")
            output.append(f"- **Size**: {file_info['line_count']} lines")
            
            # Add code block summary
            blocks = file_info['code_blocks']
            if blocks['functions']:
                output.append(f"- **Functions**: {len(blocks['functions'])}")
            if blocks['classes']:
                output.append(f"- **Classes**: {len(blocks['classes'])}")
            if file_info['complexity_indicators']['todo_count'] > 0:
                output.append(f"- **TODOs**: {file_info['complexity_indicators']['todo_count']}")
        
        # Add metrics summary
        metrics = structured_data['code_metrics']
        output.append("\n# Code Quality Metrics")
        output.append(f"- **Total Functions**: {metrics['total_functions']}")
        output.append(f"- **Total Classes**: {metrics['total_classes']}")
        output.append(f"- **Total TODOs**: {metrics['total_todos']}")
        output.append(f"- **Average File Size**: {metrics['avg_file_size']:.0f} characters")
        
        return '\n'.join(output)

class CodeIndexer:
    """Semantic search indexer for finding similar code blocks"""
    
    def __init__(self, config: Dict, index_file: str = ".llmdiver/code_index.pkl"):
        self.config = config.get("semantic_search", {})
        self.index_file = index_file
        self.embedding_model = self.config.get("embedding_model", "tfidf")
        self.code_blocks = []
        self.vectors = None
        self.embedding_backend = None
        
        # Initialize embedding backend
        self._initialize_embedding_backend()
        self.load_index()
    
    def _initialize_embedding_backend(self):
        """Initialize the appropriate embedding backend"""
        
        if self.embedding_model == "sentence_transformers" and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                from sentence_transformers import SentenceTransformer
                model_name = self.config.get("model_name", "all-MiniLM-L6-v2")
                self.embedding_backend = SentenceTransformer(model_name)
                logging.info(f"Initialized SentenceTransformers with model: {model_name}")
            except Exception as e:
                logging.warning(f"Failed to load SentenceTransformers model: {e}, falling back to TF-IDF")
                self.embedding_model = "tfidf"
                
        elif self.embedding_model == "llama_cpp" and LLAMA_CPP_AVAILABLE:
            try:
                model_path = self.config.get("model_path", "")
                if model_path and os.path.exists(model_path):
                    from llama_cpp import Llama
                    self.embedding_backend = Llama(
                        model_path=model_path,
                        embedding=True,
                        n_ctx=512,  # Context window for embeddings
                        verbose=False
                    )
                    logging.info(f"Initialized Llama.cpp embedding model: {model_path}")
                else:
                    logging.warning(f"Model path not found: {model_path}, falling back to TF-IDF")
                    self.embedding_model = "tfidf"
            except Exception as e:
                logging.warning(f"Failed to load Llama.cpp model: {e}, falling back to TF-IDF")
                self.embedding_model = "tfidf"
        
        # Default to TF-IDF
        if self.embedding_model == "tfidf" or self.embedding_backend is None:
            self.embedding_backend = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                max_df=0.8,
                min_df=2
            )
            logging.info("Initialized TF-IDF vectorizer for semantic search")
    
    def load_index(self):
        """Load existing code index from disk"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'rb') as f:
                    data = pickle.load(f)
                    self.code_blocks = data.get('code_blocks', [])
                    self.vectorizer = data.get('vectorizer', self.vectorizer)
                    self.vectors = data.get('vectors', None)
                logging.info(f"Loaded code index with {len(self.code_blocks)} code blocks")
        except Exception as e:
            logging.warning(f"Failed to load code index: {e}")
            self.code_blocks = []
            self.vectors = None
    
    def save_index(self):
        """Save code index to disk"""
        try:
            os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
            with open(self.index_file, 'wb') as f:
                pickle.dump({
                    'code_blocks': self.code_blocks,
                    'vectorizer': self.vectorizer,
                    'vectors': self.vectors
                }, f)
            logging.info(f"Saved code index with {len(self.code_blocks)} code blocks")
        except Exception as e:
            logging.error(f"Failed to save code index: {e}")
    
    def extract_code_blocks(self, file_analysis: Dict) -> List[Dict]:
        """Extract meaningful code blocks from file analysis"""
        blocks = []
        
        file_path = file_analysis['path']
        language = file_analysis['language']
        
        # Extract functions
        for func in file_analysis['code_blocks']['functions']:
            blocks.append({
                'type': 'function',
                'file': file_path,
                'language': language,
                'content': func.get('content', ''),
                'start_line': func.get('start_line', 0),
                'end_line': func.get('end_line', 0)
            })
        
        # Extract classes
        for cls in file_analysis['code_blocks']['classes']:
            blocks.append({
                'type': 'class',
                'file': file_path,
                'language': language,
                'content': cls.get('content', ''),
                'start_line': cls.get('start_line', 0),
                'end_line': cls.get('end_line', 0)
            })
        
        return blocks
    
    def update_index(self, preprocessed_data: Dict):
        """Update the semantic index with new code blocks"""
        new_blocks = []
        
        # Extract code blocks from all files
        for file_analysis in preprocessed_data.get('files', []):
            blocks = self.extract_code_blocks(file_analysis)
            new_blocks.extend(blocks)
        
        if not new_blocks:
            return
        
        # Combine with existing blocks (remove duplicates)
        existing_files = {block['file'] for block in self.code_blocks}
        updated_files = {block['file'] for block in new_blocks}
        
        # Remove old blocks for updated files
        self.code_blocks = [block for block in self.code_blocks if block['file'] not in updated_files]
        
        # Add new blocks
        self.code_blocks.extend(new_blocks)
        
        # Rebuild vectors
        self._rebuild_vectors()
        
        # Save updated index
        self.save_index()
        
        logging.info(f"Updated code index: {len(new_blocks)} new blocks, {len(self.code_blocks)} total blocks")
    
    def _rebuild_vectors(self):
        """Rebuild vectors for all code blocks using the selected embedding backend"""
        if not self.code_blocks:
            self.vectors = None
            return
        
        # Prepare text documents for vectorization
        documents = []
        for block in self.code_blocks:
            # Combine type, language, and content for better semantic understanding
            doc = f"{block['type']} {block['language']} {block['content']}"
            documents.append(doc)
        
        try:
            if self.embedding_model == "sentence_transformers":
                # Use SentenceTransformers for embeddings
                self.vectors = self.embedding_backend.encode(documents)
                logging.info(f"Rebuilt SentenceTransformers vectors for {len(documents)} code blocks")
                
            elif self.embedding_model == "llama_cpp":
                # Use Llama.cpp for embeddings
                embeddings = []
                for doc in documents:
                    embedding = self.embedding_backend.create_embedding(doc)["data"][0]["embedding"]
                    embeddings.append(embedding)
                self.vectors = np.array(embeddings)
                logging.info(f"Rebuilt Llama.cpp vectors for {len(documents)} code blocks")
                
            else:  # TF-IDF
                self.vectors = self.embedding_backend.fit_transform(documents)
                logging.info(f"Rebuilt TF-IDF vectors for {len(documents)} code blocks")
                
        except Exception as e:
            logging.error(f"Failed to rebuild vectors: {e}")
            self.vectors = None
    
    def find_similar_code(self, query_blocks: List[Dict], top_k: int = 5) -> List[Dict]:
        """Find similar code blocks using semantic search"""
        if not self.vectors or not query_blocks:
            return []
        
        similar_blocks = []
        
        for query_block in query_blocks:
            # Prepare query document
            query_doc = f"{query_block['type']} {query_block['language']} {query_block['content']}"
            
            try:
                # Generate query vector based on embedding type
                if self.embedding_model == "sentence_transformers":
                    query_vector = self.embedding_backend.encode([query_doc])
                    similarities = cosine_similarity(query_vector, self.vectors).flatten()
                    
                elif self.embedding_model == "llama_cpp":
                    query_embedding = self.embedding_backend.create_embedding(query_doc)["data"][0]["embedding"]
                    query_vector = np.array([query_embedding])
                    similarities = cosine_similarity(query_vector, self.vectors).flatten()
                    
                else:  # TF-IDF
                    query_vector = self.embedding_backend.transform([query_doc])
                    similarities = cosine_similarity(query_vector, self.vectors).flatten()
                
                # Get top-k most similar blocks (excluding exact matches)
                top_indices = similarities.argsort()[-top_k-1:][::-1]
                
                similarity_threshold = self.config.get("similarity_threshold", 0.1)
                for idx in top_indices:
                    if similarities[idx] > similarity_threshold:
                        similar_block = self.code_blocks[idx].copy()
                        similar_block['similarity'] = float(similarities[idx])
                        
                        # Avoid suggesting the same file
                        if similar_block['file'] != query_block['file']:
                            similar_blocks.append(similar_block)
                
            except Exception as e:
                logging.error(f"Error finding similar code: {e}")
        
        # Sort by similarity and remove duplicates
        similar_blocks.sort(key=lambda x: x['similarity'], reverse=True)
        seen_files = set()
        unique_blocks = []
        
        for block in similar_blocks[:top_k]:
            if block['file'] not in seen_files:
                unique_blocks.append(block)
                seen_files.add(block['file'])
        
        return unique_blocks
    
    def get_semantic_context(self, current_changes: Dict) -> str:
        """Generate semantic context for LLM analysis"""
        if not current_changes.get('files'):
            return ""
        
        # Extract code blocks from current changes
        query_blocks = []
        for file_analysis in current_changes['files'][:3]:  # Limit to first 3 files
            blocks = self.extract_code_blocks(file_analysis)
            query_blocks.extend(blocks[:2])  # Top 2 blocks per file
        
        if not query_blocks:
            return ""
        
        # Find similar code blocks
        max_blocks = self.config.get("max_similar_blocks", 5)
        similar_blocks = self.find_similar_code(query_blocks, top_k=max_blocks)
        
        if not similar_blocks:
            return ""
        
        # Format semantic context for LLM
        context = "## Semantic Context (Similar Code Found Elsewhere)\n"
        context += "The following code blocks from the repository are semantically similar to the code being analyzed. Check for potential duplication or opportunities for reuse.\n\n"
        
        for block in similar_blocks:
            context += f"- **File:** `{block['file']}` (lines {block['start_line']}-{block['end_line']})\n"
            context += f"- **Type:** {block['type']} | **Language:** {block['language']} | **Similarity:** {block['similarity']:.2f}\n"
            context += f"  ```{block['language']}\n{block['content'][:200]}{'...' if len(block['content']) > 200 else ''}\n  ```\n\n"
        
        return context

class IntelligentRouter:
    """Intelligent router that classifies code and selects specialized prompts"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.classification_prompt = """You are a code classification expert. Analyze the provided code snippet and classify its primary purpose.

Respond with ONLY ONE WORD from this list:
- Security (authentication, authorization, encryption, validation)
- UI (user interface, components, styling, frontend)
- Data (database, schemas, queries, data processing)
- Config (configuration, deployment, infrastructure, environment)
- API (endpoints, routes, web services, networking)
- Testing (tests, mocks, fixtures, validation)
- Utility (helpers, utils, common functions)
- Business (domain logic, workflows, rules)

Analyze this code and respond with the single most appropriate classification:

"""
    
    def classify_code_changes(self, preprocessed_data: Dict) -> str:
        """Classify the primary type of code changes using LLM"""
        
        if not preprocessed_data.get('files'):
            return "general"
        
        # Extract representative code samples
        code_samples = []
        file_extensions = []
        
        for file_analysis in preprocessed_data['files'][:5]:  # Analyze top 5 files
            file_path = file_analysis['path']
            file_extensions.append(file_path.split('.')[-1] if '.' in file_path else '')
            
            # Get sample code from functions and classes
            for func in file_analysis['code_blocks']['functions'][:2]:
                code_samples.append(func.get('content', ''))
            
            for cls in file_analysis['code_blocks']['classes'][:1]:
                code_samples.append(cls.get('content', ''))
        
        if not code_samples:
            return self._classify_by_file_patterns(preprocessed_data)
        
        # Create classification prompt with code samples
        combined_code = '\n\n'.join(code_samples[:3])  # Use top 3 samples
        
        # Limit code length for classification
        if len(combined_code) > 2000:
            combined_code = combined_code[:2000] + "..."
        
        classification_query = self.classification_prompt + combined_code
        
        try:
            # Use a simple classification request
            classification = self._classify_with_llm(classification_query)
            
            # Map classification to analysis types
            classification_mapping = {
                'security': 'security',
                'ui': 'ui', 
                'data': 'data',
                'config': 'config',
                'api': 'general',  # Use general for API
                'testing': 'general',  # Use general for testing
                'utility': 'general',  # Use general for utility
                'business': 'general'  # Use general for business logic
            }
            
            result = classification_mapping.get(classification.lower(), 'general')
            logging.info(f"Intelligent router classified code as: {classification} -> {result}")
            return result
            
        except Exception as e:
            logging.warning(f"Router classification failed, falling back to pattern matching: {e}")
            return self._classify_by_file_patterns(preprocessed_data)
    
    def _classify_with_llm(self, prompt: str) -> str:
        """Send classification request to LLM"""
        payload = {
            "model": self.llm_client.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,  # Low temperature for consistent classification
            "max_tokens": 10,    # Very short response expected
            "stream": False
        }
        
        try:
            response = requests.post(self.llm_client.url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            classification = result["choices"][0]["message"]["content"].strip().lower()
            
            # Extract single word classification
            valid_classifications = ['security', 'ui', 'data', 'config', 'api', 'testing', 'utility', 'business']
            for valid_class in valid_classifications:
                if valid_class in classification:
                    return valid_class
            
            return 'general'
            
        except Exception as e:
            logging.error(f"LLM classification request failed: {e}")
            raise
    
    def _classify_by_file_patterns(self, preprocessed_data: Dict) -> str:
        """Fallback classification based on file patterns and extensions"""
        
        file_paths = [f['path'] for f in preprocessed_data.get('files', [])]
        
        # Count file types
        security_count = sum(1 for path in file_paths if any(keyword in path.lower() for keyword in 
                           ['auth', 'login', 'password', 'token', 'security', 'crypto', 'encrypt', 'ssl', 'cert']))
        
        ui_count = sum(1 for path in file_paths if any(ext in path.lower() for ext in 
                      ['.jsx', '.tsx', '.vue', '.html', '.css', '.scss', '.sass', '.less', '.component']))
        
        config_count = sum(1 for path in file_paths if any(keyword in path.lower() for keyword in 
                         ['config', 'env', 'docker', 'kubernetes', 'terraform', '.yml', '.yaml', '.ini', '.conf', 'deploy']))
        
        data_count = sum(1 for path in file_paths if any(keyword in path.lower() for keyword in 
                        ['model', 'schema', 'migration', 'database', 'sql', 'query', 'orm', 'repository']))
        
        # Determine dominant pattern
        pattern_counts = {
            'security': security_count,
            'ui': ui_count,
            'config': config_count,
            'data': data_count
        }
        
        max_pattern = max(pattern_counts.items(), key=lambda x: x[1])
        
        if max_pattern[1] > 0:  # At least one matching file
            logging.info(f"Pattern-based classification: {max_pattern[0]} ({max_pattern[1]} files)")
            return max_pattern[0]
        
        return 'general'

class LLMdiverDaemon:
    def __init__(self, config_path: str = "config/llmdiver.json"):
        self.config = LLMdiverConfig(config_path)
        self.llm_client = LLMStudioClient(self.config.config)
        self.git_automation = GitAutomation(self.config.config)
        self.manifest_analyzer = ManifestAnalyzer(self.config.config)
        self.multi_project_manager = MultiProjectManager(self.config.config)
        self.code_preprocessor = CodePreprocessor()
        self.code_indexer = CodeIndexer(self.config.config)
        self.intelligent_router = IntelligentRouter(self.llm_client)
        self.observers = []
        self.running = False
        self.analysis_queue = []
        self.setup_logging()
        
        # Auto-discover projects if enabled
        if self.config.config.get("multi_project", {}).get("enabled", False):
            self.discover_and_add_projects()
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.config["daemon"]["log_level"])
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('llmdiver_daemon.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def run_repomix_analysis(self, repo_path: str) -> str:
        """Run repomix analysis on repository"""
        try:
            output_file = f"{repo_path}/.llmdiver_analysis.md"
            
            cmd = [
                "repomix", repo_path,
                "--output", output_file,
                "--style", "markdown",
                "--compress",
                "--remove-comments",
                "--remove-empty-lines",
                "--top-files-len", "10",  # Top 10 files for analysis
                "--include", ",".join(self.config.config["repomix"]["include_patterns"]),
                "--ignore", ",".join(self.config.config["repomix"]["ignore_patterns"])
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                with open(output_file, 'r') as f:
                    return f.read()
            else:
                logging.error(f"Repomix failed: {result.stderr}")
                return ""
                
        except Exception as e:
            logging.error(f"Repomix analysis error: {e}")
            return ""
    
    def schedule_analysis(self, repo_config: Dict):
        """Schedule repository analysis"""
        if repo_config not in self.analysis_queue:
            self.analysis_queue.append(repo_config)
            logging.info(f"Scheduled analysis for {repo_config['name']}")
    
    def process_analysis_queue(self):
        """Process queued analyses"""
        while self.running:
            if self.analysis_queue:
                repo_config = self.analysis_queue.pop(0)
                self.analyze_repository(repo_config)
            time.sleep(1)
    
    def analyze_repository(self, repo_config: Dict):
        """Analyze a repository completely - delegates to enhanced analysis"""
        # Use enhanced analysis by default
        self.enhanced_repository_analysis(repo_config)
    
    def start_watching(self):
        """Start file system watching"""
        for repo_config in self.config.config["repositories"]:
            repo_path = repo_config["path"]
            if not os.path.exists(repo_path):
                logging.warning(f"Repository path not found: {repo_path}")
                continue
            
            observer = Observer()
            handler = RepoWatcher(self, repo_config)
            observer.schedule(handler, repo_path, recursive=True)
            observer.start()
            self.observers.append(observer)
            
            logging.info(f"Started watching {repo_config['name']} at {repo_path}")
    
    def start(self):
        """Start the daemon"""
        logging.info("Starting LLMdiver daemon...")
        self.running = True
        
        # Start file watching
        self.start_watching()
        
        # Start analysis queue processor
        analysis_thread = threading.Thread(target=self.process_analysis_queue)
        analysis_thread.daemon = True
        analysis_thread.start()
        
        # Run initial analysis on all repos
        for repo_config in self.config.config["repositories"]:
            self.schedule_analysis(repo_config)
        
        logging.info("LLMdiver daemon started successfully")
        
        # Keep daemon running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def discover_and_add_projects(self):
        """Discover and add new projects to monitoring"""
        discovered_projects = self.multi_project_manager.discover_projects()
        existing_paths = {repo["path"] for repo in self.config.config["repositories"]}
        
        for project in discovered_projects:
            if project["path"] not in existing_paths:
                self.config.config["repositories"].append(project)
                logging.info(f"Auto-discovered project: {project['name']} at {project['path']}")
    
    def analyze_manifest_changes(self, repo_config: Dict) -> str:
        """Analyze manifest changes for incremental analysis"""
        if not self.config.config.get("manifest_analysis", {}).get("enabled", False):
            return ""
        
        changes = self.manifest_analyzer.check_manifest_changes(repo_config["path"])
        if not changes:
            return ""
        
        analysis_text = "## Dependency Change Analysis\n\n"
        
        for change in changes:
            if change["type"] == "modified":
                analysis_text += f"### 🔄 Modified: {change['file']}\n"
                if change["added_deps"]:
                    analysis_text += f"**➕ Added dependencies ({len(change['added_deps'])}):** {', '.join(change['added_deps'])}\n"
                    analysis_text += f"   *Security Assessment Required*: Review new packages for vulnerabilities and licensing\n"
                if change["removed_deps"]:
                    analysis_text += f"**➖ Removed dependencies ({len(change['removed_deps'])}):** {', '.join(change['removed_deps'])}\n"
                    analysis_text += f"   *Impact Assessment Required*: Check for breaking changes and unused imports\n"
                analysis_text += "\n"
            elif change["type"] == "new":
                analysis_text += f"### 🆕 New manifest: {change['file']}\n"
                analysis_text += f"**Total dependencies ({len(change['dependencies'])}):** {', '.join(change['dependencies'])}\n"
                analysis_text += f"   *Full Security Review Required*: New dependency ecosystem introduced\n\n"
        
        # Add analysis instructions for the LLM
        if changes:
            analysis_text += "### 🎯 LLM Analysis Focus Areas:\n"
            analysis_text += "- **Security**: Check for known vulnerabilities in added packages\n"
            analysis_text += "- **Compatibility**: Assess version conflicts and breaking changes\n"
            analysis_text += "- **Necessity**: Evaluate if dependencies are actually needed\n"
            analysis_text += "- **Alternatives**: Suggest lighter or more secure alternatives where applicable\n"
            analysis_text += "- **Impact**: Assess bundle size, performance, and maintenance implications\n\n"
        
        return analysis_text
    
    def _extract_structured_findings(self, analysis_text: str) -> Dict:
        """Extract structured findings from AI analysis text for JSON output"""
        
        findings = {
            "executive_summary": "",
            "critical_issues": [],
            "high_priority": [],
            "medium_priority": [],
            "low_priority": [],
            "recommendations": []
        }
        
        lines = analysis_text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Detect section headers
            if "executive summary" in line_stripped.lower():
                current_section = "executive_summary"
                current_content = []
            elif "critical" in line_stripped.lower() and ("issue" in line_stripped.lower() or "priority" in line_stripped.lower()):
                current_section = "critical_issues"
                current_content = []
            elif "high priority" in line_stripped.lower() or ("high" in line_stripped.lower() and "priority" in line_stripped.lower()):
                current_section = "high_priority"
                current_content = []
            elif "medium priority" in line_stripped.lower() or ("technical debt" in line_stripped.lower() and "todo" in line_stripped.lower()):
                current_section = "medium_priority"
                current_content = []
            elif "low priority" in line_stripped.lower() or "dead code" in line_stripped.lower():
                current_section = "low_priority"
                current_content = []
            elif "recommendation" in line_stripped.lower() and "action" in line_stripped.lower():
                current_section = "recommendations"
                current_content = []
            elif line_stripped.startswith("##") and current_section:
                # End of current section
                if current_section == "executive_summary":
                    findings[current_section] = '\n'.join(current_content).strip()
                else:
                    findings[current_section] = current_content.copy()
                current_section = None
                current_content = []
            elif current_section and line_stripped:
                # Add content to current section
                if line_stripped.startswith("-") or line_stripped.startswith("*"):
                    # Extract list items for structured sections
                    if current_section != "executive_summary":
                        current_content.append(line_stripped[1:].strip())
                elif current_section == "executive_summary":
                    current_content.append(line_stripped)
        
        # Handle last section
        if current_section:
            if current_section == "executive_summary":
                findings[current_section] = '\n'.join(current_content).strip()
            else:
                findings[current_section] = current_content.copy()
        
        return findings

    def enhanced_repository_analysis(self, repo_config: Dict):
        """Enhanced analysis including manifests and multi-project context"""
        logging.info(f"Starting enhanced analysis of {repo_config['name']}")
        
        try:
            # Run standard repomix analysis
            summary = self.run_repomix_analysis(repo_config["path"])
            if not summary:
                logging.error("Failed to generate repository summary")
                return
            
            # Preprocess repomix output for better analysis
            preprocessed_data = self.code_preprocessor.preprocess_repomix_output(summary)
            formatted_summary = self.code_preprocessor.format_for_llm(preprocessed_data)
            
            # Update semantic code index
            self.code_indexer.update_index(preprocessed_data)
            
            # Get semantic context for similar code
            semantic_context = self.code_indexer.get_semantic_context(preprocessed_data)
            
            # Add manifest analysis
            manifest_analysis = self.analyze_manifest_changes(repo_config)
            
            # Get project context
            project_info = self.multi_project_manager.get_project_manifest_info(repo_config["path"])
            
            # Use intelligent router to classify code and select analysis type
            analysis_type = self.intelligent_router.classify_code_changes(preprocessed_data)
            
            # Fallback to manifest-based detection if no clear classification
            if analysis_type == 'general' and manifest_analysis.strip():
                analysis_type = 'dependency'
            
            logging.info(f"Intelligent router selected analysis type: {analysis_type}")
            
            # Enhanced prompt with manifest and project context
            enhanced_summary = f"""# Repository Analysis: {repo_config['name']}

## Project Context
- Primary Language: {project_info['primary_language']}
- Framework: {project_info['framework']}
- Manifest Files: {len(project_info['manifests'])}
- Project Type: {'Multi-language' if len(project_info['manifests']) > 1 else project_info['primary_language']}

{manifest_analysis}

{semantic_context}

## Preprocessed Code Analysis
{formatted_summary}

## Raw Code Data
{summary}

## Analysis Instructions
When analyzing this codebase, pay special attention to:
1. **Dependency Security**: If manifest changes detected, assess security implications of new/removed packages
2. **Language-Specific Patterns**: Apply {project_info['primary_language']}-specific best practices and common issues
3. **Cross-Project Context**: Consider how this project fits within the broader AI workspace ecosystem
4. **Framework Alignment**: Evaluate code against {project_info['framework']} architectural patterns and conventions
5. **Code Structure**: Use the preprocessed architecture overview and complexity hotspots to focus analysis
6. **Code Reuse**: If similar code found, evaluate opportunities for refactoring and deduplication
"""
            
            # Send to LLM for analysis with specialized prompt
            analysis = self.llm_client.analyze_repo_summary(enhanced_summary, analysis_type)
            
            # Save enhanced analysis results
            analysis_dir = Path(repo_config["path"]) / ".llmdiver"
            analysis_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_file = analysis_dir / f"enhanced_analysis_{timestamp}.md"
            json_analysis_file = analysis_dir / f"analysis_data_{timestamp}.json"
            
            # Create structured JSON output for better report generation
            analysis_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "project_name": repo_config['name'],
                    "project_path": repo_config['path'],
                    "analysis_version": "enhanced_v2.0",
                    "analysis_type": analysis_type
                },
                "project_context": {
                    "primary_language": project_info['primary_language'],
                    "framework": project_info['framework'],
                    "manifest_files_count": len(project_info['manifests']),
                    "project_type": 'Multi-language' if len(project_info['manifests']) > 1 else project_info['primary_language']
                },
                "code_metrics": preprocessed_data.get('code_metrics', {}),
                "architecture_summary": preprocessed_data.get('architecture_summary', {}),
                "manifest_changes": {
                    "has_changes": bool(manifest_analysis.strip()),
                    "analysis_text": manifest_analysis
                },
                "ai_analysis": {
                    "raw_text": analysis,
                    "structured_findings": self._extract_structured_findings(analysis)
                },
                "semantic_analysis": {
                    "has_similar_code": bool(semantic_context.strip()),
                    "context_text": semantic_context
                },
                "input_data": {
                    "enhanced_summary": enhanced_summary,
                    "preprocessed_summary": formatted_summary
                }
            }
            
            # Save JSON data
            with open(json_analysis_file, 'w') as f:
                json.dump(analysis_data, f, indent=2, default=str)
            
            # Save markdown report
            with open(analysis_file, 'w') as f:
                f.write(f"# LLMdiver Enhanced Analysis - {datetime.now()}\n\n")
                f.write(f"## Project: {repo_config['name']}\n\n")
                f.write(enhanced_summary)
                f.write("\n\n## AI Analysis\n\n")
                f.write(analysis)
            
            # Update latest analysis links
            latest_md_link = analysis_dir / "latest_enhanced_analysis.md"
            latest_json_link = analysis_dir / "latest_analysis_data.json"
            
            if latest_md_link.exists():
                latest_md_link.unlink()
            latest_md_link.symlink_to(analysis_file.name)
            
            if latest_json_link.exists():
                latest_json_link.unlink()
            latest_json_link.symlink_to(json_analysis_file.name)
            
            logging.info(f"Enhanced analysis saved to {analysis_file}")
            logging.info(f"Structured JSON data saved to {json_analysis_file}")
            
            # Auto-commit if enabled
            if repo_config.get("auto_commit", False):
                commit_message = f"Enhanced analysis including manifest changes and project context"
                enhanced_analysis_data = {
                    "summary": f"Enhanced analysis for {repo_config['name']}",
                    "details": f"Manifest changes: {len(manifest_analysis.split('###')) - 1 if manifest_analysis else 0} files"
                }
                self.git_automation.auto_commit(repo_config["path"], commit_message)
            
        except Exception as e:
            logging.error(f"Enhanced repository analysis failed: {e}")
    
    def stop(self):
        """Stop the daemon"""
        logging.info("Stopping LLMdiver daemon...")
        self.running = False
        
        for observer in self.observers:
            observer.stop()
            observer.join()
        
        logging.info("LLMdiver daemon stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global daemon
    if daemon:
        daemon.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start daemon
    daemon = LLMdiverDaemon()
    daemon.start()