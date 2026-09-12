"""Real video detector: implement `detect_video` here.

Where this fits
---------------
- ``detect_video`` is scheduled through ``app/runner.py::run_detection``
  (registered by ``app/routers/video.py`` as a background task). The runner
  owns the task state machine (queued -> processing -> completed / failed)
  and executes detectors in a worker thread; this module ONLY computes the
  final result.
- Reference implementation (do not edit): ``mock.py``.

How latency is simulated vs. real inference
--------------------------------------------
The mock sleeps inside its own ``detect_video`` (``time.sleep``) so it behaves
on the same timeline as a real model. With a real detector you do NOT add any
artificial sleep - the model's own compute time provides the latency. If a
long video has natural phases (demux -> sample frames -> per-frame detection
-> aggregate), report progress from the runner between phases by updating
``task_store``; do not fake progress percentages here.

Expected behavior
-----------------
Return a ``DetectionResult`` exactly like the other detectors:
    label / ai_probability / human_probability / confidence / reasoning
Probabilities sum to 1.0; ``reasoning`` is required, brief, and honest.

About the `seed` parameter (important)
-------------------------------------
``routers/video.py` currently computes:
      1. detect_video_seed(data, context)  -> hashes raw bytes (mock artifact,
         keeps mock output deterministic), then
      2. passes the seed on to run_detection -> detect_video(seed, model, version).
A real model does not need a hash-based seed. Two options:
  (a) Keep the current signature: decode the video inside ``detect_video``
      from the seed by hashing the data again - wasteful but simple.
  (b) Preferred: change the signature to receive the raw bytes, e.g.
      ``def detect_video(data: bytes, context: str | None, model: str, version: str)``
      and update the call site in ``app/routers/video.py`` accordingly.
In both cases keep ``detect_video`` pure inference; leave task state in
``app/runner.py``.

Steps to wire up
----------------
1. Implement the body below (and, if using option (b), update video.py router).
2. In ``app/detectors/__init__.py``, import this function instead of
   ``app.detectors.mock.detect_video``.
"""
from __future__ import annotations

from app.models import DetectionResult


def detect_video(seed: int, model: str, version: str) -> DetectionResult:
    """Detect whether the video was AI-generated or not.

    Args:
        seed:    Deterministic key derived from the raw bytes by
                 ``detect_video_seed`` (mock artifact - see module docstring).
        model:   Resolved model identifier (for logging/metrics).
        version: Resolved model version (for logging/metrics).

    Returns:
        A DetectionResult matching the frontend contract.

    Raises:
        Exception on inference failure; app/main.py maps it to a 500 response.

    TODO(detect): implement the real inference; see this file's docstring for
        the contract and mock.py::detect_video for a reference implementation.
        You may change the signature (see module docstring about `seed`).
    """
    pass