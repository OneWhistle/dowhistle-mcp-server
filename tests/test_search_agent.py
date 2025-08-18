import pytest


@pytest.mark.asyncio
async def test_search_success(search_tool):
    """Search tool returns valid providers when API client succeeds."""

    async def mock_request(method, endpoint, data):
        return {
            "providers": [
                {
                    "id": "123",
                    "name": "Test Provider",
                    "address": "123 Main St",
                    "distance": 1.2,
                    "latitude": 37.7749,
                    "longitude": -122.4194,
                    "category": "service",
                    "rating": 4.5,
                }
            ]
        }

    search = search_tool(mock_request)

    result = await search(
        latitude=37.7749,
        longitude=-122.4194,
        radius=5.0,
        keyword="test",
        category="service",
        limit=10,
    )

    assert "providers" in result
    assert result["total_count"] == 1
    assert result["providers"][0]["name"] == "Test Provider"
    assert result["providers"][0]["rating"] == 4.5


@pytest.mark.asyncio
async def test_search_error(search_tool):
    """Search tool returns error response when API client raises exception."""

    async def mock_request_fail(method, endpoint, data):
        raise RuntimeError("API down")

    search = search_tool(mock_request_fail)

    result = await search(
        latitude=37.7749,
        longitude=-122.4194,
        radius=5.0,
    )

    assert "error" in result
    assert result["providers"] == []
    assert result["total_count"] == 0
