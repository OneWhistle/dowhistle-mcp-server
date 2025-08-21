import asyncio
import signal
import sys
import datetime
import structlog
from fastmcp import FastMCP
from aiohttp import web
import json
from typing import Dict, Any

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
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def create_mcp_server() -> FastMCP:
    """Create and configure MCP server with all agents"""
    mcp = FastMCP("Whistle MCP Server")
    SearchAgent(mcp)
    AuthAgent(mcp)
    WhistleAgent(mcp)
    UserAgent(mcp)
    logger.info("MCP server created with all agents registered")
    return mcp


# ---- Health & readiness ----
ready_event = asyncio.Event()
mcp_server_instance = None


async def handle_health(request):
    import datetime
    return web.json_response({
        "status": "ok", 
        "timestamp": datetime.datetime.now().isoformat()
    })


async def handle_ready(request):
    if ready_event.is_set():
        return web.json_response({
            "status": "ready",
            "server_info": settings.server_info,
            "timestamp": datetime.datetime.now().isoformat()
        })
    return web.json_response({
        "status": "not ready",
        "timestamp": datetime.datetime.now().isoformat()
    }, status=503)


# ---- MCP JSON-RPC 2.0 Handler ----
async def handle_mcp_request(request):
    """Handle MCP JSON-RPC 2.0 requests"""
    try:
        global mcp_server_instance
        if not mcp_server_instance:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": "MCP server not initialized"},
                "id": None
            }, status=500)

        data = await request.json()
        logger.info("Received MCP request", method=data.get("method"), id=data.get("id"))
        
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")

        # Handle MCP protocol methods
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {},
                    },
                    "serverInfo": {
                        "name": "Whistle MCP Server",
                        "version": "1.0.0"
                    }
                },
                "id": request_id
            }
            return web.json_response(response)
            
        elif method == "notifications/initialized":
            # This is a notification, no response needed
            logger.info("MCP client initialized")
            return web.Response(status=204)
            
        elif method == "tools/list":
            # Get available tools from MCP server
            tools = []
            if hasattr(mcp_server_instance, '_tools'):
                for tool_name, tool_info in mcp_server_instance._tools.items():
                    tools.append({
                        "name": tool_name,
                        "description": getattr(tool_info, 'description', ''),
                        "inputSchema": getattr(tool_info, 'input_schema', {})
                    })
            
            response = {
                "jsonrpc": "2.0",
                "result": {"tools": tools},
                "id": request_id
            }
            return web.json_response(response)
            
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            logger.info("Calling tool", tool=tool_name, arguments=arguments)
            
            try:
                # Call the tool through FastMCP
                if hasattr(mcp_server_instance, '_tools') and tool_name in mcp_server_instance._tools:
                    tool = mcp_server_instance._tools[tool_name]
                    if hasattr(tool, 'func'):
                        # Call the tool function
                        result = await tool.func(**arguments)
                        
                        response = {
                            "jsonrpc": "2.0",
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": json.dumps(result) if isinstance(result, dict) else str(result)
                                    }
                                ]
                            },
                            "id": request_id
                        }
                        return web.json_response(response)
                    else:
                        raise ValueError(f"Tool {tool_name} has no callable function")
                else:
                    raise ValueError(f"Tool {tool_name} not found")
                    
            except Exception as e:
                logger.error("Tool call failed", tool=tool_name, error=str(e))
                response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Tool call failed: {str(e)}"
                    },
                    "id": request_id
                }
                return web.json_response(response, status=500)
        
        else:
            # Unknown method
            response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                },
                "id": request_id
            }
            return web.json_response(response, status=404)
            
    except Exception as e:
        logger.error("MCP request handling failed", error=str(e))
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            "id": data.get("id") if 'data' in locals() else None
        }, status=500)


async def start_http_server():
    """Start aiohttp server for health/readiness probes and MCP HTTP endpoints"""
    app = web.Application()
    
    # Health endpoints
    app.router.add_get("/healthz", handle_health)
    app.router.add_get("/readyz", handle_ready)
    
    # Debug endpoint to check MCP server status
    async def handle_debug(request):
        global mcp_server_instance
        return web.json_response({
            "server_initialized": mcp_server_instance is not None,
            "ready": ready_event.is_set(),
            "transport_mode": settings.TRANSPORT_MODE,
            "environment": settings.ENVIRONMENT,
            "tools_count": len(mcp_server_instance._tools) if mcp_server_instance and hasattr(mcp_server_instance, '_tools') else 0,
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    app.router.add_get("/debug", handle_debug)
    
    # MCP JSON-RPC endpoint
    if settings.is_http_transport:
        app.router.add_post("/mcp", handle_mcp_request)
        app.router.add_options("/mcp", lambda r: web.Response(
            status=200,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': '86400'
            }
        ))
        logger.info("Added MCP JSON-RPC endpoint at /mcp")

    # Add CORS headers for cross-origin requests
    cors_origins = settings.CORS_ORIGINS.split(',') if settings.CORS_ORIGINS != '*' else ['*']
    
    @web.middleware
    async def add_cors_headers(request, handler):
        # Handle CORS preflight requests
        if request.method == "OPTIONS":
            response = web.Response()
        else:
            response = await handler(request)
            
        origin = request.headers.get('Origin')
        if settings.CORS_ORIGINS == '*' or (origin and origin in cors_origins):
            response.headers['Access-Control-Allow-Origin'] = origin or '*'
        response.headers['Access-Control-Allow-Methods'] = settings.CORS_METHODS
        response.headers['Access-Control-Allow-Headers'] = settings.CORS_HEADERS
        response.headers['Access-Control-Max-Age'] = '86400'  # Cache preflight for 24 hours
        return response

    app.middlewares.append(add_cors_headers)

    runner = web.AppRunner(app)
    await runner.setup()
    
    # Use settings for port configuration
    site = web.TCPSite(runner, "0.0.0.0", settings.HEALTH_PORT)
    await site.start()

    logger.info(
        "HTTP server started", 
        port=settings.HEALTH_PORT, 
        transport_mode=settings.TRANSPORT_MODE,
        environment=settings.ENVIRONMENT
    )
    return runner


async def stop_http_server(runner: web.AppRunner):
    logger.info("Stopping HTTP server...")
    await runner.cleanup()


async def run_mcp_stdio(mcp: FastMCP):
    """Run MCP server with stdio transport (development)"""
    ready_event.set()
    logger.info("MCP server marked as ready (stdio transport)")
    await mcp.run_async(transport="stdio")


async def run_mcp_http(mcp: FastMCP):
    """Run MCP server with HTTP transport (production)"""
    global mcp_server_instance
    mcp_server_instance = mcp
    ready_event.set()
    logger.info("MCP server marked as ready (HTTP transport)")
    
    # For HTTP transport, the server logic is handled by the HTTP endpoints
    # Keep this task running to maintain the server state
    stop_event = asyncio.Event()
    await stop_event.wait()


def get_transport_mode():
    """Get transport mode from settings"""
    return settings.TRANSPORT_MODE


# ---- Main entry point ----
async def main():
    logger.info("Starting MCP server with configuration", **settings.server_info)

    mcp = create_mcp_server()

    # Start MCP server based on transport mode
    if settings.is_http_transport:
        logger.info("Using HTTP transport for production")
        server_task = asyncio.create_task(run_mcp_http(mcp))
    else:
        logger.info("Using stdio transport for development")
        server_task = asyncio.create_task(run_mcp_stdio(mcp))

    # Always start HTTP server for health checks (and MCP endpoints in production)
    http_runner = await start_http_server()

    # Setup signal handling
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def handle_shutdown(sig):
        logger.info("Received shutdown signal", signal=sig)
        stop_event.set()

    if sys.platform == "win32":
        # Windows: fallback to signal.signal()
        signal.signal(signal.SIGINT, lambda s, f: handle_shutdown("SIGINT"))
        signal.signal(signal.SIGTERM, lambda s, f: handle_shutdown("SIGTERM"))
    else:
        # Unix/Linux/K8s: asyncio-friendly signals
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: handle_shutdown(s))

    # Wait for shutdown
    try:
        await stop_event.wait()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")

    # Shutdown sequence
    logger.info("Stopping MCP server...")
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        logger.info("MCP server shut down cleanly")

    await stop_http_server(http_runner)
    logger.info("Server shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception as e:
        logger.error("Server failed to start", error=str(e))
        sys.exit(1)