"""Detection layer: model implementations live here.

Architecture (dependency direction):
    routers/  (HTTP)
        -> runner.py   (background task execution + task state machine)
        -> detectors/  (this package: model inference)
        -> models.py   (Pydantic contracts shared with the frontend)

Every detector function returns an ``app.models.DetectionResult`` and is
responsible ONLY for inference + a short human-readable ``reasoning`` string.
Progress reporting / async task state belong to ``app/runner.py``, not here.
Detectors run in a worker thread via ``asyncio.to_thread`` (see runner.py), so
keep them synchronous blocking functions - same for the mock and real models.

Latency: the mock sleeps (``time.sleep``) inside its own detect_* functions so
it behaves on the same timeline as a real model. Real models need no artificial
delay - their own compute time replaces it.

Current layout
--------------
+---------------  module  +  status  +  what to do
+----------------  mock.py  | default  | Deterministic mock so the API works without a model.
+----------------  text.py  | stub     | Implement `detect_text` with a real AI-text detector.
+----------------  image.py | stub     | Implement `detect_image` with a real image detector.
+----------------  video.py | stub     | Implement `detect_video` with a real video detector.

Switching from mock to a real model (3 steps)
---------------------------------------------
1. Fill in the stub in the module that matches your modality, e.g.
   ``app/detectors/text.py``. Keep the function names and signatures intact.
2. Flip the imports at the bottom of this file from ``mock`` to your module,
   e.g. ``from app.detectors.text import detect_text``.
3. Nothing in ``routers/`` needs to change - they import from this package.

Contract for each ``detect_*`` function
----------------------------------------
- Inputs carry the raw user data plus the resolved model identifier/version so
  the real model can log which model produced each result.
- Return an ``app.models.DetectionResult``; keep probabilities in [0, 1] and
  always provide a non-empty, honest ``reasoning`` (the frontend shows it).
- Do not raise HTTP errors here - validation lives in ``routers/`` and
  ``app/files.py``. Raise a plain Exception on inference failure; the global
  handler in ``app/main.py`` converts it to a 500 ``internal_error`` body.

Note on ``detect_video`` and ``seed``
-------------------------------------
``detect_video_seed`` hashes the raw bytes to keep the mock deterministic
(identical input -> identical result). A real model does not need this; you
may change the signature in ``video.py`` and the matching call sites in
``app/routers/video.py``. The docstring in ``video.py`` explains the options.
"""
from __future__ import annotations

from app.detectors.mock import (
    detect_image,
    detect_text,
    detect_video,
    detect_video_seed,
    model_info,
)

__all__ = [
    "detect_text",
    "detect_image",
    "detect_video",
    "detect_video_seed",
    "model_info",
]