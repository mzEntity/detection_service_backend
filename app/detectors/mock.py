"""Deterministic mock detectors (default implementation).

These are NOT real AI models. They exist so the full API flow works without
any ML dependencies. Results are hash-derived: identical input always yields
identical output, which makes the API stable to test.

Each detect_* simulates inference latency (``time.sleep``) so the mock behaves
on the same timeline as a real model; latency is configurable via app/config.py
(MOCK_*_DELAY, disable with 0). With a real model this sleep is gone - the
model's own compute time replaces it.

Do not modify this file to add real models. Real detectors belong in
``text.py`` / ``image.py`` / ``video.py``; flip the imports in ``__init__.py``
to activate them (see the package docstring).
"""
from __future__ import annotations

import hashlib
import time

from app.config import MOCK_IMAGE_DELAY, MOCK_TEXT_DELAY, MOCK_VIDEO_DELAY
from app.models import DetectionResult, ModelInfo


def _digest(*parts: bytes | str) -> int:
    hasher = hashlib.sha256()
    for part in parts:
        if isinstance(part, str):
            part = part.encode("utf-8")
        hasher.update(part)
    return int.from_bytes(hasher.digest()[:8], "big")


def _score(seed: int, salt: str = "") -> float:
    value = _digest(f"{seed}{salt}")
    return (value % 9000) / 9000.0


def _clamp_unit(value: float, lo: float = 0.01, hi: float = 0.99) -> float:
    return round(min(max(value, lo), hi), 2)


def _label_and_confidence(ai: float) -> tuple[str, str]:
    if ai >= 0.6:
        if ai >= 0.78:
            return "ai_generated", "high"
        return "ai_generated", "medium" if ai >= 0.66 else "low"
    if ai <= 0.4:
        if ai <= 0.22:
            return "human_generated", "high"
        return "human_generated", "medium" if ai <= 0.34 else "low"
    return "uncertain", "low"


def _to_result(ai_in: float, reasoning: str) -> DetectionResult:
    label, confidence = _label_and_confidence(ai_in)
    if label == "uncertain":
        ai = _clamp_unit(0.5 + (ai_in - 0.5) * 0.3, 0.35, 0.65)
    else:
        ai = _clamp_unit(ai_in)
    return DetectionResult(
        label=label,
        ai_probability=ai,
        human_probability=round(1.0 - ai, 2),
        confidence=confidence,
        reasoning=reasoning,
    )


def detect_text(text: str, context: str | None, model: str, version: str) -> DetectionResult:
    time.sleep(MOCK_TEXT_DELAY)
    seed = _digest(text, context or "")
    length = len(text.strip())
    if length < 40:
        base = _score(seed, "short")
        return _to_result(
            base,
            "The input text is too short for reliable detection; the model "
            "could not confidently attribute it to either source.",
        )

    base = _score(seed, "text")

    ai_markers = [
        "moreover",
        "furthermore",
        "in conclusion",
        "additionally",
        "it is important to note",
        "delve",
        "tapestry",
        "landscape",
        "realm",
        "leverage",
    ]
    marker_hits = sum(1 for word in ai_markers if word in text.lower())
    base += marker_hits * 0.04

    label = _label_and_confidence(base)[0]
    if label == "ai_generated":
        reasoning = (
            "The text exhibits uniform sentence structure, predictable "
            "transition phrases, and low lexical variation, which are "
            "consistent with machine-generated writing."
        )
    elif label == "human_generated":
        reasoning = (
            "The text shows natural variation in sentence length, informal "
            "connectors, and idiosyncratic phrasing that are typical of "
            "human-authored content."
        )
    else:
        reasoning = (
            "The text mixes patterns associated with both human and machine "
            "writing; the model could not decide with sufficient confidence."
        )
    return _to_result(base, reasoning)


def detect_image(data: bytes, filename: str | None, context: str | None, model: str, version: str) -> DetectionResult:
    time.sleep(MOCK_IMAGE_DELAY)
    base = _score(_digest(data), "image")
    size = len(data)

    offset = 0.0
    if size and 100_000 < size < 900_000:
        offset = -0.05
    elif size >= 1_500_000:
        offset = 0.05

    base = _clamp_unit(base + offset)

    label = _label_and_confidence(base)[0]
    if label == "ai_generated":
        reasoning = (
            "Visual features such as overly smooth textures, strong "
            "contrast edges, and slightly unnatural proportions are "
            "consistent with image generation models."
        )
    elif label == "human_generated":
        reasoning = (
            "The image shows organic noise, realistic light falloff, and "
            "natural compression artifacts that are typical of photographs "
            "or human-created artwork."
        )
    else:
        reasoning = (
            "Image features do not strongly favor either origin; the model "
            "could not decide with sufficient confidence."
        )
    return _to_result(base, reasoning)


def detect_video_seed(data: bytes, context: str | None) -> int:
    return _digest(data, context or "")


def detect_video(seed: int, model: str, version: str) -> DetectionResult:
    time.sleep(MOCK_VIDEO_DELAY)
    base = _score(seed, "video")

    label = _label_and_confidence(base)[0]
    if label == "ai_generated":
        reasoning = (
            "Frames sampled across the video show consistent synthetic "
            "texture patterns and no natural motion blur or camera noise."
        )
    elif label == "human_generated":
        reasoning = (
            "Sampled frames show natural motion blur, per-frame noise "
            "variations, and realistic temporal continuity typical of "
            "camera-captured footage."
        )
    else:
        reasoning = (
            "Temporal and per-frame features are balanced between synthetic "
            "and captured footage; the model could not decide with "
            "sufficient confidence."
        )
    return _to_result(base, reasoning)


def model_info(name: str, version: str) -> ModelInfo:
    return ModelInfo(name=name, version=version)