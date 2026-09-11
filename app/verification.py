from typing import Any

from fastapi import UploadFile


async def verify_items(images: list[UploadFile], applications: str) -> dict[str, Any]:
    """Coordinate bounded concurrent verification once the pipeline is implemented."""
    return {
        "status": "needs-review",
        "results": [],
        "message": "Verification pipeline is not implemented yet.",
        "image_count": len(images),
        "applications_received": bool(applications),
    }
