import asyncio
import base64
import logging

from anthropic import AsyncAnthropic

from app.config import settings
from app.models import LabelFields

logger = logging.getLogger(__name__)

TOOL_NAME = "extract_label_fields"
EXTRACTION_TIMEOUT_SECONDS = 45


def _needs_review_fields() -> LabelFields:
    return LabelFields(extraction_confidence=0)


def _tool_input(response: object) -> object:
    for block in getattr(response, "content", []):
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == TOOL_NAME:
            return getattr(block, "input", None)
    raise ValueError("Claude response did not contain the extraction tool result")


async def extract_label_fields(image_bytes: bytes, media_type: str) -> LabelFields:
    """Extract label fields through a forced, schema-backed Claude tool call."""
    if not settings.anthropic_api_key:
        logger.warning("Claude extraction skipped because ANTHROPIC_API_KEY is not configured")
        return _needs_review_fields()

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    tool = {
        "name": TOOL_NAME,
        "description": "Extract the requested regulatory fields visible on an alcohol label.",
        "input_schema": LabelFields.model_json_schema(),
    }

    try:
        response = await asyncio.wait_for(
            client.messages.create(
                model=settings.claude_model,
                max_tokens=1200,
                tools=[tool],
                tool_choice={"type": "tool", "name": TOOL_NAME},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64.b64encode(image_bytes).decode("ascii"),
                                },
                            },
                            {
                                "type": "text",
                                "text": "Extract the label fields using the required tool. Do not infer text that is not visible.",
                            },
                        ],
                    }
                ],
            ),
            timeout=EXTRACTION_TIMEOUT_SECONDS,
        )
        return LabelFields.model_validate(_tool_input(response))
    except Exception as exc:
        logger.warning("Claude label extraction failed: %s", type(exc).__name__)
        return _needs_review_fields()
    finally:
        try:
            await client.close()
        except Exception as exc:
            logger.warning("Claude client cleanup failed: %s", type(exc).__name__)
