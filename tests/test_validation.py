import asyncio
import io

import pytest
from fastapi import HTTPException, UploadFile

from app.validation import validate_image_upload


def upload(content: bytes) -> UploadFile:
    return UploadFile(filename="upload.bin", file=io.BytesIO(content))


def test_non_image_upload_is_rejected_cleanly() -> None:
    with pytest.raises(HTTPException) as error:
        asyncio.run(validate_image_upload(upload(b"plain text"), 10 * 1024 * 1024))

    assert error.value.status_code == 400
    assert error.value.detail == "Uploaded file is not a supported image."


def test_oversized_upload_is_rejected_cleanly() -> None:
    with pytest.raises(HTTPException) as error:
        asyncio.run(validate_image_upload(upload(b"\xff\xd8\xff" + b"x" * 10), 10))

    assert error.value.status_code == 413
    assert "maximum size" in error.value.detail
