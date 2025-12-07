from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """Request schema for login."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Response schema for login."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    subscription_tier: str
    chart_count: int


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[str] = None
    email: Optional[str] = None

