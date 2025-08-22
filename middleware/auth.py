import structlog
from typing import Dict, Any
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError

logger = structlog.get_logger()

class AuthMiddleware(Middleware):
    """Authorization middleware for protected tools"""
    
    # Define which tools require authentication
    PROTECTED_TOOLS = {
        'toggle_visibility',
        'get_user_profile', 
        'create_whistle',
        'list_whistles'
    }
    
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Check authentication for protected tools"""
        
        tool_name = context.message.name
        
        # Skip auth for public tools
        if tool_name not in self.PROTECTED_TOOLS:
            return await call_next(context)
        
        # Check if access token exists
        access_token = context.message.arguments.get('access_token')
        
        if not access_token or not isinstance(access_token, str):
            logger.warning(f"Protected tool accessed without valid token: {tool_name}")
            raise ToolError("Authentication required. Please sign in first.")
        
        # Token exists, let Express server validate it
        logger.info(f"Token provided for protected tool: {tool_name}")
        return await call_next(context)