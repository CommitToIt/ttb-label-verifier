from fastapi import APIRouter, File, Form, UploadFile

from app.config import settings
from app.verification import verify_items

router = APIRouter()


@router.get("/config")
async def get_config() -> dict[str, int]:
    """Expose non-sensitive client configuration parameters."""
    return {
        "max_batch_size": settings.max_batch_size,
        "max_upload_size_bytes": settings.max_upload_size_bytes,
    }


@router.post("/verify")
async def verify(
    images: list[UploadFile] = File(...),
    applications: str = Form(...),
):
    """Extract structured fields for each uploaded image."""
    return await verify_items(images, applications)
