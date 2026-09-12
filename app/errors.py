from __future__ import annotations

import uuid as uuid_lib

from fastapi import HTTPException

from app.config import MODELS


def model_version(model_id: str, modality: str) -> str:
    entry = MODELS.get(model_id)
    if entry is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "invalid_model",
                    "message": f"Unknown model '{model_id}'. Supported models: {', '.join(sorted(MODELS))}.",
                }
            },
        )
    if entry["modality"] != modality:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "invalid_model",
                    "message": f"Model '{model_id}' does not support {modality} detection.",
                }
            },
        )
    return str(entry["version"])


def new_detection_id() -> str:
    return f"det_{uuid_lib.uuid4().hex[:12]}"