from __future__ import annotations

import pathlib

from fastapi import HTTPException, UploadFile

from app.config import (
    IMAGE_CONTENT_TYPES,
    IMAGE_EXTENSIONS,
    VIDEO_CONTENT_TYPES,
    VIDEO_EXTENSIONS,
)


def _bad(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"error": {"code": code, "message": message}})


def validate_file_type(ext: str, content_type: str, allowed_exts: set[str], allowed_types: set[str], modality: str) -> None:
    if ext.lower() not in allowed_exts:
        raise _bad(
            422,
            "unsupported_file_type",
            f"Unsupported {modality} file type. Allowed: {', '.join(sorted(allowed_exts))}.",
        )
    if content_type and content_type.lower() not in allowed_types:
        raise _bad(
            422,
            "unsupported_file_type",
            f"Unsupported {modality} content type. Allowed: {', '.join(sorted(allowed_types))}.",
        )


async def read_upload(file: UploadFile | None, modality: str) -> bytes:
    if file is None or file.filename is None or not file.filename:
        raise _bad(400, "missing_file", f"An upload of type '{modality}' is required.")

    filename = file.filename or ""
    ext = pathlib.Path(filename).suffix
    content_type = file.content_type or ""

    if modality == "image":
        allowed_exts, allowed_types = IMAGE_EXTENSIONS, IMAGE_CONTENT_TYPES
    else:
        allowed_exts, allowed_types = VIDEO_EXTENSIONS, VIDEO_CONTENT_TYPES

    validate_file_type(ext, content_type, allowed_exts, allowed_types, modality)

    data = await file.read()
    if len(data) == 0:
        raise _bad(400, "missing_file", f"The uploaded {modality} file is empty.")

    return data