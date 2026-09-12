"""Real AI-text detector: implement `detect_text` here.

Where this fits
---------------
- Scheduled through ``app/runner.py::run_detection`` (registered by
  ``POST /api/v1/detections/text`` in app/routers/text.py). The router handles
  validation and creates the queued task; the runner executes this detector in
  a worker thread and reports processing -> completed / failed.
- Reference implementation (do not edit): ``mock.py::detect_text``.

Expected behavior
-----------------
Analyze ``text`` (optionally taking ``context`` into account) and return a
``DetectionResult``:
    label:        one of "ai_generated" | "human_generated" | "uncertain"
    probabilities: your model score; ai_probability + human_probability == 1.0
    confidence:   "low" | "medium" | "high" (model's self-assessed certainty)
    reasoning:    short, honest, human-readable explanation of the decision

``reasoning`` is REQUIRED - the frontend renders it for interpretability.
Do not use "100% AI"-style absolutist wording.

Note
----
Keep this a synchronous blocking function: ``app/runner.py`` already executes
it in a worker thread via ``asyncio.to_thread``, so blocking is expected and
does not stall the event loop. Do not make network requests that block for
very long inside the request path.

Steps to wire up
----------------
1. Implement the body below.
2. In ``app/detectors/__init__.py``, import this function instead of
   ``app.detectors.mock.detect_text``.
"""
from __future__ import annotations

from app.models import DetectionResult


def detect_text(text: str, context: str | None, model: str, version: str) -> DetectionResult:
    """Detect whether ``text`` was AI- or human-generated.

    Args:
        text:    The raw user input to analyze.
        context: Optional user-supplied supplementary info (source, background).
        model:   Resolved model identifier from the request (for logging/metrics).
        version: Resolved model version (for logging/metrics).

    Returns:
        A DetectionResult matching the frontend contract.

    Raises:
        Exception on inference failure; app/main.py maps it to a 500 response.

    TODO(detect): implement the real inference; see this file's docstring for
        the contract and mock.py::detect_text for a reference implementation.
    """
    pass