from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from ..middleware.jwt_auth import get_current_user
import os

# Try to import stripe, but make it optional
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None

# Initialize Stripe if available
if STRIPE_AVAILABLE:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

router = APIRouter(prefix="/subscription", tags=["Subscription"])


class CreateCheckoutSessionRequest(BaseModel):
    """Request to create a Stripe checkout session."""
    success_url: str
    cancel_url: str


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a Stripe Checkout Session for upgrading to Pro.
    Returns the session URL for redirecting the user.
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Stripe is not installed. Please install it with: pip install stripe"
        )
    
    if not stripe.api_key:
        raise HTTPException(
            status_code=500,
            detail="Stripe is not configured. Please set STRIPE_SECRET_KEY environment variable."
        )
    
    try:
        # Create a Stripe Checkout Session
        # Price ID should be set in environment variable or database
        price_id = os.getenv("STRIPE_PRICE_ID", "")
        if not price_id:
            raise HTTPException(
                status_code=500,
                detail="Stripe Price ID not configured"
            )
        
        session = stripe.checkout.Session.create(
            customer_email=current_user["email"],
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                "user_id": str(current_user["id"]),
            },
        )
        
        return {
            "session_id": session.id,
            "url": session.url,
        }
    except Exception as e:
        # Check if it's a Stripe error
        error_type = type(e).__name__
        if "Stripe" in error_type or "stripe" in str(type(e)):
            raise HTTPException(
                status_code=400,
                detail=f"Stripe error: {str(e)}"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(request: dict):
    """
    Handle Stripe webhook events.
    This endpoint should be called by Stripe when payment events occur.
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Stripe is not installed"
        )
    
    # Verify webhook signature
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        raise HTTPException(
            status_code=500,
            detail="Stripe webhook secret not configured"
        )
    
    # In production, verify the webhook signature here
    # For now, we'll just process the event
    
    event_type = request.get("type")
    
    if event_type == "checkout.session.completed":
        session = request.get("data", {}).get("object", {})
        user_id = session.get("metadata", {}).get("user_id")
        
        if user_id:
            # Update user subscription to pro
            from ..services.supabase_service import SupabaseService
            await SupabaseService.update_user_subscription(user_id, "pro")
    
    return {"status": "ok"}
