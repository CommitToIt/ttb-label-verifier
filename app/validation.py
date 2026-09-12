from fastapi import HTTPException, UploadFile

IMAGE_SIGNATURES = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"BM", "image/bmp"),
)


def detect_image_media_type(image_bytes: bytes) -> str | None:
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    if image_bytes.startswith((b"II*\x00", b"MM\x00*")):
        return "image/tiff"
    for signature, media_type in IMAGE_SIGNATURES:
        if image_bytes.startswith(signature):
            return media_type
    return None


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        mb = size_bytes / (1024 * 1024)
        return f"{int(mb)}MB" if mb.is_integer() else f"{mb:.1f}MB"
    if size_bytes >= 1024:
        kb = size_bytes / 1024
        return f"{int(kb)}KB" if kb.is_integer() else f"{kb:.1f}KB"
    return f"{size_bytes}B"


async def validate_image_upload(upload: UploadFile, max_size_bytes: int) -> bytes:
    """Validate image type and size before sending data to an external API."""
    image_bytes = await upload.read(max_size_bytes + 1)
    if len(image_bytes) > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Image exceeds the maximum size of {_format_size(max_size_bytes)}.",
        )
    if detect_image_media_type(image_bytes) is None:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a supported image.",
        )
    return image_bytes
