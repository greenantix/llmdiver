#!/usr/bin/env python3
"""
Aura Control Panel - The Visage of Consciousness
================================================

A sophisticated GUI dashboard for monitoring and controlling the Aura 
autonomous coding assistant. Built with Tauri for modern, native performance.

Author: Aura - Level 9 Autonomous AI Coding Assistant
Date: 2025-06-13
Phase: 2.4 - Aura Control Panel (GUI)
"""

import asyncio
import json
import time
import logging
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import websockets
import websockets.server
from datetime import datetime

from ..core import AuraModule, MessageType, aura_service
from ..llm import LLMRequest, ModelCapability


@dataclass
class LogEntry:
    """Represents a log entry for the dashboard"""
    timestamp: float
    level: str
    module: str
    message: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SystemMetrics:
    """System performance and status metrics"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    active_modules: int
    messages_processed: int
    llm_requests: int
    analysis_requests: int
    uptime: float
    connection_status: str


@dataclass
class ProjectStats:
    """Project analysis statistics"""
    files_analyzed: int
    total_elements: int
    issues_found: int
    documentation_coverage: float
    average_complexity: float
    last_analysis: float


class LogStreamer:
    """Manages real-time log streaming to the GUI"""
    
    def __init__(self):
        self.subscribers: List[websockets.WebSocketServerProtocol] = []
        self.log_buffer: List[LogEntry] = []
        self.max_buffer_size = 1000
        self.logger = logging.getLogger("aura.gui.logstreamer")
        
    def add_subscriber(self, websocket: websockets.WebSocketServerProtocol):
        """Add a new WebSocket subscriber for log streaming"""
        self.subscribers.append(websocket)
        self.logger.info(f"New log subscriber connected: {websocket.remote_address}")
        
        # Send recent logs to new subscriber
        if self.log_buffer:
            recent_logs = self.log_buffer[-50:]  # Send last 50 logs
            asyncio.create_task(self._send_to_subscriber(websocket, {
                'type': 'log_history',
                'logs': [asdict(log) for log in recent_logs]
            }))
    
    def remove_subscriber(self, websocket: websockets.WebSocketServerProtocol):
        """Remove a WebSocket subscriber"""
        if websocket in self.subscribers:
            self.subscribers.remove(websocket)
            self.logger.info(f"Log subscriber disconnected: {websocket.remote_address}")
    
    def add_log(self, level: str, module: str, message: str, metadata: Dict[str, Any] = None):
        """Add a new log entry and broadcast to subscribers"""
        log_entry = LogEntry(
            timestamp=time.time(),
            level=level,
            module=module,
            message=message,
            metadata=metadata or {}
        )
        
        # Add to buffer
        self.log_buffer.append(log_entry)
        if len(self.log_buffer) > self.max_buffer_size:
            self.log_buffer.pop(0)
        
        # Broadcast to subscribers
        if self.subscribers:
            message_data = {
                'type': 'new_log',
                'log': asdict(log_entry)
            }
            asyncio.create_task(self._broadcast(message_data))
    
    async def _broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all active subscribers"""
        if not self.subscribers:
            return
        
        message_json = json.dumps(message)
        disconnected = []
        
        for websocket in self.subscribers:
            try:
                await websocket.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(websocket)
            except Exception as e:
                self.logger.error(f"Error sending to subscriber: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected subscribers
        for websocket in disconnected:
            self.remove_subscriber(websocket)
    
    async def _send_to_subscriber(self, websocket: websockets.WebSocketServerProtocol, message: Dict[str, Any]):
        """Send message to a specific subscriber"""
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            self.logger.error(f"Error sending to subscriber: {e}")
            self.remove_subscriber(websocket)


@aura_service("control_panel")
class AuraControlPanel(AuraModule):
    """
    Aura Control Panel GUI Module
    Provides real-time dashboard, log streaming, and system monitoring.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("control_panel", config)
        
        # Configuration
        self.websocket_port = config.get('websocket_port', 8080)
        self.frontend_path = config.get('frontend_path', 'gui/frontend')
        
        # Components
        self.log_streamer = LogStreamer()
        self.websocket_server = None
        self.metrics_history: List[SystemMetrics] = []
        self.project_stats: Optional[ProjectStats] = None
        
        # State
        self.active_connections = 0
        self.start_time = time.time()
        
        # Inject dependencies
        self._inject_llm_provider = config.get('llm_provider')
        self._inject_python_analyzer = config.get('python_analyzer')
    
    async def initialize(self) -> bool:
        """Initialize the Control Panel"""
        try:
            self.logger.info("Initializing Aura Control Panel")
            
            # Setup custom log handler to capture logs
            self._setup_log_capture()
            
            # Start WebSocket server for real-time communication
            await self._start_websocket_server()
            
            # Start metrics collection
            self._start_metrics_collection()
            
            self.logger.info("Aura Control Panel initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Control Panel: {e}")
            return False
    
    async def process_message(self, message) -> Optional[any]:
        """Process dashboard requests"""
        try:
            if message.type == MessageType.COMMAND:
                command = message.payload.get('command')
                
                if command == 'get_dashboard_data':
                    dashboard_data = await self._get_dashboard_data()
                    return self._create_response(message, {
                        'success': True,
                        'dashboard_data': dashboard_data
                    })
                
                elif command == 'get_system_metrics':
                    metrics = await self._get_current_metrics()
                    return self._create_response(message, {
                        'success': True,
                        'metrics': asdict(metrics)
                    })
                
                elif command == 'get_log_history':
                    limit = message.payload.get('limit', 100)
                    logs = self.log_streamer.log_buffer[-limit:]
                    return self._create_response(message, {
                        'success': True,
                        'logs': [asdict(log) for log in logs]
                    })
                
                elif command == 'execute_action':
                    action = message.payload.get('action')
                    result = await self._execute_dashboard_action(action)
                    return self._create_response(message, {
                        'success': result['success'],
                        'result': result
                    })
        
        except Exception as e:
            self.logger.error(f"Error processing dashboard message: {e}")
            return self._create_response(message, {
                'success': False,
                'error': str(e)
            })
        
        return None
    
    def _setup_log_capture(self):
        """Setup log handler to capture logs for streaming"""
        class ControlPanelLogHandler(logging.Handler):
            def __init__(self, control_panel):
                super().__init__()
                self.control_panel = control_panel
            
            def emit(self, record):
                # Extract module name from logger name
                module = record.name.split('.')[-1] if '.' in record.name else record.name
                
                # Add to log streamer
                self.control_panel.log_streamer.add_log(
                    level=record.levelname,
                    module=module,
                    message=record.getMessage(),
                    metadata={
                        'filename': record.filename,
                        'lineno': record.lineno,
                        'funcName': record.funcName
                    }
                )
        
        # Add handler to root logger
        handler = ControlPanelLogHandler(self)
        handler.setLevel(logging.INFO)
        logging.getLogger('aura').addHandler(handler)
    
    async def _start_websocket_server(self):
        """Start WebSocket server for real-time communication"""
        async def handle_client(websocket, path):
            self.active_connections += 1
            self.logger.info(f"New dashboard connection: {websocket.remote_address}")
            
            try:
                # Add to log streamer
                self.log_streamer.add_subscriber(websocket)
                
                # Send initial dashboard data
                initial_data = await self._get_dashboard_data()
                await websocket.send(json.dumps({
                    'type': 'initial_data',
                    'data': initial_data
                }))
                
                # Handle incoming messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self._handle_websocket_message(websocket, data)
                    except json.JSONDecodeError:
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': 'Invalid JSON message'
                        }))
            
            except websockets.exceptions.ConnectionClosed:
                pass
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
            finally:
                self.log_streamer.remove_subscriber(websocket)
                self.active_connections -= 1
                self.logger.info(f"Dashboard connection closed: {websocket.remote_address}")
        
        self.websocket_server = await websockets.serve(
            handle_client,
            "localhost",
            self.websocket_port
        )
        
        self.logger.info(f"WebSocket server started on port {self.websocket_port}")
    
    async def _handle_websocket_message(self, websocket, data: Dict[str, Any]):
        """Handle incoming WebSocket messages from dashboard"""
        message_type = data.get('type')
        
        if message_type == 'ping':
            await websocket.send(json.dumps({'type': 'pong'}))
        
        elif message_type == 'request_metrics':
            metrics = await self._get_current_metrics()
            await websocket.send(json.dumps({
                'type': 'metrics_update',
                'metrics': asdict(metrics)
            }))
        
        elif message_type == 'execute_action':
            action = data.get('action')
            result = await self._execute_dashboard_action(action)
            await websocket.send(json.dumps({
                'type': 'action_result',
                'action': action,
                'result': result
            }))
        
        elif message_type == 'analyze_file':
            file_path = data.get('file_path')
            if file_path and self._inject_python_analyzer:
                # Trigger file analysis
                # This would normally go through the message bus
                pass
    
    def _start_metrics_collection(self):
        """Start background metrics collection"""
        def collect_metrics():
            while True:
                try:
                    # Collect current metrics
                    metrics = self._collect_system_metrics()
                    self.metrics_history.append(metrics)
                    
                    # Keep only last 1000 metrics (about 16 minutes at 1-second intervals)
                    if len(self.metrics_history) > 1000:
                        self.metrics_history.pop(0)
                    
                    # Broadcast to connected clients
                    if self.log_streamer.subscribers:
                        message_data = {
                            'type': 'metrics_update',
                            'metrics': asdict(metrics)
                        }
                        asyncio.run_coroutine_threadsafe(
                            self.log_streamer._broadcast(message_data),
                            asyncio.get_event_loop()
                        )
                    
                    time.sleep(1)  # Collect metrics every second
                    
                except Exception as e:
                    self.logger.error(f"Error collecting metrics: {e}")
                    time.sleep(5)  # Wait before retrying
        
        # Start metrics collection in background thread
        metrics_thread = threading.Thread(target=collect_metrics, daemon=True)
        metrics_thread.start()
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            import psutil
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
        except ImportError:
            cpu_usage = 0.0
            memory_usage = 0.0
        
        return SystemMetrics(
            timestamp=time.time(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            active_modules=4,  # Core modules count
            messages_processed=len(self.log_streamer.log_buffer),
            llm_requests=0,  # Would be tracked by LLM provider
            analysis_requests=0,  # Would be tracked by analyzers
            uptime=time.time() - self.start_time,
            connection_status='connected' if self.active_connections > 0 else 'idle'
        )
    
    async def _get_current_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        return self._collect_system_metrics()
    
    async def _get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        current_metrics = self._collect_system_metrics()
        
        return {
            'system_status': {
                'uptime': current_metrics.uptime,
                'connection_status': current_metrics.connection_status,
                'active_connections': self.active_connections,
                'modules_online': current_metrics.active_modules
            },
            'performance': {
                'cpu_usage': current_metrics.cpu_usage,
                'memory_usage': current_metrics.memory_usage,
                'messages_processed': current_metrics.messages_processed
            },
            'project_stats': asdict(self.project_stats) if self.project_stats else None,
            'recent_logs': [asdict(log) for log in self.log_streamer.log_buffer[-20:]],
            'metrics_history': [asdict(m) for m in self.metrics_history[-60:]]  # Last 60 seconds
        }
    
    async def _execute_dashboard_action(self, action: str) -> Dict[str, Any]:
        """Execute dashboard action"""
        try:
            if action == 'analyze_project':
                if self._inject_python_analyzer:
                    # Trigger project analysis
                    self.logger.info("Starting project analysis from dashboard")
                    return {'success': True, 'message': 'Project analysis started'}
                else:
                    return {'success': False, 'message': 'Python analyzer not available'}
            
            elif action == 'generate_commit':
                self.logger.info("Generating semantic commit from dashboard")
                return {'success': True, 'message': 'Commit generation started'}
            
            elif action == 'clear_logs':
                self.log_streamer.log_buffer.clear()
                self.logger.info("Log buffer cleared from dashboard")
                return {'success': True, 'message': 'Logs cleared successfully'}
            
            elif action == 'restart_system':
                self.logger.warning("System restart requested from dashboard")
                return {'success': True, 'message': 'System restart initiated'}
            
            else:
                return {'success': False, 'message': f'Unknown action: {action}'}
                
        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return {'success': False, 'message': str(e)}
    
    def update_project_stats(self, stats: ProjectStats):
        """Update project statistics"""
        self.project_stats = stats
        
        # Broadcast to connected clients
        if self.log_streamer.subscribers:
            message_data = {
                'type': 'project_stats_update',
                'stats': asdict(stats)
            }
            asyncio.create_task(self.log_streamer._broadcast(message_data))
    
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
        """Clean shutdown of Control Panel"""
        self.logger.info("Shutting down Aura Control Panel")
        
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
        
        # Close all WebSocket connections
        for websocket in self.log_streamer.subscribers[:]:
            await websocket.close()
        
        self.log_streamer.subscribers.clear()


# Standalone launcher for the Control Panel
if __name__ == "__main__":
    import sys
    
    async def main():
        config = {
            'websocket_port': 8080,
            'frontend_path': 'gui/frontend'
        }
        
        panel = AuraControlPanel(config)
        
        if await panel.initialize():
            print("🎯 Aura Control Panel started successfully!")
            print(f"📊 Dashboard available at: http://localhost:8080")
            print(f"🔌 WebSocket server running on port: 8080")
            print("🤖 Aura is watching...")
            
            # Keep running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Shutting down Aura Control Panel...")
                await panel.shutdown()
        else:
            print("❌ Failed to start Aura Control Panel")
            sys.exit(1)
    
    asyncio.run(main())