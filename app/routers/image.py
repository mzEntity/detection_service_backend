from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile

from app.detectors import detect_image, model_info
from app.errors import model_version
from app.files import read_upload
from app.models import DetectionResponse
from app.runner import run_detection
from app.task_store import task_store

router = APIRouter()


@router.post("/detections/image", response_model=DetectionResponse)
async def create_image_detection(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model: str = Form(...),
    context: str | None = Form(default=None),
) -> DetectionResponse:
    version = model_version(model, "image")
    data = await read_upload(file, "image")

    task_id = task_store.new_id()
    task = DetectionResponse(
        id=task_id,
        modality="image",
        status="queued",
        model=model_info(model, version),
    )
    task_store.create(task)
    background_tasks.add_task(
        run_detection, task_id, detect_image, (data, file.filename, context, model, version), model, version
    )
    return task