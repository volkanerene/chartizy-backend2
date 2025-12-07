from pydantic import BaseModel
from typing import Literal, Optional


class SubscriptionUpdate(BaseModel):
    """Request schema for subscription updates."""
    user_id: str
    tier: Literal["free", "pro"]
    payment_method: Optional[str] = None  # "stripe" or "iap"
    transaction_id: Optional[str] = None


class SubscriptionResponse(BaseModel):
    """Response schema for subscription operations."""
    success: bool
    message: str
    subscription_tier: str

