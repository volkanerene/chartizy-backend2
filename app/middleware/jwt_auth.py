from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional
from ..config import get_settings
from ..services.supabase_service import SupabaseService


security = HTTPBearer()


class JWTAuthMiddleware:
    """JWT Authentication middleware."""
    
    @staticmethod
    async def verify_token(token: str) -> Optional[dict]:
        """Verify JWT token."""
        settings = get_settings()
        try:
            # First try to verify with Supabase
            user_data = await SupabaseService.verify_token(token)
            if user_data and user_data.get("user"):
                return {
                    "user_id": str(user_data["user"].id),
                    "email": user_data["user"].email
                }
            
            # Fallback to manual JWT verification
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm]
            )
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email")
            }
        except JWTError:
            return None
        except Exception:
            return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Dependency to get current authenticated user."""
    token = credentials.credentials
    user_data = await JWTAuthMiddleware.verify_token(token)
    
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Get full user data from database
    user = await SupabaseService.get_user_by_id(user_data["user_id"])
    
    # Auto-create user in graphzy_users if they don't exist but are authenticated
    if not user and user_data.get("user_id") and user_data.get("email"):
        try:
            user = await SupabaseService.create_user(
                user_data["user_id"],
                user_data["email"]
            )
        except Exception:
            # If creation fails, return basic user data
            user = {
                "id": user_data["user_id"],
                "email": user_data["email"],
                "subscription_tier": "free",
                "chart_count": 0
            }
    
    if not user:
        # Return basic user data if everything fails
        user = {
            "id": user_data.get("user_id", ""),
            "email": user_data.get("email", ""),
            "subscription_tier": "free",
            "chart_count": 0
        }
    
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """Dependency to optionally get current user (for public endpoints)."""
    if not credentials:
        return None
    
    token = credentials.credentials
    user_data = await JWTAuthMiddleware.verify_token(token)
    
    if not user_data:
        return None
    
    user = await SupabaseService.get_user_by_id(user_data["user_id"])
    
    # Return basic user data if not found in database
    if not user and user_data:
        return {
            "id": user_data.get("user_id", ""),
            "email": user_data.get("email", ""),
            "subscription_tier": "free",
            "chart_count": 0
        }
    
    return user

