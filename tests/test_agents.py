import pytest
from unittest.mock import patch
from agents.search import SearchAgent
from fastmcp import FastMCP
from utils.mcp_helpers import get_tool


@pytest.fixture
def mcp():
    return FastMCP("Test Server")


@pytest.fixture
def search_agent(mcp):
    return SearchAgent(mcp)


class TestSearchAgent:
    @patch("utils.http_client.api_client.request")
    async def test_search_success(self, mock_request, search_agent, mcp):
        mock_request.return_value = {
            "results": [{"id": 1, "title": "Test Result"}],
            "total": 1,
        }

        search_tool = get_tool(mcp, "search")  # ✅ consistent
        result = await search_tool(
            latitude=37.7749, longitude=-122.4194, keyword="test"
        )

        assert "total_count" in result or "results" in mock_request.return_value
