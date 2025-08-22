# agents/user.py
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
        async def toggle_visibility(access_token: str, visible: str) -> Dict[str, Any]:
            """
            Toggle user visibility status

            Args:
                access_token: User authentication token from sign_in or verify_otp
                visible: Whether the user should be visible ("true") or hidden ("false")
            """
            try:
                # Validate access_token
                if not access_token or not isinstance(access_token, str):
                    raise ValueError(
                        "Authentication needed — sign in first.")

                # Validate visible parameter
                if visible not in ["true", "false"]:
                    raise ValueError(
                        "visible must be either 'true' or 'false'.")

                payload = {"visible": visible}
                print("toggle_visibility payload:", payload)  # debug log

                result = await api_client.request(
                    method="PUT",
                    endpoint="/user",
                    data=payload,
                    headers={"Authorization": access_token}
                )

                logger.info("Visibility toggle successful", visible=visible)

                return {
                    "success": True,
                    "message": f"User visibility set to {visible}",
                    "data": result
                }

            except Exception as e:
                logger.error("Visibility toggle failed",
                             error=str(e), visible=visible)
                return {
                    "success": False,
                    "error": str(e),
                    "payload": locals().get("payload")
                }

        @self.mcp.tool()
        async def get_user_profile(access_token: str) -> Dict[str, Any]:
            """
            Get user profile details and whistles

            Args:
                access_token: User authentication token from sign_in or verify_otp
            """
            try:
                # Validate access_token
                if not access_token or not isinstance(access_token, str):
                    raise ValueError(
                        "Authentication needed — sign in first.")

                print("get_user_profile called")  # debug log

                result = await api_client.request(
                    method="GET",
                    endpoint="/user",
                    headers={"Authorization": access_token}
                )

                # Process the response similar to get_user_details
                if "user" in result:
                    user_data = result["user"]

                    # Transform Whistles data if present
                    if "Whistles" in user_data:
                        for whistle in user_data["Whistles"]:
                            if "_id" in whistle:
                                whistle["id"] = whistle.pop("_id")
                            whistle["expiry"] = whistle.get(
                                "expiry") or "never"
                        user_data["whistles"] = user_data.pop("Whistles")

                    # debug log
                    print(f"get_user_profile response: {user_data}")

                    logger.info("User profile retrieved successfully",
                                user_id=user_data.get("_id"))

                    return {
                        "success": True,
                        "data": user_data
                    }
                else:
                    raise Exception("User not found")

            except Exception as e:
                logger.error("User profile retrieval failed", error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "payload": locals().get("payload")
                }