#!/usr/bin/env python3

import ast
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
from llm_providers import ProviderOrchestrator, AnalysisTask
from caching_layer import AnalysisCache, CachedRepomixProcessor
from security_scanner import SecurityScanner

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
    def __init__(self, config, repo_config, code_preprocessor=None):
        self.config = config['git_automation']
        self.repo_config = repo_config
        self.repo = git.Repo(repo_config['path'])
        self.lock = Lock()
        self.code_preprocessor = code_preprocessor

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

    def auto_commit(self, analysis_file_path: Path, json_analysis_path: Path, analysis_data: Dict):
        """Perform git operations, including documentation updates."""
        if not self.config['enabled'] or not self.repo_config['auto_commit']:
            logging.info(f"Git auto-commit skipped (disabled for this repository).")
            return

        with self.lock:
            try:
                # Check if this is LLMdiver's own repository - if so, only commit project files
                is_self_analysis = self.repo_config['name'] == 'LLMdiver'
                
                if is_self_analysis:
                    # For LLMdiver repo, only commit non-LLMdiver files (actual project files)
                    changed_files = self._get_smart_changed_files()
                    if not changed_files:
                        logging.info("Smart Commit: No source file changes detected. Skipping commit.")
                        return
                    
                    # Stage only the actual project files, not analysis outputs
                    logging.info(f"Smart Commit: Staging {len(changed_files)} changed source files.")
                    self.repo.index.add(changed_files)
                    
                    # Generate commit message for actual code changes
                    commit_message = f"🤖 LLMdiver: Automated commit for {len(changed_files)} file(s)."
                    
                    # Commit and push for LLMdiver repo
                    self.repo.index.commit(commit_message)
                    logging.info(f"✅ Smart commit created: {commit_message.splitlines()[0]}")
                    
                    if self.config.get('auto_push', False) and self.repo_config.get('auto_push', False):
                        logging.info("Attempting to push to remote...")
                        self.repo.remote().push()
                        logging.info("✅ Successfully pushed changes to remote.")
                    
                else:
                    # For other repos, use the standard approach
                    # 1. Update the core documentation from the analysis results
                    doc_path = self.update_documentation(analysis_data)

                    # 2. Stage the analysis files and the updated documentation
                    files_to_add = [str(analysis_file_path), str(json_analysis_path)]
                    if doc_path and doc_path.exists():
                        files_to_add.append(str(doc_path))

                    logging.info(f"Standard Commit: Staging {len(files_to_add)} analysis artifacts.")
                    self.repo.index.add(files_to_add)

                    # 3. Generate a detailed commit message
                    commit_message = self.generate_commit_message_from_data(analysis_data)
                    
                    # Commit and push for other repos
                    self.repo.index.commit(commit_message)
                    logging.info(f"✅ Successfully created commit: {commit_message.splitlines()[0]}")

                    if self.config.get('auto_push', False) and self.repo_config.get('auto_push', False):
                        logging.info("Attempting to push to remote...")
                        self.repo.remote().push()
                        logging.info("✅ Successfully pushed changes to remote.")

            except Exception as e:
                logging.error(f"❌ Git automation failed: {e}", exc_info=True)

    def _get_smart_changed_files(self):
        """Get changed files excluding LLMdiver's own files"""
        changed_files = []
        
        # Get all changed files
        for item in self.repo.index.diff(None):
            file_path = item.a_path
            # Skip LLMdiver internal files
            if not self.code_preprocessor._is_llmdiver_internal_file(file_path):
                changed_files.append(file_path)
        
        # Also check untracked files
        for untracked in self.repo.untracked_files:
            if not self.code_preprocessor._is_llmdiver_internal_file(untracked):
                changed_files.append(untracked)
        
        return changed_files
    
    

    def commit_and_push(self, changed_files, analysis_result):
        """Legacy method for backwards compatibility"""
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
                    self.update_documentation_legacy()
                    
            except Exception as e:
                logger.error(f"Git automation failed: {e}")

    def generate_commit_message_from_data(self, analysis_data: Dict) -> str:
        """Create a detailed commit message from structured analysis data."""
        template = self.config.get('commit_message_template', "🤖 LLMdiver Analysis: {summary}")
        findings = analysis_data.get("ai_analysis", {}).get("structured_findings", {})

        crit_count = len(findings.get("critical_issues", []))
        high_count = len(findings.get("high_priority", []))
        med_count = len(findings.get("medium_priority", []))

        summary = f"Found {crit_count} critical, {high_count} high, {med_count} medium issues."
        details = findings.get('executive_summary', 'No executive summary provided.')

        return template.format(summary=summary, details=details)

    def update_documentation(self, analysis_data: Dict) -> Path:
        """Generate and update the main analysis documentation file."""
        docs_path = Path(self.repo_config['path']) / '.llmdiver'
        docs_path.mkdir(exist_ok=True)
        doc_file = docs_path / 'llmdiver_analysis.md'

        logging.info(f"Updating documentation at {doc_file}...")

        with open(doc_file, 'w') as f:
            f.write(f"# LLMdiver Code Health Report: {self.repo_config['name']}\n")
            f.write(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            findings = analysis_data.get("ai_analysis", {}).get("structured_findings", {})
            f.write("## Executive Summary\n")
            f.write(f"{findings.get('executive_summary', 'Not available.')}\n\n")

            for key, name in [
                ('critical_issues', 'Critical Issues'),
                ('high_priority', 'High Priority Issues'),
                ('medium_priority', 'Medium Priority Issues'),
            ]:
                items = findings.get(key, [])
                if items:
                    f.write(f"### {name} ({len(items)})\n")
                    for item in items:
                        f.write(f"- {item.strip()}\n")
                    f.write("\n")
        
        logging.info("Documentation update complete.")
        return doc_file

    def update_documentation_legacy(self):
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
                    file_content = '\n'.join(current_content_lines).strip()
                    files.append({
                        'path': current_file_path,
                        'language': current_language,
                        'content': file_content,
                        'size': len(file_content),
                        'code_blocks': self._extract_code_blocks(file_content, current_language)
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
            file_content = '\n'.join(current_content_lines).strip()
            files.append({
                'path': current_file_path,
                'language': current_language,
                'content': file_content,
                'size': len(file_content),
                'code_blocks': self._extract_code_blocks(file_content, current_language)
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

    def _extract_code_blocks(self, content: str, language: str) -> List[Dict]:
        """Extract functions and classes from code content"""
        blocks = []
        
        if language == 'python':
            blocks.extend(self._extract_python_blocks(content))
        elif language in ['javascript', 'typescript']:
            blocks.extend(self._extract_js_blocks(content))
        elif language == 'bash':
            blocks.extend(self._extract_bash_blocks(content))
        else:
            # For other languages, treat the whole content as one block
            if content.strip():
                blocks.append({
                    'type': 'file_content',
                    'name': f'{language}_content',
                    'content': content.strip(),
                    'line_start': 1,
                    'line_end': len(content.split('\n'))
                })
        
        logging.debug(f"Extracted {len(blocks)} code blocks for {language}")
        return blocks

    def _extract_python_blocks(self, content: str) -> List[Dict]:
        """Extract Python functions and classes using the AST module."""
        blocks = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start_line = node.lineno
                    # Get the full source segment for the node
                    end_line = getattr(node, 'end_lineno', start_line)
                    source_segment = ast.get_source_segment(content, node)

                    if source_segment:
                        block_type = 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class'
                        blocks.append({
                            'type': block_type,
                            'name': node.name,
                            'content': source_segment,
                            'line_start': start_line,
                            'line_end': end_line,
                        })
        except SyntaxError as e:
            logging.warning(f"Could not parse Python file with AST due to syntax error: {e}")
        except Exception as e:
            logging.error(f"Failed to extract Python blocks using AST: {e}")

        return blocks

    def _extract_js_blocks(self, content: str) -> List[Dict]:
        """Extract JavaScript/TypeScript functions"""
        import re
        blocks = []
        lines = content.split('\n')
        
        # Patterns for JS/TS functions
        func_patterns = [
            re.compile(r'^\s*function\s+(\w+)\s*\(([^)]*)\)'),
            re.compile(r'^\s*const\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>'),
            re.compile(r'^\s*(\w+)\s*:\s*function\s*\(([^)]*)\)'),
        ]
        
        for i, line in enumerate(lines):
            for pattern in func_patterns:
                match = pattern.search(line)
                if match:
                    func_name = match.group(1)
                    params = match.group(2) if len(match.groups()) > 1 else ''
                    
                    # Extract function body (simplified - just take a few lines)
                    block_lines = [line]
                    for j in range(i + 1, min(i + 20, len(lines))):
                        block_lines.append(lines[j])
                        if '}' in lines[j]:
                            break
                    
                    blocks.append({
                        'type': 'function',
                        'name': func_name,
                        'content': '\n'.join(block_lines),
                        'line_start': i + 1,
                        'line_end': i + len(block_lines),
                        'parameters': params.strip()
                    })
                    break
        
        return blocks

    def _extract_bash_blocks(self, content: str) -> List[Dict]:
        """Extract Bash functions"""
        import re
        blocks = []
        lines = content.split('\n')
        
        func_pattern = re.compile(r'^\s*(\w+)\s*\(\s*\)\s*\{?')
        
        for i, line in enumerate(lines):
            match = func_pattern.match(line)
            if match:
                func_name = match.group(1)
                
                # Extract function body
                block_lines = [line]
                brace_count = line.count('{') - line.count('}')
                
                for j in range(i + 1, len(lines)):
                    block_lines.append(lines[j])
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    
                    if brace_count <= 0:
                        break
                
                blocks.append({
                    'type': 'function',
                    'name': func_name,
                    'content': '\n'.join(block_lines),
                    'line_start': i + 1,
                    'line_end': i + len(block_lines)
                })
        
        return blocks

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
        metrics = preprocessed_data.get('metrics', {})
        files = preprocessed_data.get('files', [])

        output.append("## Project Metrics")
        output.append(f"- Total Files: {metrics.get('total_files', 0)}")
        output.append(f"- Total Code Size: {metrics.get('total_size', 0)} characters")
        output.append(f"- Average File Size: {metrics.get('average_file_size', 0):.1f} characters")
        output.append(f"- Languages: {', '.join(metrics.get('languages', ['unknown']))}")
        output.append("")

        if not files:
            output.append("## File Analysis")
            output.append("No valid code files found for analysis. This may indicate:")
            output.append("- Repository contains only configuration or documentation files")
            output.append("- File patterns in repomix configuration are too restrictive")
            output.append("- All code files are being filtered out by ignore patterns")
            output.append("")
            return '\n'.join(output)

        output.append("## File Analysis")
        for file_data in files:
            output.append(f"### {file_data['path']}")
            output.append(f"- Language: {file_data['language']}")
            output.append(f"- Size: {file_data['size']} characters")
            output.append("```" + file_data['language'])
            output.append(file_data['content'])
            output.append("```")
            output.append("")

        return '\n'.join(output)

    def _is_llmdiver_internal_file(self, file_path: str) -> bool:
        """Check if a file is internal to LLMdiver's operations."""
        llmdiver_patterns = [
            '.llmdiver/',
            'llmdiver_daemon.log',
            'llmdiver.pid',
            'metrics/',
            'audits/',
            'analysis_data_',
            'enhanced_analysis_',
            'Action_Plan',
            'indexing_test/'
        ]
        return any(pattern in file_path for pattern in llmdiver_patterns)


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

    def update_index(self, preprocessed_data):
        """Update the indexed code blocks from preprocessed data"""
        all_blocks = []
        block_files = []
        
        for file_data in preprocessed_data.get('files', []):
            file_path = file_data['path']
            code_blocks = file_data.get('code_blocks', [])
            
            for block in code_blocks:
                # Store the actual function/class content for similarity comparison
                all_blocks.append(block['content'])
                block_files.append(f"{file_path}:{block.get('name', 'unknown')}")
        
        self.stored_blocks = all_blocks
        self.block_files = block_files
        logging.info(f"Updated code index with {len(all_blocks)} code blocks from {len(preprocessed_data.get('files', []))} files")

    def get_semantic_context(self, preprocessed_data):
        """Get semantic context by finding similar code patterns"""
        try:
            files = preprocessed_data.get('files', [])
            if not files:
                return ""
            
            # Extract all code blocks from all files
            all_query_blocks = []
            for file_data in files:
                code_blocks = file_data.get('code_blocks', [])
                for block in code_blocks:
                    all_query_blocks.append(block['content'])
            
            if len(all_query_blocks) < 2:
                logging.info("Not enough code blocks for semantic comparison.")
                return ""
            
            # Use the first few blocks as queries to find similar patterns
            query_blocks = all_query_blocks[:3]  # Use first 3 blocks as queries
            similar_results = self.find_similar_code(query_blocks, similarity_threshold=0.3)
            
            if not similar_results:
                logging.info("No semantically similar code found matching the threshold.")
                return ""
            
            # --- FIX: The log message should only appear if we actually build a context string ---
            context_lines = ["## Semantic Code Analysis", ""]
            context_lines.append(f"Found {len(similar_results)} similar code patterns:")
            
            for i, result in enumerate(similar_results[:5]):  # Top 5 results
                context_lines.append(f"### Similar Pattern {i+1} (Score: {result['similarity']:.3f})")
                context_lines.append(f"Location: {result.get('file_path', 'Unknown')}")
                context_lines.append("```")
                # Show a meaningful snippet
                snippet = result['similar_block']
                if len(snippet) > 300:
                    snippet = snippet[:300] + "..."
                context_lines.append(snippet)
                context_lines.append("```")
                context_lines.append("")
            
            logging.info(f"Successfully generated semantic context with {len(similar_results)} blocks.")
            return "\n".join(context_lines)
            
        except Exception as e:
            logging.error(f"Error in get_semantic_context: {e}", exc_info=True)
            return ""

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

class LLMStudioClient:
    def __init__(self, config):
        self.config = config
        # Initialize multi-provider system
        provider_config = {
            "providers": {
                "lmstudio": {
                    "url": config["llm_integration"]["url"],
                    "model": config["llm_integration"]["model"],
                    "max_tokens": config["llm_integration"]["max_tokens"]
                }
            },
            "fallback_chain": ["lmstudio"],
            "cost_budget": config.get("cost_budget", 0.0)  # Default to free only
        }
        
        # Add other providers if configured
        if config.get("openai_api_key"):
            provider_config["providers"]["openai"] = {
                "api_key": config["openai_api_key"],
                "model": config.get("openai_model", "gpt-4")
            }
            provider_config["fallback_chain"].append("openai")
        
        if config.get("ollama_enabled", False):
            provider_config["providers"]["ollama"] = {
                "url": config.get("ollama_url", "http://localhost:11434/api/generate"),
                "model": config.get("ollama_model", "llama2")
            }
            provider_config["fallback_chain"].insert(-1, "ollama")  # Before OpenAI
        
        self.orchestrator = ProviderOrchestrator(provider_config)
        self.specialized_prompts = self._load_specialized_prompts()
        
        # Legacy compatibility
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

    async def analyze_repo_summary(self, summary_text: str, analysis_type: str = "general") -> str:
        """Send repo summary for analysis using multi-provider system"""
        system_prompt = self.specialized_prompts.get(analysis_type, self.specialized_prompts["general"])
        full_prompt = f"{system_prompt}\n\nAnalyze this repository:\n\n{summary_text}"
        
        # Create analysis task
        task = AnalysisTask(
            task_type=analysis_type,
            content=full_prompt,
            context={"analysis_type": analysis_type},
            max_tokens=self.config["llm_integration"].get("max_tokens", 4096),
            temperature=self.config["llm_integration"].get("temperature", 0.3)
        )
        
        # Check if chunking is enabled and needed
        enable_chunking = self.config["llm_integration"].get("enable_chunking", False)
        chunk_size = self.config["llm_integration"].get("chunk_size", 16000)
        
        if enable_chunking and len(summary_text) > chunk_size:
            logging.info(f"Large repository detected ({len(summary_text)} chars), using chunking...")
            chunks = self.chunk_text(summary_text, chunk_size)
            all_analyses = []
            
            for i, chunk in enumerate(chunks):
                logging.info(f"Analyzing chunk {i+1}/{len(chunks)} using multi-provider system")
                chunk_prompt = f"{system_prompt}\n\nAnalyze this repository section ({i+1}/{len(chunks)}):\n\n{chunk}"
                
                chunk_task = AnalysisTask(
                    task_type=analysis_type,
                    content=chunk_prompt,
                    context={"chunk": i+1, "total_chunks": len(chunks)},
                    max_tokens=task.max_tokens,
                    temperature=task.temperature
                )
                
                response = await self.orchestrator.route_request(chunk_task)
                if not response.success:
                    return f"Analysis failed: {response.error}"
                
                all_analyses.append(f"## Chunk {i+1}/{len(chunks)} Analysis\n{response.content}")
            
            # Combine analyses
            combined = "\n\n".join(all_analyses)
            
            # Send combined analysis for final summary
            final_prompt = "You are consolidating multiple code audit reports. Combine similar findings and prioritize the most critical issues.\n\n" + combined
            final_task = AnalysisTask(
                task_type="consolidation",
                content=final_prompt,
                context={"final_summary": True},
                max_tokens=task.max_tokens,
                temperature=task.temperature
            )
            
            final_response = await self.orchestrator.route_request(final_task)
            if final_response.success:
                logging.info(f"Multi-provider analysis completed. Provider: {final_response.provider}, Cost: ${final_response.cost_estimate:.4f}")
                return final_response.content
            else:
                return f"Final analysis failed: {final_response.error}"
        else:
            # Single request for small repositories
            response = await self.orchestrator.route_request(task)
            if response.success:
                logging.info(f"Multi-provider analysis completed. Provider: {response.provider}, Cost: ${response.cost_estimate:.4f}")
                return response.content
            else:
                return f"Analysis failed: {response.error}"
    
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
            import requests
            response = requests.post(self.url, json=payload, timeout=300)  # 5 minutes
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(f"LM Studio API error: {e}")
            return f"Analysis failed: {e}"

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
            
            # Get sample code from file content directly
            content = file_analysis.get('content', '')
            if content.strip():
                # Take a representative sample of the file content
                code_samples.append(content[:1000])  # First 1000 chars as sample
        
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
            import requests
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
        manifest_files = ["package.json", "requirements.txt", "Cargo.toml", "pom.xml", "build.gradle"]
        manifests = []
        
        info = {
            "project_path": project_path,
            "manifests": manifests,
            "primary_language": "unknown",
            "framework": "unknown"
        }
        
        project_path_obj = Path(project_path)
        for manifest_file in manifest_files:
            manifest_path = project_path_obj / manifest_file
            if manifest_path.exists():
                manifests.append({"file": manifest_file, "path": str(manifest_path)})
                
                # Determine primary language/framework
                if "package.json" in manifest_file:
                    info["primary_language"] = "javascript"
                elif "requirements.txt" in manifest_file or "pyproject.toml" in manifest_file:
                    info["primary_language"] = "python"
                elif "Cargo.toml" in manifest_file:
                    info["primary_language"] = "rust"
                elif "pom.xml" in manifest_file:
                    info["primary_language"] = "java"
                elif "build.gradle" in manifest_file:
                    info["primary_language"] = "kotlin"
        
        return info

class RepomixProcessor:
    def __init__(self, config):
        self.config = config
        self.lock = Lock()
        self.git_automations = {}
        self.metrics = MetricsCollector()

        # Initialize caching system
        self.cache = AnalysisCache(config.get('cache_dir', '.llmdiver/cache'))

        # Use the existing LLMStudioClient class for LLM communication
        self.llm_client = LLMStudioClient(self.config) 

        # Instantiate the preprocessor
        self.code_preprocessor = CodePreprocessor(
            remove_comments=self.config.get('preprocessing', {}).get('remove_comments', True),
            remove_whitespace=self.config.get('preprocessing', {}).get('remove_whitespace', True)
        )

        # Instantiate the semantic indexer
        self.code_indexer = CodeIndexer(config.get('semantic_search', {}))

        # Instantiate the intelligent router, passing the llm_client to it
        self.intelligent_router = IntelligentRouter(self.llm_client)

        # Instantiate the multi-project manager
        self.multi_project_manager = MultiProjectManager(config.get('multi_project', {}))

        # Create cached processor wrapper
        self.cached_processor = CachedRepomixProcessor(self, config.get('cache_dir', '.llmdiver/cache'))

        # Initialize security scanner
        self.security_scanner = SecurityScanner()

        # Initialize git automation for each repo
        for repo in config.get('repositories', []):
            self.git_automations[repo['name']] = GitAutomation(config, repo, self.code_preprocessor)

    def run_repomix_analysis(self, repo_path):
        """Run initial repomix analysis on repository and return the summary"""
        try:
            output_dir = Path(repo_path) / '.llmdiver'
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / 'repomix.md'
            
            # Always regenerate to get fresh analysis
            repomix_config = self.config['repomix']
            
            # Use simpler command with key patterns only
            cmd = [
                'repomix', repo_path,
                '--output', str(output_file),
                '--style', 'markdown',
                '--include', '*.py',
                '--include', '*.js', 
                '--include', '*.ts',
                '--include', '*.sh',
                '--ignore', '*.md',
                '--ignore', '*.log', 
                '--ignore', '*test*.py',
                '--ignore', 'node_modules',
                '--ignore', '__pycache__',
                '--ignore', '.git',
                '--ignore', '.llmdiver'
            ]

            if repomix_config.get('compress', False):
                cmd.append('--compress')
            if repomix_config.get('remove_empty_lines', False):
                cmd.append('--remove-empty-lines')

            logging.info(f"Running repomix with command: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"Repomix analysis failed: {result.stderr}")
                return None
            
            with open(output_file) as f:
                return f.read()
                
        except Exception as e:
            logging.error(f"Failed to run repomix analysis: {e}")
            return None

    def run_repomix_diff_analysis(self, repo_path: str) -> str:
        """Runs repomix using --include-diffs to get only changed content."""
        try:
            output_dir = Path(repo_path) / '.llmdiver'
            output_dir.mkdir(exist_ok=True)
            diff_output_file = output_dir / 'repomix_diff.md'
            
            # This command is much faster as it only processes the git diff
            cmd = ['repomix', repo_path, '--output', str(diff_output_file), '--include-diffs']
            
            logging.info(f"Running incremental diff analysis with command: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                logging.error(f"Repomix diff analysis failed: {result.stderr}")
                return "" # Return empty string on failure

            with open(diff_output_file) as f:
                content = f.read()
            # If repomix finds no changes, it may return a header but no file content.
            if "## File:" not in content:
                logging.info("Repomix diff analysis found no substantive code changes.")
                return ""
            return content

        except Exception as e:
            logging.error(f"Failed to run repomix diff analysis: {e}", exc_info=True)
            return ""

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


    async def enhanced_repository_analysis(self, repo_config: Dict):
        """Enhanced analysis including manifests and multi-project context"""
        logging.info(f"--- Starting Enhanced Analysis for {repo_config['name']} ---")

        try:
            # Step 1: Run repomix to generate an INCREMENTAL repository summary (with caching)
            logging.info("Step 1: Running cached repomix --include-diffs to get changes...")
            summary = self.cached_processor.run_repomix_diff_analysis_cached(repo_config["path"])

            if not summary:
                logging.info("No file changes detected by git diff. Skipping full analysis cycle.")
                return # Exit the analysis cycle cleanly
            
            logging.info(f"Repomix diff summary generated ({len(summary)} characters). Cache stats: {self.cache.get_stats()}")

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

            # Step 4.5: Security Scanning (if enabled)
            security_results = None
            if self.config.get('security_scanning', {}).get('enabled', False):
                logging.info("Step 4.5: Running security vulnerability scan...")
                try:
                    security_results = await self.security_scanner.comprehensive_scan(repo_config["path"])
                    critical_count = security_results.summary.get('critical', 0)
                    high_count = security_results.summary.get('high', 0)
                    logging.info(f"Security scan completed: {critical_count} critical, {high_count} high severity issues found (Score: {security_results.security_score}/100)")
                except Exception as e:
                    logging.error(f"Security scan failed: {e}")
            else:
                logging.info("Step 4.5: Security scanning disabled, skipping...")

            # Step 5: Classify code and select prompt
            logging.info("Step 5: Using intelligent router to classify changes...")
            project_info = self.multi_project_manager.get_project_manifest_info(repo_config["path"])
            analysis_type = self.intelligent_router.classify_code_changes(preprocessed_data)
            if analysis_type == 'general' and manifest_analysis.strip():
                analysis_type = 'dependency'
            logging.info(f"Intelligent router selected analysis type: '{analysis_type.upper()}'")

            # Step 6: Construct the final prompt for the LLM
            logging.info("Step 6: Constructing final prompt for LLM analysis...")
            
            # Add security context if available
            security_context = ""
            if security_results:
                security_context = f"""
## Security Scan Results
- **Security Score:** {security_results.security_score}/100
- **Critical Issues:** {security_results.summary.get('critical', 0)}
- **High Priority Issues:** {security_results.summary.get('high', 0)}
- **Medium Priority Issues:** {security_results.summary.get('medium', 0)}
- **Low Priority Issues:** {security_results.summary.get('low', 0)}

### Top Security Findings:
"""
                # Add top 5 most critical findings
                critical_findings = [f for f in security_results.findings if f.severity in ['critical', 'high']][:5]
                for i, finding in enumerate(critical_findings, 1):
                    security_context += f"{i}. **{finding.severity.upper()}**: {finding.description} ({finding.file_path}:{finding.line_number})\n"
                
                if not critical_findings:
                    security_context += "No critical security issues detected in recent changes.\n"

            enhanced_summary = f"""# Repository Analysis for: {repo_config['name']}

## Project Context
- Primary Language: {project_info['primary_language']}
- Framework: {project_info['framework']}

{manifest_analysis}

{security_context}

{semantic_context}

## Code To Be Analyzed (Recent Changes)
{formatted_summary}

## Analysis Instructions
You are a principal software architect. Your task is to review the provided code changes ("Code To Be Analyzed").
1. **Primary Focus:** Analyze the new code for bugs, security vulnerabilities, and maintainability issues.
2. **Security Priority:** If security scan results are provided, prioritize addressing any critical or high-severity security findings.
3. **Use Semantic Context:** If "Semantic Context" is provided, check if the new code is redundant or could be refactored to use the existing similar code blocks.
4. **Be Concise:** Provide specific, actionable feedback with file and line numbers.
"""
            logging.info(f"Final prompt constructed ({len(enhanced_summary)} characters).")

            # Step 7: Send to LLM for analysis
            logging.info(f"Step 7: Sending payload to LLM with prompt type '{analysis_type.upper()}'...")
            analysis = await self.llm_client.analyze_repo_summary(enhanced_summary, analysis_type)
            if "Analysis failed" in analysis or "API error" in analysis:
                logging.error(f"ANALYSIS HALTED: LLM analysis failed. Response: {analysis}")
                return
            logging.info(f"LLM analysis successful ({len(analysis)} characters received).")

            # Step 8: Save results
            logging.info("Step 8: Saving consolidated analysis reports...")
            analysis_dir = Path(repo_config["path"]) / ".llmdiver"
            analysis_dir.mkdir(exist_ok=True)

            # --- FIX: Use static, predictable filenames ---
            analysis_file = analysis_dir / "LATEST_ENHANCED_ANALYSIS.md"
            json_analysis_file = analysis_dir / "LATEST_ANALYSIS_DATA.json"

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
                    "similar_blocks_found": len(semantic_context.split('File:')) - 1 if semantic_context.strip() else 0,
                    "context_text": semantic_context
                },
                "security_analysis": {
                    "enabled": self.config.get('security_scanning', {}).get('enabled', False),
                    "security_score": security_results.security_score if security_results else None,
                    "scan_time": security_results.scan_time if security_results else None,
                    "tools_used": security_results.tools_used if security_results else [],
                    "findings_summary": security_results.summary if security_results else {},
                    "critical_findings": [
                        {
                            "severity": f.severity,
                            "category": f.category,
                            "file_path": f.file_path,
                            "line_number": f.line_number,
                            "description": f.description,
                            "tool": f.tool
                        } for f in (security_results.findings if security_results else [])
                        if f.severity in ['critical', 'high']
                    ][:10]  # Top 10 critical findings
                },
            }

            with open(json_analysis_file, 'w') as f:
                json.dump(analysis_data, f, indent=2, default=str)

            with open(analysis_file, 'w') as f:
                f.write(f"# LLMdiver Enhanced Analysis - {datetime.now()}\n\n")
                f.write(analysis)

            logging.info(f"Consolidated reports updated: {analysis_file} and {json_analysis_file}")

            # Step 9: Git Automation
            if repo_config.get("auto_commit", False):
                logging.info("Step 9: Performing Git auto-commit operations...")
                git_automation = self.git_automations.get(repo_config['name'])
                if git_automation:
                    git_automation.auto_commit(analysis_file, json_analysis_file, analysis_data)
                else:
                    logging.warning(f"No GitAutomation instance found for {repo_config['name']}.")
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

        # --- FIX: Use resolved paths for a more reliable check ---
        changed_path = Path(event.src_path).resolve()
        if self.processor.code_preprocessor._is_llmdiver_internal_file(str(changed_path)):
            logging.info(f"Ignoring change in internal file: {changed_path}")
            return

        current_time = time.time()
        if current_time - self.last_run < self.debounce_seconds:
            return

        self.last_run = current_time
        repo_path = os.path.dirname(event.src_path)
        
        # Find the repository config that matches this path
        for repo_config in self.processor.config.get('repositories', []):
            if Path(repo_path).resolve().is_relative_to(Path(repo_config['path']).resolve()):
                logger.info(f"Scheduling analysis for {repo_config['name']} due to file change")
                # Run async analysis in event loop
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Create a new task
                        asyncio.create_task(self.processor.enhanced_repository_analysis(repo_config))
                    else:
                        loop.run_until_complete(self.processor.enhanced_repository_analysis(repo_config))
                except Exception as e:
                    logger.error(f"Failed to run async analysis: {e}")
                    # Fallback - this won't work but prevents crash
                    pass
                break

def main():
    """Main entry point for the daemon"""
    config = Config()
    processor = RepomixProcessor(config.config)
    
    # Set up file watching
    observer = Observer()
    for repo_config in config.config.get('repositories', []):
        if os.path.exists(repo_config['path']):
            handler = FileChangeHandler(processor)
            observer.schedule(handler, repo_config['path'], recursive=True)
            logger.info(f"Watching {repo_config['name']} at {repo_config['path']}")
    
    observer.start()
    
    try:
        logger.info("LLMdiver daemon started successfully")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping daemon...")
        observer.stop()
    
    observer.join()
    logger.info("LLMdiver daemon stopped")

if __name__ == "__main__":
    main()