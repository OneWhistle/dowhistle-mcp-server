from fastmcp import FastMCP
from typing import Dict, Any
import structlog
from utils.http_client import api_client

logger = structlog.get_logger()

class UserAgent:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self.register_tools()
    
    def register_tools(self):
        @self.mcp.tool()
        async def toggle_live_tracking(user_id: str, enabled: bool) -> Dict[str, Any]:
            """
            Toggle live tracking for a user
            
            Args:
                user_id: User ID
                enabled: Whether to enable live tracking
            """
            try:
                payload = {"live_tracking_enabled": enabled}
                
                result = await api_client.request(
                    method="PUT",
                    endpoint=f"/users/{user_id}/settings",
                    data=payload
                )
                
                logger.info(
                    "Live tracking toggled", 
                    user_id=user_id, 
                    enabled=enabled
                )
                
                return {
                    "success": True,
                    "data": result,
                    "message": f"Live tracking {'enabled' if enabled else 'disabled'}"
                }
                
            except Exception as e:
                logger.error("Live tracking toggle failed", error=str(e), user_id=user_id)
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp.tool()
        async def toggle_visibility(user_id: str, visible: bool) -> Dict[str, Any]:
            """
            Toggle user visibility
            
            Args:
                user_id: User ID
                visible: Whether user should be visible
            """
            try:
                payload = {"is_visible": visible}
                
                result = await api_client.request(
                    method="PUT",
                    endpoint=f"/users/{user_id}/settings",
                    data=payload
                )
                
                logger.info("Visibility toggled", user_id=user_id, visible=visible)
                
                return {
                    "success": True,
                    "data": result,
                    "message": f"User {'visible' if visible else 'hidden'}"
                }
                
            except Exception as e:
                logger.error("Visibility toggle failed", error=str(e), user_id=user_id)
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp.tool()
        async def toggle_whistle_sound(user_id: str, enabled: bool) -> Dict[str, Any]:
            """
            Toggle whistle sound notifications
            
            Args:
                user_id: User ID
                enabled: Whether to enable whistle sounds
            """
            try:
                payload = {"whistle_sound_enabled": enabled}
                
                result = await api_client.request(
                    method="PUT",
                    endpoint=f"/users/{user_id}/settings",
                    data=payload
                )
                
                logger.info("Whistle sound toggled", user_id=user_id, enabled=enabled)
                
                return {
                    "success": True,
                    "data": result,
                    "message": f"Whistle sound {'enabled' if enabled else 'disabled'}"
                }
                
            except Exception as e:
                logger.error("Whistle sound toggle failed", error=str(e), user_id=user_id)
                return {
                    "success": False,
                    "error": str(e)
                }