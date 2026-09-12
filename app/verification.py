import asyncio
import json
import logging
from typing import Any

from anthropic import AsyncAnthropic
from fastapi import HTTPException, UploadFile

from app.claude_client import extract_label_fields
from app.comparison import compare_label_fields
from app.config import settings
from app.models import ApplicationData
from app.validation import detect_image_media_type, validate_image_upload

logger = logging.getLogger(__name__)

LOW_EXTRACTION_CONFIDENCE_THRESHOLD = 0.3


async def verify_items(images: list[UploadFile], applications: str) -> dict[str, Any]:
    """Extract fields for each uploaded label and expose review-safe results concurrently."""
    try:
        submitted = json.loads(applications)
    except json.JSONDecodeError:
        submitted = []
    if not isinstance(submitted, list):
        submitted = [submitted]

    client = None
    if settings.anthropic_api_key:
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    semaphore = asyncio.Semaphore(settings.verification_concurrency)

    async def process_item(item_index: int, image: UploadFile) -> dict[str, Any]:
        submitted_item = submitted[item_index] if item_index < len(submitted) else {}
        async with semaphore:
            try:
                image_bytes = await validate_image_upload(image, settings.max_upload_size_bytes)
            except HTTPException as exc:
                reason = str(exc.detail)
                return {
                    "item_index": item_index,
                    "status": "fail",
                    "submitted": submitted_item,
                    "extracted": {},
                    "extraction_confidence": 0.0,
                    "fields": {
                        "image_upload": {
                            "status": "fail",
                            "reason": reason,
                        }
                    },
                    "reason": reason,
                }
            except Exception as exc:
                reason = f"Image validation failed: {exc}"
                return {
                    "item_index": item_index,
                    "status": "needs-review",
                    "submitted": submitted_item,
                    "extracted": {},
                    "extraction_confidence": 0.0,
                    "fields": {
                        "image_upload": {
                            "status": "needs-review",
                            "reason": reason,
                        }
                    },
                    "reason": reason,
                }

            media_type = detect_image_media_type(image_bytes)
            extracted = await extract_label_fields(
                image_bytes, media_type or "application/octet-stream", client=client
            )

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

            return {
                "item_index": item_index,
                "status": item_status,
                "submitted": submitted_item,
                "extracted": extracted.model_dump(exclude={"extraction_confidence"}),
                "extraction_confidence": extracted.extraction_confidence,
                "fields": {name: result.model_dump() for name, result in field_results.items()},
            }

    try:
        tasks = [process_item(index, image) for index, image in enumerate(images)]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        results = []
        for index, res in enumerate(raw_results):
            if isinstance(res, BaseException):
                logger.error("Unexpected error processing item %d: %s", index, res, exc_info=res)
                submitted_item = submitted[index] if index < len(submitted) else {}
                results.append(
                    {
                        "item_index": index,
                        "status": "needs-review",
                        "submitted": submitted_item,
                        "extracted": {},
                        "extraction_confidence": 0.0,
                        "fields": {
                            "processing_error": {
                                "status": "needs-review",
                                "reason": f"An unexpected error occurred during processing: {res}",
                            }
                        },
                        "reason": f"An unexpected error occurred during processing: {res}",
                    }
                )
            else:
                results.append(res)
    finally:
        if client is not None:
            try:
                await client.close()
            except Exception as exc:
                logger.warning("Shared Claude client cleanup failed: %s", type(exc).__name__)

    return {
        "status": (
            "fail"
            if any(item["status"] == "fail" for item in results)
            else "needs-review"
            if any(item["status"] == "needs-review" for item in results)
            else "pass"
        ),
        "results": list(results),
        "image_count": len(images),
    }
