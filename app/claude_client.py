from app.models import LabelFields


async def extract_label_fields(image_bytes: bytes, media_type: str) -> LabelFields:
    """Extract structured fields with Claude tool use in the implementation phase."""
    raise NotImplementedError
