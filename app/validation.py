from fastapi import UploadFile


async def validate_image_upload(upload: UploadFile, max_size_bytes: int) -> bytes:
    """Validate image type and size before sending data to an external API."""
    raise NotImplementedError
