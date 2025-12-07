from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
from uuid import UUID


class ChartBase(BaseModel):
    """Base chart schema."""
    template_id: str
    input_data: Dict[str, Any]


class ChartCreate(ChartBase):
    """Schema for creating a chart."""
    user_id: str


class Chart(ChartBase):
    """Full chart schema."""
    id: UUID
    user_id: UUID
    result_visual: Optional[str] = None
    result_code: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChartGenerateRequest(BaseModel):
    """Request schema for chart generation."""
    user_id: str
    template_id: str
    data: Dict[str, Any]
    chart_type: Optional[str] = None


class ChartGenerateResponse(BaseModel):
    """Response schema for chart generation."""
    id: str
    chart_config: Dict[str, Any]
    jsx: str
    svg: Optional[str] = None
    description: str
    created_at: str


class ChartResponse(BaseModel):
    """Response schema for chart list."""
    id: str
    template_id: str
    input_data: Dict[str, Any]
    result_visual: Optional[str] = None
    result_code: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True

