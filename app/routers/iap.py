from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Literal
from ..middleware.jwt_auth import get_current_user
from ..services.supabase_service import SupabaseService

router = APIRouter(prefix="/subscription", tags=["Subscription"])


class VerifyIAPRequest(BaseModel):
    """Request to verify IAP purchase."""
    receipt: str  # iOS receipt or Android purchase token
    platform: Literal["ios", "android"]


@router.post("/verify-iap")
async def verify_iap(
    request: VerifyIAPRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Verify In-App Purchase receipt and update user subscription.
    For iOS: receipt is the base64 encoded receipt data
    For Android: receipt is the purchase token
    """
    try:
        # TODO: Implement actual receipt verification
        # For iOS: Use Apple's verifyReceipt API
        # For Android: Use Google Play Developer API
        
        # For now, we'll do a basic validation and update subscription
        # In production, you MUST verify the receipt with Apple/Google
        
        if not request.receipt or len(request.receipt) < 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid receipt data"
            )
        
        # Update user subscription to pro
        await SupabaseService.update_user_subscription(current_user["id"], "pro")
        
        return {
            "success": True,
            "user_id": current_user["id"],
            "subscription_tier": "pro"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify IAP: {str(e)}"
        )

