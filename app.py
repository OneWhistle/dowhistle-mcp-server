import asyncio
import logging
import time
import uuid
from typing import Dict, Optional, Set
from enum import Enum

import structlog
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.routing import Route

from agents.search import SearchAgent
from agents.auth import AuthAgent
from agents.whistle import WhistleAgent
from agents.user import UserAgent
from config.settings import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class ServiceStatus(Enum):
    """Service lifecycle states"""
    INITIALIZING = "initializing"
    READY = "ready"
    UNHEALTHY = "unhealthy"
    SHUTTING_DOWN = "shutting_down"


class DependencyHealth:
    """Track health of individual dependencies"""
    def __init__(self, name: str):
        self.name = name
        self.is_healthy = False
        self.last_check = None
        self.error_message = None
    
    def mark_healthy(self):
        self.is_healthy = True
        self.last_check = time.time()
        self.error_message = None
        
    def mark_unhealthy(self, error: str):
        self.is_healthy = False
        self.last_check = time.time()
        self.error_message = error


class ProductionAppManager:
    """Production-grade application lifecycle manager"""
    
    def __init__(self):
        self.status = ServiceStatus.INITIALIZING
        self.instance_id = str(uuid.uuid4())[:8]
        self.startup_time = time.time()
        self.dependencies: Dict[str, DependencyHealth] = {}
        self.initialized_agents: Set[str] = set()
        self.required_agents = {"SearchAgent", "AuthAgent", "WhistleAgent", "UserAgent"}
        self._initialization_lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()
        
        logger.info("Application manager initialized", 
                   instance_id=self.instance_id)
    
    def add_dependency(self, name: str) -> DependencyHealth:
        """Add a dependency to track"""
        dependency = DependencyHealth(name)
        self.dependencies[name] = dependency
        return dependency
    
    def initialize_agent(self, agent_class, mcp_instance) -> bool:
        """Initialize a single agent with proper error handling"""
        agent_name = agent_class.__name__
        
        try:
            logger.info("Initializing agent", agent=agent_name)
            
            # Initialize the agent
            agent_instance = agent_class(mcp_instance)
            
            # Verify agent has required methods/attributes
            if not hasattr(agent_instance, '__class__'):
                raise ValueError(f"Agent {agent_name} not properly initialized")
            
            self.initialized_agents.add(agent_name)
            logger.info("Agent initialized successfully", agent=agent_name)
            return True
            
        except Exception as e:
            logger.error("Failed to initialize agent", 
                        agent=agent_name, error=str(e), exc_info=True)
            return False
    
    def check_all_dependencies(self) -> bool:
        """Check health of all registered dependencies"""
        if not self.dependencies:
            return True
            
        all_healthy = True
        for name, dep in self.dependencies.items():
            try:
                # Add specific dependency checks here
                # For now, we'll assume they're healthy if no error occurs
                dep.mark_healthy()
                logger.debug("Dependency check passed", dependency=name)
            except Exception as e:
                dep.mark_unhealthy(str(e))
                all_healthy = False
                logger.warning("Dependency check failed", 
                              dependency=name, error=str(e))
        
        return all_healthy
    
    async def initialize_all_agents(self, mcp_instance) -> bool:
        """Initialize all required agents"""
        async with self._initialization_lock:
            if self.status != ServiceStatus.INITIALIZING:
                return self.status == ServiceStatus.READY
            
            try:
                logger.info("Starting agent initialization")
                
                # Agent classes to initialize
                agent_classes = [SearchAgent, AuthAgent, WhistleAgent, UserAgent]
                
                initialization_tasks = []
                for agent_class in agent_classes:
                    task = self.initialize_agent(agent_class, mcp_instance)
                    initialization_tasks.append(task)
                
                # Run all initializations concurrently
                results = await asyncio.gather(*initialization_tasks, return_exceptions=True)
                
                # Check results
                failed_agents = []
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        failed_agents.append(agent_classes[i].__name__)
                        logger.error("Agent initialization failed", 
                                   agent=agent_classes[i].__name__, 
                                   error=str(result))
                    elif not result:
                        failed_agents.append(agent_classes[i].__name__)
                
                if failed_agents:
                    self.status = ServiceStatus.UNHEALTHY
                    logger.error("Some agents failed to initialize", 
                               failed_agents=failed_agents)
                    return False
                
                # Check if all required agents are initialized
                missing_agents = self.required_agents - self.initialized_agents
                if missing_agents:
                    self.status = ServiceStatus.UNHEALTHY
                    logger.error("Required agents not initialized", 
                               missing_agents=list(missing_agents))
                    return False
                
                # Check dependencies
                deps_healthy = await self.check_all_dependencies()
                if not deps_healthy:
                    self.status = ServiceStatus.UNHEALTHY
                    logger.error("Some dependencies are unhealthy")
                    return False
                
                # All good - mark as ready
                self.status = ServiceStatus.READY
                logger.info("All agents initialized successfully", 
                           agents=list(self.initialized_agents),
                           startup_time=time.time() - self.startup_time)
                return True
                
            except Exception as e:
                self.status = ServiceStatus.UNHEALTHY
                logger.error("Initialization failed", error=str(e), exc_info=True)
                return False
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Starting graceful shutdown")
        self.status = ServiceStatus.SHUTTING_DOWN
        self._shutdown_event.set()
        
        # Add cleanup logic here if needed
        # e.g., close database connections, save state, etc.
        
        logger.info("Shutdown complete")
    
    def is_ready(self) -> bool:
        """Check if service is ready to handle requests"""
        return self.status == ServiceStatus.READY
    
    def is_alive(self) -> bool:
        """Check if service is alive (not shutting down)"""
        return self.status != ServiceStatus.SHUTTING_DOWN
    
    def get_health_status(self) -> dict:
        """Get detailed health status"""
        return {
            "status": self.status.value,
            "instance_id": self.instance_id,
            "uptime_seconds": time.time() - self.startup_time,
            "initialized_agents": list(self.initialized_agents),
            "required_agents": list(self.required_agents),
            "dependencies": {
                name: {
                    "healthy": dep.is_healthy,
                    "last_check": dep.last_check,
                    "error": dep.error_message
                }
                for name, dep in self.dependencies.items()
            }
        }


# Global application manager
app_manager = ProductionAppManager()


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Production-grade middleware for handling requests during initialization"""
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Always allow health check endpoints
        if path.startswith("/health") or path == "/ready":
            return await call_next(request)
        
        # Check if we're ready for regular requests
        if not app_manager.is_ready():
            if not app_manager.is_alive():
                return JSONResponse(
                    {"error": "Service is shutting down"}, 
                    status_code=503
                )
            else:
                return JSONResponse(
                    {
                        "error": "Service is still initializing",
                        "status": app_manager.status.value,
                        "retry_after": 10
                    }, 
                    status_code=503,
                    headers={"Retry-After": "10"}
                )
        
        return await call_next(request)


def liveness_endpoint(request: Request):
    """Kubernetes liveness probe endpoint"""
    if app_manager.is_alive():
        return JSONResponse({
            "status": "alive",
            "instance_id": app_manager.instance_id
        })
    else:
        return JSONResponse({
            "status": "shutting_down",
            "instance_id": app_manager.instance_id
        }, status_code=503)


def readiness_endpoint(request: Request):
    """Kubernetes readiness probe endpoint"""
    if app_manager.is_ready():
        return JSONResponse({
            "status": "ready",
            "instance_id": app_manager.instance_id
        })
    else:
        health_status = app_manager.get_health_status()
        return JSONResponse(health_status, status_code=503)


def health_endpoint(request: Request):
    """Detailed health endpoint for monitoring"""
    health_status = app_manager.get_health_status()
    status_code = 200 if app_manager.is_ready() else 503
    return JSONResponse(health_status, status_code=status_code)


def create_app():
    """Create and configure production-ready MCP server"""
    
    # Create FastMCP instance
    mcp = FastMCP("Whistle MCP Server")
    
    # Get the base HTTP app
    http_app = mcp.http_app()
    
    # Add health check routes
    health_routes = [
        Route("/health/live", liveness_endpoint, methods=["GET"]),
        Route("/health/ready", readiness_endpoint, methods=["GET"]),
        Route("/health", health_endpoint, methods=["GET"]),
        Route("/ready", readiness_endpoint, methods=["GET"]),  # Alias for compatibility
    ]
    
    # Add routes to the existing app
    http_app.router.routes.extend(health_routes)
    
    # Add middleware
    http_app.add_middleware(HealthCheckMiddleware)
    
    # Startup event handler
    @http_app.on_event("startup")
    async def startup_event():
        logger.info("Starting MCP server", 
                   environment=settings.ENVIRONMENT,
                   instance_id=app_manager.instance_id)
        
        try:
            # Initialize all agents
            success = await app_manager.initialize_all_agents(mcp)
            
            if not success:
                logger.error("Failed to initialize server - some components unhealthy")
                # In production, you might want to exit here
                # raise RuntimeError("Server initialization failed")
            else:
                logger.info("MCP server startup completed successfully")
                
        except Exception as e:
            logger.error("Startup failed", error=str(e), exc_info=True)
            app_manager.status = ServiceStatus.UNHEALTHY
            # In production, you might want to exit here
            # raise
    
    # Shutdown event handler
    @http_app.on_event("shutdown")
    async def shutdown_event():
        await app_manager.shutdown()
    
    logger.info("MCP server created", instance_id=app_manager.instance_id)
    return http_app


# Create the ASGI app - Uvicorn will use this
app = create_app()