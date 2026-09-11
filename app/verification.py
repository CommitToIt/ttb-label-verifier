import json
from typing import Any

from fastapi import UploadFile

from app.claude_client import extract_label_fields
from app.comparison import compare_label_fields
from app.config import settings
from app.models import ApplicationData
from app.validation import detect_image_media_type, validate_image_upload

LOW_EXTRACTION_CONFIDENCE_THRESHOLD = 0.3


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
        image_bytes = await validate_image_upload(image, settings.max_upload_size_bytes)
        media_type = detect_image_media_type(image_bytes)
        extracted = await extract_label_fields(image_bytes, media_type or "application/octet-stream")
        submitted_item = submitted[item_index] if item_index < len(submitted) else {}
        try:
            submitted_data = ApplicationData.model_validate(submitted_item)
            field_results = compare_label_fields(extracted, submitted_data)
            statuses = {result.status for result in field_results.values()}
            item_status = (
                "fail" if "fail" in statuses else "needs-review" if "needs-review" in statuses else "pass"
            )
            if (
                extracted.extraction_confidence is not None
                and extracted.extraction_confidence < LOW_EXTRACTION_CONFIDENCE_THRESHOLD
            ):
                item_status = "needs-review"
        except Exception:
            field_results = {}
            item_status = "needs-review"
        results.append(
            {
                "item_index": item_index,
                "status": item_status,
                "submitted": submitted_item,
                "extracted": extracted.model_dump(exclude={"extraction_confidence"}),
                "extraction_confidence": extracted.extraction_confidence,
                "fields": {name: result.model_dump() for name, result in field_results.items()},
            }
        )

    return {
        "status": (
            "fail"
            if any(item["status"] == "fail" for item in results)
            else "needs-review"
            if any(item["status"] == "needs-review" for item in results)
            else "pass"
        ),
        "results": results,
        "image_count": len(images),
    }
