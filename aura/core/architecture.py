"""
Aura Core Architecture Module
============================

This module defines the foundational architecture for the Aura autonomous coding assistant.
Implements a microservices-inspired architecture with lightweight message bus communication.

Author: Aura - Level 9 Autonomous AI Coding Assistant
Date: 2025-06-13
Phase: 1.1 - Core System Architecture
"""

import asyncio
import logging
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
import zmq
import zmq.asyncio
from threading import Lock
import uuid


class MessageType(Enum):
    """Message types for inter-module communication"""
    COMMAND = "command"
    RESPONSE = "response" 
    EVENT = "event"
    HEALTH_CHECK = "health_check"
    SHUTDOWN = "shutdown"


class ModuleStatus(Enum):
    """Module operational status"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    IDLE = "idle"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class Message:
    """Standard message format for inter-module communication"""
    id: str
    type: MessageType
    source: str
    target: str
    timestamp: float
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None

    def to_json(self) -> str:
        """Serialize message to JSON"""
        data = asdict(self)
        data['type'] = data['type'].value
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Deserialize message from JSON"""
        data = json.loads(json_str)
        data['type'] = MessageType(data['type'])
        return cls(**data)


class AuraModule(ABC):
    """
    Base class for all Aura modules.
    Implements the standard lifecycle and communication protocols.
    """

    def __init__(self, module_name: str, config: Dict[str, Any]):
        self.module_name = module_name
        self.config = config
        self.status = ModuleStatus.INITIALIZING
        self.logger = self._setup_logging()
        self.message_handlers: Dict[MessageType, Callable] = {}
        self._startup_time = time.time()
        self._health_metrics = {
            'messages_processed': 0,
            'errors_count': 0,
            'last_activity': time.time()
        }
        
        # ZeroMQ contexts
        self.context = None
        self.socket = None
        self._lock = Lock()

    def _setup_logging(self) -> logging.Logger:
        """Setup structured logging for the module"""
        logger = logging.getLogger(f"aura.{self.module_name}")
        logger.setLevel(self.config.get('log_level', 'INFO'))
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            f'%(asctime)s - AURA.{self.module_name.upper()} - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the module. Must be implemented by subclasses."""
        pass

    @abstractmethod
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages. Must be implemented by subclasses."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Clean shutdown. Must be implemented by subclasses."""
        pass

    async def start(self) -> None:
        """Start the module lifecycle"""
        try:
            self.logger.info(f"Starting module {self.module_name}")
            
            # Initialize ZeroMQ
            self.context = zmq.asyncio.Context()
            self.socket = self.context.socket(zmq.ROUTER)
            bind_address = self.config.get('bind_address', f"tcp://*:{self.config.get('port', 5555)}")
            self.socket.bind(bind_address)
            
            # Initialize module
            if await self.initialize():
                self.status = ModuleStatus.RUNNING
                self.logger.info(f"Module {self.module_name} started successfully")
                
                # Start message processing loop
                await self._message_loop()
            else:
                self.status = ModuleStatus.ERROR
                self.logger.error(f"Module {self.module_name} failed to initialize")
                
        except Exception as e:
            self.status = ModuleStatus.ERROR
            self.logger.error(f"Error starting module {self.module_name}: {e}")
            raise

    async def _message_loop(self) -> None:
        """Main message processing loop"""
        while self.status == ModuleStatus.RUNNING:
            try:
                # Poll for messages with timeout
                if await self.socket.poll(timeout=1000):
                    frames = await self.socket.recv_multipart()
                    if len(frames) >= 2:
                        client_id = frames[0]
                        message_data = frames[1].decode('utf-8')
                        
                        # Process message
                        message = Message.from_json(message_data)
                        response = await self._handle_message(message)
                        
                        # Send response if generated
                        if response:
                            await self.socket.send_multipart([
                                client_id,
                                response.to_json().encode('utf-8')
                            ])
                            
                # Update health metrics
                self._health_metrics['last_activity'] = time.time()
                
            except Exception as e:
                self.logger.error(f"Error in message loop: {e}")
                self._health_metrics['errors_count'] += 1

    async def _handle_message(self, message: Message) -> Optional[Message]:
        """Handle incoming message with error handling and metrics"""
        try:
            with self._lock:
                self._health_metrics['messages_processed'] += 1
            
            self.logger.debug(f"Processing message: {message.type.value} from {message.source}")
            
            # Handle system messages
            if message.type == MessageType.HEALTH_CHECK:
                return self._create_health_response(message)
            elif message.type == MessageType.SHUTDOWN:
                self.status = ModuleStatus.SHUTDOWN
                await self.shutdown()
                return None
            
            # Delegate to module-specific handler
            response = await self.process_message(message)
            
            self.logger.debug(f"Message processed successfully")
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self._health_metrics['errors_count'] += 1
            
            # Return error response
            return Message(
                id=str(uuid.uuid4()),
                type=MessageType.RESPONSE,
                source=self.module_name,
                target=message.source,
                timestamp=time.time(),
                payload={'error': str(e), 'success': False},
                correlation_id=message.id
            )

    def _create_health_response(self, message: Message) -> Message:
        """Create health check response"""
        uptime = time.time() - self._startup_time
        
        health_data = {
            'module': self.module_name,
            'status': self.status.value,
            'uptime_seconds': uptime,
            'metrics': self._health_metrics.copy(),
            'config': {k: v for k, v in self.config.items() if k not in ['secrets', 'api_keys']}
        }
        
        return Message(
            id=str(uuid.uuid4()),
            type=MessageType.RESPONSE,
            source=self.module_name,
            target=message.source,
            timestamp=time.time(),
            payload=health_data,
            correlation_id=message.id
        )

    async def send_message(self, target: str, message_type: MessageType, payload: Dict[str, Any]) -> None:
        """Send message to another module"""
        message = Message(
            id=str(uuid.uuid4()),
            type=message_type,
            source=self.module_name,
            target=target,
            timestamp=time.time(),
            payload=payload
        )
        
        # TODO: Implement message routing through message bus
        self.logger.debug(f"Sending message to {target}: {message_type.value}")


class MessageBus:
    """
    Lightweight message bus for inter-module communication.
    Implements pub/sub and request/response patterns using ZeroMQ.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("aura.messagebus")
        self.context = zmq.asyncio.Context()
        self.frontend = None  # Router socket for clients
        self.backend = None   # Dealer socket for workers
        self.running = False
        self.module_registry: Dict[str, Dict[str, Any]] = {}

    async def start(self) -> None:
        """Start the message bus"""
        try:
            self.logger.info("Starting Aura Message Bus")
            
            # Setup sockets
            self.frontend = self.context.socket(zmq.ROUTER)
            self.backend = self.context.socket(zmq.DEALER)
            
            frontend_port = self.config.get('frontend_port', 5559)
            backend_port = self.config.get('backend_port', 5560)
            
            self.frontend.bind(f"tcp://*:{frontend_port}")
            self.backend.bind(f"tcp://*:{backend_port}")
            
            self.running = True
            self.logger.info(f"Message bus started - Frontend: {frontend_port}, Backend: {backend_port}")
            
            # Start routing
            await self._route_messages()
            
        except Exception as e:
            self.logger.error(f"Failed to start message bus: {e}")
            raise

    async def _route_messages(self) -> None:
        """Route messages between frontend and backend"""
        poller = zmq.asyncio.Poller()
        poller.register(self.frontend, zmq.POLLIN)
        poller.register(self.backend, zmq.POLLIN)
        
        while self.running:
            try:
                socks = dict(await poller.poll(timeout=1000))
                
                if self.frontend in socks:
                    frames = await self.frontend.recv_multipart()
                    await self.backend.send_multipart(frames)
                
                if self.backend in socks:
                    frames = await self.backend.recv_multipart()
                    await self.frontend.send_multipart(frames)
                    
            except Exception as e:
                self.logger.error(f"Error in message routing: {e}")

    def register_module(self, module_name: str, module_info: Dict[str, Any]) -> None:
        """Register a module with the message bus"""
        self.module_registry[module_name] = {
            'info': module_info,
            'registered_at': time.time(),
            'last_heartbeat': time.time()
        }
        self.logger.info(f"Module registered: {module_name}")

    async def shutdown(self) -> None:
        """Shutdown the message bus"""
        self.logger.info("Shutting down message bus")
        self.running = False
        
        if self.frontend:
            self.frontend.close()
        if self.backend:
            self.backend.close()
        
        self.context.term()


class DependencyInjection:
    """
    Simple dependency injection container for managing module dependencies.
    """

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self.logger = logging.getLogger("aura.di")

    def register_service(self, name: str, service: Any) -> None:
        """Register a service instance"""
        self._services[name] = service
        self.logger.debug(f"Service registered: {name}")

    def register_factory(self, name: str, factory: Callable) -> None:
        """Register a factory function for creating services"""
        self._factories[name] = factory
        self.logger.debug(f"Factory registered: {name}")

    def register_singleton(self, name: str, factory: Callable) -> None:
        """Register a singleton service"""
        self._singletons[name] = factory
        self.logger.debug(f"Singleton registered: {name}")

    def get_service(self, name: str) -> Any:
        """Get a service by name"""
        # Check for direct service
        if name in self._services:
            return self._services[name]
        
        # Check for singleton
        if name in self._singletons:
            if name not in self._services:
                self._services[name] = self._singletons[name]()
            return self._services[name]
        
        # Check for factory
        if name in self._factories:
            return self._factories[name]()
        
        raise ValueError(f"Service not found: {name}")

    def inject_dependencies(self, obj: Any) -> None:
        """Inject dependencies into an object based on type hints"""
        # Simple implementation - can be extended for more sophisticated injection
        for attr_name in dir(obj):
            if attr_name.startswith('_inject_'):
                service_name = attr_name[8:]  # Remove '_inject_' prefix
                if hasattr(obj, attr_name) and getattr(obj, attr_name) is None:
                    try:
                        service = self.get_service(service_name)
                        setattr(obj, attr_name, service)
                        self.logger.debug(f"Injected {service_name} into {obj.__class__.__name__}")
                    except ValueError:
                        self.logger.warning(f"Could not inject {service_name} into {obj.__class__.__name__}")


# Global dependency injection container
aura_di = DependencyInjection()


def aura_service(name: str):
    """Decorator to register a class as a service"""
    def decorator(cls):
        aura_di.register_factory(name, cls)
        return cls
    return decorator


def aura_singleton(name: str):
    """Decorator to register a class as a singleton service"""
    def decorator(cls):
        aura_di.register_singleton(name, cls)
        return cls
    return decorator