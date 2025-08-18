from fastmcp import FastMCP
from typing import Dict, Any
import structlog
from utils.http_client import api_client

logger = structlog.get_logger()

class AuthAgent:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self.register_tools()
    
    def register_tools(self):
        @self.mcp.tool()
        async def sign_in(phone: str,
    country_code: str,
    name: str,
    location: str,
    ) -> Dict[str, Any]:
            """
            Authenticate user with phone number, country code, name, location using OTP verification 
            
            Args:
                phone: User phone number
                country_code: User country code (e.g. "+1" for USA)
                name: User name
                location: User location
                """
            try:
                payload = {"phone": phone, "country_code": country_code, "name": name, "location": location}
                
                result = await api_client.request(
                    method="POST",
                    endpoint="/twilio/sign-in",
                    data=payload
                )
                
                logger.info("Sign in successful", phone=phone)
                
                return {
                    "success": True,
                    "data": {
                        "user": result.get("user", {}),
                        "token": result.get("token", {}),
                        "user_id": result.get("user", {}).get("_id", "")
                    }
                }
                
            except Exception as e:
                logger.error("Sign in failed", error=str(e), phone=phone)
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp.tool()
        async def verify_otp( otp_code: str,user_id: str) -> Dict[str, Any]:
            """
            Verify OTP code for user authentication
            
            Args:
                user_id: User ID
                otp_code: OTP verification code
            """
            try:
                payload = {"user_id": user_id, "otp_code": otp_code}
                
                result = await api_client.request(
                    method="POST",
                    endpoint="/twilio/verify-otp",
                    data=payload
                )
                
                logger.info("OTP verification successful", user_id=user_id)
                
                return {
                    "success": True,
                    "data": result
                }
                
            except Exception as e:
                logger.error("OTP verification failed", error=str(e), user_id=user_id)
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp.tool()
        async def resend_otp(user_id: str) -> Dict[str, Any]:
            """
            Resend OTP code to user phone number
            
            Args:
                user_id: User ID
            """
            try:
                payload = {"user_id": user_id}
                
                result = await api_client.request(
                    method="POST",
                        endpoint="/twilio/resend-otp",
                    data=payload
                )
                
                logger.info("OTP resent successfully", user_id=user_id)
                
                return {
                    "success": True,
                    "message": "OTP sent successfully"
                }
                
            except Exception as e:
                logger.error("OTP resend failed", error=str(e), user_id=user_id)
                return {
                    "success": False,
                    "error": str(e)
                }
