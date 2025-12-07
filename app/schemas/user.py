from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str


class User(UserBase):
    """Full user schema with all fields."""
    id: UUID
    created_at: datetime
    subscription_tier: Literal["free", "pro"] = "free"
    chart_count: int = 0
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Response schema for user data."""
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    subscription_tier: str
    chart_count: int
    created_at: str
    
    class Config:
        from_attributes = True

