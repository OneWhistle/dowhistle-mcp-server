from fastmcp import FastMCP
from typing import Dict, Any
import structlog
from utils.http_client import api_client

logger = structlog.get_logger()


class UserAgent:
    def __init__(self, mcp: FastMCP):
        @self.mcp.tool()
        async def toggle_visibility(auth_token: str, visible: str) -> Dict[str, Any]:
            """
            Toggle user visibility status

            Args:
                auth_token: User authentication token from sign_in or verify_otp
                visible: Whether the user should be visible ("true") or hidden ("false")
            """
            try:
                # Validate auth_token
                if not auth_token or not isinstance(auth_token, str):
                    raise ValueError(
                        "Invalid auth_token. Must be a non-empty string.")

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
                    headers={"Authorization": auth_token}
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
        async def get_user_profile(auth_token: str) -> Dict[str, Any]:
            """
            Get user profile details and whistles

            Args:
                auth_token: User authentication token from sign_in or verify_otp
            """
            try:
                # Validate auth_token
                if not auth_token or not isinstance(auth_token, str):
                    raise ValueError(
                        "Invalid auth_token. Must be a non-empty string.")

                print("get_user_profile called")  # debug log

                result = await api_client.request(
                    method="GET",
                    endpoint="/user",
                    headers={"Authorization": auth_token}
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

        # @self.mcp.tool()
        # async def toggle_live_tracking(auth_token: str, tracking: str) -> Dict[str, Any]:
        #     """
        #     Toggle live tracking for a user

        #     Args:
        #         auth_token: User authentication token from sign_in or verify_otp
        #         tracking: Whether to enable ("true") or disable ("false") live tracking
        #     """
        #     try:
        #         # Validate auth_token
        #         if not auth_token or not isinstance(auth_token, str):
        #             raise ValueError(
        #                 "Invalid auth_token. Must be a non-empty string.")

        #         # Validate tracking parameter
        #         if tracking not in ["true", "false"]:
        #             raise ValueError(
        #                 "tracking must be either 'true' or 'false'.")

        #         payload = {"tracking": tracking}
        #         print("toggle_live_tracking payload:", payload)  # debug log

        #         result = await api_client.request(
        #             method="PUT",
        #             endpoint="/user",
        #             data=payload,
        #             headers={"Authorization": auth_token}
        #         )

        #         logger.info("Live tracking toggle successful",
        #                     tracking=tracking)

        #         return {
        #             "success": True,
        #             "message": f"Live tracking {'enabled' if tracking == 'true' else 'disabled'}",
        #             "data": result
        #         }

        #     except Exception as e:
        #         logger.error("Live tracking toggle failed",
        #                      error=str(e), tracking=tracking)
        #         return {
        #             "success": False,
        #             "error": str(e),
        #             "payload": locals().get("payload")
        #         }

        # @self.mcp.tool()
        # async def toggle_whistle_sound(auth_token: str, enable: str) -> Dict[str, Any]:
        #     """
        #     Toggle whistle sound notifications for a user

        #     Args:
        #         auth_token: User authentication token from sign_in or verify_otp
        #         enable: Whether to enable ("true") or disable ("false") whistle sound notifications
        #     """
        #     try:
        #         # Validate auth_token
        #         if not auth_token or not isinstance(auth_token, str):
        #             raise ValueError(
        #                 "Invalid auth_token. Must be a non-empty string.")

        #         # Validate enable parameter
        #         if enable not in ["true", "false"]:
        #             raise ValueError(
        #                 "enable must be either 'true' or 'false'.")

        #         payload = {"enable": enable}
        #         print("toggle_whistle_sound payload:", payload)  # debug log

        #         result = await api_client.request(
        #             method="PUT",
        #             endpoint="/user",
        #             data=payload,
        #             headers={"Authorization": auth_token}
        #         )

        #         logger.info("Whistle sound toggle successful", enable=enable)

        #         return {
        #             "success": True,
        #             "message": f"Whistle sound notifications {'enabled' if enable == 'true' else 'disabled'}",
        #             "data": result
        #         }

        #     except Exception as e:
        #         logger.error("Whistle sound toggle failed",
        #                      error=str(e), enable=enable)
        #         return {
        #             "success": False,
        #             "error": str(e),
        #             "payload": locals().get("payload")
        #         }
