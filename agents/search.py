from fastmcp import FastMCP
from typing import Optional, Dict, Any
import structlog
from utils.http_client import api_client
from models.search_model import Provider, SearchNearMeResponse

logger = structlog.get_logger()


class SearchAgent:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self.register_tools()

    def register_tools(self):
        @self.mcp.tool()
        async def search(
            latitude: float,
            longitude: float,
            radius: float = 2.0,
            keyword: Optional[str] = None,
            category: Optional[str] = None,
            limit: int = 100,
        ) -> Dict[str, Any]:
            """
            Search for providers near a specific location.
            
            Args:
                latitude: The latitude coordinate of the search location
                longitude: The longitude coordinate of the search location
                radius: Search radius in kilometers (default: 2.0)
                keyword: Optional keyword to search for (e.g., "mechanic", "restaurant")
                category: Optional category filter (e.g., "revamp", "service", "business")
                limit: Maximum number of results to return (default: 100)
            
            Returns:
                A dictionary containing providers found near the location
            """
            try:
                payload = {
                    "category": category,
                    "keyword": keyword or "",
                    "limit": limit,
                    "location": [longitude, latitude],
                    "provider": True,
                    "radius": radius,
                    "visible": True,
                }

                result = await api_client.request(
                    method="POST",
                    endpoint="/searchAround",
                    data=payload,
                )

                logger.info(
                    "Search completed",
                    query=keyword,
                    results_count=len(result.get("results", [])),
                )

                providers = []

                # Normalize response
                data = result
                if isinstance(data, dict):
                    providers_data = data.get("providers", [])
                    if not providers_data and "matchingWhistles" in data:
                        providers_data = data.get("matchingWhistles", [])
                elif isinstance(data, list):
                    providers_data = data
                else:
                    providers_data = []

                for provider_data in providers_data:
                    if "item" in provider_data:  # matchingWhistles format
                        item = provider_data["item"]
                        provider = Provider(
                            id=item.get("_id", ""),
                            name=item.get("name", ""),
                            address=item.get("location", {}).get("address", ""),
                            distance=provider_data.get("dis", 0.0),
                            latitude=(
                                item.get("location", {}).get("coordinates", [0, 0])[1]
                                if item.get("location", {}).get("coordinates")
                                else 0.0
                            ),
                            longitude=(
                                item.get("location", {}).get("coordinates", [0, 0])[0]
                                if item.get("location", {}).get("coordinates")
                                else 0.0
                            ),
                            category=category,
                            rating=provider_data.get("score"),
                        )
                    else:  # direct provider format
                        provider = Provider(
                            id=provider_data.get("id", str(provider_data.get("_id", ""))),
                            name=provider_data.get("name", provider_data.get("title", "")),
                            address=provider_data.get("address", provider_data.get("location", "")),
                            distance=provider_data.get("distance", 0.0),
                            latitude=provider_data.get("latitude", provider_data.get("lat", 0.0)),
                            longitude=provider_data.get("longitude", provider_data.get("lng", 0.0)),
                            category=provider_data.get("category"),
                            rating=provider_data.get("rating", provider_data.get("score", None)),
                        )
                    providers.append(provider)

                response = SearchNearMeResponse(
                    providers=providers,
                    total_count=len(providers),
                    search_radius=radius,
                    search_location={
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                )

                # ✅ Always return JSON-safe dict
                return response.model_dump()

            except Exception as e:
                logger.error("Search failed", error=str(e))

                error_response = SearchNearMeResponse(
                    providers=[],
                    total_count=0,
                    search_radius=radius,
                    search_location={
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                )

                # ✅ Include error info in JSON response
                resp = error_response.model_dump()
                resp["error"] = f"Unexpected error: {str(e)}"
                return resp
