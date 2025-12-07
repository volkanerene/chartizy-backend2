from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from ..schemas.template import TemplateResponse
from ..services.supabase_service import SupabaseService
from ..middleware.jwt_auth import get_optional_user


router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get("", response_model=List[TemplateResponse])
async def get_templates(
    current_user: Optional[dict] = Depends(get_optional_user)
) -> List[TemplateResponse]:
    """
    Get all available templates.
    
    - Public templates are always visible
    - Premium templates show as locked for free users
    - All templates are accessible for pro users
    """
    templates = await SupabaseService.get_all_templates()
    
    # Determine user's subscription tier
    subscription_tier = "free"
    if current_user:
        subscription_tier = current_user.get("subscription_tier", "free")
    
    result = []
    for template in templates:
        result.append(
            TemplateResponse(
                id=str(template["id"]),
                name=template["name"],
                description=template.get("description"),
                chart_type=template["chart_type"],
                is_premium=template.get("is_premium", False),
                example_data=template.get("example_data"),
                thumbnail_url=template.get("thumbnail_url")
            )
        )
    
    return result


@router.get("/public", response_model=List[TemplateResponse])
async def get_public_templates() -> List[TemplateResponse]:
    """Get only non-premium (public) templates."""
    templates = await SupabaseService.get_public_templates()
    
    return [
        TemplateResponse(
            id=str(template["id"]),
            name=template["name"],
            description=template.get("description"),
            chart_type=template["chart_type"],
            is_premium=False,
            example_data=template.get("example_data"),
            thumbnail_url=template.get("thumbnail_url")
        )
        for template in templates
    ]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
) -> TemplateResponse:
    """Get a specific template by ID."""
    template = await SupabaseService.get_template_by_id(template_id)
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail="Template not found"
        )
    
    return TemplateResponse(
        id=str(template["id"]),
        name=template["name"],
        description=template.get("description"),
        chart_type=template["chart_type"],
        is_premium=template.get("is_premium", False),
        example_data=template.get("example_data"),
        thumbnail_url=template.get("thumbnail_url")
    )

