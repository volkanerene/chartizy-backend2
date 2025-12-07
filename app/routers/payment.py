from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from ..middleware.jwt_auth import get_current_user
from ..config import get_settings
import os
import requests
import json
import hashlib
import hmac
import base64
from urllib.parse import urlencode

router = APIRouter(prefix="/payment", tags=["Payment"])
settings = get_settings()


class CreatePaymentRequest(BaseModel):
    """Request to create a payment."""
    success_url: str
    cancel_url: str
    amount: float  # Amount in USD
    currency: str = "USD"


class CapturePaymentRequest(BaseModel):
    """Request to capture a PayPal payment."""
    order_id: str


class CreatePayTRRequest(BaseModel):
    """Request to create a PayTR payment."""
    success_url: str
    fail_url: str
    amount: float  # Amount in TRY
    user_id: str  # User ID for order tracking


class PayPalAccessToken(BaseModel):
    """PayPal access token response."""
    access_token: str
    token_type: str
    expires_in: int


@router.post("/create-paypal-session")
async def create_paypal_session(
    request: CreatePaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a PayPal payment session for upgrading to Pro.
    Returns the approval URL for redirecting the user.
    """
    paypal_client_id = os.getenv("PAYPAL_CLIENT_ID", "")
    paypal_secret = os.getenv("PAYPAL_SECRET", "")
    paypal_mode = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox or live
    
    if not paypal_client_id or not paypal_secret:
        raise HTTPException(
            status_code=500,
            detail="PayPal is not configured. Please set PAYPAL_CLIENT_ID and PAYPAL_SECRET environment variables."
        )
    
    base_url = "https://api.sandbox.paypal.com" if paypal_mode == "sandbox" else "https://api.paypal.com"
    
    try:
        # Step 1: Get PayPal access token
        auth_response = requests.post(
            f"{base_url}/v1/oauth2/token",
            headers={
                "Accept": "application/json",
                "Accept-Language": "en_US",
            },
            auth=(paypal_client_id, paypal_secret),
            data={
                "grant_type": "client_credentials"
            }
        )
        
        if auth_response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get PayPal access token: {auth_response.text}"
            )
        
        access_token = auth_response.json()["access_token"]
        
        # Step 2: Create PayPal order
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": request.currency,
                        "value": str(request.amount)
                    },
                    "description": "Graphzy Pro Subscription"
                }
            ],
            "application_context": {
                "brand_name": "Graphzy",
                "landing_page": "BILLING",
                "user_action": "PAY_NOW",
                "return_url": request.success_url,
                "cancel_url": request.cancel_url
            }
        }
        
        order_response = requests.post(
            f"{base_url}/v2/checkout/orders",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            },
            json=order_data
        )
        
        if order_response.status_code != 201:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create PayPal order: {order_response.text}"
            )
        
        order = order_response.json()
        
        # Find approval URL
        approval_url = None
        for link in order.get("links", []):
            if link.get("rel") == "approve":
                approval_url = link.get("href")
                break
        
        if not approval_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to get PayPal approval URL"
            )
        
        return {
            "order_id": order["id"],
            "approval_url": approval_url,
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"PayPal API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create PayPal session: {str(e)}"
        )


@router.post("/capture-paypal-payment")
async def capture_paypal_payment(
    request: CapturePaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Capture a PayPal payment after user approval.
    This should be called from the success URL callback.
    """
    order_id = request.order_id
    
    paypal_client_id = os.getenv("PAYPAL_CLIENT_ID", "")
    paypal_secret = os.getenv("PAYPAL_SECRET", "")
    paypal_mode = os.getenv("PAYPAL_MODE", "sandbox")
    
    if not paypal_client_id or not paypal_secret:
        raise HTTPException(
            status_code=500,
            detail="PayPal is not configured"
        )
    
    base_url = "https://api.sandbox.paypal.com" if paypal_mode == "sandbox" else "https://api.paypal.com"
    
    try:
        # Get access token
        auth_response = requests.post(
            f"{base_url}/v1/oauth2/token",
            headers={
                "Accept": "application/json",
                "Accept-Language": "en_US",
            },
            auth=(paypal_client_id, paypal_secret),
            data={
                "grant_type": "client_credentials"
            }
        )
        
        if auth_response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail="Failed to get PayPal access token"
            )
        
        access_token = auth_response.json()["access_token"]
        
        # Capture the payment
        capture_response = requests.post(
            f"{base_url}/v2/checkout/orders/{order_id}/capture",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        if capture_response.status_code != 201:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to capture payment: {capture_response.text}"
            )
        
        capture_data = capture_response.json()
        
        # Check if payment was successful
        if capture_data.get("status") == "COMPLETED":
            # Update user subscription to pro
            from ..services.supabase_service import SupabaseService
            await SupabaseService.update_user_subscription(str(current_user["id"]), "pro")
            
            return {
                "success": True,
                "order_id": order_id,
                "status": "completed"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Payment not completed: {capture_data.get('status')}"
            )
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"PayPal API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to capture payment: {str(e)}"
        )


@router.post("/webhook")
async def paypal_webhook(request: dict):
    """
    Handle PayPal webhook events.
    This endpoint should be called by PayPal when payment events occur.
    """
    # In production, verify the webhook signature here
    # For now, we'll just process the event
    
    event_type = request.get("event_type", "")
    
    if event_type == "PAYMENT.CAPTURE.COMPLETED":
        resource = request.get("resource", {})
        order_id = resource.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
        
        # You can store order_id -> user_id mapping in database
        # For now, we'll need to handle this differently
        # This is a simplified version
    
    return {"status": "ok"}


# PayTR Integration (Türkiye için)
@router.post("/create-paytr-session")
async def create_paytr_session(
    request: CreatePayTRRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a PayTR payment session for upgrading to Pro.
    Returns the redirect URL for payment (works on both web and mobile).
    """
    merchant_id = settings.paytr_merchant_id
    merchant_key = settings.paytr_merchant_key
    merchant_salt = settings.paytr_merchant_salt
    paytr_mode = settings.paytr_mode
    
    if not merchant_id or not merchant_key or not merchant_salt:
        raise HTTPException(
            status_code=500,
            detail="PayTR is not configured. Please set PAYTR_MERCHANT_ID, PAYTR_MERCHANT_KEY, and PAYTR_MERCHANT_SALT environment variables in your .env file."
        )
    
    # PayTR API endpoint
    api_url = "https://www.paytr.com/odeme/api/get-token" if paytr_mode == "live" else "https://www.paytr.com/odeme/test/get-token"
    
    # Generate order ID
    import uuid
    order_id = f"graphzy-{current_user['id']}-{uuid.uuid4().hex[:8]}"
    
    # Amount in kuruş (multiply by 100)
    amount_kurus = int(request.amount * 100)
    
    # Prepare user basket (base64 encoded)
    basket = json.dumps([["Graphzy Pro Subscription", request.amount, 1]])
    user_basket = base64.b64encode(basket.encode("utf-8")).decode("utf-8")
    
    # Create hash for PayTR (PayTR dokümantasyonuna göre)
    # Format: merchant_id + merchant_salt + merchant_oid + email + payment_amount + user_basket + no_installment + max_installment + test_mode
    hash_str = f"{merchant_id}{merchant_salt}{order_id}{current_user['email']}{amount_kurus}{user_basket}00{'1' if paytr_mode == 'test' else '0'}"
    hash_value = base64.b64encode(
        hmac.new(merchant_key.encode("utf-8"), hash_str.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")
    print(f"PayTR Hash String: {hash_str[:50]}...")  # Debug için
    
    # Prepare payment data
    payment_data = {
        "merchant_id": merchant_id,
        "user_ip": "127.0.0.1",  # In production, get from request headers
        "merchant_oid": order_id,
        "email": current_user["email"],
        "payment_amount": amount_kurus,
        "paytr_token": hash_value,
        "user_basket": user_basket,
        "no_installment": 0,
        "max_installment": 0,
        "currency": "TL",
        "test_mode": "1" if paytr_mode == "test" else "0",
        "lang": "tr",
        "success_url": request.success_url,
        "fail_url": request.fail_url,
    }
    
    try:
        # Send request to PayTR
        response = requests.post(api_url, data=payment_data, timeout=30)
        
        if response.status_code != 200:
            error_text = response.text
            print(f"PayTR API HTTP Error {response.status_code}: {error_text}")
            raise HTTPException(
                status_code=500,
                detail=f"PayTR API HTTP error ({response.status_code}): {error_text[:200]}"
            )
        
        result = response.json()
        print(f"PayTR API Response: {result}")
        
        if result.get("status") == "success":
            token = result.get("token")
            redirect_url = f"https://www.paytr.com/odeme/guvenli/{token}" if paytr_mode == "live" else f"https://www.paytr.com/odeme/test/guvenli/{token}"
            
            return {
                "success": True,
                "order_id": order_id,
                "iframe_url": token,  # For iframe integration (optional)
                "redirect_url": redirect_url,  # For redirect (works on mobile too)
            }
        else:
            error_reason = result.get('reason', 'Unknown error')
            error_status = result.get('status', 'failed')
            print(f"PayTR API Error - Status: {error_status}, Reason: {error_reason}")
            raise HTTPException(
                status_code=400,
                detail=f"PayTR error: {error_reason} (Status: {error_status})"
            )
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"PayTR API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create PayTR session: {str(e)}"
        )


@router.post("/paytr-callback")
async def paytr_callback(request: Request):
    """
    Handle PayTR payment callback.
    This endpoint should be called by PayTR after payment completion.
    PayTR sends form data via POST.
    """
    merchant_key = settings.paytr_merchant_key
    merchant_salt = settings.paytr_merchant_salt
    
    if not merchant_key or not merchant_salt:
        raise HTTPException(
            status_code=500,
            detail="PayTR is not configured"
        )
    
    # Get form data from PayTR
    form_data = await request.form()
    
    merchant_oid = form_data.get("merchant_oid")
    status = form_data.get("status")
    total_amount = form_data.get("total_amount")
    hash_value = form_data.get("hash")
    
    if not merchant_oid or not status or not total_amount or not hash_value:
        raise HTTPException(
            status_code=400,
            detail="Missing required PayTR callback parameters"
        )
    
    # Verify hash
    hash_str = f"{merchant_oid}{merchant_salt}{status}{total_amount}"
    calculated_hash = base64.b64encode(
        hmac.new(merchant_key.encode("utf-8"), hash_str.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")
    
    if calculated_hash != hash_value:
        raise HTTPException(
            status_code=400,
            detail="Invalid hash - possible security issue"
        )
    
    # Check payment status
    if status == "success":
        # Extract user_id from order_id (format: graphzy-{user_id}-{uuid})
        try:
            user_id = merchant_oid.split("-")[1] if "-" in merchant_oid else None
            
            if user_id:
                # Update user subscription to pro
                from ..services.supabase_service import SupabaseService
                await SupabaseService.update_user_subscription(user_id, "pro")
                
                return {"status": "success", "message": "Payment completed and subscription updated"}
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract user_id from order_id"
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update subscription: {str(e)}"
            )
    else:
        return {"status": "failed", "message": "Payment failed"}

