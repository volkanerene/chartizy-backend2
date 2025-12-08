from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from ..config import get_settings


class SupabaseService:
    """Service for Supabase database operations."""
    
    _client: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client."""
        if cls._client is None:
            settings = get_settings()
            cls._client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
        return cls._client
    
    # User operations
    @classmethod
    async def get_user_by_id(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        client = cls.get_client()
        try:
            response = client.table("graphzy_users").select("*").eq("id", user_id).maybe_single().execute()
            return response.data if response.data else None
        except Exception:
            # Table might not exist yet or other error
            return None
    
    @classmethod
    async def get_user_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        client = cls.get_client()
        response = client.table("graphzy_users").select("*").eq("email", email).single().execute()
        return response.data if response.data else None
    
    @classmethod
    async def create_user(cls, user_id: str, email: str) -> Dict[str, Any]:
        """Create a new user record."""
        client = cls.get_client()
        try:
            response = client.table("graphzy_users").upsert({
                "id": user_id,
                "email": email,
                "subscription_tier": "free",
                "chart_count": 0
            }, on_conflict="id").execute()
            return response.data[0] if response.data else {
                "id": user_id,
                "email": email,
                "subscription_tier": "free",
                "chart_count": 0
            }
        except Exception:
            # Return basic user data if table doesn't exist
            return {
                "id": user_id,
                "email": email,
                "subscription_tier": "free",
                "chart_count": 0
            }
    
    @classmethod
    async def update_user_profile(cls, user_id: str, first_name: Optional[str] = None, last_name: Optional[str] = None) -> bool:
        """Update user profile (first_name, last_name)."""
        client = cls.get_client()
        update_data = {}
        if first_name is not None:
            update_data["first_name"] = first_name
        if last_name is not None:
            update_data["last_name"] = last_name
        
        if not update_data:
            return False
        
        try:
            # First, ensure user exists in graphzy_users table
            existing_user = await cls.get_user_by_id(user_id)
            if not existing_user:
                # Create user if doesn't exist
                await cls.create_user(user_id, "")
            
            # Update user profile
            response = client.table("graphzy_users").update(update_data).eq("id", user_id).execute()
            return bool(response.data)
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False
    
    @classmethod
    async def update_user_chart_count(cls, user_id: str, count: int) -> bool:
        """Update user's chart count."""
        client = cls.get_client()
        response = client.table("graphzy_users").update({
            "chart_count": count
        }).eq("id", user_id).execute()
        return bool(response.data)
    
    @classmethod
    async def update_user_subscription(cls, user_id: str, tier: str) -> bool:
        """Update user's subscription tier."""
        client = cls.get_client()
        response = client.table("graphzy_users").update({
            "subscription_tier": tier
        }).eq("id", user_id).execute()
        return bool(response.data)
    
    # Chart operations
    @classmethod
    async def get_charts_by_user(cls, user_id: str) -> List[Dict[str, Any]]:
        """Get all charts for a user."""
        client = cls.get_client()
        response = client.table("graphzy_charts").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data if response.data else []
    
    @classmethod
    async def get_chart_by_id(cls, chart_id: str) -> Optional[Dict[str, Any]]:
        """Get chart by ID."""
        client = cls.get_client()
        try:
            response = client.table("graphzy_charts").select("*").eq("id", chart_id).maybe_single().execute()
            return response.data if response.data else None
        except Exception as e:
            print(f"Error fetching chart {chart_id}: {e}")
            return None
    
    @classmethod
    async def create_chart(
        cls,
        user_id: str,
        template_id: str,
        input_data: Dict[str, Any],
        result_visual: Optional[str] = None,
        result_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new chart."""
        client = cls.get_client()
        response = client.table("graphzy_charts").insert({
            "user_id": user_id,
            "template_id": template_id,
            "input_data": input_data,
            "result_visual": result_visual,
            "result_code": result_code
        }).execute()
        return response.data[0] if response.data else {}
    
    @classmethod
    async def delete_chart(cls, chart_id: str) -> bool:
        """Delete a chart."""
        client = cls.get_client()
        response = client.table("graphzy_charts").delete().eq("id", chart_id).execute()
        return bool(response.data)
    
    # Template operations
    @classmethod
    async def get_all_templates(cls) -> List[Dict[str, Any]]:
        """Get all templates."""
        client = cls.get_client()
        response = client.table("graphzy_templates").select("*").order("name").execute()
        return response.data if response.data else []
    
    @classmethod
    async def get_template_by_id(cls, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID."""
        client = cls.get_client()
        response = client.table("graphzy_templates").select("*").eq("id", template_id).single().execute()
        return response.data if response.data else None
    
    @classmethod
    async def get_public_templates(cls) -> List[Dict[str, Any]]:
        """Get non-premium templates."""
        client = cls.get_client()
        response = client.table("graphzy_templates").select("*").eq("is_premium", False).order("name").execute()
        return response.data if response.data else []
    
    # Auth operations
    @classmethod
    async def sign_in_with_password(cls, email: str, password: str) -> Dict[str, Any]:
        """Sign in user with email and password."""
        client = cls.get_client()
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return {
            "user": response.user,
            "session": response.session
        }
    
    @classmethod
    async def sign_up(cls, email: str, password: str) -> Dict[str, Any]:
        """Sign up a new user."""
        client = cls.get_client()
        response = client.auth.sign_up({
            "email": email,
            "password": password
        })
        return {
            "user": response.user,
            "session": response.session
        }
    
    @classmethod
    async def verify_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and get user."""
        client = cls.get_client()
        try:
            response = client.auth.get_user(token)
            return {"user": response.user} if response.user else None
        except Exception:
            return None

