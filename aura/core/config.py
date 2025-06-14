"""
Aura Configuration Management
Handles application configuration, settings, and environment variables
"""

import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
from dotenv import load_dotenv


@dataclass
class LLMConfig:
    provider: str = "lm_studio"
    base_url: str = "http://localhost:1234"
    model_name: str = "meta-llama-3.1-8b-instruct"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 30


@dataclass 
class GitConfig:
    auto_commit: bool = True
    commit_message_template: str = "conventional"
    branch_strategy: str = "gitflow"
    auto_push: bool = False
    github_token: Optional[str] = None
    gitlab_token: Optional[str] = None


@dataclass
class GUIConfig:
    port: int = 8080
    host: str = "localhost"
    auto_open: bool = True
    theme: str = "dark"
    log_level: str = "INFO"


@dataclass
class IDEConfig:
    vscode_enabled: bool = True
    jetbrains_enabled: bool = False
    auto_suggestions: bool = True
    real_time_analysis: bool = True


@dataclass
class PlanningConfig:
    auto_decompose: bool = True
    estimation_method: str = "story_points"  # story_points, hours, days
    dependency_analysis: bool = True
    vision_analysis: bool = True
    template_preference: str = "agile"


class AuraConfig:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".aura" / "config.yaml"
        self.env_file = Path.cwd() / ".env"
        
        # Load environment variables
        if self.env_file.exists():
            load_dotenv(self.env_file)
        
        # Initialize configuration sections
        self.llm = LLMConfig()
        self.git = GitConfig()  
        self.gui = GUIConfig()
        self.ide = IDEConfig()
        self.planning = PlanningConfig()
        
        # Load configuration from file
        self.load_config()
        
        # Override with environment variables
        self._load_from_env()
    
    def load_config(self):
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            self.save_config()  # Create default config
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data:
                return
            
            # Update LLM config
            if 'llm' in config_data:
                llm_data = config_data['llm']
                self.llm.provider = llm_data.get('provider', self.llm.provider)
                self.llm.base_url = llm_data.get('base_url', self.llm.base_url)
                self.llm.model_name = llm_data.get('model_name', self.llm.model_name)
                self.llm.api_key = llm_data.get('api_key', self.llm.api_key)
                self.llm.temperature = llm_data.get('temperature', self.llm.temperature)
                self.llm.max_tokens = llm_data.get('max_tokens', self.llm.max_tokens)
                self.llm.timeout = llm_data.get('timeout', self.llm.timeout)
            
            # Update Git config
            if 'git' in config_data:
                git_data = config_data['git']
                self.git.auto_commit = git_data.get('auto_commit', self.git.auto_commit)
                self.git.commit_message_template = git_data.get('commit_message_template', self.git.commit_message_template)
                self.git.branch_strategy = git_data.get('branch_strategy', self.git.branch_strategy)
                self.git.auto_push = git_data.get('auto_push', self.git.auto_push)
                self.git.github_token = git_data.get('github_token', self.git.github_token)
                self.git.gitlab_token = git_data.get('gitlab_token', self.git.gitlab_token)
            
            # Update GUI config
            if 'gui' in config_data:
                gui_data = config_data['gui']
                self.gui.port = gui_data.get('port', self.gui.port)
                self.gui.host = gui_data.get('host', self.gui.host)
                self.gui.auto_open = gui_data.get('auto_open', self.gui.auto_open)
                self.gui.theme = gui_data.get('theme', self.gui.theme)
                self.gui.log_level = gui_data.get('log_level', self.gui.log_level)
            
            # Update IDE config
            if 'ide' in config_data:
                ide_data = config_data['ide']
                self.ide.vscode_enabled = ide_data.get('vscode_enabled', self.ide.vscode_enabled)
                self.ide.jetbrains_enabled = ide_data.get('jetbrains_enabled', self.ide.jetbrains_enabled)
                self.ide.auto_suggestions = ide_data.get('auto_suggestions', self.ide.auto_suggestions)
                self.ide.real_time_analysis = ide_data.get('real_time_analysis', self.ide.real_time_analysis)
            
            # Update Planning config
            if 'planning' in config_data:
                planning_data = config_data['planning']
                self.planning.auto_decompose = planning_data.get('auto_decompose', self.planning.auto_decompose)
                self.planning.estimation_method = planning_data.get('estimation_method', self.planning.estimation_method)
                self.planning.dependency_analysis = planning_data.get('dependency_analysis', self.planning.dependency_analysis)
                self.planning.vision_analysis = planning_data.get('vision_analysis', self.planning.vision_analysis)
                self.planning.template_preference = planning_data.get('template_preference', self.planning.template_preference)
            
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    
    def save_config(self):
        """Save current configuration to YAML file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_data = {
            'llm': {
                'provider': self.llm.provider,
                'base_url': self.llm.base_url,
                'model_name': self.llm.model_name,
                'api_key': self.llm.api_key,
                'temperature': self.llm.temperature,
                'max_tokens': self.llm.max_tokens,
                'timeout': self.llm.timeout
            },
            'git': {
                'auto_commit': self.git.auto_commit,
                'commit_message_template': self.git.commit_message_template,
                'branch_strategy': self.git.branch_strategy,
                'auto_push': self.git.auto_push,
                'github_token': self.git.github_token,
                'gitlab_token': self.git.gitlab_token
            },
            'gui': {
                'port': self.gui.port,
                'host': self.gui.host,
                'auto_open': self.gui.auto_open,
                'theme': self.gui.theme,
                'log_level': self.gui.log_level
            },
            'ide': {
                'vscode_enabled': self.ide.vscode_enabled,
                'jetbrains_enabled': self.ide.jetbrains_enabled,
                'auto_suggestions': self.ide.auto_suggestions,
                'real_time_analysis': self.ide.real_time_analysis
            },
            'planning': {
                'auto_decompose': self.planning.auto_decompose,
                'estimation_method': self.planning.estimation_method,
                'dependency_analysis': self.planning.dependency_analysis,
                'vision_analysis': self.planning.vision_analysis,
                'template_preference': self.planning.template_preference
            }
        }
        
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        
        # LLM configuration
        if os.getenv('AURA_LLM_PROVIDER'):
            self.llm.provider = os.getenv('AURA_LLM_PROVIDER')
        if os.getenv('AURA_LLM_BASE_URL'):
            self.llm.base_url = os.getenv('AURA_LLM_BASE_URL')
        if os.getenv('AURA_LLM_MODEL'):
            self.llm.model_name = os.getenv('AURA_LLM_MODEL')
        if os.getenv('AURA_LLM_API_KEY'):
            self.llm.api_key = os.getenv('AURA_LLM_API_KEY')
        if os.getenv('AURA_LLM_TEMPERATURE'):
            self.llm.temperature = float(os.getenv('AURA_LLM_TEMPERATURE'))
        if os.getenv('AURA_LLM_MAX_TOKENS'):
            self.llm.max_tokens = int(os.getenv('AURA_LLM_MAX_TOKENS'))
        
        # Git configuration
        if os.getenv('GITHUB_TOKEN'):
            self.git.github_token = os.getenv('GITHUB_TOKEN')
        if os.getenv('GITLAB_TOKEN'):
            self.git.gitlab_token = os.getenv('GITLAB_TOKEN')
        if os.getenv('AURA_AUTO_COMMIT'):
            self.git.auto_commit = os.getenv('AURA_AUTO_COMMIT').lower() == 'true'
        if os.getenv('AURA_AUTO_PUSH'):
            self.git.auto_push = os.getenv('AURA_AUTO_PUSH').lower() == 'true'
        
        # GUI configuration
        if os.getenv('AURA_GUI_PORT'):
            self.gui.port = int(os.getenv('AURA_GUI_PORT'))
        if os.getenv('AURA_GUI_HOST'):
            self.gui.host = os.getenv('AURA_GUI_HOST')
        if os.getenv('AURA_LOG_LEVEL'):
            self.gui.log_level = os.getenv('AURA_LOG_LEVEL')
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key"""
        parts = key.split('.')
        current = self
        
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any):
        """Set configuration value by dot notation key"""
        parts = key.split('.')
        current = self
        
        for part in parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return False
        
        if hasattr(current, parts[-1]):
            setattr(current, parts[-1], value)
            return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'llm': self.llm.__dict__,
            'git': self.git.__dict__, 
            'gui': self.gui.__dict__,
            'ide': self.ide.__dict__,
            'planning': self.planning.__dict__
        }
    
    def update_from_dict(self, config_dict: Dict[str, Any]):
        """Update configuration from dictionary"""
        for section, values in config_dict.items():
            if hasattr(self, section):
                section_obj = getattr(self, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)