from fastmcp import FastMCP
from typing import Dict, Any, List
import re
import structlog
from utils.http_client import api_client
from models.auth_model import (
    SignInRequest, SignInResponse,
    VerifyOtpRequest, VerifyOtpResponse,
    ResendOtpRequest, ResendOtpResponse
)
logger = structlog.get_logger()


class AuthAgent:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self.register_tools()

    def register_tools(self):
        # -------------------------
        # Sign In Tool
        # -------------------------
        @self.mcp.tool()
        async def sign_in(
            phone: str,
            country_code: str,
            name: str,
            location: List[float],
        ) -> Dict[str, Any]:
            """
            Authenticate user with phone number, country code, name, and location using OTP verification.
            
            Args:
                phone: Digits only, without country code (e.g., "9994076214")
                country_code: User country code (e.g. "+1" for USA or "+91" for India)
                name: User name
                location: [latitude, longitude]
            """
            try:
                raw_phone = phone.strip()
                raw_phone = re.sub(r"[()\-\s]", "", raw_phone)

                # Case: starts with +<countrycode><number>
                if raw_phone.startswith("+"):
                    match = re.match(r"^(\+\d{1,3})(\d+)$", raw_phone)
                    if not match:
                        raise ValueError("Invalid phone format. Expected '+<code><number>'.")
                    country_code = match.group(1)
                    raw_phone = match.group(2)

                # Case: starts with 0 (strip leading zeros)
                elif raw_phone.startswith("0"):
                    raw_phone = raw_phone.lstrip("0")

                # Ensure phone digits only
                if not raw_phone.isdigit():
                    raise ValueError("Phone must contain digits only, without country code.")

                # Ensure country_code valid
                if not country_code.startswith("+") or not country_code[1:].isdigit():
                    raise ValueError("Country code must start with '+' followed by digits.")

                phone = raw_phone

                payload = {
                    "phone": phone,
                    "countryCode": country_code,
                    "name": name,
                    "location": location,
                }
                print("payload", payload)  # debug log

                result = await api_client.request(
                    method="POST",
                    endpoint="/twilio/sign-in",
                    data=payload
                )

                logger.info("Sign in successful", phone=phone, country_code=country_code)

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
                return {"success": False, "error": str(e),  "payload": locals().get("payload")}

        # -------------------------
        # Verify OTP Tool
        # -------------------------
        @self.mcp.tool()
        async def verify_otp(otp_code: str, user_id: str) -> Dict[str, Any]:
            """
            Verify OTP code for user authentication.
            
            Args:
                user_id: User ID returned from sign_in (must not be a phone number)
                otp_code: OTP code digits
            """
            try:
                if not user_id or not isinstance(user_id, str):
                    raise ValueError("Invalid user_id. Must be a non-empty string.")

                # Block mistake: passing phone number instead of user_id
                if user_id.isdigit() or user_id.startswith("+"):
                    raise ValueError("user_id looks like a phone number. Please provide valid user_id from sign_in.")

                if not otp_code.isdigit():
                    raise ValueError("otp_code must contain only digits.")

                payload = {"user_id": user_id, "otp": otp_code}
                result = await api_client.request(
                    method="POST",
                    endpoint="/twilio/verify-otp",
                    data=payload
                )

                logger.info("OTP verification successful", user_id=user_id)
                return {"success": True, "data": result}

            except Exception as e:
                logger.error("OTP verification failed", error=str(e), user_id=user_id)
                return {"success": False, "error": str(e)}

        # -------------------------
        # Resend OTP Tool
        # -------------------------
        @self.mcp.tool()
        async def resend_otp(user_id: str) -> Dict[str, Any]:
            """
            Resend OTP code to user phone number.
            
            Args:
                user_id: User ID returned from sign_in (must not be a phone number)
            """
            try:
                if not user_id or not isinstance(user_id, str):
                    raise ValueError("Invalid user_id. Must be a non-empty string.")

                # Block mistake: passing phone number
                if user_id.isdigit() or user_id.startswith("+"):
                    raise ValueError("user_id looks like a phone number. Please provide valid user_id from sign_in.")

                payload = {"user_id": user_id}
                await api_client.request(
                    method="POST",
                    endpoint="/twilio/resend-otp",
                    data=payload
                )

                logger.info("OTP resent successfully", user_id=user_id)
                return {"success": True, "message": "OTP sent successfully"}

            except Exception as e:
                logger.error("OTP resend failed", error=str(e), user_id=user_id)
                return {"success": False, "error": str(e)}
