from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from ..services.supabase_service import SupabaseService
from ..middleware.jwt_auth import get_current_user


router = APIRouter(prefix="/profile", tags=["Profile"])


class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ProfileUpdateResponse(BaseModel):
    success: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None


@router.put("/update", response_model=ProfileUpdateResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user)
) -> ProfileUpdateResponse:
    """
    Update user profile (first_name, last_name).
    """
    user_id = str(current_user["id"])
    
    success = await SupabaseService.update_user_profile(
        user_id=user_id,
        first_name=request.first_name,
        last_name=request.last_name
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to update profile"
        )
    
    # Get updated user data
    updated_user = await SupabaseService.get_user_by_id(user_id)
    
    return ProfileUpdateResponse(
        success=True,
        first_name=updated_user.get("first_name") if updated_user else request.first_name,
        last_name=updated_user.get("last_name") if updated_user else request.last_name
    )

