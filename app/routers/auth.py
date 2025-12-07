from fastapi import APIRouter, HTTPException, Depends
from ..schemas.auth import LoginRequest, LoginResponse
from ..schemas.user import UserCreate, UserResponse
from ..services.supabase_service import SupabaseService
from ..middleware.jwt_auth import get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Authenticate user with email and password.
    Returns access token and user information.
    """
    try:
        auth_result = await SupabaseService.sign_in_with_password(
            email=request.email,
            password=request.password
        )
        
        if not auth_result.get("user") or not auth_result.get("session"):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        user = auth_result["user"]
        session = auth_result["session"]
        
        # Get or create user record in our users table
        user_data = await SupabaseService.get_user_by_id(str(user.id))
        if not user_data:
            user_data = await SupabaseService.create_user(
                user_id=str(user.id),
                email=user.email
            )
        
        return LoginResponse(
            access_token=session.access_token,
            token_type="bearer",
            user_id=str(user.id),
            email=user.email,
            subscription_tier=user_data.get("subscription_tier", "free"),
            chart_count=user_data.get("chart_count", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/register", response_model=LoginResponse)
async def register(request: UserCreate) -> LoginResponse:
    """
    Register a new user with email and password.
    Returns access token and user information.
    """
    try:
        auth_result = await SupabaseService.sign_up(
            email=request.email,
            password=request.password
        )
        
        if not auth_result.get("user"):
            raise HTTPException(
                status_code=400,
                detail="Registration failed"
            )
        
        user = auth_result["user"]
        session = auth_result.get("session")
        
        # Create user record in our users table
        user_data = await SupabaseService.create_user(
            user_id=str(user.id),
            email=user.email
        )
        
        # If email confirmation is required, session might be None
        access_token = session.access_token if session else ""
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            email=user.email,
            subscription_tier="free",
            chart_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Registration failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
) -> UserResponse:
    """Get current authenticated user's information."""
    return UserResponse(
        id=str(current_user["id"]),
        email=current_user["email"],
        first_name=current_user.get("first_name"),
        last_name=current_user.get("last_name"),
        subscription_tier=current_user.get("subscription_tier", "free"),
        chart_count=current_user.get("chart_count", 0),
        created_at=str(current_user.get("created_at", ""))
    )

