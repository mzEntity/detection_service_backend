from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query

from app.config import MODELS
from app.models import ModelCatalogItem, ModelCatalogResponse

router = APIRouter()


@router.get("/models", response_model=ModelCatalogResponse)
async def list_models(
    modality: Literal["text", "image", "video"] | None = Query(default=None),
) -> ModelCatalogResponse:
    entries = MODELS.values()
    if modality is not None:
        entries = [entry for entry in entries if entry["modality"] == modality]
    return ModelCatalogResponse(
        models=[
            ModelCatalogItem(
                name=entry["name"],
                version=entry["version"],
                modality=entry["modality"],
            )
            for entry in entries
        ]
    )