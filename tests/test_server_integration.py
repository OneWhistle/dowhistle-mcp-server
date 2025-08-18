import pytest
from aiohttp import ClientSession


@pytest.mark.asyncio
async def test_health_and_ready_endpoints(running_server, assert_status_ok, assert_status_ready):
    """End-to-end: MCP server exposes working health and readiness probes."""
    port = running_server

    async with ClientSession() as session:
        await assert_status_ok(session, f"http://localhost:{port}/healthz")
        await assert_status_ready(session, f"http://localhost:{port}/readyz")
