from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class DetectionResult(BaseModel):
    label: Literal["ai_generated", "human_generated", "uncertain"]
    ai_probability: float = Field(ge=0.0, le=1.0)
    human_probability: float = Field(ge=0.0, le=1.0)
    confidence: Literal["low", "medium", "high"]
    reasoning: str


class ModelInfo(BaseModel):
    name: str
    version: str


class ErrorInfo(BaseModel):
    code: Optional[str] = None
    message: str = Field(min_length=1)


class DetectionResponse(BaseModel):
    id: str
    modality: Literal["text", "image", "video"]
    status: Literal["queued", "processing", "completed", "failed"]
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    result: Optional[DetectionResult] = None
    model: Optional[ModelInfo] = None
    error: Optional[ErrorInfo] = None


class TextDetectionRequest(BaseModel):
    model: str
    context: Optional[str] = None
    text: str = Field(min_length=1)


class ErrorResponse(BaseModel):
    error: ErrorInfo


class ModelCatalogItem(BaseModel):
    name: str
    version: str
    modality: str


class ModelCatalogResponse(BaseModel):
    models: list[ModelCatalogItem]