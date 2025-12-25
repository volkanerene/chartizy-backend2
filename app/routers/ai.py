from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from ..services.openai_service import OpenAIService
from ..middleware.jwt_auth import get_current_user, get_optional_user
import json

router = APIRouter(prefix="/ai", tags=["AI"])


class AnalyzePromptRequest(BaseModel):
    prompt: str
    language: Optional[str] = "auto"


class ChartSuggestion(BaseModel):
    chart_type: str
    confidence: int
    reason: str


class AnalyzePromptResponse(BaseModel):
    success: bool
    labels: List[str]
    values: List[float]
    title: Optional[str]
    description: Optional[str]
    suggested_charts: List[ChartSuggestion]
    data_interpretation: str


class TranscribeAudioRequest(BaseModel):
    audio_base64: str
    mime_type: Optional[str] = None


class TranscribeAudioResponse(BaseModel):
    text: str


@router.post("/analyze-prompt", response_model=AnalyzePromptResponse)
async def analyze_prompt(
    request: AnalyzePromptRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Use AI to analyze a natural language prompt and generate chart data.
    """
    try:
        result = await OpenAIService.analyze_chart_prompt(request.prompt)
        return AnalyzePromptResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(e)}"
        )


@router.post("/transcribe-audio", response_model=TranscribeAudioResponse)
async def transcribe_audio(request: TranscribeAudioRequest):
    result = await OpenAIService.transcribe_audio(request.audio_base64, request.mime_type)
    if "error" in result:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {result['error']}")
    return TranscribeAudioResponse(text=result.get("text", ""))


class GenerateDataRequest(BaseModel):
    description: str
    data_points: Optional[int] = 6
    chart_type: Optional[str] = None


class GenerateDataResponse(BaseModel):
    labels: List[str]
    values: List[float]
    title: str
    suggested_type: str


@router.post("/generate-data", response_model=GenerateDataResponse)
async def generate_data(
    request: GenerateDataRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Generate sample data based on a description.
    """
    try:
        result = await OpenAIService.generate_chart_data(
            request.description,
            request.data_points,
            request.chart_type
        )
        return GenerateDataResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Data generation failed: {str(e)}"
        )
