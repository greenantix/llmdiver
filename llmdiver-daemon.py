#!/usr/bin/env python3

import json
import logging
import os
import sys
import psutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
from threading import Thread, Lock
import time
from datetime import datetime
import git
from pathlib import Path
from typing import Dict, List
import tiktoken

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('llmdiver-daemon')

class Config:
    def __init__(self):
        self.config_path = 'config/llmdiver.json'
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)

class GitAutomation:
    def __init__(self, config, repo_config):
        self.config = config['git_automation']
        self.repo_config = repo_config
        self.repo = git.Repo(repo_config['path'])
        self.lock = Lock()

    def should_commit(self, changed_files):
        """Determine if changes warrant a commit based on threshold"""
        if not self.config['enabled'] or not self.repo_config['auto_commit']:
            return False
        
        # Check if current branch is protected
        current = self.repo.active_branch.name
        if current in self.config['branch_protection']:
            logger.warning(f"Skip auto-commit: {current} is a protected branch")
            return False
            
        return len(changed_files) >= self.repo_config['commit_threshold']

    def generate_commit_message(self, analysis_result):
        """Create commit message from template and analysis"""
        template = self.config['commit_message_template']
        summary = "Updated code analysis"
        details = "Changes detected by LLMdiver automated analysis"
        
        if analysis_result and 'summary' in analysis_result:
            summary = analysis_result['summary']
            details = analysis_result.get('details', '')
            
        return template.format(summary=summary, details=details)

    def commit_and_push(self, changed_files, analysis_result):
        """Perform git operations with locking"""
        with self.lock:
            try:
                # Stage files
                self.repo.index.add(changed_files)
                
                # Create commit
                message = self.generate_commit_message(analysis_result)
                self.repo.index.commit(message)
                logger.info(f"Created commit: {message}")

                # Push if configured
                if self.config['auto_push'] and self.repo_config['auto_push']:
                    self.repo.remote().push()
                    logger.info("Pushed changes to remote")

                # Update documentation if enabled
                if self.config['documentation_update']:
                    self.update_documentation()
                    
            except Exception as e:
                logger.error(f"Git automation failed: {e}")

    def update_documentation(self):
        """Generate and commit documentation updates"""
        docs_path = Path(self.repo_config['path']) / 'docs'
        docs_path.mkdir(exist_ok=True)
        
        # Generate documentation index
        index_path = docs_path / 'llmdiver_analysis.md'
        with open(index_path, 'w') as f:
            f.write(f"# LLMdiver Analysis\n\n")
            f.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Add analysis summary
            analysis_path = Path(self.repo_config['path']) / '.llmdiver/repomix.md'
            if analysis_path.exists():
                with open(analysis_path) as af:
                    f.write(af.read())

        # Commit documentation
        if index_path.exists():
            self.repo.index.add([str(index_path)])
            self.repo.index.commit("📚 Update LLMdiver documentation")
            logger.info("Updated documentation")

class MetricsCollector:
    def __init__(self):
        self.metrics_path = Path("metrics/metrics.json")
        self.metrics_path.parent.mkdir(exist_ok=True)
        self.lock = Lock()
        self.metrics: Dict = {
            'analysis': {
                'total_runs': 0,
                'total_tokens': 0,
                'avg_duration': 0,
                'last_run': None
            },
            'api': {
                'requests': {},
                'errors': 0
            },
            'git': {
                'commits': 0,
                'pushes': 0,
                'doc_updates': 0
            },
            'system': {
                'cpu_percent': 0,
                'memory_mb': 0,
                'disk_usage_mb': 0
            }
        }
        self.load_metrics()

    def load_metrics(self):
        """Load metrics from disk if available"""
        try:
            if self.metrics_path.exists():
                with open(self.metrics_path) as f:
                    self.metrics.update(json.load(f))
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")

    def save_metrics(self):
        """Save metrics to disk"""
        try:
            with open(self.metrics_path, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def update_system_metrics(self):
        """Update system resource usage metrics"""
        try:
            process = psutil.Process()
            self.metrics['system'].update({
                'cpu_percent': process.cpu_percent(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'disk_usage_mb': self.get_project_size() / 1024 / 1024
            })
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")

    def get_project_size(self) -> float:
        """Calculate total size of project files in KB"""
        total = 0
        try:
            for root, _, files in os.walk('.'):
                if any(ignore in root for ignore in ['.git', 'node_modules', '__pycache__']):
                    continue
                total += sum(os.path.getsize(os.path.join(root, name))
                           for name in files)
        except Exception as e:
            logger.error(f"Failed to calculate project size: {e}")
        return total

    def record_analysis(self, duration: float, token_count: int):
        """Record metrics for a repomix analysis run"""
        with self.lock:
            stats = self.metrics['analysis']
            stats['total_runs'] += 1
            stats['total_tokens'] += token_count
            stats['avg_duration'] = (
                (stats['avg_duration'] * (stats['total_runs'] - 1) + duration)
                / stats['total_runs']
            )
            stats['last_run'] = datetime.now().isoformat()
            self.update_system_metrics()
            self.save_metrics()

    def record_api_call(self, endpoint: str, success: bool):
        """Record API endpoint usage"""
        with self.lock:
            if endpoint not in self.metrics['api']['requests']:
                self.metrics['api']['requests'][endpoint] = {
                    'total': 0,
                    'success': 0,
                    'errors': 0
                }
            
            stats = self.metrics['api']['requests'][endpoint]
            stats['total'] += 1
            if success:
                stats['success'] += 1
            else:
                stats['errors'] += 1
                self.metrics['api']['errors'] += 1
            
            self.save_metrics()

    def record_git_operation(self, operation: str):
        """Record git operation statistics"""
        with self.lock:
            if operation in self.metrics['git']:
                self.metrics['git'][operation] += 1
                self.save_metrics()

    def get_metrics(self) -> Dict:
        """Get current metrics"""
        with self.lock:
            self.update_system_metrics()
            return self.metrics

class RepomixProcessor:
    def __init__(self, config):
        self.config = config
        self.lock = Lock()
        self.git_automations = {}
        self.metrics = MetricsCollector()
        
        # Initialize git automation for each repo
        for repo in config.get('repositories', []):
            self.git_automations[repo['name']] = GitAutomation(config, repo)

    def run_analysis(self, repo_path):
        with self.lock:
            repomix_config = self.config['repomix']
            output_dir = Path(repo_path) / '.llmdiver'
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / 'repomix.md'
            
            cmd = [
                'repomix', repo_path,
                '--output', str(output_file),
                '--style', repomix_config['style'],
                '--token-count-encoding', repomix_config['token_encoding']
            ]

            if repomix_config['compress']:
                cmd.append('--compress')
            if repomix_config['remove_comments']:
                cmd.append('--remove-comments')
            if repomix_config['remove_empty_lines']:
                cmd.append('--remove-empty-lines')
            if not repomix_config['use_gitignore']:
                cmd.append('--no-gitignore')

            for pattern in repomix_config['include_patterns']:
                cmd.extend(['--include', pattern])
            for pattern in repomix_config['ignore_patterns']:
                cmd.extend(['--ignore', pattern])

            start_time = time.time()
            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                duration = time.time() - start_time
                logger.info(f"Repomix analysis completed for {repo_path}")

                # Calculate token count
                try:
                    encoder = tiktoken.get_encoding("cl100k_base")
                    token_count = len(encoder.encode(result.stdout))
                except Exception as e:
                    logger.warning(f"Failed to count tokens: {e}")
                    token_count = len(result.stdout) // 4  # rough estimate

                # Record metrics
                self.metrics.record_analysis(duration, token_count)
                
                # Handle git automation
                for repo_config in self.config.get('repositories', []):
                    if Path(repo_path).resolve() == Path(repo_config['path']).resolve():
                        git_automation = self.git_automations[repo_config['name']]
                        changed_files = self.get_changed_files(repo_path)
                        
                        if git_automation.should_commit(changed_files):
                            analysis_result = self.parse_analysis_result(output_file)
                            git_automation.commit_and_push(changed_files, analysis_result)
                            self.metrics.record_git_operation('commits')
                            if self.config.get('git_automation', {}).get('auto_push'):
                                self.metrics.record_git_operation('pushes')
                        break
                        
            except subprocess.CalledProcessError as e:
                logger.error(f"Repomix analysis failed: {e}")
                self.metrics.record_analysis(time.time() - start_time, 0)  # failed run

    def get_changed_files(self, repo_path):
        """Get list of files changed since last commit"""
        repo = git.Repo(repo_path)
        return [item.a_path for item in repo.index.diff(None)]

    def parse_analysis_result(self, output_file):
        """Parse repomix output for git commit details"""
        try:
            with open(output_file) as f:
                content = f.read()
                # Simple parsing for now - could be enhanced
                lines = content.split('\n')
                return {
                    'summary': lines[0] if lines else 'Updated code analysis',
                    'details': '\n'.join(lines[1:5]) if len(lines) > 1 else ''
                }
        except Exception as e:
            logger.error(f"Failed to parse analysis result: {e}")
            return None

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, processor):
        self.processor = processor
        self.last_run = 0
        self.debounce_seconds = 5

    def on_modified(self, event):
        if event.is_directory:
            return

        current_time = time.time()
        if current_time - self.last_run < self.debounce_seconds:
            return

        self.last_run = current_time
        repo_path = os.path.dirname(event.src_path)
        logger.info(f"Change detected in {event.src_path}")
        self.processor.run_analysis(repo_path)

class APIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, processor=None, **kwargs):
        self.processor = processor
        super().__init__(*args, **kwargs)

    def do_GET(self):
        try:
            if self.path == '/status':
                self.send_json_response({'status': 'running', 'version': '1.0.0'})
            elif self.path == '/repos':
                repos = [{'name': r['name'], 'path': r['path']}
                        for r in self.processor.config['repositories']]
                self.send_json_response({'repositories': repos})
            elif self.path.startswith('/repos/'):
                parts = self.path.split('/')
                if len(parts) < 4:
                    raise ValueError("Invalid repo path")
                    
                repo_name = parts[2]
                action = parts[3]
                repo = self.get_repo_config(repo_name)
                
                if action == 'issues':
                    issues = self.get_repo_issues(repo)
                    self.send_json_response({'issues': issues})
                elif action == 'insights':
                    insights = self.get_repo_insights(repo)
                    self.send_json_response({'insights': insights})
                else:
                    self.send_error(404, "Unknown action")
            else:
                self.send_error(404, "Not found")
        except Exception as e:
            self.send_error(500, str(e))

    def do_POST(self):
        try:
            if self.path.startswith('/repos/'):
                parts = self.path.split('/')
                if len(parts) < 4:
                    raise ValueError("Invalid repo path")
                    
                repo_name = parts[2]
                action = parts[3]
                
                if action == 'analyze':
                    repo = self.get_repo_config(repo_name)
                    self.processor.run_analysis(repo['path'])
                    self.send_json_response({'status': 'analysis_started'})
                elif action == 'clone':
                    content_length = int(self.headers.get('content-length', 0))
                    if content_length:
                        body = self.rfile.read(content_length)
                        data = json.loads(body)
                        if 'url' not in data:
                            raise ValueError("Missing repository URL")
                        
                        # Clone remote repository
                        repo_path = self.clone_remote_repo(data['url'], repo_name)
                        self.send_json_response({
                            'status': 'cloned',
                            'path': repo_path
                        })
                    else:
                        raise ValueError("Missing request body")
                else:
                    self.send_error(404, "Unknown action")
            else:
                self.send_error(404, "Not found")
        except Exception as e:
            self.send_error(500, str(e))

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def get_repo_config(self, repo_name):
        for repo in self.processor.config['repositories']:
            if repo['name'] == repo_name:
                return repo
        raise ValueError(f"Repository {repo_name} not found")

    def get_repo_issues(self, repo):
        """Get current issues from latest analysis"""
        try:
            analysis_file = Path(repo['path']) / '.llmdiver/repomix.md'
            if analysis_file.exists():
                with open(analysis_file) as f:
                    content = f.read()
                    # Simple parsing - could be enhanced
                    if '## Issues' in content:
                        issues_section = content.split('## Issues')[1].split('##')[0]
                        return [issue.strip() for issue in issues_section.split('\n') if issue.strip()]
            return []
        except Exception as e:
            logger.error(f"Failed to get repo issues: {e}")
            return []

    def get_repo_insights(self, repo):
        """Get insights from latest analysis"""
        try:
            analysis_file = Path(repo['path']) / '.llmdiver/repomix.md'
            if analysis_file.exists():
                with open(analysis_file) as f:
                    content = f.read()
                    # Simple parsing - could be enhanced
                    if '## Insights' in content:
                        insights_section = content.split('## Insights')[1].split('##')[0]
                        return [insight.strip() for insight in insights_section.split('\n') if insight.strip()]
            return []
        except Exception as e:
            logger.error(f"Failed to get repo insights: {e}")
            return []

    def clone_remote_repo(self, url, repo_name):
        """Clone a remote repository for analysis"""
        base_path = Path(self.processor.config['repositories'][0]['path']).parent
        repo_path = base_path / repo_name
        
        if repo_path.exists():
            logger.warning(f"Repository path already exists: {repo_path}")
            return str(repo_path)
            
        try:
            git.Repo.clone_from(url, str(repo_path))
            logger.info(f"Cloned repository to {repo_path}")
            
            # Add to monitored repositories
            self.processor.config['repositories'].append({
                'name': repo_name,
                'path': str(repo_path),
                'auto_commit': False,
                'auto_push': False,
                'analysis_triggers': ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.sh"],
                'commit_threshold': 10
            })
            
            # Start watching the new repository
            event_handler = FileChangeHandler(self.processor)
            observer = Observer()
            observer.schedule(event_handler, str(repo_path), recursive=True)
            observer.start()
            
            return str(repo_path)
        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise

def main():
    # Load configuration
    config = Config()
    
    # Initialize components
    processor = RepomixProcessor(config.config)
    
    # Set up file watching for each repository
    observer = Observer()
    for repo_config in config.config.get('repositories', []):
        repo_path = repo_config['path']
        event_handler = FileChangeHandler(processor)
        observer.schedule(event_handler, repo_path, recursive=True)
        logger.info(f"Watching repository: {repo_path}")
    
    observer.start()

    # Set up API server
    daemon_config = config.config['daemon']
    server = HTTPServer(
        (daemon_config['host'], daemon_config['port']),
        lambda *args: APIHandler(*args, processor=processor)
    )
    
    logger.info(f"Starting API server on {daemon_config['host']}:{daemon_config['port']}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        observer.stop()
        server.shutdown()
    
    observer.join()

if __name__ == '__main__':
    main()