from fastapi import APIRouter, File, Form, UploadFile

from app.verification import verify_items

router = APIRouter()


@router.post("/verify")
async def verify(
    images: list[UploadFile] = File(...),
    applications: str = Form(...),
):
    """Accept paired images and application data; implementation follows."""
    return await verify_items(images, applications)
