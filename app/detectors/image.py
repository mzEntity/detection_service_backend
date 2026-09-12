"""Real image detector: implement `detect_image` here.

Where this fits
---------------
- Scheduled through ``app/runner.py::run_detection`` (registered by
  ``POST /api/v1/detections/image`` in app/routers/image.py). The router
  validates the file (type/empty) and creates the queued task; the runner
  executes this detector in a worker thread.
- Reference implementation (do not edit): ``mock.py::detect_image``.

Received input
--------------
``data`` is the raw file bytes. Decode them with an image library of your
choice (e.g. Pillow / torchvision / opencv). ``filename`` carries the original
name (extension already validated by app/files.py) and may be useful for
heuristics; the real security boundary is the backend, not the client.

Expected behavior
-----------------
Return a ``DetectionResult`` exactly like the text detector:
    label / ai_probability / human_probability / confidence / reasoning
Probabilities must sum to 1.0, confidence in {"low","medium","high"},
and ``reasoning`` must be a short, honest, human-readable explanation.

Steps to wire up
----------------
1. Implement the body below.
2. In ``app/detectors/__init__.py``, import this function instead of
   ``app.detectors.mock.detect_image``.
"""
from __future__ import annotations

from app.models import DetectionResult


def detect_image(data: bytes, filename: str | None, context: str | None, model: str, version: str) -> DetectionResult:
    """Detect whether the uploaded image was AI-generated or not.

    Args:
        data:     Raw bytes of the uploaded image.
        filename: Original filename (extension already pre-validated).
        context:  Optional user-supplied supplementary info.
        model:    Resolved model identifier (for logging/metrics).
        version:  Resolved model version (for logging/metrics).

    Returns:
        A DetectionResult matching the frontend contract.

    Raises:
        Exception on inference failure; app/main.py maps it to a 500 response.

    TODO(detect): implement the real inference; see this file's docstring for
        the contract and mock.py::detect_image for a reference implementation.
    """
    pass