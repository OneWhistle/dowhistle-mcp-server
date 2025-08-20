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
            title: str,
            description: str,
            location: List[float],  # [longitude, latitude] to match backend format
            category: str,
            sub_category: Optional[str] = None,
            keyword: Optional[str] = None,
            priority: Optional[str] = "medium",
            is_anonymous: Optional[bool] = False,
            provider: Optional[bool] = False,
            active: Optional[bool] = True,
            visible: Optional[bool] = True,
            tags: Optional[List[str]] = None,
            alert_radius: Optional[float] = 2.0,
            limit: Optional[int] = 50,
            radius: Optional[float] = None,
            referral_code: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Create a new whistle report
            
            Args:
                title: Whistle title
                description: Detailed description of the whistle
                location: Location as [longitude, latitude] array
                category: Main category of the whistle
                sub_category: Optional subcategory
                keyword: Optional keyword for better searchability
                priority: Priority level (low, medium, high)
                is_anonymous: Whether to create anonymously
                provider: Whether this is a provider whistle
                active: Whether the whistle is active
                visible: Whether the whistle is visible to others
                tags: Optional list of tags (max 20)
                alert_radius: Radius for matching alerts in km
                limit: Limit for matching whistles returned
                radius: Search radius for matching
                referral_code: Optional referral code
            """
            try:
                # Construct whistle object following backend format
                whistle_data = {
                    "title": title,
                    "description": description,
                    "location": {
                        "type": "Point",
                        "coordinates": location  # [longitude, latitude]
                    },
                    "category": category,
                    "priority": priority,
                    "provider": provider,
                    "active": active,
                    "visible": visible,
                    "alertRadius": alert_radius
                }
                
                # Add optional fields if provided
                if sub_category:
                    whistle_data["subCategory"] = sub_category
                if keyword:
                    whistle_data["keyword"] = keyword
                if tags:
                    if len(tags) > 20:
                        return {
                            "success": False,
                            "error": "Please specify only up to 20 tags"
                        }
                    whistle_data["tags"] = tags
                
                # Construct payload following backend API format
                payload = {
                    "whistle": whistle_data,
                    "limit": limit
                }
                
                # Add optional payload fields
                if radius:
                    payload["radius"] = radius
                if referral_code:
                    payload["referralCode"] = referral_code
                
                # Make API request to create whistle
                result = await api_client.request(
                    method="POST",
                    endpoint="/whistle",  # Backend uses /whistle endpoint
                    data=payload
                )
                
                logger.info(
                    "Whistle created successfully", 
                    whistle_id=result.get("newWhistle", {}).get("_id"),
                    title=title,
                    category=category
                )
                
                # Format response to match expected structure
                response = {
                    "success": True,
                    "data": {
                        "whistle": result.get("newWhistle"),
                        "matching_whistles": result.get("matchingWhistles", []),
                        "total_matches": len(result.get("matchingWhistles", [])),
                    }
                }
                
                # Include reward info if present
                if "reward" in result:
                    response["data"]["reward"] = result["reward"]
                
                # Include certification info if present
                if "certified" in result:
                    response["data"]["certified"] = result["certified"]
                
                return response
                
            except Exception as e:
                error_msg = str(e)
                logger.error("Whistle creation failed", error=error_msg, title=title)
                
                # Handle specific error cases based on backend patterns
                if "ETLIMIT" in error_msg:
                    return {
                        "success": False,
                        "error": "Please specify only up to 20 tags"
                    }
                elif "No data sent" in error_msg:
                    return {
                        "success": False,
                        "error": "No whistle data provided. Please provide whistle details"
                    }
                elif "referral" in error_msg.lower():
                    return {
                        "success": False,
                        "error": error_msg
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Error creating whistle: {error_msg}"
                    }
        
        @self.mcp.tool()
        async def update_whistle(
            whistle_id: str,
            comment: Optional[str] = None,
            description: Optional[str] = None,
            images: Optional[List[str]] = None,
            tags: Optional[List[str]] = None,
            active: Optional[bool] = None,
            expiry: Optional[str] = None,
            public: Optional[bool] = None,
            alert_radius: Optional[float] = None,
            location: Optional[List[float]] = None,
            category: Optional[str] = None,
            sub_category: Optional[str] = None,
            updates: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """
            Update an existing whistle
            
            Args:
                whistle_id: ID of the whistle to update
                comment: Comment or additional notes
                description: Updated description
                images: List of image URLs
                tags: List of tags (max 20)
                active: Whether the whistle is active
                expiry: Expiry setting ('never' or date string)
                public: Whether the whistle is public
                alert_radius: Alert radius in kilometers
                location: Updated location as [longitude, latitude]
                category: Updated category
                sub_category: Updated subcategory
                updates: Additional updates dictionary (for other fields)
            """
            try:
                # Build update payload with only provided fields
                update_data = {}
                
                # Add individual parameters if provided
                if comment is not None:
                    update_data["comment"] = comment
                if description is not None:
                    update_data["description"] = description
                if images is not None:
                    update_data["images"] = images
                if tags is not None:
                    if len(tags) > 20:
                        return {
                            "success": False,
                            "error": "Please specify only up to 20 tags"
                        }
                    update_data["tags"] = tags
                if active is not None:
                    update_data["active"] = active
                if expiry is not None:
                    update_data["expiry"] = expiry
                if public is not None:
                    update_data["public"] = public
                if alert_radius is not None:
                    update_data["alertRadius"] = alert_radius
                if location is not None:
                    # Convert to proper location format if needed
                    if isinstance(location, list) and len(location) == 2:
                        update_data["location"] = {
                            "type": "Point",
                            "coordinates": location  # [longitude, latitude]
                        }
                    else:
                        update_data["location"] = location
                if category is not None:
                    update_data["category"] = category
                if sub_category is not None:
                    update_data["subCategory"] = sub_category
                
                # Merge with additional updates if provided
                if updates:
                    # Only allow whitelisted fields for security
                    allowed_fields = [
                        'comment', 'description', 'images', 'tags', 'active',
                        'expiry', 'public', 'alertRadius', 'location', 
                        'category', 'subCategory'
                    ]
                    for key, value in updates.items():
                        if key in allowed_fields:
                            update_data[key] = value
                
                if not update_data:
                    return {
                        "success": False,
                        "error": "No valid update fields provided"
                    }
                
                # Make API request to update whistle
                result = await api_client.request(
                    method="PUT",
                    endpoint=f"/whistle/{whistle_id}",  # Backend uses /whistle/{id} format
                    data=update_data
                )
                
                logger.info(
                    "Whistle updated successfully", 
                    whistle_id=whistle_id,
                    updated_fields=list(update_data.keys())
                )
                
                return {
                    "success": True,
                    "data": {
                        "updated_whistle": result.get("updatedWhistle"),
                        "whistle_id": whistle_id,
                        "updated_fields": list(update_data.keys())
                    }
                }
                
            except Exception as e:
                error_msg = str(e)
                logger.error("Whistle update failed", error=error_msg, whistle_id=whistle_id)
                
                # Handle specific error cases based on backend patterns
                if "ETLIMIT" in error_msg:
                    return {
                        "success": False,
                        "error": "Please specify only up to 20 tags"
                    }
                elif "not found" in error_msg.lower():
                    return {
                        "success": False,
                        "error": f"Whistle not found: {whistle_id}"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Error updating whistle: {error_msg}"
                    }
        
        @self.mcp.tool()
        async def delete_whistle(whistle_id: str) -> Dict[str, Any]:
            """
            Delete a whistle by setting it to inactive
            
            Args:
                whistle_id: ID of the whistle to delete
            """
            try:
                # Most apps use soft delete - set active to false instead of hard delete
                result = await api_client.request(
                    method="PUT",
                    endpoint=f"/whistle/{whistle_id}",
                    data={"active": False}
                )
                
                logger.info("Whistle deleted successfully", whistle_id=whistle_id)
                
                return {
                    "success": True,
                    "message": "Whistle deleted successfully",
                    "data": {
                        "whistle_id": whistle_id,
                        "deleted_at": result.get("lastUpdatedAt")
                    }
                }
                
            except Exception as e:
                error_msg = str(e)
                logger.error("Whistle deletion failed", error=error_msg, whistle_id=whistle_id)
                
                if "not found" in error_msg.lower():
                    return {
                        "success": False,
                        "error": f"Whistle not found: {whistle_id}"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Error deleting whistle: {error_msg}"
                    }
        
        @self.mcp.tool()
        async def list_whistles(
            limit: Optional[int] = 10,
            offset: Optional[int] = 0,
            category: Optional[str] = None,
            sub_category: Optional[str] = None,
            active_only: Optional[bool] = True,
            provider_only: Optional[bool] = None,
            public_only: Optional[bool] = None,
            keyword: Optional[str] = None,
            location: Optional[List[float]] = None,
            radius: Optional[float] = None,
            filters: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """
            List user's whistles with pagination and filters
            
            Args:
                limit: Number of whistles to return (max 100)
                offset: Number of whistles to skip for pagination
                category: Filter by category
                sub_category: Filter by subcategory
                active_only: Only return active whistles
                provider_only: Filter by provider status
                public_only: Only return public whistles
                keyword: Search by keyword in title/description
                location: Center location for radius search [longitude, latitude]
                radius: Search radius in kilometers (requires location)
                filters: Additional filters dictionary
            """
            try:
                # Build query parameters
                params = {
                    "limit": min(limit, 100),  # Cap at 100 for performance
                    "offset": offset
                }
                
                # Build search query similar to searchAround functionality
                search_query = {}
                
                if category:
                    search_query["category"] = category
                if sub_category:
                    search_query["subCategory"] = sub_category
                if keyword:
                    search_query["keyword"] = keyword
                
                # Add filters based on boolean flags
                if active_only is True:
                    search_query["active"] = True
                elif active_only is False:
                    search_query["active"] = False
                    
                if provider_only is not None:
                    search_query["provider"] = provider_only
                    
                if public_only is not None:
                    search_query["public"] = public_only
                
                # Add additional filters if provided
                if filters:
                    search_query.update(filters)
                
                # If location and radius provided, use searchAround-style endpoint
                if location and radius:
                    payload = {
                        "location": location,
                        "radius": radius,
                        "limit": params["limit"],
                        "keyword": keyword or "",
                        "category": category,
                        "subCategory": sub_category,
                        "provider": provider_only,
                        "visible": True
                    }
                    
                    result = await api_client.request(
                        method="POST",
                        endpoint="/searchAround",
                        data=payload
                    )
                    
                    # Extract whistles from search results
                    whistles = []
                    matching_whistles = result.get("matchingWhistles", [])
                    
                    # Skip offset number of results
                    paginated_whistles = matching_whistles[offset:offset + limit]
                    
                    for whistle_data in paginated_whistles:
                        if "item" in whistle_data:
                            whistles.append(whistle_data["item"])
                        else:
                            whistles.append(whistle_data)
                    
                    response_data = {
                        "whistles": whistles,
                        "total_count": len(matching_whistles),
                        "limit": limit,
                        "offset": offset,
                        "has_more": len(matching_whistles) > offset + limit,
                        "search_criteria": {
                            "location": location,
                            "radius": radius,
                            "category": category,
                            "keyword": keyword
                        }
                    }
                    
                else:
                    # For user's own whistles, we'd typically get them from user profile
                    # Since we don't have a dedicated endpoint, simulate with searchAround
                    # using a very small radius around user's location or default location
                    default_location = location or [-121.3269, 38.7531]  # Default to Rocklin, CA
                    default_radius = radius or 50.0  # Large radius to capture user's whistles
                    
                    payload = {
                        "location": default_location,
                        "radius": default_radius,
                        "limit": 1000,  # Get more results for filtering
                        "keyword": keyword or "",
                        "category": category,
                        "subCategory": sub_category,
                        "provider": provider_only,
                        "visible": True
                    }
                    
                    result = await api_client.request(
                        method="POST",
                        endpoint="/searchAround",
                        data=payload
                    )
                    
                    # Filter and paginate results
                    all_whistles = []
                    matching_whistles = result.get("matchingWhistles", [])
                    
                    for whistle_data in matching_whistles:
                        whistle = whistle_data.get("item", whistle_data)
                        
                        # Apply additional filters
                        if active_only is not None and whistle.get("active") != active_only:
                            continue
                        if public_only is not None and whistle.get("public") != public_only:
                            continue
                            
                        all_whistles.append(whistle)
                    
                    # Apply pagination
                    paginated_whistles = all_whistles[offset:offset + limit]
                    
                    response_data = {
                        "whistles": paginated_whistles,
                        "total_count": len(all_whistles),
                        "limit": limit,
                        "offset": offset,
                        "has_more": len(all_whistles) > offset + limit,
                        "filters_applied": {
                            "category": category,
                            "sub_category": sub_category,
                            "active_only": active_only,
                            "provider_only": provider_only,
                            "public_only": public_only,
                            "keyword": keyword
                        }
                    }
                
                logger.info(
                    "Whistles listed successfully", 
                    count=len(response_data["whistles"]),
                    total=response_data["total_count"],
                    filters=response_data.get("filters_applied", {})
                )
                
                return {
                    "success": True,
                    "data": response_data
                }
                
            except Exception as e:
                error_msg = str(e)
                logger.error("Whistle listing failed", error=error_msg)
                
                return {
                    "success": False,
                    "error": f"Error listing whistles: {error_msg}",
                    "data": {
                        "whistles": [],
                        "total_count": 0,
                        "limit": limit,
                        "offset": offset,
                        "has_more": False
                    }
                }