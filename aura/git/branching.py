"""
Aura Intelligent Branching System with GitFlow
===============================================

Implements intelligent Git branching with full GitFlow support.
Autonomous branch management, feature lifecycle, and release workflows.

Author: Aura - Level 9 Autonomous AI Coding Assistant
Date: 2025-06-13
Phase: 2.1.2 - Intelligent Branching System
"""

import subprocess
import re
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from ..core import AuraModule, MessageType, aura_service


class BranchType(Enum):
    """GitFlow branch types"""
    MAIN = "main"
    DEVELOP = "develop"
    FEATURE = "feature"
    RELEASE = "release"
    HOTFIX = "hotfix"
    SUPPORT = "support"


class GitFlowAction(Enum):
    """GitFlow workflow actions"""
    START = "start"
    FINISH = "finish"
    PUBLISH = "publish"
    PULL = "pull"
    TRACK = "track"


@dataclass
class BranchInfo:
    """Information about a Git branch"""
    name: str
    branch_type: BranchType
    base_branch: str
    is_current: bool
    is_published: bool
    ahead_count: int
    behind_count: int
    last_commit_hash: str
    last_commit_message: str
    last_commit_date: str
    author: str


@dataclass
class GitFlowConfig:
    """GitFlow configuration"""
    main_branch: str = "main"
    develop_branch: str = "develop"
    feature_prefix: str = "feature/"
    release_prefix: str = "release/"
    hotfix_prefix: str = "hotfix/"
    support_prefix: str = "support/"
    version_tag_prefix: str = "v"


@dataclass
class WorkflowSuggestion:
    """Suggested workflow action"""
    action: GitFlowAction
    branch_type: BranchType
    branch_name: str
    description: str
    commands: List[str]
    confidence: float
    reasoning: str


@aura_service("intelligent_branching")
class IntelligentBranchingSystem(AuraModule):
    """
    Aura Intelligent Branching System
    Provides autonomous Git branching with GitFlow support.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__("git_branching", config)
        
        self.repo_path = config.get('repo_path', '.')
        self.gitflow_config = GitFlowConfig(**config.get('gitflow_config', {}))
        self.auto_publish = config.get('auto_publish', False)
        self.auto_cleanup = config.get('auto_cleanup', True)
        
        # State tracking
        self.branch_cache: Dict[str, BranchInfo] = {}
        self.workflow_history: List[Dict[str, Any]] = []

    async def initialize(self) -> bool:
        """Initialize the branching system"""
        try:
            self.logger.info("Initializing Intelligent Branching System")
            
            if not self._is_git_repo():
                self.logger.error("Not a Git repository")
                return False
            
            # Initialize GitFlow if not already configured
            await self._ensure_gitflow_initialized()
            
            # Cache current branch information
            await self._refresh_branch_cache()
            
            self.logger.info("Intelligent Branching System initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize branching system: {e}")
            return False

    async def process_message(self, message) -> Optional[any]:
        """Process branching requests"""
        try:
            if message.type == MessageType.COMMAND:
                command = message.payload.get('command')
                
                if command == 'create_branch':
                    branch_type = BranchType(message.payload.get('branch_type'))
                    branch_name = message.payload.get('branch_name')
                    base_branch = message.payload.get('base_branch')
                    
                    result = await self.create_branch(branch_type, branch_name, base_branch)
                    return self._create_response(message, result)
                
                elif command == 'finish_branch':
                    branch_name = message.payload.get('branch_name')
                    delete_branch = message.payload.get('delete_branch', True)
                    
                    result = await self.finish_branch(branch_name, delete_branch)
                    return self._create_response(message, result)
                
                elif command == 'suggest_workflow':
                    context = message.payload.get('context', {})
                    suggestions = await self.suggest_workflow_actions(context)
                    
                    return self._create_response(message, {
                        'success': True,
                        'suggestions': [asdict(s) for s in suggestions]
                    })
                
                elif command == 'get_branch_status':
                    await self._refresh_branch_cache()
                    return self._create_response(message, {
                        'success': True,
                        'branches': {name: asdict(info) for name, info in self.branch_cache.items()},
                        'current_branch': self._get_current_branch()
                    })
                
                elif command == 'merge_branches':
                    source_branch = message.payload.get('source_branch')
                    target_branch = message.payload.get('target_branch')
                    strategy = message.payload.get('strategy', 'merge')
                    
                    result = await self.merge_branches(source_branch, target_branch, strategy)
                    return self._create_response(message, result)

        except Exception as e:
            self.logger.error(f"Error processing branching message: {e}")
            return self._create_response(message, {
                'success': False,
                'error': str(e)
            })

        return None

    def _is_git_repo(self) -> bool:
        """Check if current directory is a Git repository"""
        try:
            subprocess.run(['git', 'rev-parse', '--git-dir'], 
                          cwd=self.repo_path, capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    async def _ensure_gitflow_initialized(self):
        """Ensure GitFlow is properly initialized"""
        try:
            # Check if main and develop branches exist
            branches = self._get_all_branches()
            
            if self.gitflow_config.main_branch not in branches:
                # Create main branch if it doesn't exist
                current_branch = self._get_current_branch()
                if current_branch and current_branch != self.gitflow_config.main_branch:
                    self._run_git_command(['checkout', '-b', self.gitflow_config.main_branch])
                    self.logger.info(f"Created {self.gitflow_config.main_branch} branch")
            
            if self.gitflow_config.develop_branch not in branches:
                # Create develop branch from main
                self._run_git_command(['checkout', self.gitflow_config.main_branch])
                self._run_git_command(['checkout', '-b', self.gitflow_config.develop_branch])
                self.logger.info(f"Created {self.gitflow_config.develop_branch} branch")
            
        except Exception as e:
            self.logger.error(f"Error initializing GitFlow: {e}")

    async def _refresh_branch_cache(self):
        """Refresh the branch information cache"""
        try:
            branches = self._get_all_branches()
            current_branch = self._get_current_branch()
            
            self.branch_cache.clear()
            
            for branch in branches:
                if branch.startswith('origin/'):
                    continue  # Skip remote tracking branches
                
                branch_info = self._get_branch_info(branch)
                if branch_info:
                    branch_info.is_current = (branch == current_branch)
                    self.branch_cache[branch] = branch_info
                    
        except Exception as e:
            self.logger.error(f"Error refreshing branch cache: {e}")

    def _get_branch_info(self, branch_name: str) -> Optional[BranchInfo]:
        """Get detailed information about a branch"""
        try:
            # Get branch type
            branch_type = self._classify_branch(branch_name)
            
            # Get base branch
            base_branch = self._get_base_branch(branch_name, branch_type)
            
            # Check if published (has remote tracking)
            is_published = self._is_branch_published(branch_name)
            
            # Get ahead/behind counts
            ahead_count, behind_count = self._get_branch_tracking_status(branch_name)
            
            # Get last commit info
            commit_info = self._get_last_commit_info(branch_name)
            
            return BranchInfo(
                name=branch_name,
                branch_type=branch_type,
                base_branch=base_branch,
                is_current=False,  # Set by caller
                is_published=is_published,
                ahead_count=ahead_count,
                behind_count=behind_count,
                **commit_info
            )
            
        except Exception as e:
            self.logger.error(f"Error getting branch info for {branch_name}: {e}")
            return None

    def _classify_branch(self, branch_name: str) -> BranchType:
        """Classify branch type based on name"""
        if branch_name == self.gitflow_config.main_branch:
            return BranchType.MAIN
        elif branch_name == self.gitflow_config.develop_branch:
            return BranchType.DEVELOP
        elif branch_name.startswith(self.gitflow_config.feature_prefix):
            return BranchType.FEATURE
        elif branch_name.startswith(self.gitflow_config.release_prefix):
            return BranchType.RELEASE
        elif branch_name.startswith(self.gitflow_config.hotfix_prefix):
            return BranchType.HOTFIX
        elif branch_name.startswith(self.gitflow_config.support_prefix):
            return BranchType.SUPPORT
        else:
            return BranchType.FEATURE  # Default to feature

    def _get_base_branch(self, branch_name: str, branch_type: BranchType) -> str:
        """Determine the base branch for a given branch"""
        if branch_type == BranchType.MAIN:
            return ""
        elif branch_type == BranchType.DEVELOP:
            return self.gitflow_config.main_branch
        elif branch_type in [BranchType.FEATURE, BranchType.RELEASE]:
            return self.gitflow_config.develop_branch
        elif branch_type == BranchType.HOTFIX:
            return self.gitflow_config.main_branch
        else:
            return self.gitflow_config.develop_branch

    async def create_branch(self, branch_type: BranchType, branch_name: str, 
                          base_branch: Optional[str] = None) -> Dict[str, Any]:
        """Create a new branch following GitFlow conventions"""
        try:
            # Determine full branch name with prefix
            full_branch_name = self._format_branch_name(branch_type, branch_name)
            
            # Determine base branch if not specified
            if not base_branch:
                base_branch = self._get_base_branch(full_branch_name, branch_type)
            
            # Ensure we're on the base branch
            self._run_git_command(['checkout', base_branch])
            
            # Pull latest changes from remote
            try:
                self._run_git_command(['pull', 'origin', base_branch])
            except subprocess.CalledProcessError:
                self.logger.warning(f"Could not pull latest changes for {base_branch}")
            
            # Create and checkout new branch
            self._run_git_command(['checkout', '-b', full_branch_name])
            
            # Publish branch if auto-publish is enabled
            if self.auto_publish:
                self._run_git_command(['push', '-u', 'origin', full_branch_name])
            
            # Update cache
            await self._refresh_branch_cache()
            
            # Log workflow action
            self._log_workflow_action(GitFlowAction.START, branch_type, full_branch_name)
            
            self.logger.info(f"Created {branch_type.value} branch: {full_branch_name}")
            
            return {
                'success': True,
                'branch_name': full_branch_name,
                'base_branch': base_branch,
                'published': self.auto_publish,
                'message': f"Successfully created {branch_type.value} branch '{full_branch_name}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating branch: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def finish_branch(self, branch_name: str, delete_branch: bool = True) -> Dict[str, Any]:
        """Finish a branch following GitFlow conventions"""
        try:
            # Get branch info
            if branch_name not in self.branch_cache:
                await self._refresh_branch_cache()
            
            if branch_name not in self.branch_cache:
                return {
                    'success': False,
                    'error': f"Branch '{branch_name}' not found"
                }
            
            branch_info = self.branch_cache[branch_name]
            target_branch = self._get_finish_target_branch(branch_info.branch_type)
            
            # Ensure we're on the target branch
            self._run_git_command(['checkout', target_branch])
            
            # Pull latest changes
            try:
                self._run_git_command(['pull', 'origin', target_branch])
            except subprocess.CalledProcessError:
                self.logger.warning(f"Could not pull latest changes for {target_branch}")
            
            # Merge the feature branch
            merge_result = await self.merge_branches(branch_name, target_branch, 'merge')
            
            if not merge_result['success']:
                return merge_result
            
            # Delete the branch if requested
            if delete_branch:
                self._run_git_command(['branch', '-d', branch_name])
                
                # Delete remote branch if it was published
                if branch_info.is_published:
                    try:
                        self._run_git_command(['push', 'origin', '--delete', branch_name])
                    except subprocess.CalledProcessError:
                        self.logger.warning(f"Could not delete remote branch {branch_name}")
            
            # Update cache
            await self._refresh_branch_cache()
            
            # Log workflow action
            self._log_workflow_action(GitFlowAction.FINISH, branch_info.branch_type, branch_name)
            
            self.logger.info(f"Finished {branch_info.branch_type.value} branch: {branch_name}")
            
            return {
                'success': True,
                'branch_name': branch_name,
                'target_branch': target_branch,
                'deleted': delete_branch,
                'message': f"Successfully finished {branch_info.branch_type.value} branch '{branch_name}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error finishing branch: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def merge_branches(self, source_branch: str, target_branch: str, 
                           strategy: str = 'merge') -> Dict[str, Any]:
        """Merge branches with conflict resolution"""
        try:
            # Ensure we're on the target branch
            self._run_git_command(['checkout', target_branch])
            
            # Attempt merge
            if strategy == 'rebase':
                # Rebase source onto target
                self._run_git_command(['checkout', source_branch])
                merge_cmd = ['rebase', target_branch]
            else:
                # Merge source into target
                merge_cmd = ['merge', source_branch, '--no-ff']
            
            try:
                result = self._run_git_command(merge_cmd)
                
                return {
                    'success': True,
                    'strategy': strategy,
                    'source_branch': source_branch,
                    'target_branch': target_branch,
                    'conflicts': [],
                    'message': f"Successfully merged {source_branch} into {target_branch}"
                }
                
            except subprocess.CalledProcessError as e:
                # Check for merge conflicts
                conflicts = self._detect_merge_conflicts()
                
                if conflicts:
                    return {
                        'success': False,
                        'strategy': strategy,
                        'source_branch': source_branch,
                        'target_branch': target_branch,
                        'conflicts': conflicts,
                        'error': 'Merge conflicts detected',
                        'resolution_needed': True
                    }
                else:
                    raise e
                    
        except Exception as e:
            self.logger.error(f"Error merging branches: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def suggest_workflow_actions(self, context: Dict[str, Any]) -> List[WorkflowSuggestion]:
        """Suggest GitFlow workflow actions based on current state"""
        suggestions = []
        
        try:
            await self._refresh_branch_cache()
            current_branch = self._get_current_branch()
            
            if not current_branch:
                return suggestions
            
            current_info = self.branch_cache.get(current_branch)
            if not current_info:
                return suggestions
            
            # Analyze current state and suggest actions
            
            # Feature branch suggestions
            if current_info.branch_type == BranchType.FEATURE:
                # Suggest finishing feature if it has commits ahead
                if current_info.ahead_count > 0:
                    suggestions.append(WorkflowSuggestion(
                        action=GitFlowAction.FINISH,
                        branch_type=BranchType.FEATURE,
                        branch_name=current_branch,
                        description=f"Finish feature branch and merge into {self.gitflow_config.develop_branch}",
                        commands=[
                            f"git checkout {self.gitflow_config.develop_branch}",
                            f"git merge --no-ff {current_branch}",
                            f"git branch -d {current_branch}"
                        ],
                        confidence=0.8,
                        reasoning=f"Feature has {current_info.ahead_count} commits ready to merge"
                    ))
                
                # Suggest publishing if not published
                if not current_info.is_published:
                    suggestions.append(WorkflowSuggestion(
                        action=GitFlowAction.PUBLISH,
                        branch_type=BranchType.FEATURE,
                        branch_name=current_branch,
                        description="Publish feature branch to remote repository",
                        commands=[f"git push -u origin {current_branch}"],
                        confidence=0.6,
                        reasoning="Feature branch is not published to remote"
                    ))
            
            # Develop branch suggestions
            elif current_info.branch_type == BranchType.DEVELOP:
                # Suggest creating release if develop has unreleased features
                if current_info.ahead_count > 0:
                    next_version = self._suggest_next_version()
                    suggestions.append(WorkflowSuggestion(
                        action=GitFlowAction.START,
                        branch_type=BranchType.RELEASE,
                        branch_name=f"release/{next_version}",
                        description=f"Start release branch for version {next_version}",
                        commands=[
                            f"git checkout -b release/{next_version} {self.gitflow_config.develop_branch}"
                        ],
                        confidence=0.7,
                        reasoning=f"Develop branch has {current_info.ahead_count} unreleased commits"
                    ))
            
            # Main branch suggestions
            elif current_info.branch_type == BranchType.MAIN:
                # Suggest hotfix if on main
                suggestions.append(WorkflowSuggestion(
                    action=GitFlowAction.START,
                    branch_type=BranchType.HOTFIX,
                    branch_name="hotfix/critical-fix",
                    description="Start hotfix branch for critical bug fixes",
                    commands=[f"git checkout -b hotfix/critical-fix {self.gitflow_config.main_branch}"],
                    confidence=0.5,
                    reasoning="Create hotfix branch for urgent production fixes"
                ))
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating workflow suggestions: {e}")
            return suggestions

    def _format_branch_name(self, branch_type: BranchType, branch_name: str) -> str:
        """Format branch name with appropriate prefix"""
        if branch_type == BranchType.FEATURE:
            return f"{self.gitflow_config.feature_prefix}{branch_name}"
        elif branch_type == BranchType.RELEASE:
            return f"{self.gitflow_config.release_prefix}{branch_name}"
        elif branch_type == BranchType.HOTFIX:
            return f"{self.gitflow_config.hotfix_prefix}{branch_name}"
        elif branch_type == BranchType.SUPPORT:
            return f"{self.gitflow_config.support_prefix}{branch_name}"
        else:
            return branch_name

    def _get_finish_target_branch(self, branch_type: BranchType) -> str:
        """Get the target branch for finishing a branch"""
        if branch_type in [BranchType.FEATURE, BranchType.RELEASE]:
            return self.gitflow_config.develop_branch
        elif branch_type == BranchType.HOTFIX:
            return self.gitflow_config.main_branch
        else:
            return self.gitflow_config.develop_branch

    def _suggest_next_version(self) -> str:
        """Suggest next version number based on Git tags"""
        try:
            # Get latest tag
            result = self._run_git_command(['describe', '--tags', '--abbrev=0'])
            latest_tag = result.stdout.strip()
            
            if latest_tag.startswith(self.gitflow_config.version_tag_prefix):
                version = latest_tag[len(self.gitflow_config.version_tag_prefix):]
                # Simple version increment (major.minor.patch)
                parts = version.split('.')
                if len(parts) >= 2:
                    minor = int(parts[1]) + 1
                    return f"{parts[0]}.{minor}.0"
            
            return "1.0.0"
            
        except subprocess.CalledProcessError:
            return "1.0.0"

    def _run_git_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run a Git command and return the result"""
        full_cmd = ['git'] + cmd
        return subprocess.run(
            full_cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )

    def _get_all_branches(self) -> List[str]:
        """Get all local branches"""
        try:
            result = self._run_git_command(['branch'])
            branches = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and not line.startswith('*'):
                    branches.append(line)
                elif line.startswith('* '):
                    branches.append(line[2:])
            return branches
        except subprocess.CalledProcessError:
            return []

    def _get_current_branch(self) -> Optional[str]:
        """Get the current branch name"""
        try:
            result = self._run_git_command(['branch', '--show-current'])
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def _is_branch_published(self, branch_name: str) -> bool:
        """Check if branch has a remote tracking branch"""
        try:
            self._run_git_command(['rev-parse', '--verify', f"origin/{branch_name}"])
            return True
        except subprocess.CalledProcessError:
            return False

    def _get_branch_tracking_status(self, branch_name: str) -> Tuple[int, int]:
        """Get ahead/behind counts for a branch"""
        try:
            result = self._run_git_command([
                'rev-list', '--left-right', '--count',
                f"{branch_name}...origin/{branch_name}"
            ])
            ahead, behind = map(int, result.stdout.strip().split('\t'))
            return ahead, behind
        except subprocess.CalledProcessError:
            return 0, 0

    def _get_last_commit_info(self, branch_name: str) -> Dict[str, str]:
        """Get last commit information for a branch"""
        try:
            result = self._run_git_command([
                'log', '-1', '--format=%H|%s|%ad|%an',
                '--date=iso', branch_name
            ])
            
            parts = result.stdout.strip().split('|', 3)
            if len(parts) == 4:
                return {
                    'last_commit_hash': parts[0],
                    'last_commit_message': parts[1],
                    'last_commit_date': parts[2],
                    'author': parts[3]
                }
        except subprocess.CalledProcessError:
            pass
        
        return {
            'last_commit_hash': '',
            'last_commit_message': '',
            'last_commit_date': '',
            'author': ''
        }

    def _detect_merge_conflicts(self) -> List[str]:
        """Detect merge conflicts in the repository"""
        try:
            result = self._run_git_command(['diff', '--name-only', '--diff-filter=U'])
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError:
            return []

    def _log_workflow_action(self, action: GitFlowAction, branch_type: BranchType, branch_name: str):
        """Log workflow action for history tracking"""
        self.workflow_history.append({
            'timestamp': time.time(),
            'action': action.value,
            'branch_type': branch_type.value,
            'branch_name': branch_name,
            'user': 'aura'
        })
        
        # Keep only last 100 actions
        if len(self.workflow_history) > 100:
            self.workflow_history.pop(0)

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
        self.logger.info("Shutting down Intelligent Branching System")
        self.branch_cache.clear()
        self.workflow_history.clear()