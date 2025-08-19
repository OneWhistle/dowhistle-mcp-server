from pydantic import BaseModel, Field
from typing import Optional, List


# -------------------------
# Sign In
# -------------------------
class SignInRequest(BaseModel):
    phone: str = Field(..., description="Digits only, without country code")
    countryCode: str = Field(..., description="Country code starting with +")
    name: str
    location: List[float] = Field(..., description="[latitude, longitude]")


class SignInUser(BaseModel):
    id: str
    _id: Optional[str]
    otp: Optional[str]


class SignInResponse(BaseModel):
    message: str
    user: SignInUser
    success: bool


# -------------------------
# Verify OTP
# -------------------------
class VerifyOtpRequest(BaseModel):
    id: str
    otp: str


class VerifyOtpUser(BaseModel):
    name: str
    phone: str
    countryCode: str
    taxiProvider: bool
    certified: bool


class VerifyOtpResponse(BaseModel):
    message: str
    user: VerifyOtpUser
    token: str
    uploadToken: str
    success: bool


# -------------------------
# Resend OTP
# -------------------------
class ResendOtpRequest(BaseModel):
    userid: str


class ResendOtpResponse(BaseModel):
    message: str
    success: bool
