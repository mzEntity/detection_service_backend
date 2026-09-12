from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import API_PREFIX
from app.routers import image, material, tasks, text, video

logger = logging.getLogger("detection-service")

app = FastAPI(
    title="AI Detection Service",
    version="1.0.0",
    description="Backend for an AI-content detection service (text / image / video).",
)

allowed_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": str(exc.detail)}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "invalid_request",
                "message": "The request is invalid or missing required fields.",
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred while processing the request.",
            }
        },
    )


for router in (text.router, image.router, video.router, tasks.router, material.router):
    app.include_router(router, prefix=API_PREFIX)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}