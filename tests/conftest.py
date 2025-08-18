import pytest
import asyncio
from fastmcp import FastMCP
from agents.search import SearchAgent
from agents.auth import AuthAgent
from agents.whistle import WhistleAgent
from agents.user import UserAgent
from main import create_mcp_server, run_mcp_with_ready, start_http_server, stop_http_server, ready_event
from config.settings import settings
from utils.mcp_helpers import get_tool


async def _assert_status(client, path: str, expected: str, code: int = 200):
    """Helper to assert JSON {status: expected} responses."""
    resp = await client.get(path)
    assert resp.status == code
    data = await resp.json()
    assert data["status"] == expected
    return data


@pytest.fixture
def assert_status_ok():
    """Fixture to assert {status: ok} with 200."""
    async def _assert(client, path: str):
        return await _assert_status(client, path, expected="ok", code=200)
    return _assert


@pytest.fixture
def assert_status_ready():
    """Fixture to assert {status: ready} with 200."""
    async def _assert(client, path: str):
        return await _assert_status(client, path, expected="ready", code=200)
    return _assert


@pytest.fixture
def assert_status_not_ready():
    """Fixture to assert {status: not ready} with 503."""
    async def _assert(client, path: str):
        return await _assert_status(client, path, expected="not ready", code=503)
    return _assert


@pytest.fixture
def search_tool(monkeypatch):
    """
    Fixture that provides the `search` tool with an overridable API client.
    """

    def _make(mock_request_fn):
        mcp = FastMCP("Test MCP")
        # Patch the API client before registering tools
        from utils import http_client
        monkeypatch.setattr(http_client.api_client, "request", mock_request_fn)
        SearchAgent(mcp)
        return mcp._tools["search"]

    return _make


@pytest.fixture
def mcp_server():
    """Fixture: full MCP server with all agents registered."""
    mcp = FastMCP("Test MCP Server")
    SearchAgent(mcp)
    AuthAgent(mcp)
    WhistleAgent(mcp)
    UserAgent(mcp)
    return mcp


@pytest.fixture
async def running_server():
    """
    Fixture: starts MCP server and health endpoints for integration tests.
    Yields the health port, cleans up on teardown.
    """
    mcp = create_mcp_server()
    server_task = asyncio.create_task(run_mcp_with_ready(mcp))

    http_runner = await start_http_server()
    await asyncio.wait_for(ready_event.wait(), timeout=5)

    yield settings.HEALTH_PORT

    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass
    await stop_http_server(http_runner)
