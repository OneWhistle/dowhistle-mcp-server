from fastmcp import FastMCP
from typing import Optional, Dict, Any
import structlog
from utils.http_client import api_client
from models.search_model import Provider, SearchNearMeResponse
from utils.helper import compute_feedback_rating

logger = structlog.get_logger()


class SearchAgent:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self.register_tools()

    def register_tools(self):
        @self.mcp.tool()
        async def search_businesses(
            latitude: float,
            longitude: float,
            radius: int = 10,
            keyword: str = None,
            category: Optional[str] = None,
            limit: int = 100,
        ) -> Dict[str, Any]:
            """
            Search for providers near a specific location.
            
            Args:
                latitude: The latitude coordinate of the search location
                longitude: The longitude coordinate of the search location
                radius: Search radius in kilometers (default: 10)
                keyword: Keyword to search for (e.g., "mechanic", "restaurant")
                category: Optional category filter (e.g., "revamp", "service", "business")
                limit: Maximum number of results to return (default: 100)
            
            Returns:
                A dictionary containing providers found near the location
            """
            try:
                payload = {
                    "category": category or "revamp",
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
                            phone=f"{item.get('countryCode', '')} {item.get('phone', '')}",

                            address=item.get("location", {}).get("address", ""),
                            distance=round(item.get("dis", 0.0), 1),
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
                            rating=compute_feedback_rating(item),
                        )
                    else:  # direct provider format
                        provider = Provider(
                            id=provider_data.get("id", str(provider_data.get("_id", ""))),
                            name=provider_data.get("name", provider_data.get("title", "")),
                            phone=f"{provider_data.get('countryCode', '')} {provider_data.get('phone', '')}",
                            address=provider_data.get("address", provider_data.get("location", "")),
                            distance=round(provider_data.get("distance", 0.0), 1),  
                            latitude=provider_data.get("latitude", provider_data.get("lat", 0.0)),
                            longitude=provider_data.get("longitude", provider_data.get("lng", 0.0)),
                            category=provider_data.get("category"),
                                rating=compute_feedback_rating(provider_data),
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
