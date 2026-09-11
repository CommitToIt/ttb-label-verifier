import asyncio
import io
import json

from fastapi import UploadFile

from app.comparison import REQUIRED_GOVERNMENT_WARNING
from app.models import LabelFields
from app.verification import verify_items


def upload() -> UploadFile:
    return UploadFile(
        filename="label.jpg",
        file=io.BytesIO(b"\xff\xd8\xffimage-bytes"),
        headers={"content-type": "image/jpeg"},
    )


def submission() -> dict[str, str | bool]:
    return {
        "brand_name": "Example Gin",
        "class_type": "Gin",
        "alcohol_content": "45% Alc./Vol.",
        "net_contents": "750 mL",
        "bottler_name_address": "Example Bottler, Austin, TX",
        "is_import": False,
    }


def extracted(**overrides: str | bool | float) -> LabelFields:
    values: dict[str, str | bool | float] = {
        "brand_name": "EXAMPLE GIN",
        "class_type": "Gin",
        "alcohol_content": "90 proof",
        "net_contents": "750 mL",
        "bottler_name_address": "Example Bottler, Austin, TX",
        "government_warning_text": REQUIRED_GOVERNMENT_WARNING.title(),
        "government_warning_is_bold_and_caps": True,
        "extraction_confidence": 0.95,
    }
    values.update(overrides)
    return LabelFields(**values)


def test_verify_items_returns_field_statuses_and_reasons(monkeypatch) -> None:
    async def fake_extract(image_bytes: bytes, media_type: str) -> LabelFields:
        assert image_bytes == b"\xff\xd8\xffimage-bytes"
        assert media_type == "image/jpeg"
        return extracted()

    monkeypatch.setattr("app.verification.extract_label_fields", fake_extract)

    response = asyncio.run(verify_items([upload()], json.dumps([submission()])))
    fields = response["results"][0]["fields"]

    assert response["status"] == "fail"
    assert response["results"][0]["status"] == "fail"
    assert fields["brand_name"]["status"] == "pass"
    assert fields["alcohol_content"]["status"] == "pass"
    assert fields["government_warning_text"]["status"] == "fail"
    assert "exactly match" in fields["government_warning_text"]["reason"]


def test_moderate_confidence_preserves_field_verdicts(monkeypatch) -> None:
    async def fake_extract(image_bytes: bytes, media_type: str) -> LabelFields:
        return extracted(
            government_warning_text=REQUIRED_GOVERNMENT_WARNING,
            extraction_confidence=0.55,
        )

    monkeypatch.setattr("app.verification.extract_label_fields", fake_extract)

    response = asyncio.run(verify_items([upload()], json.dumps([submission()])))
    fields = response["results"][0]["fields"]

    assert response["status"] == "pass"
    assert response["results"][0]["status"] == "pass"
    assert fields["brand_name"]["status"] == "pass"
    assert fields["alcohol_content"]["status"] == "pass"
    assert fields["government_warning_text"]["status"] == "pass"


def test_very_low_confidence_marks_only_item_for_review(monkeypatch) -> None:
    async def fake_extract(image_bytes: bytes, media_type: str) -> LabelFields:
        return extracted(
            government_warning_text=REQUIRED_GOVERNMENT_WARNING,
            extraction_confidence=0.2,
        )

    monkeypatch.setattr("app.verification.extract_label_fields", fake_extract)

    response = asyncio.run(verify_items([upload()], json.dumps([submission()])))
    fields = response["results"][0]["fields"]

    assert response["status"] == "needs-review"
    assert response["results"][0]["status"] == "needs-review"
    assert fields["brand_name"]["status"] == "pass"
    assert fields["alcohol_content"]["status"] == "pass"
