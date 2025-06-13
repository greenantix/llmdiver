#!/usr/bin/env python3
"""
LLMdiver Background Daemon
Monitors repositories, runs analysis, and automates git operations
"""
# Test trigger for LLM analysis

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

    def analyze_repo_summary(self, summary_text: str) -> str:
        """Send repo summary to LM Studio for analysis with auto-chunking"""
        system_prompt = """You are an expert code auditor. Analyze the repository summary and identify:

1. TODO/FIXME items that need attention
2. Mock/stub implementations that should be replaced with real code
3. Dead or unused code that can be removed
4. Infinite loops or performance issues
5. Missing connections between components

Format your response as:
## Critical Issues
## TODOs and Tech Debt  
## Mock/Stub Implementations
## Dead Code Candidates
## Performance Concerns
## Architectural Improvements

Be specific and actionable in your recommendations."""

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

class LLMdiverDaemon:
    def __init__(self, config_path: str = "config/llmdiver.json"):
        self.config = LLMdiverConfig(config_path)
        self.llm_client = LLMStudioClient(self.config.config)
        self.git_automation = GitAutomation(self.config.config)
        self.manifest_analyzer = ManifestAnalyzer(self.config.config)
        self.multi_project_manager = MultiProjectManager(self.config.config)
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
        
        analysis_text = "## Manifest Analysis\n\n"
        
        for change in changes:
            if change["type"] == "modified":
                analysis_text += f"### Modified: {change['file']}\n"
                if change["added_deps"]:
                    analysis_text += f"**Added dependencies:** {', '.join(change['added_deps'])}\n"
                if change["removed_deps"]:
                    analysis_text += f"**Removed dependencies:** {', '.join(change['removed_deps'])}\n"
                analysis_text += "\n"
            elif change["type"] == "new":
                analysis_text += f"### New manifest: {change['file']}\n"
                analysis_text += f"**Dependencies:** {', '.join(change['dependencies'])}\n\n"
        
        return analysis_text
    
    def enhanced_repository_analysis(self, repo_config: Dict):
        """Enhanced analysis including manifests and multi-project context"""
        logging.info(f"Starting enhanced analysis of {repo_config['name']}")
        
        try:
            # Run standard repomix analysis
            summary = self.run_repomix_analysis(repo_config["path"])
            if not summary:
                logging.error("Failed to generate repository summary")
                return
            
            # Add manifest analysis
            manifest_analysis = self.analyze_manifest_changes(repo_config)
            
            # Get project context
            project_info = self.multi_project_manager.get_project_manifest_info(repo_config["path"])
            
            # Enhanced prompt with manifest and project context
            enhanced_summary = f"""# Repository Analysis: {repo_config['name']}

## Project Information
- Primary Language: {project_info['primary_language']}
- Framework: {project_info['framework']}
- Manifests: {len(project_info['manifests'])}

{manifest_analysis}

## Code Analysis
{summary}
"""
            
            # Send to LLM for analysis
            analysis = self.llm_client.analyze_repo_summary(enhanced_summary)
            
            # Save enhanced analysis results
            analysis_dir = Path(repo_config["path"]) / ".llmdiver"
            analysis_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_file = analysis_dir / f"enhanced_analysis_{timestamp}.md"
            
            with open(analysis_file, 'w') as f:
                f.write(f"# LLMdiver Enhanced Analysis - {datetime.now()}\n\n")
                f.write(f"## Project: {repo_config['name']}\n\n")
                f.write(enhanced_summary)
                f.write("\n\n## AI Analysis\n\n")
                f.write(analysis)
            
            # Update latest analysis link
            latest_link = analysis_dir / "latest_enhanced_analysis.md"
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(analysis_file.name)
            
            logging.info(f"Enhanced analysis saved to {analysis_file}")
            
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