import pytest
from aiohttp import web
from main import handle_health, handle_ready, ready_event


@pytest.mark.asyncio
async def test_healthz_ok(aiohttp_client, assert_status_ok):
    """Health endpoint should always return status=ok"""
    app = web.Application()
    app.router.add_get("/healthz", handle_health)

    client = await aiohttp_client(app)
    await assert_status_ok(client, "/healthz")


@pytest.mark.asyncio
async def test_readyz_not_ready(aiohttp_client, assert_status_not_ready):
    """Readiness should return 503 until ready_event is set"""
    ready_event.clear()

    app = web.Application()
    app.router.add_get("/readyz", handle_ready)

    client = await aiohttp_client(app)
    await assert_status_not_ready(client, "/readyz")


@pytest.mark.asyncio
async def test_readyz_ready(aiohttp_client, assert_status_ready):
    """Readiness should return 200 once ready_event is set"""
    ready_event.set()

    app = web.Application()
    app.router.add_get("/readyz", handle_ready)

    client = await aiohttp_client(app)
    await assert_status_ready(client, "/readyz")
