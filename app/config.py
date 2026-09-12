from __future__ import annotations

import os


API_PREFIX = "/api/v1"

# Mock-only artificial inference delay, in seconds. Real models are naturally
# slow, so this only exists to make the mock behave like a real model on the
# timeline. Override any value with the MOCK_*_DELAY env var; set 0 to disable.
def _delay(name: str, default: float) -> float:
    return float(os.environ.get(name, default))


MOCK_TEXT_DELAY = _delay("MOCK_TEXT_DELAY", 1.0)
MOCK_IMAGE_DELAY = _delay("MOCK_IMAGE_DELAY", 2.0)
MOCK_VIDEO_DELAY = _delay("MOCK_VIDEO_DELAY", 6.0)

MODELS: dict[str, dict[str, str | list[str]]] = {
    "text-detector": {
        "name": "text-detector",
        "version": "1.0.0",
        "modality": "text",
    },
    "image-detector": {
        "name": "image-detector",
        "version": "1.0.0",
        "modality": "image",
    },
    "video-detector": {
        "name": "video-detector",
        "version": "1.0.0",
        "modality": "video",
    },
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
IMAGE_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
    "image/bmp",
}

VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
VIDEO_CONTENT_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
}