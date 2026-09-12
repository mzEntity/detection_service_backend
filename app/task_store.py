from __future__ import annotations

import threading
import uuid as uuid_lib

from app.models import DetectionResponse


class TaskStore:
    def __init__(self) -> None:
        self._tasks: dict[str, DetectionResponse] = {}
        self._lock = threading.Lock()

    def new_id(self) -> str:
        return f"det_{uuid_lib.uuid4().hex[:12]}"

    def create(self, task: DetectionResponse) -> None:
        with self._lock:
            self._tasks[task.id] = task

    def get(self, task_id: str) -> DetectionResponse | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            return task.model_copy(deep=True)

    def update(self, task_id: str, **fields) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return
            for key, value in fields.items():
                setattr(task, key, value)


task_store = TaskStore()