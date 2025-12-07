from pydantic import BaseModel
from typing import Optional, Any, Dict
from uuid import UUID


class TemplateBase(BaseModel):
    """Base template schema."""
    name: str
    description: Optional[str] = None
    chart_type: str
    is_premium: bool = False
    example_data: Optional[Dict[str, Any]] = None
    thumbnail_url: Optional[str] = None


class Template(TemplateBase):
    """Full template schema."""
    id: UUID
    
    class Config:
        from_attributes = True


class TemplateResponse(BaseModel):
    """Response schema for templates."""
    id: str
    name: str
    description: Optional[str] = None
    chart_type: str
    is_premium: bool
    example_data: Optional[Dict[str, Any]] = None
    thumbnail_url: Optional[str] = None
    
    class Config:
        from_attributes = True

