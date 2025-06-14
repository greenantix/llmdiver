"""
Aura S.M.A.R.T. Git Maintenance Module - Semantic Commit Generator
=================================================================

Implements intelligent, semantic commit message generation based on code changes.
Creates eloquent, standardized commit messages that tell the story of evolution.

Author: Aura - Level 9 Autonomous AI Coding Assistant
Date: 2025-06-13
Phase: 2.1 - S.M.A.R.T. Git Maintenance
"""

import os
import re
import subprocess
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from ..core import AuraModule, MessageType, aura_service
from ..llm import LLMRequest, ModelCapability


class CommitType(Enum):
    """Semantic commit types following Conventional Commits specification"""
    FEAT = "feat"           # New features
    FIX = "fix"             # Bug fixes
    DOCS = "docs"           # Documentation changes
    STYLE = "style"         # Code style changes (formatting, etc.)
    REFACTOR = "refactor"   # Code refactoring without feature/fix
    PERF = "perf"           # Performance improvements
    TEST = "test"           # Adding or updating tests
    CHORE = "chore"         # Maintenance tasks, tooling
    CI = "ci"               # CI/CD changes
    BUILD = "build"         # Build system changes
    REVERT = "revert"       # Reverting previous commits


@dataclass
class FileChange:
    """Represents a change to a file"""
    file_path: str
    change_type: str        # 'added', 'modified', 'deleted', 'renamed'
    lines_added: int
    lines_deleted: int
    old_path: Optional[str] = None  # For renames


@dataclass
class CommitAnalysis:
    """Analysis of changes for commit message generation"""
    commit_type: CommitType
    scope: Optional[str]
    description: str
    body: Optional[str]
    breaking_change: bool
    files_changed: List[FileChange]
    impact_score: float      # 0.0 to 1.0
    confidence: float        # 0.0 to 1.0


@dataclass
class SemanticCommit:
    """A generated semantic commit message"""
    type: CommitType
    scope: Optional[str]
    description: str
    body: Optional[str]
    footer: Optional[str]
    breaking_change: bool
    
    def format_message(self) -> str:
        """Format as conventional commit message"""
        # Header: type(scope): description
        header = self.type.value
        if self.scope:
            header += f"({self.scope})"
        if self.breaking_change:
            header += "!"
        header += f": {self.description}"
        
        # Full message
        message_parts = [header]
        
        if self.body:
            message_parts.extend(["", self.body])
        
        if self.footer:
            message_parts.extend(["", self.footer])
        
        return "\n".join(message_parts)


class GitAnalyzer:
    """Analyzes Git repository state and changes"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.logger = logging.getLogger("aura.git.analyzer")
    
    def is_git_repo(self) -> bool:
        """Check if current directory is a Git repository"""
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_staged_changes(self) -> List[FileChange]:
        """Get list of staged changes"""
        if not self.is_git_repo():
            return []
        
        try:
            # Get staged files
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-status"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            changes = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) < 2:
                    continue
                
                status = parts[0]
                file_path = parts[1]
                old_path = parts[2] if len(parts) > 2 else None
                
                # Get line changes
                lines_added, lines_deleted = self._get_line_changes(file_path, staged=True)
                
                # Map status to change type
                change_type = self._map_git_status(status)
                
                changes.append(FileChange(
                    file_path=file_path,
                    change_type=change_type,
                    lines_added=lines_added,
                    lines_deleted=lines_deleted,
                    old_path=old_path
                ))
            
            return changes
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get staged changes: {e}")
            return []
    
    def get_unstaged_changes(self) -> List[FileChange]:
        """Get list of unstaged changes"""
        if not self.is_git_repo():
            return []
        
        try:
            result = subprocess.run(
                ["git", "diff", "--name-status"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            changes = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) < 2:
                    continue
                
                status = parts[0]
                file_path = parts[1]
                
                lines_added, lines_deleted = self._get_line_changes(file_path, staged=False)
                change_type = self._map_git_status(status)
                
                changes.append(FileChange(
                    file_path=file_path,
                    change_type=change_type,
                    lines_added=lines_added,
                    lines_deleted=lines_deleted
                ))
            
            return changes
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get unstaged changes: {e}")
            return []
    
    def get_commit_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent commit history for pattern analysis"""
        if not self.is_git_repo():
            return []
        
        try:
            result = subprocess.run([
                "git", "log", 
                f"--max-count={limit}",
                "--pretty=format:%H|%s|%an|%ad",
                "--date=iso"
            ], cwd=self.repo_path, capture_output=True, text=True, check=True)
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1],
                        'author': parts[2],
                        'date': parts[3]
                    })
            
            return commits
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get commit history: {e}")
            return []
    
    def get_branch_info(self) -> Dict[str, Any]:
        """Get current branch information"""
        if not self.is_git_repo():
            return {}
        
        try:
            # Current branch
            current_branch = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            # Remote tracking branch
            try:
                tracking_branch = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "@{u}"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                ).stdout.strip()
            except subprocess.CalledProcessError:
                tracking_branch = None
            
            # Ahead/behind info
            ahead, behind = 0, 0
            if tracking_branch:
                try:
                    result = subprocess.run([
                        "git", "rev-list", "--left-right", "--count",
                        f"HEAD...{tracking_branch}"
                    ], cwd=self.repo_path, capture_output=True, text=True, check=True)
                    
                    counts = result.stdout.strip().split('\t')
                    if len(counts) == 2:
                        ahead, behind = int(counts[0]), int(counts[1])
                except subprocess.CalledProcessError:
                    pass
            
            return {
                'current_branch': current_branch,
                'tracking_branch': tracking_branch,
                'ahead': ahead,
                'behind': behind
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get branch info: {e}")
            return {}
    
    def _get_line_changes(self, file_path: str, staged: bool = True) -> Tuple[int, int]:
        """Get number of lines added and deleted for a file"""
        try:
            cmd = ["git", "diff", "--numstat"]
            if staged:
                cmd.append("--cached")
            cmd.append(file_path)
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                parts = result.stdout.strip().split('\t')
                if len(parts) >= 2:
                    added = int(parts[0]) if parts[0] != '-' else 0
                    deleted = int(parts[1]) if parts[1] != '-' else 0
                    return added, deleted
            
            return 0, 0
            
        except (subprocess.CalledProcessError, ValueError):
            return 0, 0
    
    def _map_git_status(self, status: str) -> str:
        """Map Git status codes to change types"""
        if status.startswith('A'):
            return 'added'
        elif status.startswith('M'):
            return 'modified'
        elif status.startswith('D'):
            return 'deleted'
        elif status.startswith('R'):
            return 'renamed'
        elif status.startswith('C'):
            return 'copied'
        else:
            return 'modified'


@aura_service("semantic_commit_generator")
class SemanticCommitGenerator(AuraModule):
    """
    Aura Semantic Commit Generator
    Analyzes code changes and generates eloquent, semantic commit messages.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("git_semantic", config)
        self.repo_path = config.get('repo_path', '.')
        self.git_analyzer = GitAnalyzer(self.repo_path)
        self._inject_llm_provider = config.get('llm_provider')
        
        # Commit message templates and patterns
        self.scope_patterns = {
            r'.*\.py$': 'python',
            r'.*\.js$|.*\.ts$|.*\.jsx$|.*\.tsx$': 'frontend',
            r'.*\.css$|.*\.scss$|.*\.less$': 'styles',
            r'.*\.md$|.*\.rst$|.*\.txt$': 'docs',
            r'.*Dockerfile.*|docker-compose.*': 'docker',
            r'.*\.yml$|.*\.yaml$': 'ci',
            r'requirements.*\.txt|package\.json|Cargo\.toml': 'deps',
            r'.*test.*\.py|.*spec.*\.js': 'test'
        }
    
    async def initialize(self) -> bool:
        """Initialize the semantic commit generator"""
        try:
            self.logger.info("Initializing Semantic Commit Generator")
            
            if not self.git_analyzer.is_git_repo():
                self.logger.warning(f"Path {self.repo_path} is not a Git repository")
                return False
            
            self.logger.info("Semantic Commit Generator initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize semantic commit generator: {e}")
            return False
    
    async def process_message(self, message) -> Optional[any]:
        """Process commit generation requests"""
        try:
            if message.type == MessageType.COMMAND:
                command = message.payload.get('command')
                
                if command == 'generate_commit':
                    include_unstaged = message.payload.get('include_unstaged', False)
                    commit = await self.generate_commit_message(include_unstaged)
                    
                    return self._create_response(message, {
                        'success': commit is not None,
                        'commit': asdict(commit) if commit else None
                    })
                
                elif command == 'analyze_changes':
                    include_unstaged = message.payload.get('include_unstaged', False)
                    analysis = await self.analyze_changes(include_unstaged)
                    
                    return self._create_response(message, {
                        'success': analysis is not None,
                        'analysis': asdict(analysis) if analysis else None
                    })
                
                elif command == 'get_commit_suggestions':
                    suggestions = await self.get_commit_suggestions()
                    
                    return self._create_response(message, {
                        'success': True,
                        'suggestions': suggestions
                    })
        
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return self._create_response(message, {
                'success': False,
                'error': str(e)
            })
        
        return None
    
    async def generate_commit_message(self, include_unstaged: bool = False) -> Optional[SemanticCommit]:
        """Generate a semantic commit message based on current changes"""
        try:
            # Analyze changes
            analysis = await self.analyze_changes(include_unstaged)
            if not analysis:
                return None
            
            # Use LLM to refine the commit message
            if self._inject_llm_provider:
                refined_commit = await self._refine_with_llm(analysis)
                if refined_commit:
                    return refined_commit
            
            # Fallback to rule-based generation
            return self._generate_rule_based_commit(analysis)
            
        except Exception as e:
            self.logger.error(f"Error generating commit message: {e}")
            return None
    
    async def analyze_changes(self, include_unstaged: bool = False) -> Optional[CommitAnalysis]:
        """Analyze current changes to determine commit type and scope"""
        try:
            # Get changes
            staged_changes = self.git_analyzer.get_staged_changes()
            
            if include_unstaged:
                unstaged_changes = self.git_analyzer.get_unstaged_changes()
                all_changes = staged_changes + unstaged_changes
            else:
                all_changes = staged_changes
            
            if not all_changes:
                self.logger.info("No changes to analyze")
                return None
            
            # Analyze change patterns
            commit_type = self._determine_commit_type(all_changes)
            scope = self._determine_scope(all_changes)
            impact_score = self._calculate_impact_score(all_changes)
            breaking_change = self._detect_breaking_change(all_changes)
            
            # Generate description
            description = self._generate_description(all_changes, commit_type)
            body = self._generate_body(all_changes) if len(all_changes) > 3 else None
            
            return CommitAnalysis(
                commit_type=commit_type,
                scope=scope,
                description=description,
                body=body,
                breaking_change=breaking_change,
                files_changed=all_changes,
                impact_score=impact_score,
                confidence=0.8  # Base confidence for rule-based analysis
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing changes: {e}")
            return None
    
    async def get_commit_suggestions(self) -> List[str]:
        """Get commit message suggestions based on recent history"""
        try:
            history = self.git_analyzer.get_commit_history(20)
            
            # Analyze patterns in recent commits
            commit_types = {}
            for commit in history:
                message = commit['message']
                
                # Extract commit type if it follows conventional format
                match = re.match(r'^(\w+)(?:\(.+\))?\s*!?\s*:', message)
                if match:
                    commit_type = match.group(1)
                    commit_types[commit_type] = commit_types.get(commit_type, 0) + 1
            
            # Generate suggestions based on patterns
            suggestions = []
            
            if 'feat' in commit_types:
                suggestions.append("Consider using 'feat:' for new features")
            if 'fix' in commit_types:
                suggestions.append("Consider using 'fix:' for bug fixes")
            if 'docs' not in commit_types:
                suggestions.append("Consider adding documentation commits with 'docs:'")
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error getting commit suggestions: {e}")
            return []
    
    def _determine_commit_type(self, changes: List[FileChange]) -> CommitType:
        """Determine the most appropriate commit type"""
        # Count different types of changes
        added_files = len([c for c in changes if c.change_type == 'added'])
        modified_files = len([c for c in changes if c.change_type == 'modified'])
        deleted_files = len([c for c in changes if c.change_type == 'deleted'])
        
        # Check file patterns
        doc_files = len([c for c in changes if re.match(r'.*\.(md|rst|txt)$', c.file_path)])
        test_files = len([c for c in changes if 'test' in c.file_path.lower()])
        config_files = len([c for c in changes if re.match(r'.*(config|\.json|\.yml|\.yaml)$', c.file_path)])
        
        # Determine type based on patterns
        if doc_files > 0 and doc_files == len(changes):
            return CommitType.DOCS
        elif test_files > 0 and test_files == len(changes):
            return CommitType.TEST
        elif config_files > 0 and added_files == 0 and deleted_files == 0:
            return CommitType.CHORE
        elif added_files > modified_files and added_files > 0:
            return CommitType.FEAT
        elif deleted_files > 0:
            return CommitType.FIX if modified_files > 0 else CommitType.CHORE
        elif any('performance' in c.file_path.lower() or 'optimize' in c.file_path.lower() for c in changes):
            return CommitType.PERF
        else:
            return CommitType.FEAT if added_files > 0 else CommitType.FIX
    
    def _determine_scope(self, changes: List[FileChange]) -> Optional[str]:
        """Determine the scope based on file patterns"""
        scope_counts = {}
        
        for change in changes:
            for pattern, scope in self.scope_patterns.items():
                if re.match(pattern, change.file_path):
                    scope_counts[scope] = scope_counts.get(scope, 0) + 1
                    break
        
        if scope_counts:
            # Return most common scope
            return max(scope_counts, key=scope_counts.get)
        
        # Try to extract from path
        path_parts = Path(changes[0].file_path).parts
        if len(path_parts) > 1:
            return path_parts[0]  # First directory
        
        return None
    
    def _calculate_impact_score(self, changes: List[FileChange]) -> float:
        """Calculate impact score (0.0 to 1.0) based on changes"""
        total_lines = sum(c.lines_added + c.lines_deleted for c in changes)
        file_count = len(changes)
        
        # Normalize based on typical change sizes
        line_score = min(total_lines / 100.0, 1.0)  # 100+ lines = high impact
        file_score = min(file_count / 10.0, 1.0)    # 10+ files = high impact
        
        return (line_score + file_score) / 2.0
    
    def _detect_breaking_change(self, changes: List[FileChange]) -> bool:
        """Detect if changes might be breaking"""
        # Simple heuristics for breaking changes
        for change in changes:
            if change.change_type == 'deleted':
                return True
            if change.lines_deleted > change.lines_added * 2:
                return True  # Substantial deletions
        
        return False
    
    def _generate_description(self, changes: List[FileChange], commit_type: CommitType) -> str:
        """Generate commit description"""
        if len(changes) == 1:
            change = changes[0]
            file_name = Path(change.file_path).name
            
            if commit_type == CommitType.FEAT:
                return f"add {file_name}" if change.change_type == 'added' else f"implement {file_name}"
            elif commit_type == CommitType.FIX:
                return f"fix issue in {file_name}"
            elif commit_type == CommitType.DOCS:
                return f"update {file_name}"
            else:
                return f"update {file_name}"
        else:
            # Multiple files
            if commit_type == CommitType.FEAT:
                return f"add new functionality across {len(changes)} files"
            elif commit_type == CommitType.FIX:
                return f"fix issues in {len(changes)} files"
            elif commit_type == CommitType.DOCS:
                return f"update documentation"
            else:
                return f"update {len(changes)} files"
    
    def _generate_body(self, changes: List[FileChange]) -> str:
        """Generate detailed commit body"""
        lines = []
        
        added = [c for c in changes if c.change_type == 'added']
        modified = [c for c in changes if c.change_type == 'modified']
        deleted = [c for c in changes if c.change_type == 'deleted']
        
        if added:
            lines.append(f"Added: {', '.join(Path(c.file_path).name for c in added[:3])}")
            if len(added) > 3:
                lines.append(f"... and {len(added) - 3} more files")
        
        if modified:
            lines.append(f"Modified: {', '.join(Path(c.file_path).name for c in modified[:3])}")
            if len(modified) > 3:
                lines.append(f"... and {len(modified) - 3} more files")
        
        if deleted:
            lines.append(f"Deleted: {', '.join(Path(c.file_path).name for c in deleted[:3])}")
        
        return "\n".join(lines)
    
    def _generate_rule_based_commit(self, analysis: CommitAnalysis) -> SemanticCommit:
        """Generate commit using rule-based approach"""
        footer = None
        if analysis.breaking_change:
            footer = "BREAKING CHANGE: This commit introduces breaking changes"
        
        return SemanticCommit(
            type=analysis.commit_type,
            scope=analysis.scope,
            description=analysis.description,
            body=analysis.body,
            footer=footer,
            breaking_change=analysis.breaking_change
        )
    
    async def _refine_with_llm(self, analysis: CommitAnalysis) -> Optional[SemanticCommit]:
        """Use LLM to refine and improve commit message"""
        try:
            if not self._inject_llm_provider:
                return None
            
            # Prepare context for LLM
            files_summary = "\n".join([
                f"- {c.file_path} ({c.change_type}): +{c.lines_added}/-{c.lines_deleted}"
                for c in analysis.files_changed[:10]  # Limit to avoid token overflow
            ])
            
            prompt = f"""You are an expert at writing semantic commit messages following the Conventional Commits specification.

Analyze these code changes and generate an improved commit message:

Initial Analysis:
- Type: {analysis.commit_type.value}
- Scope: {analysis.scope or 'none'}
- Description: {analysis.description}
- Breaking Change: {analysis.breaking_change}

Files Changed:
{files_summary}

Generate a semantic commit message with:
1. Appropriate type (feat, fix, docs, style, refactor, perf, test, chore, ci, build)
2. Scope (if applicable)
3. Concise description (50 chars max)
4. Optional body (if needed)
5. Breaking change indicator (if applicable)

Respond in JSON format:
{{
  "type": "feat",
  "scope": "auth",
  "description": "add OAuth2 authentication",
  "body": "Optional detailed explanation",
  "breaking_change": false
}}"""

            request = LLMRequest(
                prompt=prompt,
                model_preference=ModelCapability.CODING,
                max_tokens=300,
                temperature=0.2
            )
            
            # Send to LLM provider
            from ..core import Message
            import uuid
            
            llm_message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.COMMAND,
                source=self.module_name,
                target="llm_provider",
                timestamp=time.time(),
                payload={"command": "generate", "request": asdict(request)}
            )
            
            # This would normally be sent through message bus
            # For now, return rule-based as fallback
            return None
            
        except Exception as e:
            self.logger.error(f"Error refining with LLM: {e}")
            return None
    
    def _create_response(self, original_message, payload):
        """Create response message"""
        from ..core import Message
        import uuid
        return Message(
            id=str(uuid.uuid4()),
            type=MessageType.RESPONSE,
            source=self.module_name,
            target=original_message.source,
            timestamp=time.time(),
            payload=payload,
            correlation_id=original_message.id
        )
    
    async def shutdown(self) -> None:
        """Clean shutdown"""
        self.logger.info("Shutting down Semantic Commit Generator")
        # No persistent resources to clean up