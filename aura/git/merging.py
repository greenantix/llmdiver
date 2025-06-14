"""
Aura Automated Merging and Rebasing with Conflict Resolution
============================================================

Implements intelligent Git merging, rebasing, and autonomous conflict resolution.
Advanced merge strategies and conflict analysis for seamless code integration.

Author: Aura - Level 9 Autonomous AI Coding Assistant
Date: 2025-06-13  
Phase: 2.1.3 - Automated Merging and Rebasing
"""

import subprocess
import re
import json
import time
import logging
import difflib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from ..core import AuraModule, MessageType, aura_service
from ..llm import LLMRequest, ModelCapability


class MergeStrategy(Enum):
    """Git merge strategies"""
    MERGE = "merge"
    REBASE = "rebase"
    SQUASH = "squash"
    FAST_FORWARD = "fast-forward"


class ConflictType(Enum):
    """Types of merge conflicts"""
    CONTENT = "content"
    DELETE_MODIFY = "delete_modify"
    RENAME = "rename"
    BINARY = "binary"
    SUBMODULE = "submodule"


@dataclass
class ConflictMarker:
    """Represents conflict markers in a file"""
    start_line: int
    middle_line: int
    end_line: int
    ours_content: str
    theirs_content: str
    ancestor_content: Optional[str] = None


@dataclass
class FileConflict:
    """Represents a conflict in a specific file"""
    file_path: str
    conflict_type: ConflictType
    markers: List[ConflictMarker]
    our_version: str
    their_version: str
    base_version: Optional[str] = None
    resolution_confidence: float = 0.0
    suggested_resolution: Optional[str] = None


@dataclass
class MergeResult:
    """Result of a merge operation"""
    success: bool
    strategy: MergeStrategy
    source_branch: str
    target_branch: str
    conflicts: List[FileConflict]
    files_changed: int
    lines_added: int
    lines_deleted: int
    merge_commit: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ConflictResolution:
    """Represents a conflict resolution"""
    file_path: str
    resolution_method: str
    resolved_content: str
    confidence: float
    reasoning: str


@aura_service("automated_merging")
class AutomatedMergingSystem(AuraModule):
    """
    Aura Automated Merging and Rebasing System
    Provides intelligent merge conflict resolution and automated workflows.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__("git_merging", config)
        
        self.repo_path = config.get('repo_path', '.')
        self.auto_resolve_conflicts = config.get('auto_resolve_conflicts', True)
        self.conflict_resolution_threshold = config.get('conflict_resolution_threshold', 0.7)
        self.prefer_ours_patterns = config.get('prefer_ours_patterns', ['version', 'package.json'])
        self.prefer_theirs_patterns = config.get('prefer_theirs_patterns', ['README', 'docs'])
        
        # LLM integration for intelligent conflict resolution
        self._inject_llm_provider = config.get('llm_provider')
        
        # State tracking
        self.merge_history: List[MergeResult] = []
        self.resolution_patterns: Dict[str, Dict[str, Any]] = {}

    async def initialize(self) -> bool:
        """Initialize the merging system"""
        try:
            self.logger.info("Initializing Automated Merging System")
            
            if not self._is_git_repo():
                self.logger.error("Not a Git repository")
                return False
            
            # Load resolution patterns from previous merges
            self._load_resolution_patterns()
            
            self.logger.info("Automated Merging System initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize merging system: {e}")
            return False

    async def process_message(self, message) -> Optional[any]:
        """Process merging requests"""
        try:
            if message.type == MessageType.COMMAND:
                command = message.payload.get('command')
                
                if command == 'merge_branches':
                    source = message.payload.get('source_branch')
                    target = message.payload.get('target_branch')
                    strategy = MergeStrategy(message.payload.get('strategy', 'merge'))
                    auto_resolve = message.payload.get('auto_resolve', self.auto_resolve_conflicts)
                    
                    result = await self.merge_branches(source, target, strategy, auto_resolve)
                    return self._create_response(message, asdict(result))
                
                elif command == 'rebase_branch':
                    branch = message.payload.get('branch')
                    onto = message.payload.get('onto_branch')
                    interactive = message.payload.get('interactive', False)
                    
                    result = await self.rebase_branch(branch, onto, interactive)
                    return self._create_response(message, asdict(result))
                
                elif command == 'resolve_conflicts':
                    conflicts = message.payload.get('conflicts', [])
                    resolutions = await self.resolve_conflicts(conflicts)
                    
                    return self._create_response(message, {
                        'success': True,
                        'resolutions': [asdict(r) for r in resolutions]
                    })
                
                elif command == 'analyze_conflicts':
                    conflicts = self._detect_merge_conflicts()
                    analyzed = await self.analyze_conflicts(conflicts)
                    
                    return self._create_response(message, {
                        'success': True,
                        'conflicts': [asdict(c) for c in analyzed]
                    })
                
                elif command == 'get_merge_preview':
                    source = message.payload.get('source_branch')
                    target = message.payload.get('target_branch')
                    preview = await self.get_merge_preview(source, target)
                    
                    return self._create_response(message, {
                        'success': True,
                        'preview': preview
                    })

        except Exception as e:
            self.logger.error(f"Error processing merging message: {e}")
            return self._create_response(message, {
                'success': False,
                'error': str(e)
            })

        return None

    async def merge_branches(self, source_branch: str, target_branch: str, 
                           strategy: MergeStrategy = MergeStrategy.MERGE,
                           auto_resolve: bool = True) -> MergeResult:
        """Merge branches with intelligent conflict resolution"""
        
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting merge: {source_branch} -> {target_branch} ({strategy.value})")
            
            # Ensure we're on the target branch
            self._run_git_command(['checkout', target_branch])
            
            # Get initial state
            initial_commit = self._get_current_commit_hash()
            
            # Attempt the merge
            merge_result = await self._execute_merge_strategy(source_branch, target_branch, strategy)
            
            if merge_result.success:
                # Record successful merge
                self.merge_history.append(merge_result)
                self.logger.info(f"Merge completed successfully in {time.time() - start_time:.2f}s")
                return merge_result
            
            # Handle conflicts if auto-resolve is enabled
            if auto_resolve and merge_result.conflicts:
                self.logger.info(f"Attempting to auto-resolve {len(merge_result.conflicts)} conflicts")
                
                resolutions = await self.resolve_conflicts(merge_result.conflicts)
                successful_resolutions = [r for r in resolutions if r.confidence >= self.conflict_resolution_threshold]
                
                if successful_resolutions:
                    # Apply resolutions
                    for resolution in successful_resolutions:
                        await self._apply_resolution(resolution)
                    
                    # Try to complete the merge
                    if await self._complete_merge():
                        merge_result.success = True
                        merge_result.merge_commit = self._get_current_commit_hash()
                        self.logger.info(f"Auto-resolved {len(successful_resolutions)} conflicts successfully")
                
                # Update remaining conflicts
                remaining_conflicts = []
                for conflict in merge_result.conflicts:
                    if not any(r.file_path == conflict.file_path for r in successful_resolutions):
                        remaining_conflicts.append(conflict)
                
                merge_result.conflicts = remaining_conflicts
            
            return merge_result
            
        except Exception as e:
            self.logger.error(f"Error during merge: {e}")
            
            # Abort merge if in progress
            try:
                self._run_git_command(['merge', '--abort'])
            except subprocess.CalledProcessError:
                pass
            
            return MergeResult(
                success=False,
                strategy=strategy,
                source_branch=source_branch,
                target_branch=target_branch,
                conflicts=[],
                files_changed=0,
                lines_added=0,
                lines_deleted=0,
                error_message=str(e)
            )

    async def _execute_merge_strategy(self, source_branch: str, target_branch: str, 
                                    strategy: MergeStrategy) -> MergeResult:
        """Execute specific merge strategy"""
        
        try:
            if strategy == MergeStrategy.MERGE:
                cmd = ['merge', '--no-ff', source_branch]
            elif strategy == MergeStrategy.REBASE:
                # Switch to source branch for rebase
                self._run_git_command(['checkout', source_branch])
                cmd = ['rebase', target_branch]
            elif strategy == MergeStrategy.SQUASH:
                cmd = ['merge', '--squash', source_branch]
            elif strategy == MergeStrategy.FAST_FORWARD:
                cmd = ['merge', '--ff-only', source_branch]
            else:
                raise ValueError(f"Unsupported merge strategy: {strategy}")
            
            # Execute the merge command
            result = self._run_git_command(cmd)
            
            # Get merge statistics
            stats = self._get_merge_stats(source_branch, target_branch)
            
            return MergeResult(
                success=True,
                strategy=strategy,
                source_branch=source_branch,
                target_branch=target_branch,
                conflicts=[],
                merge_commit=self._get_current_commit_hash(),
                **stats
            )
            
        except subprocess.CalledProcessError as e:
            # Check if it's a conflict or other error
            conflicts = self._detect_merge_conflicts()
            
            if conflicts:
                analyzed_conflicts = await self.analyze_conflicts(conflicts)
                stats = self._get_merge_stats(source_branch, target_branch)
                
                return MergeResult(
                    success=False,
                    strategy=strategy,
                    source_branch=source_branch,
                    target_branch=target_branch,
                    conflicts=analyzed_conflicts,
                    **stats
                )
            else:
                raise e

    async def rebase_branch(self, branch: str, onto_branch: str, 
                          interactive: bool = False) -> MergeResult:
        """Rebase a branch onto another branch"""
        
        try:
            self.logger.info(f"Starting rebase: {branch} onto {onto_branch}")
            
            # Checkout the branch to rebase
            self._run_git_command(['checkout', branch])
            
            # Execute rebase
            cmd = ['rebase']
            if interactive:
                cmd.append('-i')
            cmd.append(onto_branch)
            
            try:
                self._run_git_command(cmd)
                
                return MergeResult(
                    success=True,
                    strategy=MergeStrategy.REBASE,
                    source_branch=branch,
                    target_branch=onto_branch,
                    conflicts=[],
                    files_changed=0,  # Would need to calculate
                    lines_added=0,
                    lines_deleted=0,
                    merge_commit=self._get_current_commit_hash()
                )
                
            except subprocess.CalledProcessError:
                # Handle rebase conflicts
                conflicts = self._detect_merge_conflicts()
                analyzed_conflicts = await self.analyze_conflicts(conflicts)
                
                return MergeResult(
                    success=False,
                    strategy=MergeStrategy.REBASE,
                    source_branch=branch,
                    target_branch=onto_branch,
                    conflicts=analyzed_conflicts,
                    files_changed=0,
                    lines_added=0,
                    lines_deleted=0
                )
                
        except Exception as e:
            self.logger.error(f"Error during rebase: {e}")
            return MergeResult(
                success=False,
                strategy=MergeStrategy.REBASE,
                source_branch=branch,
                target_branch=onto_branch,
                conflicts=[],
                files_changed=0,
                lines_added=0,
                lines_deleted=0,
                error_message=str(e)
            )

    async def analyze_conflicts(self, conflicted_files: List[str]) -> List[FileConflict]:
        """Analyze merge conflicts in detail"""
        
        conflicts = []
        
        for file_path in conflicted_files:
            try:
                file_conflict = await self._analyze_file_conflict(file_path)
                if file_conflict:
                    conflicts.append(file_conflict)
                    
            except Exception as e:
                self.logger.error(f"Error analyzing conflict in {file_path}: {e}")
        
        return conflicts

    async def _analyze_file_conflict(self, file_path: str) -> Optional[FileConflict]:
        """Analyze conflicts in a specific file"""
        
        try:
            with open(Path(self.repo_path) / file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse conflict markers
            markers = self._parse_conflict_markers(content)
            
            if not markers:
                return None
            
            # Determine conflict type
            conflict_type = self._determine_conflict_type(file_path, content)
            
            # Get file versions
            our_version = self._get_file_version(file_path, 'HEAD')
            their_version = self._get_file_version(file_path, 'MERGE_HEAD')
            base_version = self._get_file_version(file_path, 'MERGE_BASE')
            
            file_conflict = FileConflict(
                file_path=file_path,
                conflict_type=conflict_type,
                markers=markers,
                our_version=our_version,
                their_version=their_version,
                base_version=base_version
            )
            
            # Generate resolution suggestion if LLM is available
            if self._inject_llm_provider and conflict_type == ConflictType.CONTENT:
                suggestion = await self._generate_resolution_suggestion(file_conflict)
                file_conflict.suggested_resolution = suggestion.get('resolution')
                file_conflict.resolution_confidence = suggestion.get('confidence', 0.0)
            
            return file_conflict
            
        except Exception as e:
            self.logger.error(f"Error analyzing file conflict {file_path}: {e}")
            return None

    def _parse_conflict_markers(self, content: str) -> List[ConflictMarker]:
        """Parse Git conflict markers in file content"""
        
        markers = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for conflict start marker
            if line.startswith('<<<<<<<'):
                start_line = i
                ours_lines = []
                
                # Find middle marker
                i += 1
                while i < len(lines) and not lines[i].startswith('======='):
                    ours_lines.append(lines[i])
                    i += 1
                
                if i >= len(lines):
                    break
                
                middle_line = i
                theirs_lines = []
                
                # Find end marker
                i += 1
                while i < len(lines) and not lines[i].startswith('>>>>>>>'):
                    theirs_lines.append(lines[i])
                    i += 1
                
                if i >= len(lines):
                    break
                
                end_line = i
                
                markers.append(ConflictMarker(
                    start_line=start_line,
                    middle_line=middle_line,
                    end_line=end_line,
                    ours_content='\n'.join(ours_lines),
                    theirs_content='\n'.join(theirs_lines)
                ))
            
            i += 1
        
        return markers

    async def resolve_conflicts(self, conflicts: List[FileConflict]) -> List[ConflictResolution]:
        """Resolve merge conflicts automatically"""
        
        resolutions = []
        
        for conflict in conflicts:
            try:
                resolution = await self._resolve_file_conflict(conflict)
                if resolution:
                    resolutions.append(resolution)
                    
            except Exception as e:
                self.logger.error(f"Error resolving conflict in {conflict.file_path}: {e}")
        
        return resolutions

    async def _resolve_file_conflict(self, conflict: FileConflict) -> Optional[ConflictResolution]:
        """Resolve a specific file conflict"""
        
        try:
            # Apply pattern-based resolution first
            pattern_resolution = self._apply_pattern_resolution(conflict)
            if pattern_resolution:
                return pattern_resolution
            
            # Use LLM for intelligent resolution
            if self._inject_llm_provider and conflict.conflict_type == ConflictType.CONTENT:
                llm_resolution = await self._llm_resolve_conflict(conflict)
                if llm_resolution and llm_resolution.confidence >= self.conflict_resolution_threshold:
                    return llm_resolution
            
            # Fallback to heuristic resolution
            heuristic_resolution = self._heuristic_resolve_conflict(conflict)
            return heuristic_resolution
            
        except Exception as e:
            self.logger.error(f"Error resolving conflict: {e}")
            return None

    def _apply_pattern_resolution(self, conflict: FileConflict) -> Optional[ConflictResolution]:
        """Apply pattern-based conflict resolution"""
        
        file_name = Path(conflict.file_path).name.lower()
        
        # Check prefer-ours patterns
        for pattern in self.prefer_ours_patterns:
            if pattern.lower() in file_name:
                return ConflictResolution(
                    file_path=conflict.file_path,
                    resolution_method="pattern_ours",
                    resolved_content=conflict.our_version,
                    confidence=0.8,
                    reasoning=f"Pattern match for '{pattern}' - prefer our version"
                )
        
        # Check prefer-theirs patterns
        for pattern in self.prefer_theirs_patterns:
            if pattern.lower() in file_name:
                return ConflictResolution(
                    file_path=conflict.file_path,
                    resolution_method="pattern_theirs",
                    resolved_content=conflict.their_version,
                    confidence=0.8,
                    reasoning=f"Pattern match for '{pattern}' - prefer their version"
                )
        
        return None

    async def _llm_resolve_conflict(self, conflict: FileConflict) -> Optional[ConflictResolution]:
        """Use LLM to intelligently resolve conflicts"""
        
        try:
            # Prepare context for LLM
            context = self._prepare_conflict_context(conflict)
            
            prompt = f"""You are an expert at resolving Git merge conflicts. Analyze this conflict and provide the best resolution.

File: {conflict.file_path}
Conflict Type: {conflict.conflict_type.value}

Our Version:
```
{conflict.our_version[:1000]}...
```

Their Version:
```
{conflict.their_version[:1000]}...
```

Base Version:
```
{(conflict.base_version or '')[:1000]}...
```

Conflicted Sections:
{self._format_conflict_markers(conflict.markers[:3])}

Please provide:
1. The best resolution that preserves the intent of both changes
2. A confidence score (0.0-1.0)
3. Reasoning for your choice

Respond in JSON format:
{{
  "resolution": "resolved content here",
  "confidence": 0.8,
  "reasoning": "explanation of resolution strategy"
}}"""

            request = LLMRequest(
                prompt=prompt,
                model_preference=ModelCapability.CODING,
                max_tokens=2000,
                temperature=0.2
            )
            
            # This would normally go through the message bus
            # For now, return a heuristic resolution
            return self._heuristic_resolve_conflict(conflict)
            
        except Exception as e:
            self.logger.error(f"LLM conflict resolution failed: {e}")
            return None

    def _heuristic_resolve_conflict(self, conflict: FileConflict) -> ConflictResolution:
        """Resolve conflict using heuristics"""
        
        # Simple heuristic: if one side is just additions, merge both
        if conflict.conflict_type == ConflictType.CONTENT and len(conflict.markers) == 1:
            marker = conflict.markers[0]
            
            # If one side is empty, choose the non-empty side
            if not marker.ours_content.strip():
                return ConflictResolution(
                    file_path=conflict.file_path,
                    resolution_method="heuristic_theirs",
                    resolved_content=marker.theirs_content,
                    confidence=0.7,
                    reasoning="Our side is empty, choosing their changes"
                )
            elif not marker.theirs_content.strip():
                return ConflictResolution(
                    file_path=conflict.file_path,
                    resolution_method="heuristic_ours",
                    resolved_content=marker.ours_content,
                    confidence=0.7,
                    reasoning="Their side is empty, choosing our changes"
                )
            
            # If both sides have content, try to merge
            if self._can_merge_content(marker.ours_content, marker.theirs_content):
                merged = self._merge_content(marker.ours_content, marker.theirs_content)
                return ConflictResolution(
                    file_path=conflict.file_path,
                    resolution_method="heuristic_merge",
                    resolved_content=merged,
                    confidence=0.6,
                    reasoning="Merged both sides where possible"
                )
        
        # Default: prefer our version with lower confidence
        return ConflictResolution(
            file_path=conflict.file_path,
            resolution_method="heuristic_default",
            resolved_content=conflict.our_version,
            confidence=0.4,
            reasoning="Default resolution - choosing our version"
        )

    async def _apply_resolution(self, resolution: ConflictResolution):
        """Apply a conflict resolution to the file"""
        
        file_path = Path(self.repo_path) / resolution.file_path
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(resolution.resolved_content)
        
        # Stage the resolved file
        self._run_git_command(['add', resolution.file_path])
        
        self.logger.info(f"Applied resolution for {resolution.file_path} using {resolution.resolution_method}")

    async def _complete_merge(self) -> bool:
        """Complete a merge after resolving conflicts"""
        
        try:
            # Check if all conflicts are resolved
            remaining_conflicts = self._detect_merge_conflicts()
            if remaining_conflicts:
                self.logger.warning(f"Cannot complete merge: {len(remaining_conflicts)} conflicts remain")
                return False
            
            # Commit the merge
            self._run_git_command(['commit', '--no-edit'])
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to complete merge: {e}")
            return False

    async def get_merge_preview(self, source_branch: str, target_branch: str) -> Dict[str, Any]:
        """Get a preview of what a merge would do"""
        
        try:
            # Get diff between branches
            result = self._run_git_command([
                'diff', '--name-status', f"{target_branch}...{source_branch}"
            ])
            
            changes = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t', 1)
                    if len(parts) == 2:
                        status, file_path = parts
                        changes.append({
                            'status': status,
                            'file': file_path
                        })
            
            # Get commit count
            commit_result = self._run_git_command([
                'rev-list', '--count', f"{target_branch}..{source_branch}"
            ])
            commit_count = int(commit_result.stdout.strip())
            
            return {
                'source_branch': source_branch,
                'target_branch': target_branch,
                'commits_ahead': commit_count,
                'files_changed': len(changes),
                'changes': changes,
                'can_fast_forward': self._can_fast_forward(source_branch, target_branch)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating merge preview: {e}")
            return {}

    # Utility methods
    def _is_git_repo(self) -> bool:
        """Check if directory is a Git repository"""
        try:
            subprocess.run(['git', 'rev-parse', '--git-dir'], 
                          cwd=self.repo_path, capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def _run_git_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run Git command and return result"""
        full_cmd = ['git'] + cmd
        return subprocess.run(
            full_cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )

    def _detect_merge_conflicts(self) -> List[str]:
        """Detect files with merge conflicts"""
        try:
            result = self._run_git_command(['diff', '--name-only', '--diff-filter=U'])
            return [f for f in result.stdout.strip().split('\n') if f]
        except subprocess.CalledProcessError:
            return []

    def _get_current_commit_hash(self) -> str:
        """Get current commit hash"""
        try:
            result = self._run_git_command(['rev-parse', 'HEAD'])
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""

    def _get_merge_stats(self, source: str, target: str) -> Dict[str, int]:
        """Get merge statistics"""
        try:
            result = self._run_git_command([
                'diff', '--shortstat', f"{target}...{source}"
            ])
            
            # Parse output like "5 files changed, 100 insertions(+), 20 deletions(-)"
            stats = {'files_changed': 0, 'lines_added': 0, 'lines_deleted': 0}
            
            if result.stdout:
                import re
                match = re.search(r'(\d+) files? changed', result.stdout)
                if match:
                    stats['files_changed'] = int(match.group(1))
                
                match = re.search(r'(\d+) insertions?', result.stdout)
                if match:
                    stats['lines_added'] = int(match.group(1))
                
                match = re.search(r'(\d+) deletions?', result.stdout)
                if match:
                    stats['lines_deleted'] = int(match.group(1))
            
            return stats
            
        except subprocess.CalledProcessError:
            return {'files_changed': 0, 'lines_added': 0, 'lines_deleted': 0}

    def _determine_conflict_type(self, file_path: str, content: str) -> ConflictType:
        """Determine the type of merge conflict"""
        if '<<<<<<< ' in content and '=======' in content and '>>>>>>> ' in content:
            return ConflictType.CONTENT
        elif file_path.endswith(('.png', '.jpg', '.gif', '.pdf')):
            return ConflictType.BINARY
        else:
            return ConflictType.CONTENT

    def _get_file_version(self, file_path: str, ref: str) -> str:
        """Get file content at specific Git reference"""
        try:
            result = self._run_git_command(['show', f"{ref}:{file_path}"])
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def _can_fast_forward(self, source: str, target: str) -> bool:
        """Check if merge can be fast-forwarded"""
        try:
            result = self._run_git_command([
                'merge-base', '--is-ancestor', target, source
            ])
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False

    def _prepare_conflict_context(self, conflict: FileConflict) -> Dict[str, Any]:
        """Prepare context for LLM conflict resolution"""
        return {
            'file_path': conflict.file_path,
            'conflict_type': conflict.conflict_type.value,
            'markers_count': len(conflict.markers),
            'file_extension': Path(conflict.file_path).suffix
        }

    def _format_conflict_markers(self, markers: List[ConflictMarker]) -> str:
        """Format conflict markers for display"""
        formatted = []
        for i, marker in enumerate(markers):
            formatted.append(f"Conflict {i+1}:")
            formatted.append("<<<<<<< HEAD (ours)")
            formatted.append(marker.ours_content[:200] + "..." if len(marker.ours_content) > 200 else marker.ours_content)
            formatted.append("=======")
            formatted.append(marker.theirs_content[:200] + "..." if len(marker.theirs_content) > 200 else marker.theirs_content)
            formatted.append(">>>>>>> branch")
            formatted.append("")
        return '\n'.join(formatted)

    def _can_merge_content(self, ours: str, theirs: str) -> bool:
        """Check if content can be safely merged"""
        # Simple heuristic: if they don't overlap, they can be merged
        ours_lines = set(ours.split('\n'))
        theirs_lines = set(theirs.split('\n'))
        return len(ours_lines & theirs_lines) == 0

    def _merge_content(self, ours: str, theirs: str) -> str:
        """Merge content from both sides"""
        # Simple merge: combine both sides
        return f"{ours}\n{theirs}"

    def _load_resolution_patterns(self):
        """Load resolution patterns from previous merges"""
        # Would load from a configuration file or database
        pass

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
        self.logger.info("Shutting down Automated Merging System")