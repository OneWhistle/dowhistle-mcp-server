from fastmcp import FastMCP
from typing import Dict, Any
import structlog
from utils.http_client import api_client
from models.user_model import UserSettingsResponse

logger = structlog.get_logger()


class UserAgent:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self.register_tools()

    def register_tools(self):
        @self.mcp.tool()
        async def toggle_visibility(auth_token: str, visible: str) -> Dict[str, Any]:
            """
            Toggle user visibility status

            Args:
                auth_token: User authentication token from sign_in
                visible: Whether the user should be visible ("true") or hidden ("false")

            Returns:
                A dictionary containing the operation result
            """
            try:
                # Validate input parameters
                if not auth_token or not isinstance(auth_token, str):
                    raise ValueError("auth_token must be a non-empty string")

                if visible not in ["true", "false"]:
                    raise ValueError(
                        "visible must be either 'true' or 'false'")

                # Prepare request payload - matches the API client pattern
                payload = {"visible": visible}

                # Make API request to PUT /user endpoint
                result = await api_client.request(
                    method="PUT",
                    endpoint="/user",
                    data=payload,
                    # Direct token format from API client
                    headers={"Authorization": auth_token}
                )

                response = UserSettingsResponse(
                    success=True,
                    message=f"User visibility set to {visible}"
                )

                logger.info(
                    "User visibility toggled successfully",
                    visible=visible,
                    operation="toggle_visibility"
                )

                return response.model_dump()

            except ValueError as ve:
                logger.error("Invalid input parameters", error=str(ve))
                error_response = UserSettingsResponse(
                    success=False,
                    message="Invalid input parameters",
                    error=str(ve)
                )
                return error_response.model_dump()

            except Exception as e:
                logger.error("Visibility toggle failed", error=str(e))
                error_response = UserSettingsResponse(
                    success=False,
                    message="Failed to toggle user visibility",
                    error=f"Unexpected error: {str(e)}"
                )
                return error_response.model_dump()

        @self.mcp.tool()
        async def toggle_live_tracking(auth_token: str, tracking: str) -> Dict[str, Any]:
            """
            Toggle live tracking for a user

            Args:
                auth_token: User authentication token from sign_in
                tracking: Whether to enable ("true") or disable ("false") live tracking

            Returns:
                A dictionary containing the operation result
            """
            try:
                # Validate input parameters
                if not auth_token or not isinstance(auth_token, str):
                    raise ValueError("auth_token must be a non-empty string")

                if tracking not in ["true", "false"]:
                    raise ValueError(
                        "tracking must be either 'true' or 'false'")

                # Prepare request payload - following the same pattern as toggle_visibility
                payload = {"tracking": tracking}

                # Make API request to PUT /user endpoint
                result = await api_client.request(
                    method="PUT",
                    endpoint="/user",
                    data=payload,
                    headers={"Authorization": auth_token}
                )

                response = UserSettingsResponse(
                    success=True,
                    message=f"Live tracking {'enabled' if tracking == 'true' else 'disabled'}"
                )

                logger.info(
                    "Live tracking toggled successfully",
                    tracking=tracking,
                    operation="toggle_live_tracking"
                )

                return response.model_dump()

            except ValueError as ve:
                logger.error("Invalid input parameters", error=str(ve))
                error_response = UserSettingsResponse(
                    success=False,
                    message="Invalid input parameters",
                    error=str(ve)
                )
                return error_response.model_dump()

            except Exception as e:
                logger.error("Live tracking toggle failed", error=str(e))
                error_response = UserSettingsResponse(
                    success=False,
                    message="Failed to toggle live tracking",
                    error=f"Unexpected error: {str(e)}"
                )
                return error_response.model_dump()

        @self.mcp.tool()
        async def toggle_whistle_sound(auth_token: str, enable: str) -> Dict[str, Any]:
            """
            Toggle whistle sound notifications for a user

            Args:
                auth_token: User authentication token from sign_in
                enable: Whether to enable ("true") or disable ("false") whistle sound notifications

            Returns:
                A dictionary containing the operation result
            """
            try:
                # Validate input parameters
                if not auth_token or not isinstance(auth_token, str):
                    raise ValueError("auth_token must be a non-empty string")

                if enable not in ["true", "false"]:
                    raise ValueError("enable must be either 'true' or 'false'")

                # Prepare request payload - following the same pattern as other toggle functions
                payload = {"enable": enable}

                # Make API request to PUT /user endpoint
                result = await api_client.request(
                    method="PUT",
                    endpoint="/user",
                    data=payload,
                    headers={"Authorization": auth_token}
                )

                response = UserSettingsResponse(
                    success=True,
                    message=f"Whistle sound notifications {'enabled' if enable == 'true' else 'disabled'}"
                )

                logger.info(
                    "Whistle sound toggled successfully",
                    enable=enable,
                    operation="toggle_whistle_sound"
                )

                return response.model_dump()

            except ValueError as ve:
                logger.error("Invalid input parameters", error=str(ve))
                error_response = UserSettingsResponse(
                    success=False,
                    message="Invalid input parameters",
                    error=str(ve)
                )
                return error_response.model_dump()

            except Exception as e:
                logger.error("Whistle sound toggle failed", error=str(e))
                error_response = UserSettingsResponse(
                    success=False,
                    message="Failed to toggle whistle sound",
                    error=f"Unexpected error: {str(e)}"
                )
                return error_response.model_dump()
