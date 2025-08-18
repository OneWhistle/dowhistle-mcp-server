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
        async def sign_in(email: str, password: str) -> Dict[str, Any]:
            """
            Authenticate user with email and password
            
            Args:
                email: User email address
                password: User password
            """
            try:
                payload = {"email": email, "password": password}
                
                result = await api_client.request(
                    method="POST",
                    endpoint="/auth/signin",
                    data=payload
                )
                
                logger.info("Sign in successful", email=email)
                
                return {
                    "success": True,
                    "data": {
                        "user": result.get("user"),
                        "token": result.get("token"),
                        "expires_at": result.get("expires_at")
                    }
                }
                
            except Exception as e:
                logger.error("Sign in failed", error=str(e), email=email)
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp.tool()
        async def verify_otp(email: str, otp_code: str) -> Dict[str, Any]:
            """
            Verify OTP code for user authentication
            
            Args:
                email: User email address
                otp_code: OTP verification code
            """
            try:
                payload = {"email": email, "otp_code": otp_code}
                
                result = await api_client.request(
                    method="POST",
                    endpoint="/auth/verify-otp",
                    data=payload
                )
                
                logger.info("OTP verification successful", email=email)
                
                return {
                    "success": True,
                    "data": result
                }
                
            except Exception as e:
                logger.error("OTP verification failed", error=str(e), email=email)
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp.tool()
        async def resend_otp(email: str) -> Dict[str, Any]:
            """
            Resend OTP code to user email
            
            Args:
                email: User email address
            """
            try:
                payload = {"email": email}
                
                result = await api_client.request(
                    method="POST",
                    endpoint="/auth/resend-otp",
                    data=payload
                )
                
                logger.info("OTP resent successfully", email=email)
                
                return {
                    "success": True,
                    "message": "OTP sent successfully"
                }
                
            except Exception as e:
                logger.error("OTP resend failed", error=str(e), email=email)
                return {
                    "success": False,
                    "error": str(e)
                }
