from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime
from ..schemas.chart import (
    ChartGenerateRequest,
    ChartGenerateResponse,
    ChartResponse
)
from ..services.supabase_service import SupabaseService
from ..services.openai_service import OpenAIService
from ..middleware.jwt_auth import get_current_user
import json


router = APIRouter(prefix="/chart", tags=["Charts"])


FREE_CHART_LIMIT = 5


@router.post("/generate", response_model=ChartGenerateResponse)
async def generate_chart(
    request: ChartGenerateRequest,
    current_user: dict = Depends(get_current_user)
) -> ChartGenerateResponse:
    """
    Generate a chart using AI.
    
    - Validates user subscription and quota
    - Calls OpenAI to generate chart configuration
    - Saves result to database
    - Returns chart config, JSX code, and description
    """
    user_id = str(current_user["id"])
    subscription_tier = current_user.get("subscription_tier", "free")
    chart_count = current_user.get("chart_count", 0)
    
    # Check quota for free users
    if subscription_tier == "free" and chart_count >= FREE_CHART_LIMIT:
        raise HTTPException(
            status_code=403,
            detail=f"Free users can only generate {FREE_CHART_LIMIT} charts. Upgrade to Pro for unlimited charts."
        )
    
    # Get template info
    template = await SupabaseService.get_template_by_id(request.template_id)
    if not template:
        raise HTTPException(
            status_code=404,
            detail="Template not found"
        )
    
    # Check if template is premium and user is free
    if template.get("is_premium") and subscription_tier == "free":
        raise HTTPException(
            status_code=403,
            detail="This template requires a Pro subscription"
        )
    
    # Determine chart type
    chart_type = request.chart_type or template.get("chart_type", "bar")
    
    # Generate chart with OpenAI
    result = await OpenAIService.generate_chart(
        chart_type=chart_type,
        data=request.data
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Chart generation failed: {result.get('error', 'Unknown error')}"
        )
    
    # Save chart to database
    chart_data = await SupabaseService.create_chart(
        user_id=user_id,
        template_id=request.template_id,
        input_data=request.data,
        result_visual=json.dumps(result.get("chartConfig", {})),
        result_code=result.get("jsx", "")
    )
    
    # Update user's chart count
    await SupabaseService.update_user_chart_count(user_id, chart_count + 1)
    
    return ChartGenerateResponse(
        id=str(chart_data.get("id", "")),
        chart_config=result.get("chartConfig", {}),
        jsx=result.get("jsx", ""),
        svg=result.get("svg"),
        description=result.get("description", ""),
        created_at=str(chart_data.get("created_at", datetime.now().isoformat()))
    )


@router.get("/user/{user_id}", response_model=List[ChartResponse])
async def get_user_charts(
    user_id: str,
    current_user: dict = Depends(get_current_user)
) -> List[ChartResponse]:
    """Get all charts for a specific user."""
    # Verify the requesting user is the same as the user_id or implement admin check
    if str(current_user["id"]) != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own charts"
        )
    
    charts = await SupabaseService.get_charts_by_user(user_id)
    
    return [
        ChartResponse(
            id=str(chart["id"]),
            template_id=str(chart["template_id"]),
            input_data=chart.get("input_data", {}),
            result_visual=chart.get("result_visual"),
            result_code=chart.get("result_code"),
            created_at=str(chart.get("created_at", ""))
        )
        for chart in charts
    ]


@router.get("/{chart_id}", response_model=ChartResponse)
async def get_chart(
    chart_id: str,
    current_user: dict = Depends(get_current_user)
) -> ChartResponse:
    """Get a specific chart by ID."""
    chart = await SupabaseService.get_chart_by_id(chart_id)
    
    if not chart:
        raise HTTPException(
            status_code=404,
            detail="Chart not found"
        )
    
    # Verify ownership
    if str(chart["user_id"]) != str(current_user["id"]):
        raise HTTPException(
            status_code=403,
            detail="You can only view your own charts"
        )
    
    return ChartResponse(
        id=str(chart["id"]),
        template_id=str(chart["template_id"]),
        input_data=chart.get("input_data", {}),
        result_visual=chart.get("result_visual"),
        result_code=chart.get("result_code"),
        created_at=str(chart.get("created_at", ""))
    )


@router.delete("/{chart_id}")
async def delete_chart(
    chart_id: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Delete a chart."""
    chart = await SupabaseService.get_chart_by_id(chart_id)
    
    if not chart:
        raise HTTPException(
            status_code=404,
            detail="Chart not found"
        )
    
    # Verify ownership
    if str(chart["user_id"]) != str(current_user["id"]):
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own charts"
        )
    
    success = await SupabaseService.delete_chart(chart_id)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete chart"
        )
    
    # Decrement chart count
    chart_count = current_user.get("chart_count", 1)
    await SupabaseService.update_user_chart_count(
        str(current_user["id"]),
        max(0, chart_count - 1)
    )
    
    return {"success": True, "message": "Chart deleted successfully"}

