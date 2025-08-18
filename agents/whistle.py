from fastmcp import FastMCP
from typing import Dict, Any, Optional
import structlog
from utils.http_client import api_client

logger = structlog.get_logger()

class WhistleAgent:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self.register_tools()
    
    def register_tools(self):
        @self.mcp.tool()
        async def create_whistle(
            title: str,
            description: str,
            location: Dict[str, float],
            category: str,
            priority: Optional[str] = "medium",
            is_anonymous: Optional[bool] = False
        ) -> Dict[str, Any]:
            """
            Create a new whistle report
            
            Args:
                title: Whistle title
                description: Detailed description
                location: Location dict with lat, lng
                category: Whistle category
                priority: Priority level (low, medium, high)
                is_anonymous: Whether to create anonymously
            """
            try:
                payload = {
                    "title": title,
                    "description": description,
                    "location": location,
                    "category": category,
                    "priority": priority,
                    "is_anonymous": is_anonymous
                }
                
                result = await api_client.request(
                    method="POST",
                    endpoint="/whistles",
                    data=payload
                )
                
                logger.info("Whistle created successfully", whistle_id=result.get("id"))
                
                return {
                    "success": True,
                    "data": result
                }
                
            except Exception as e:
                logger.error("Whistle creation failed", error=str(e))
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp.tool()
        async def update_whistle(
            whistle_id: str,
            updates: Dict[str, Any]
        ) -> Dict[str, Any]:
            """
            Update an existing whistle
            
            Args:
                whistle_id: ID of the whistle to update
                updates: Dictionary of fields to update
            """
            try:
                result = await api_client.request(
                    method="PUT",
                    endpoint=f"/whistles/{whistle_id}",
                    data=updates
                )
                
                logger.info("Whistle updated successfully", whistle_id=whistle_id)
                
                return {
                    "success": True,
                    "data": result
                }
                
            except Exception as e:
                logger.error("Whistle update failed", error=str(e), whistle_id=whistle_id)
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp.tool()
        async def delete_whistle(whistle_id: str) -> Dict[str, Any]:
            """
            Delete a whistle
            
            Args:
                whistle_id: ID of the whistle to delete
            """
            try:
                await api_client.request(
                    method="DELETE",
                    endpoint=f"/whistles/{whistle_id}"
                )
                
                logger.info("Whistle deleted successfully", whistle_id=whistle_id)
                
                return {
                    "success": True,
                    "message": "Whistle deleted successfully"
                }
                
            except Exception as e:
                logger.error("Whistle deletion failed", error=str(e), whistle_id=whistle_id)
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp.tool()
        async def list_whistles(
            limit: Optional[int] = 10,
            offset: Optional[int] = 0,
            filters: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """
            List whistles with pagination and filters
            
            Args:
                limit: Number of whistles to return
                offset: Number of whistles to skip
                filters: Optional filters to apply
            """
            try:
                params = {
                    "limit": limit,
                    "offset": offset,
                    **(filters or {})
                }
                
                result = await api_client.request(
                    method="GET",
                    endpoint="/whistles",
                    params=params
                )
                
                logger.info("Whistles listed successfully", count=len(result.get("whistles", [])))
                
                return {
                    "success": True,
                    "data": result
                }
                
            except Exception as e:
                logger.error("Whistle listing failed", error=str(e))
                return {
                    "success": False,
                    "error": str(e)
                }