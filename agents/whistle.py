from fastmcp import FastMCP
from typing import Dict, Any, Optional, List
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
            description: str,
            alert_radius: Optional[float] = 2.0,
            tags: Optional[List[str]] = None,
            provider: Optional[bool] = False,
            expiry: Optional[str] = "never"
        ) -> Dict[str, Any]:
            """
            Create a new whistle (service request) for the authenticated user.
            
            Args:
                description: A detailed description of the service/need
                alert_radius: Alert radius in kilometers (default: 2.0)
                tags: List of relevant tags for the whistle
                provider: True if offering a service, False if seeking (default: False)
                expiry: Expiry setting - "never" or date string (default: "never")
            
            Returns:
                Dictionary with success status, whistle data, and message
            """
            try:
                # Prepare whistle data following the whistletools.py pattern
                whistle_data = {
                    "description": description,
                    "alertRadius": alert_radius,
                    "tags": tags or [],
                    "provider": provider,
                    "expiry": expiry
                }
                
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
                
                # Format response following whistletools.py pattern
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
        async def update_whistle(
            whistle_id: str,
            description: Optional[str] = None,
            alert_radius: Optional[float] = None,
            tags: Optional[List[str]] = None,
            provider: Optional[bool] = None,
            expiry: Optional[str] = None,
            active: Optional[bool] = None,
            public: Optional[bool] = None,
            comment: Optional[str] = None,
            images: Optional[List[str]] = None,
            location: Optional[List[float]] = None,
            category: Optional[str] = None,
            sub_category: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Update an existing whistle for the authenticated user.
            
            Args:
                whistle_id: ID of the whistle to update
                description: Updated description
                alert_radius: Updated alert radius in kilometers
                tags: Updated list of tags (max 20)
                provider: Updated provider status
                expiry: Updated expiry setting
                active: Whether the whistle is active
                public: Whether the whistle is public
                comment: Additional comment
                images: List of image URLs
                location: Updated location as [longitude, latitude]
                category: Updated category
                sub_category: Updated subcategory
            
            Returns:
                Dictionary with success status, updated whistle data, and message
            """
            try:
                # Build update data with only provided fields (following whistletools.py pattern)
                update_data = {}
                updatable_fields = {
                    "description": description,
                    "alertRadius": alert_radius, 
                    "tags": tags,
                    "provider": provider,
                    "expiry": expiry,
                    "active": active,
                    "public": public,
                    "comment": comment,
                    "images": images,
                    "category": category,
                    "subCategory": sub_category
                }
                
                # Only include fields that are not None
                for field, value in updatable_fields.items():
                    if value is not None:
                        update_data[field] = value
                
                # Handle location format conversion
                if location is not None:
                    if isinstance(location, list) and len(location) == 2:
                        update_data["location"] = {
                            "type": "Point", 
                            "coordinates": location
                        }
                    else:
                        update_data["location"] = location
                
                # Validate tags limit
                if tags is not None and len(tags) > 20:
                    return {
                        "status": "error",
                        "message": "Please specify only up to 20 tags"
                    }
                
                if not update_data:
                    return {
                        "status": "error",
                        "message": "No valid updates were identified from your request."
                    }
                
                # Make API request to update whistle
                result = await api_client.request(
                    method="PUT",
                    endpoint=f"/whistle/{whistle_id}",
                    data=update_data
                )
                
                # Extract updated whistle from response
                updated_whistle = result.get("updatedWhistle")
                if not updated_whistle:
                    return {
                        "status": "error",
                        "message": "Whistle update failed - no response from server"
                    }
                
                # Format response following whistletools.py pattern
                formatted_whistle = {
                    "id": updated_whistle.get("_id") or updated_whistle.get("id"),
                    "description": updated_whistle.get("description", ""),
                    "tags": updated_whistle.get("tags", []),
                    "alertRadius": updated_whistle.get("alertRadius", 2),
                    "expiry": updated_whistle.get("expiry", "never"),
                    "provider": updated_whistle.get("provider", False),
                    "active": updated_whistle.get("active", True),
                }
                
                logger.info(
                    "Whistle updated successfully",
                    whistle_id=whistle_id,
                    updated_fields=list(update_data.keys())
                )
                
                return {
                    "status": "success", 
                    "whistle": formatted_whistle,
                    "message": f"Successfully updated whistle: {formatted_whistle.get('description', '')}"
                }
                
            except Exception as e:
                error_msg = str(e)
                logger.error("Whistle update failed", error=error_msg, whistle_id=whistle_id)
                
                # Handle specific error cases
                if "ETLIMIT" in error_msg:
                    return {
                        "status": "error",
                        "message": "Please specify only up to 20 tags"
                    }
                elif "not found" in error_msg.lower():
                    return {
                        "status": "error",
                        "message": f"Whistle not found: {whistle_id}"
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to update whistle: {error_msg}"
                    }
        
        @self.mcp.tool()
        async def delete_whistle(whistle_id: str) -> Dict[str, Any]:
            """
            Delete (deactivate) an existing whistle for the authenticated user.
            
            Args:
                whistle_id: ID of the whistle to delete
            
            Returns:
                Dictionary with success status and message
            """
            try:
                # Use soft delete by setting active to false (following whistletools.py pattern)
                result = await api_client.request(
                    method="PUT",
                    endpoint=f"/whistle/{whistle_id}",
                    data={"active": False}
                )
                
                # Extract whistle info for response message
                updated_whistle = result.get("updatedWhistle", {})
                whistle_description = updated_whistle.get("description", "Unknown")
                
                logger.info("Whistle deleted successfully", whistle_id=whistle_id)
                
                return {
                    "status": "success",
                    "message": f"Whistle '{whistle_description}' deleted successfully",
                    "whistle_id": whistle_id
                }
                
            except Exception as e:
                error_msg = str(e)
                logger.error("Whistle deletion failed", error=error_msg, whistle_id=whistle_id)
                
                if "not found" in error_msg.lower():
                    return {
                        "status": "error",
                        "message": "No matching whistle found to delete"
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Error deleting whistle: {error_msg}"
                    }
        
        @self.mcp.tool()
        async def list_whistles(
            active_only: Optional[bool] = False
        ) -> Dict[str, Any]:
            """
            Fetch all whistles for the authenticated user.
            
            Args:
                active_only: If True, only return active whistles
            
            Returns:
                Dictionary with success status and list of whistles
            """
            try:
                # Get user details which includes their whistles
                # Note: This assumes the API client has a method to get user details with whistles
                # If not available, we might need to use searchAround with user's location
                
                # For now, we'll simulate getting user whistles using searchAround
                # with a large radius around a default location
                default_location = [-121.3269, 38.7531]  # Default to Rocklin, CA
                
                payload = {
                    "location": default_location,
                    "radius": 100.0,  # Large radius to capture user's whistles
                    "limit": 1000,
                    "keyword": "",
                    "visible": True
                }
                
                result = await api_client.request(
                    method="POST",
                    endpoint="/searchAround", 
                    data=payload
                )
                
                # Extract whistles from search results
                all_whistles = []
                matching_whistles = result.get("matchingWhistles", [])
                
                for whistle_data in matching_whistles:
                    whistle = whistle_data.get("item", whistle_data)
                    
                    # Apply active filter if requested
                    if active_only and not whistle.get("active", True):
                        continue
                    
                    # Format whistle following whistletools.py pattern
                    formatted_whistle = {
                        "id": whistle.get("_id") or whistle.get("id"),
                        "description": whistle.get("description", ""),
                        "tags": whistle.get("tags", []),
                        "alertRadius": whistle.get("alertRadius", 2),
                        "expiry": whistle.get("expiry", "never"),
                        "provider": whistle.get("provider", False),
                        "active": whistle.get("active", True),
                    }
                    all_whistles.append(formatted_whistle)
                
                logger.info(
                    "Whistles listed successfully",
                    total_count=len(all_whistles),
                    active_only=active_only
                )
                
                return {
                    "status": "success",
                    "whistles": all_whistles
                }
                
            except Exception as e:
                error_msg = str(e)
                logger.error("Whistle listing failed", error=error_msg)
                
                return {
                    "status": "error",
                    "message": f"Error listing whistles: {error_msg}",
                    "whistles": []
                }