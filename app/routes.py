from fastapi import APIRouter, File, Form, UploadFile

from app.verification import verify_items

router = APIRouter()


@router.post("/verify")
async def verify(
    images: list[UploadFile] = File(...),
    applications: str = Form(...),
):
    """Extract structured fields for each uploaded image."""
    return await verify_items(images, applications)
