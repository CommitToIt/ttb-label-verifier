import json
from typing import Any

from fastapi import UploadFile

from app.claude_client import extract_label_fields


async def verify_items(images: list[UploadFile], applications: str) -> dict[str, Any]:
    """Extract fields for each uploaded label and expose review-safe results."""
    try:
        submitted = json.loads(applications)
    except json.JSONDecodeError:
        submitted = []
    if not isinstance(submitted, list):
        submitted = [submitted]

    results = []
    for item_index, image in enumerate(images):
        extracted = await extract_label_fields(
            await image.read(), image.content_type or "application/octet-stream"
        )
        needs_review = extracted.extraction_confidence == 0
        results.append(
            {
                "item_index": item_index,
                "status": "needs-review" if needs_review else "pass",
                "submitted": submitted[item_index] if item_index < len(submitted) else None,
                "extracted": extracted.model_dump(exclude={"extraction_confidence"}),
                "extraction_confidence": extracted.extraction_confidence,
            }
        )

    return {
        "status": "needs-review" if any(item["status"] == "needs-review" for item in results) else "pass",
        "results": results,
        "image_count": len(images),
    }
