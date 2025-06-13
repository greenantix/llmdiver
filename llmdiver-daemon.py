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
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Check for optional dependencies
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

class CodePreprocessor:
    def __init__(self, remove_comments=True, remove_whitespace=True):
        self.remove_comments = remove_comments
        self.remove_whitespace = remove_whitespace

    def _extract_file_sections(self, content: str) -> List[Dict]:
        """Extract individual file sections from repomix output"""
        files = []
        current_file_path = None
        current_language = 'unknown'
        current_content_lines = []
        in_code_block = False

        for line in content.split('\n'):
            # Check for the start of a new file
            if line.startswith("## File: "):
                # If we were already in a file, save the previous one
                if current_file_path and current_content_lines:
                    files.append({
                        'path': current_file_path,
                        'language': current_language,
                        'content': '\n'.join(current_content_lines).strip(),
                        'size': len('\n'.join(current_content_lines))
                    })

                # Reset for the new file
                current_file_path = line.replace("## File: ", "").strip()
                current_content_lines = []
                in_code_block = False  # Wait for the code block to start
                current_language = self._detect_language(current_file_path)

            # Check for the start of a code block
            elif line.startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    # Optional: capture language from ```bash, ```python etc.
                    lang_spec = line.replace("```", "").strip()
                    if lang_spec:
                        current_language = lang_spec
                else:
                    # End of code block for the current file
                    in_code_block = False

            # If we are inside a code block, append the line
            elif current_file_path and in_code_block:
                current_content_lines.append(line)

        # Append the last file after the loop finishes
        if current_file_path and current_content_lines:
            files.append({
                'path': current_file_path,
                'language': current_language,
                'content': '\n'.join(current_content_lines).strip(),
                'size': len('\n'.join(current_content_lines))
            })

        logging.info(f"Preprocessor extracted {len(files)} file sections from repomix output.")
        return files

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rb': 'ruby',
            '.php': 'php',
            '.sh': 'bash'
        }
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext, 'unknown')

    def preprocess_repomix_output(self, content: str) -> Dict:
        """Preprocess the repomix markdown output into structured format"""
        files = self._extract_file_sections(content)

        if not files:
            logging.warning("No valid file sections found in repomix output")
            return {'files': [], 'metrics': {}}

        total_size = sum(f['size'] for f in files)
        avg_size = total_size / len(files) if files else 0

        metrics = {
            'total_files': len(files),
            'total_size': total_size,
            'average_file_size': avg_size,
            'languages': list(set(f['language'] for f in files))
        }

        return {
            'files': files,
            'metrics': metrics
        }

    def format_for_llm(self, preprocessed_data: Dict) -> str:
        """Format preprocessed data for LLM consumption"""
        output = []
        metrics = preprocessed_data['metrics']

        output.append("## Project Metrics")
        output.append(f"- Total Files: {metrics['total_files']}")
        output.append(f"- Total Code Size: {metrics['total_size']} characters")
        output.append(f"- Average File Size: {metrics['average_file_size']:.1f} characters")
        output.append(f"- Languages: {', '.join(metrics['languages'])}")
        output.append("")

        output.append("## File Analysis")
        for file_data in preprocessed_data['files']:
            output.append(f"### {file_data['path']}")
            output.append(f"- Language: {file_data['language']}")
            output.append(f"- Size: {file_data['size']} characters")
            output.append("```" + file_data['language'])
            output.append(file_data['content'])
            output.append("```")
            output.append("")

        return '\n'.join(output)


class CodeIndexer:
    def __init__(self, config):
        self.config = config
        self.embedding_model = None
        self.embedding_backend = None
        self._initialize_embedding_backend()

    def _initialize_embedding_backend(self):
        """Initialize the appropriate embedding backend"""
        model_choice = self.config.get("embedding_model", "tfidf")
        logging.info(f"Attempting to initialize embedding model: '{model_choice}'")

        if model_choice == "sentence_transformers" and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                from sentence_transformers import SentenceTransformer
                model_name = self.config.get("model_name", "all-MiniLM-L6-v2")
                self.embedding_backend = SentenceTransformer(model_name)
                logging.info(f"SUCCESS: Initialized SentenceTransformers with model: {model_name}")
                self.embedding_model = "sentence_transformers"
                return
            except Exception as e:
                logging.warning(f"Failed to load SentenceTransformers model: {e}. Falling back to TF-IDF.")

        if model_choice == "llama_cpp" and LLAMA_CPP_AVAILABLE:
            try:
                model_path = self.config.get("model_path", "")
                if model_path and os.path.exists(model_path):
                    from llama_cpp import Llama
                    self.embedding_backend = Llama(model_path=model_path, embedding=True, n_ctx=512, verbose=False)
                    logging.info(f"SUCCESS: Initialized Llama.cpp embedding model from path: {model_path}")
                    self.embedding_model = "llama_cpp"
                    return
                else:
                    logging.warning(f"Llama.cpp model path not found or not specified: '{model_path}'. Falling back to TF-IDF.")
            except Exception as e:
                logging.warning(f"Failed to load Llama.cpp model: {e}. Falling back to TF-IDF.")

        # Default to TF-IDF
        self.embedding_model = "tfidf"
        self.embedding_backend = TfidfVectorizer(max_features=1000, stop_words='english', ngram_range=(1, 2))
        logging.info("Initialized fallback TF-IDF vectorizer for semantic search.")

    def find_similar_code(self, query_blocks, similarity_threshold=0.7):
        """Find code blocks similar to the query blocks"""
        logging.info(f"Searching for code similar to {len(query_blocks)} block(s)...")
        if not query_blocks:
            return []

        # Get embeddings based on the current backend
        if self.embedding_model == "sentence_transformers":
            query_embeddings = self.embedding_backend.encode(query_blocks)
            stored_embeddings = self.embedding_backend.encode(self.stored_blocks)
        elif self.embedding_model == "llama_cpp":
            query_embeddings = np.array([self.embedding_backend.embed(block) for block in query_blocks])
            stored_embeddings = np.array([self.embedding_backend.embed(block) for block in self.stored_blocks])
        else:  # TF-IDF
            vectorizer = self.embedding_backend.fit(self.stored_blocks + query_blocks)
            all_embeddings = vectorizer.transform(self.stored_blocks + query_blocks).toarray()
            stored_embeddings = all_embeddings[:len(self.stored_blocks)]
            query_embeddings = all_embeddings[len(self.stored_blocks):]

        # Calculate similarities
        similar_blocks = []
        for i, query_embedding in enumerate(query_embeddings):
            similarities = cosine_similarity([query_embedding], stored_embeddings)[0]
            for j, similarity in enumerate(similarities):
                if similarity > similarity_threshold and i != j:
                    similar_blocks.append({
                        'query_block': query_blocks[i],
                        'similar_block': self.stored_blocks[j],
                        'similarity': similarity,
                        'file_path': self.block_files[j]
                    })

        # Sort by similarity
        similar_blocks.sort(key=lambda x: x['similarity'], reverse=True)

        # Remove duplicates while preserving order
        seen = set()
        unique_blocks = []
        for block in similar_blocks:
            block_key = (block['query_block'], block['similar_block'])
            if block_key not in seen:
                seen.add(block_key)
                unique_blocks.append(block)

        logging.info(f"Found {len(unique_blocks)} unique similar code blocks with threshold > {similarity_threshold}.")
        return unique_blocks

    def update_index(self, code_blocks):
        """Update the indexed code blocks"""
        self.stored_blocks = code_blocks
        self.block_files = []  # Store file paths for each block
        logging.info(f"Updated code index with {len(code_blocks)} blocks")

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
        
        # Initialize core components
        self.code_indexer = CodeIndexer(config.get('semantic_search', {}))
        self.code_preprocessor = self.create_preprocessor()
        self.intelligent_router = self.create_intelligent_router()
        self.multi_project_manager = self.create_project_manager()
        self.llm_client = LLM_Client(config.get('llm_integration', {})) # Assuming LLM_Client class exists
        
        # Initialize git automation for each repo
        for repo in config.get('repositories', []):
            self.git_automations[repo['name']] = GitAutomation(config, repo)
            
    def create_preprocessor(self):
        """Create and configure the code preprocessor"""
        return CodePreprocessor(
            remove_comments=self.config.get('preprocessing', {}).get('remove_comments', True),
            remove_whitespace=self.config.get('preprocessing', {}).get('remove_whitespace', True)
        )
        
    def create_intelligent_router(self):
        """Create and configure the intelligent router"""
        return IntelligentRouter(
            thresholds=self.config.get('analysis', {}).get('classification_thresholds', {})
        )
        
    def create_project_manager(self):
        """Create and configure the multi-project manager"""
        return MultiProjectManager(
            auto_discover=self.config.get('multi_project', {}).get('auto_discover', False),
            max_depth=self.config.get('multi_project', {}).get('max_depth', 2)
        )

    def run_repomix_analysis(self, repo_path):
        """Run initial repomix analysis on repository and return the summary"""
        try:
            output_dir = Path(repo_path) / '.llmdiver'
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / 'repomix.md'
            
            if not output_file.exists():
                cmd = ['repomix', repo_path, '--output', str(output_file)]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                if result.returncode != 0:
                    logging.error(f"Repomix analysis failed: {result.stderr}")
                    return None
            
            with open(output_file) as f:
                return f.read()
                
        except Exception as e:
            logging.error(f"Failed to run repomix analysis: {e}")
            return None

    def _extract_structured_findings(self, analysis_text: str) -> Dict: #
        """Extract structured findings from AI analysis text for JSON output"""
        findings = {
            "executive_summary": "", #
            "critical_issues": [], #
            "high_priority": [], #
            "medium_priority": [], #
            "low_priority": [], #
            "recommendations": [] #
        }

        section_map = {
            "executive summary": "executive_summary",
            "critical vulnerabilities": "critical_issues",
            "critical security & stability issues": "critical_issues",
            "critical issues": "critical_issues",
            "authentication & authorization issues": "high_priority",
            "architectural problems": "high_priority",
            "performance & scalability concerns": "high_priority",
            "high priority concerns": "high_priority",
            "input validation & injection risks": "medium_priority",
            "technical debt & todos": "medium_priority",
            "technical debt analysis": "medium_priority",
            "security configuration & headers": "low_priority",
            "dead code & optimization": "low_priority",
            "recommendations": "recommendations",
            "implementation roadmap": "recommendations",
            "claude code action items": "recommendations"
        }

        current_section_key = None

        for line in analysis_text.split('\n'):
            line_stripped = line.strip()

            # Check if the line is a section header
            is_header = False
            if line_stripped.startswith('## '):
                header_text = line_stripped.replace('## ', '').lower()
                # Find the corresponding key in our map
                for key, value in section_map.items():
                    if key in header_text:
                        current_section_key = value
                        is_header = True
                        break

            # If it's not a header and we are in a section, append the content
            if not is_header and current_section_key:
                if line_stripped:
                    # For lists, just append the content
                    if current_section_key != 'executive_summary':
                         if line_stripped.startswith(('-', '*', '1.', '2.', '3.')):
                            findings[current_section_key].append(line_stripped)
                    # For summary, append the whole line
                    else:
                        # Re-constitute the summary paragraph
                        if findings[current_section_key]:
                            findings[current_section_key] += " " + line_stripped
                        else:
                            findings[current_section_key] = line_stripped

        return findings
    def analyze_manifest_changes(self, repo_config):
        """Analyze changes in dependency manifests"""
        try:
            repo_path = Path(repo_config['path'])
            manifest_files = [
                'package.json',
                'requirements.txt', 
                'Cargo.toml',
                'go.mod',
                'pom.xml',
                'build.gradle'
            ]
            
            changes = []
            for manifest in manifest_files:
                manifest_path = repo_path / manifest
                if manifest_path.exists():
                    changes.append(f"Found manifest: {manifest}")
                    # Add manifest specific analysis here
                    
            return "\n".join(changes) if changes else ""
        except Exception as e:
            logging.error(f"Failed to analyze manifests: {e}")
            return ""


    def enhanced_repository_analysis(self, repo_config: Dict):
        """Enhanced analysis including manifests and multi-project context"""
        logging.info(f"--- Starting Enhanced Analysis for {repo_config['name']} ---")

        try:
            # Step 1: Run repomix
            logging.info("Step 1: Running repomix to generate repository summary...")
            summary = self.run_repomix_analysis(repo_config["path"])
            if not summary:
                logging.error("ANALYSIS HALTED: Repomix failed to generate a summary.")
                return
            logging.info(f"Repomix summary generated ({len(summary)} characters).")

            # Step 2: Preprocess and index code
            logging.info("Step 2: Preprocessing code and updating semantic index...")
            preprocessed_data = self.code_preprocessor.preprocess_repomix_output(summary)
            self.code_indexer.update_index(preprocessed_data)
            formatted_summary = self.code_preprocessor.format_for_llm(preprocessed_data)
            logging.info("Code preprocessing and indexing complete.")

            # Step 3: Get Semantic Context
            logging.info("Step 3: Performing semantic search for similar code...")
            semantic_context = self.code_indexer.get_semantic_context(preprocessed_data)
            if semantic_context:
                logging.info(f"Semantic context found with {len(semantic_context.split('File:'))-1} similar blocks.")
            else:
                logging.info("No semantically similar code found.")

            # Step 4: Analyze Dependencies
            logging.info("Step 4: Analyzing manifest for dependency changes...")
            manifest_analysis = self.analyze_manifest_changes(repo_config)
            if manifest_analysis:
                logging.info("Dependency changes detected.")
            else:
                logging.info("No dependency changes found.")

            # Step 5: Classify code and select prompt
            logging.info("Step 5: Using intelligent router to classify changes...")
            project_info = self.multi_project_manager.get_project_manifest_info(repo_config["path"])
            analysis_type = self.intelligent_router.classify_code_changes(preprocessed_data)
            if analysis_type == 'general' and manifest_analysis.strip():
                analysis_type = 'dependency'
            logging.info(f"Intelligent router selected analysis type: '{analysis_type.upper()}'")

            # Step 6: Construct the final prompt for the LLM
            logging.info("Step 6: Constructing final prompt for LLM analysis...")
            enhanced_summary = f"""# Repository Analysis: {repo_config['name']}

            ## Project Context
            - Primary Language: {project_info['primary_language']}
            - Framework: {project_info['framework']}
            - Manifest Files: {len(project_info['manifests'])}

            {manifest_analysis}

            {semantic_context}

            ## Preprocessed Code Analysis
            {formatted_summary}

            ## Analysis Instructions
            When analyzing this codebase, pay special attention to:
            1. **Dependency Security**: If manifest changes detected, assess security implications of new/removed packages
            2. **Language-Specific Patterns**: Apply {project_info['primary_language']}-specific best practices and common issues
            3. **Code Structure**: Use the preprocessed architecture overview and complexity hotspots to focus analysis
            4. **Code Reuse**: If similar code found, evaluate opportunities for refactoring and deduplication
            """
            logging.info(f"Final prompt constructed ({len(enhanced_summary)} characters).")

            # Step 7: Send to LLM for analysis
            logging.info(f"Step 7: Sending payload to LLM with prompt type '{analysis_type.upper()}'...")
            analysis = self.llm_client.analyze_repo_summary(enhanced_summary, analysis_type)
            if "Analysis failed" in analysis or "API error" in analysis:
                logging.error(f"ANALYSIS HALTED: LLM analysis failed. Response: {analysis}")
                return
            logging.info(f"LLM analysis successful ({len(analysis)} characters received).")

            # Step 8: Save results
            logging.info("Step 8: Saving Markdown report and structured JSON output...")
            analysis_dir = Path(repo_config["path"]) / ".llmdiver"
            analysis_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_file = analysis_dir / f"enhanced_analysis_{timestamp}.md"
            json_analysis_file = analysis_dir / f"analysis_data_{timestamp}.json"

            analysis_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "project_name": repo_config['name'],
                    "analysis_type": analysis_type
                },
                "project_context": {
                    "primary_language": project_info['primary_language'],
                    "framework": project_info['framework'],
                },
                "code_metrics": preprocessed_data.get('code_metrics', {}),
                "ai_analysis": {
                    "raw_text": analysis,
                    "structured_findings": self._extract_structured_findings(analysis)
                },
                "semantic_analysis": {
                    "has_similar_code": bool(semantic_context.strip()),
                    "context_text": semantic_context
                },
            }

            with open(json_analysis_file, 'w') as f:
                json.dump(analysis_data, f, indent=2, default=str)

            with open(analysis_file, 'w') as f:
                f.write(f"# LLMdiver Enhanced Analysis - {datetime.now()}\n\n")
                f.write(analysis)

            logging.info(f"Saved Markdown to {analysis_file} and JSON to {json_analysis_file}")

            # Step 9: Git Automation
            if repo_config.get("auto_commit", False):
                logging.info("Step 9: Performing Git auto-commit operations...")
                commit_message = f"LLMdiver enhanced analysis for {repo_config['name']}"
                self.git_automation.auto_commit(repo_config["path"], commit_message)
            else:
                logging.info("Step 9: Git auto-commit skipped (disabled for this repository).")

            logging.info(f"--- Analysis for {repo_config['name']} Complete ---")

        except Exception as e:
            logging.error(f"FATAL ERROR in enhanced_repository_analysis for {repo_config['name']}: {e}", exc_info=True)

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
        repo_path = os