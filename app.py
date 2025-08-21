import structlog
from fastmcp import FastMCP
from starlette.responses import JSONResponse

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


def create_app():
    """Create and configure MCP server with all agents"""
    mcp = FastMCP("Whistle MCP Server")

    # Register all agents
    SearchAgent(mcp)
    AuthAgent(mcp)
    WhistleAgent(mcp)
    UserAgent(mcp)

    # Add health check endpoint
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request):
        return JSONResponse(
            {
                "status": "healthy",
                "service": "whistle-mcp-server",
                "environment": settings.ENVIRONMENT,
            }
        )

    logger.info("MCP server created with all agents registered")
    return mcp.http_app()


# Create the ASGI app - Uvicorn will use this
app = create_app()
