from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile

from app.detectors import detect_video, detect_video_seed, model_info
from app.errors import model_version
from app.files import read_upload
from app.models import DetectionResponse
from app.runner import run_detection
from app.task_store import task_store

router = APIRouter()


@router.post("/detections/video", response_model=DetectionResponse, status_code=200)
async def create_video_detection(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model: str = Form(...),
    context: str | None = Form(default=None),
) -> DetectionResponse:
    version = model_version(model, "video")
    data = await read_upload(file, "video")

    task_id = task_store.new_id()
    seed = detect_video_seed(data, context)
    task = DetectionResponse(
        id=task_id,
        modality="video",
        status="queued",
        model=model_info(model, version),
    )
    task_store.create(task)
    background_tasks.add_task(run_detection, task_id, detect_video, (seed, model, version), model, version)
    return task