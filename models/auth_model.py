from pydantic import BaseModel, Field, computed_field
from typing import Optional, List


# -------------------------
# Sign In
# -------------------------
class SignInRequest(BaseModel):
    phone: str = Field(..., description="Digits only, without country code")
    countryCode: str = Field(..., description="Country code starting with +")
    name: str
    latitude: float = Field(
        ..., ge=-90, le=90, description="Latitude coordinate (-90 to 90)"
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude   coordinate (-180 to 180)"
    )

    @computed_field(alias="location", return_type=List[float])
    @property
    def location_array(self) -> List[float]:
        return [self.latitude, self.longitude]


class SignInUser(BaseModel):
    id: str = Field(..., description="Unique user identifier")
    # _id: str = Field(
    #     ..., description="Unique user identifier (duplicate of id)", alias="id"
    # )
    otp: str = Field(..., description="One-time password for verification")


class SignInResponse(BaseModel):
    message: str
    user: SignInUser
    success: bool


class SignInErrorResponse(BaseModel):
    success: bool = False
    error: str
    payload: Optional[SignInRequest] = None


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


class VerifyOtpErrorResponse(BaseModel):
    success: bool = False
    error: str
    payload: Optional[VerifyOtpRequest] = None


# -------------------------
# Resend OTP
# -------------------------
class ResendOtpRequest(BaseModel):
    userid: str


class ResendOtpResponse(BaseModel):
    message: str
    success: bool


class ResendOtpErrorResponse(BaseModel):
    success: bool = False
    error: str
    payload: Optional[ResendOtpRequest] = None
