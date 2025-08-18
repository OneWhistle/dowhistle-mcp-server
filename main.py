import asyncio
import signal
import sys
import structlog
from fastmcp import FastMCP
from aiohttp import web  # lightweight async web server

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


async def handle_health(request):
    return web.json_response({"status": "ok"})


async def handle_ready(request):
    if ready_event.is_set():
        return web.json_response({"status": "ready"})
    return web.json_response({"status": "not ready"}, status=503)


async def start_http_server():
    """Start aiohttp server for health/readiness probes"""
    app = web.Application()
    app.router.add_get("/healthz", handle_health)
    app.router.add_get("/readyz", handle_ready)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.HEALTH_PORT)
    await site.start()

    logger.info("Health/readiness server started", port=settings.HEALTH_PORT)
    return runner


async def stop_http_server(runner: web.AppRunner):
    logger.info("Stopping health/readiness server...")
    await runner.cleanup()

async def run_mcp_with_ready(mcp: FastMCP):
    ready_event.set()
    logger.info("MCP server marked as ready")
    await mcp.run_async(transport="stdio")    


# ---- Main entry point ----
async def main():
    logger.info(
        "Starting MCP server",
        port=settings.MCP_SERVER_PORT,
        api_base_url=settings.EXPRESS_API_BASE_URL
    )

    mcp = create_mcp_server()

    # Start MCP server as background task
    server_task = asyncio.create_task(run_mcp_with_ready(mcp))

    # Mark as ready once MCP is initialized
    async def mark_ready():
        await asyncio.sleep(1)  # adjust if MCP init takes longer
        ready_event.set()
        logger.info("MCP server marked as ready")

    asyncio.create_task(mark_ready())

    # Start health server
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
    await stop_event.wait()

    # Shutdown sequence
    logger.info("Stopping MCP server...")
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        logger.info("MCP server shut down cleanly")

    await stop_http_server(http_runner)


if __name__ == "__main__":
    asyncio.run(main())
