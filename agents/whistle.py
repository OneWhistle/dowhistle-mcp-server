from fastmcp import FastMCP
from typing import Dict, Any, Optional, List, Annotated
import structlog
from datetime import datetime
import re
from utils.http_client import api_client
from pydantic import Field

logger = structlog.get_logger()

class WhistleAgent:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self.register_tools()

    def auth_access(self, access_token: str) -> bool:
        """
        Validate the provided access_token to ensure the user is authenticated.

        Args:
            access_token: User authentication token

        Returns:
            bool: True if token is valid, False otherwise
        """
        if not access_token or not isinstance(access_token, str):
            logger.error("Authentication needed — sign in first.")
            return False
        return True
    
    def convert_to_iso_format(self, expiry: str) -> str:
        """
        Convert various date formats to ISO format.
        
        Args:
            expiry: Date string in various formats
            
        Returns:
            str: ISO formatted date string or "never"
        """
        if expiry.lower() == "never":
            return "never"
            
        # If already in ISO format, return as is
        if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}([.]\d+)?(Z|[+-]\d{2}:\d{2})$', expiry):
            return expiry
            
        # Common date formats to try
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y',
            '%d-%m-%Y %H:%M:%S',
            '%d-%m-%Y',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(expiry, fmt)
                # Convert to ISO format with Z suffix
                return dt.isoformat() + 'Z'
            except ValueError:
                continue
                
        # If no format matches, raise error
        raise ValueError(f"Unable to parse date format: {expiry}")
    
    def validate_expiry(self, expiry: str) -> tuple[bool, str]:
        """
        Validate expiry date format and ensure it's in the future.
        
        Args:
            expiry: Expiry date string
            
        Returns:
            tuple: (is_valid, converted_expiry_or_error_message)
        """
        try:
            converted_expiry = self.convert_to_iso_format(expiry)
            
            if converted_expiry == "never":
                return True, converted_expiry
                
            # Parse ISO format datetime
            expiry_dt = datetime.fromisoformat(converted_expiry.replace('Z', '+00:00'))
            # Check if it's in the future
            if expiry_dt > datetime.now(expiry_dt.tzinfo):
                return True, converted_expiry
            else:
                return False, "Expiry date must be in the future"
                
        except ValueError as e:
            return False, str(e)
    
    def register_tools(self):
        @self.mcp.tool()
        async def create_whistle(
            access_token: Annotated[
                str, Field(description="User authentication token")
            ],
            description: Annotated[
                str, Field(description="A detailed description of the service/need")
            ],
            alert_radius: Annotated[
                int,
                Field(
                    description="Alert radius in kilometers",
                    ge=1,
                    le=1000,
                    default=2
                )
            ] = 2,
            tags: Annotated[
                Optional[List[str]],
                Field(
                    description="List of relevant tags for the whistle (max 20)",
                    default=None
                )
            ] = None,
            provider: Annotated[
                bool,
                Field(
                    description="True if offering a service, False if seeking",
                    default=False
                )
            ] = False,
            expiry: Annotated[
                str,
                Field(
                    description="Expiry setting - 'never' or date string (will be converted to ISO format)",
                    default="never"
                )
            ] = "never"
        ) -> Dict[str, Any]:
            """
            Create a new whistle (service request) for the authenticated user.

            Args:
                access_token: User authentication token
                description: A detailed description of the service/need
                alert_radius: Alert radius in kilometers (1-1000, default: 2)
                tags: List of relevant tags for the whistle (max 20)
                provider: True if offering a service, False if seeking (default: False)
                expiry: Expiry setting - "never" or date string (default: "never")
            
            Returns:
                Dictionary with success status, whistle data, and message
            """
            try:
                # Check authentication
                if not self.auth_access(access_token):
                    return {
                        "status": "error",
                        "message": "Authentication needed — sign in first."
                    }

                # Validate and convert expiry
                is_valid_expiry, converted_expiry_or_error = self.validate_expiry(expiry)
                if not is_valid_expiry:
                    return {
                        "status": "error",
                        "message": f"Invalid expiry date: {converted_expiry_or_error}"
                    }

                # Prepare whistle data
                whistle_data = {
                    "description": description,
                    "alertRadius": int(alert_radius),  # Ensure it's an integer
                    "tags": tags or [],
                    "provider": bool(provider),  # Ensure it's a boolean
                    "expiry": converted_expiry_or_error  # Use the converted ISO format
                }

                print("whistle_data",whistle_data)

                # Validate tags limit (max 20 as per backend validation)
                if len(whistle_data["tags"]) > 20:
                    return {
                        "status": "error",
                        "message": "Please specify only up to 20 tags"
                    }

                # Make API request to create whistle
                result = await api_client.request(
                    method="POST",
                    endpoint="/whistle",
                    data={"whistle": whistle_data}
                )

                # Extract the created whistle from response
                new_whistle = result.get("newWhistle")
                if not new_whistle:
                    return {
                        "status": "error",
                        "message": "Whistle creation failed - no whistle returned"
                    }

                # Format response
                formatted_whistle = {
                    "id": new_whistle.get("_id") or new_whistle.get("id"),
                    "description": new_whistle.get("description", ""),
                    "tags": new_whistle.get("tags", []),
                    "alertRadius": new_whistle.get("alertRadius", 2),
                    "expiry": new_whistle.get("expiry", "never"),
                    "provider": new_whistle.get("provider", False),
                    "active": new_whistle.get("active", True),
                }

                logger.info(
                    "Whistle created successfully", 
                    whistle_id=formatted_whistle["id"],
                    description=description,
                    provider=provider
                )

                return {
                    "status": "success",
                    "whistle": formatted_whistle,
                    "message": "Whistle created successfully",
                    "matching_whistles": result.get("matchingWhistles", [])
                }

            except Exception as e:
                error_msg = str(e)
                logger.error("Whistle creation failed", error=error_msg, description=description)

                # Handle specific error cases
                if "ETLIMIT" in error_msg:
                    return {
                        "status": "error",
                        "message": "Please specify only up to 20 tags"
                    }
                elif "referral" in error_msg.lower():
                    return {
                        "status": "error", 
                        "message": error_msg
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Error creating whistle: {error_msg}"
                    }

        @self.mcp.tool()
        async def list_whistles(
            access_token: Annotated[
                str, Field(description="User authentication token")
            ],
            active_only: Annotated[
                bool,
                Field(
                    description="If True, only return active whistles",
                    default=False
                )
            ] = False
        ) -> Dict[str, Any]:
            """
            Fetch all whistles for the authenticated user.

            Args:
                access_token: User authentication token
                active_only: If True, only return active whistles

            Returns:
                Dictionary with success status and list of whistles
            """
            try:
                # Check authentication
                if not self.auth_access(access_token):
                    return {
                        "status": "error",
                        "message": "Authentication needed — sign in first."
                    }

                # Fetch user details from the 'user' endpoint
                result = await api_client.request(
                    method="GET",
                    endpoint="/user",
                    headers={"Authorization": access_token}
                )

                user = result.get("user", {})
                whistles = user.get("whistles", [])

                # Apply active filter if requested
                if active_only:
                    whistles = [w for w in whistles if w.get("active", True)]

                # Format whistles in a consistent manner
                formatted_whistles = [
                    {
                        "id": w.get("id") or w.get("_id"),
                        "description": w.get("description", ""),
                        "tags": w.get("tags", []),
                        "alertRadius": w.get("alertRadius", 2),
                        "expiry": w.get("expiry", "never"),
                        "provider": w.get("provider", False),
                        "active": w.get("active", True),
                    }
                    for w in whistles
                ]

                logger.info(
                    "Whistles listed successfully",
                    total_count=len(formatted_whistles),
                    active_only=active_only
                )

                return {
                    "status": "success",
                    "whistles": formatted_whistles
                }

            except Exception as e:
                error_msg = str(e)
                logger.error("Whistle listing failed", error=error_msg)

                return {
                    "status": "error",
                    "message": f"Error listing whistles: {error_msg}",
                    "whistles": []
                }