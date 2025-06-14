#!/usr/bin/env python3
"""
Aura - Level 9 Autonomous AI Coding Assistant
==============================================

Main orchestrator for the Aura autonomous coding assistant.
Manages module lifecycle, message bus, and system coordination.

Author: Aura - Level 9 Autonomous AI Coding Assistant
Date: 2025-06-13
Phase: 1 - Foundation and Core Intelligence
"""

import asyncio
import json
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any

from core import MessageBus, aura_di
from llm import LLMProviderManager
from intelligence import PythonCodeAnalyzer


class AuraOrchestrator:
    """
    Main orchestrator for the Aura system.
    Manages module lifecycle and coordinates system-wide operations.
    """

    def __init__(self, config_path: str = "config/architecture_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
        
        # Core components
        self.message_bus: MessageBus = None
        self.modules: Dict[str, Any] = {}
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_config(self) -> Dict[str, Any]:
        """Load system configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration
            return {
                "message_bus": {
                    "frontend_port": 5559,
                    "backend_port": 5560
                },
                "modules": {
                    "llm_provider": {"port": 5562},
                    "python_intelligence": {"port": 5561}
                },
                "logging": {"level": "INFO"}
            }

    def _setup_logging(self) -> logging.Logger:
        """Setup system-wide logging"""
        log_config = self.config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO'))
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - AURA.ORCHESTRATOR - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('logs/aura.log') if Path('logs').exists() else logging.NullHandler()
            ]
        )
        
        return logging.getLogger('aura.orchestrator')

    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
        self.running = False

    async def initialize_modules(self) -> bool:
        """Initialize all Aura modules"""
        try:
            self.logger.info("Initializing Aura modules")
            
            # Initialize LLM Provider Manager
            llm_config = self.config.get('modules', {}).get('llm_provider', {})
            llm_config.update({
                'providers': ['lm_studio', 'ollama'],
                'default_provider': 'lm_studio',
                'lm_studio': {'base_url': 'http://localhost:1234'},
                'ollama': {'base_url': 'http://localhost:11434'}
            })
            
            llm_manager = LLMProviderManager(llm_config)
            if await llm_manager.initialize():
                self.modules['llm_provider'] = llm_manager
                aura_di.register_service('llm_provider', llm_manager)
                self.logger.info("LLM Provider Manager initialized")
            else:
                self.logger.error("Failed to initialize LLM Provider Manager")
                return False

            # Initialize Python Code Analyzer
            python_config = self.config.get('modules', {}).get('python_intelligence', {})
            python_config.update({
                'project_root': '.',
                'watch_files': True,
                'llm_provider': llm_manager
            })
            
            python_analyzer = PythonCodeAnalyzer(python_config)
            if await python_analyzer.initialize():
                self.modules['python_intelligence'] = python_analyzer
                aura_di.register_service('python_analyzer', python_analyzer)
                self.logger.info("Python Code Analyzer initialized")
            else:
                self.logger.error("Failed to initialize Python Code Analyzer")
                return False

            self.logger.info(f"Successfully initialized {len(self.modules)} modules")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing modules: {e}")
            return False

    async def start_message_bus(self) -> bool:
        """Start the message bus"""
        try:
            bus_config = self.config.get('message_bus', {})
            self.message_bus = MessageBus(bus_config)
            await self.message_bus.start()
            self.logger.info("Message bus started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start message bus: {e}")
            return False

    async def start_modules(self) -> bool:
        """Start all initialized modules"""
        try:
            self.logger.info("Starting Aura modules")
            
            for name, module in self.modules.items():
                try:
                    await module.start()
                    self.logger.info(f"Module {name} started successfully")
                except Exception as e:
                    self.logger.error(f"Failed to start module {name}: {e}")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error starting modules: {e}")
            return False

    async def run_system_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics"""
        self.logger.info("Running system diagnostics")
        
        diagnostics = {
            'timestamp': asyncio.get_event_loop().time(),
            'modules': {},
            'message_bus': {},
            'system': {}
        }
        
        # Module health checks
        for name, module in self.modules.items():
            try:
                if hasattr(module, 'get_health_status'):
                    diagnostics['modules'][name] = await module.get_health_status()
                else:
                    diagnostics['modules'][name] = {'status': 'running', 'available': True}
            except Exception as e:
                diagnostics['modules'][name] = {'status': 'error', 'error': str(e)}
        
        # Message bus status
        if self.message_bus:
            diagnostics['message_bus'] = {
                'running': self.message_bus.running,
                'registered_modules': len(self.message_bus.module_registry)
            }
        
        # System resources
        try:
            import psutil
            diagnostics['system'] = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('.').percent
            }
        except ImportError:
            diagnostics['system'] = {'note': 'psutil not available'}
        
        self.logger.info("System diagnostics completed")
        return diagnostics

    async def main_loop(self):
        """Main system loop"""
        self.logger.info("Aura main loop started")
        self.running = True
        
        # Periodic system checks
        check_interval = 60  # seconds
        last_check = 0
        
        while self.running:
            try:
                current_time = asyncio.get_event_loop().time()
                
                # Periodic health checks
                if current_time - last_check > check_interval:
                    diagnostics = await self.run_system_diagnostics()
                    
                    # Log any issues
                    for module_name, status in diagnostics['modules'].items():
                        if status.get('status') == 'error':
                            self.logger.warning(f"Module {module_name} reporting error: {status.get('error')}")
                    
                    last_check = current_time
                
                # Sleep briefly to prevent busy waiting
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying

    async def shutdown(self):
        """Graceful system shutdown"""
        self.logger.info("Initiating Aura shutdown sequence")
        
        # Stop modules
        for name, module in self.modules.items():
            try:
                await module.shutdown()
                self.logger.info(f"Module {name} shut down")
            except Exception as e:
                self.logger.error(f"Error shutting down module {name}: {e}")
        
        # Stop message bus
        if self.message_bus:
            await self.message_bus.shutdown()
            self.logger.info("Message bus shut down")
        
        self.logger.info("Aura shutdown complete")

    async def run(self):
        """Main entry point for Aura system"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("AURA - Level 9 Autonomous AI Coding Assistant")
            self.logger.info("Phase 1: Foundation and Core Intelligence")
            self.logger.info("=" * 60)
            
            # Initialize system components
            if not await self.initialize_modules():
                self.logger.error("Module initialization failed, aborting startup")
                return False
            
            if not await self.start_message_bus():
                self.logger.error("Message bus startup failed, aborting startup")
                return False
            
            if not await self.start_modules():
                self.logger.error("Module startup failed, aborting startup")
                return False
            
            # Run initial diagnostics
            diagnostics = await self.run_system_diagnostics()
            self.logger.info("Initial system diagnostics:")
            for module_name, status in diagnostics['modules'].items():
                self.logger.info(f"  {module_name}: {status.get('status', 'unknown')}")
            
            self.logger.info("Aura system startup complete - entering main loop")
            
            # Run main loop
            await self.main_loop()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Critical error in Aura system: {e}")
            return False
        finally:
            await self.shutdown()


async def main():
    """Application entry point"""
    orchestrator = AuraOrchestrator()
    
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    
    try:
        success = await orchestrator.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        orchestrator.logger.info("Received keyboard interrupt")
        sys.exit(0)
    except Exception as e:
        orchestrator.logger.error(f"Unhandled exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())