"""Unified background runner for detection tasks.

Each detection endpoint creates a task in ``queued`` state and registers this
runner as a BackgroundTask. The runner owns the task state machine past the
queued state:

    processing  ->  (run detector in a worker thread)  ->  completed / failed

Detectors are synchronous functions (both the mock and real models are CPU/GPU
bound). ``asyncio.to_thread`` executes them in the default thread pool so the
event loop stays responsive. Replace this with a process pool / GPU queue when
a real model needs it - the public signature is the only thing routers touch.

Progress is intentionally NOT fabricated: it stays unset during processing and
is set to 100 only on completion (matches the API contract).
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from app.detectors import model_info
from app.models import ErrorInfo, DetectionResult
from app.task_store import task_store

logger = logging.getLogger("detection-service")


async def run_detection(
    task_id: str,
    detect_fn: Callable[..., DetectionResult],
    args: tuple,
    model: str,
    version: str,
) -> None:
    task_store.update(task_id, status="processing")
    try:
        result = await asyncio.to_thread(detect_fn, *args)
    except Exception:
        logger.exception("Detector failed for task %s", task_id)
        task_store.update(
            task_id,
            status="failed",
            error=ErrorInfo(code="processing_error", message="The detection could not be completed."),
        )
        return

    task_store.update(
        task_id,
        status="completed",
        progress=100,
        result=result,
        model=model_info(model, version),
    )