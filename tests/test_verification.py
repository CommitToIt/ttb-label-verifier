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
    async def fake_extract(image_bytes: bytes, media_type: str, **kwargs) -> LabelFields:
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
    async def fake_extract(image_bytes: bytes, media_type: str, **kwargs) -> LabelFields:
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
    async def fake_extract(image_bytes: bytes, media_type: str, **kwargs) -> LabelFields:
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


def test_batch_with_invalid_file_preserves_valid_item_results(monkeypatch) -> None:
    async def fake_extract(image_bytes: bytes, media_type: str, **kwargs) -> LabelFields:
        return extracted(government_warning_text=REQUIRED_GOVERNMENT_WARNING)

    monkeypatch.setattr("app.verification.extract_label_fields", fake_extract)

    valid_1 = upload()
    invalid_file = UploadFile(
        filename="bad.txt",
        file=io.BytesIO(b"not an image"),
        headers={"content-type": "text/plain"},
    )
    valid_2 = upload()

    submissions = [submission(), submission(), submission()]

    response = asyncio.run(
        verify_items([valid_1, invalid_file, valid_2], json.dumps(submissions))
    )

    assert response["image_count"] == 3
    assert response["status"] == "fail"
    results = response["results"]
    assert results[0]["status"] == "pass"
    assert results[0]["fields"]["brand_name"]["status"] == "pass"
    assert results[1]["status"] == "fail"
    assert "image_upload" in results[1]["fields"]
    assert "not a supported image" in results[1]["fields"]["image_upload"]["reason"]
    assert results[2]["status"] == "pass"
    assert results[2]["fields"]["brand_name"]["status"] == "pass"


def test_batch_processed_concurrently(monkeypatch) -> None:
    active_calls = 0
    max_concurrent_calls = 0

    async def fake_extract(image_bytes: bytes, media_type: str, **kwargs) -> LabelFields:
        nonlocal active_calls, max_concurrent_calls
        active_calls += 1
        max_concurrent_calls = max(max_concurrent_calls, active_calls)
        await asyncio.sleep(0.05)
        active_calls -= 1
        return extracted(government_warning_text=REQUIRED_GOVERNMENT_WARNING)

    monkeypatch.setattr("app.verification.extract_label_fields", fake_extract)

    uploads = [upload() for _ in range(3)]
    submissions = [submission() for _ in range(3)]

    response = asyncio.run(verify_items(uploads, json.dumps(submissions)))

    assert len(response["results"]) == 3
    assert max_concurrent_calls > 1
    assert response["status"] == "pass"


def test_batch_unexpected_exception_in_one_item_preserves_others(monkeypatch) -> None:
    async def fake_extract(image_bytes: bytes, media_type: str, **kwargs) -> LabelFields:
        if image_bytes == b"\xff\xd8\xffimage-bytes-fail":
            raise RuntimeError("Unexpected boom in worker")
        return extracted(government_warning_text=REQUIRED_GOVERNMENT_WARNING)

    monkeypatch.setattr("app.verification.extract_label_fields", fake_extract)

    valid_1 = upload()
    failing_item = UploadFile(
        filename="failing.jpg",
        file=io.BytesIO(b"\xff\xd8\xffimage-bytes-fail"),
        headers={"content-type": "image/jpeg"},
    )
    valid_2 = upload()

    submissions = [submission(), submission(), submission()]

    response = asyncio.run(
        verify_items([valid_1, failing_item, valid_2], json.dumps(submissions))
    )

    assert len(response["results"]) == 3
    assert response["image_count"] == 3
    assert response["status"] == "needs-review"

    results = response["results"]
    assert results[0]["status"] == "pass"
    assert results[0]["fields"]["brand_name"]["status"] == "pass"

    assert results[1]["status"] == "needs-review"
    assert "processing_error" in results[1]["fields"]
    assert (
        results[1]["fields"]["processing_error"]["reason"]
        == "An unexpected error occurred while processing this item."
    )
    assert (
        results[1]["reason"]
        == "An unexpected error occurred while processing this item."
    )

    assert results[2]["status"] == "pass"
    assert results[2]["fields"]["brand_name"]["status"] == "pass"


def test_verify_items_logging_emits_timing_outcomes_and_no_sensitive_values(
    monkeypatch, caplog
) -> None:
    import logging

    async def fake_extract(image_bytes: bytes, media_type: str, **kwargs) -> LabelFields:
        return extracted(
            brand_name="Extracted Secret Brand",
            government_warning_text=REQUIRED_GOVERNMENT_WARNING,
            extraction_confidence=0.92,
        )

    monkeypatch.setattr("app.verification.extract_label_fields", fake_extract)

    secret_submitted_brand = "Secret Submitted Brand"
    sub = submission()
    sub["brand_name"] = secret_submitted_brand

    with caplog.at_level(logging.INFO):
        response = asyncio.run(verify_items([upload()], json.dumps([sub])))

    assert response["status"] in ("pass", "fail", "needs-review")

    log_text = caplog.text
    # 1. Start and finish logs with image count and seconds
    assert "Starting verification batch for 1 image(s)" in log_text
    assert "Finished verification batch for 1 image(s) in" in log_text
    assert "seconds" in log_text

    # 2. Outcome summary
    assert "Batch outcome summary:" in log_text
    assert "pass=" in log_text

    # 3. Field names, status, and numeric scores
    assert "brand_name:" in log_text
    assert "score=" in log_text
    assert "extraction_confidence=0.92" in log_text

    # 4. Never log the extracted or submitted text values or raw image bytes
    assert secret_submitted_brand not in log_text
    assert "Extracted Secret Brand" not in log_text
    assert "image-bytes" not in log_text


def test_batch_exceeding_max_batch_size_rejected_cleanly(monkeypatch) -> None:
    from fastapi import HTTPException
    import pytest

    monkeypatch.setattr("app.verification.settings.max_batch_size", 3)

    uploads = [upload() for _ in range(4)]
    submissions = [submission() for _ in range(4)]

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(verify_items(uploads, json.dumps(submissions)))

    assert exc_info.value.status_code == 400
    assert "exceeds maximum allowed limit" in exc_info.value.detail


def test_batch_at_max_batch_size_processed_normally(monkeypatch) -> None:
    async def fake_extract(image_bytes: bytes, media_type: str, **kwargs) -> LabelFields:
        return extracted(government_warning_text=REQUIRED_GOVERNMENT_WARNING)

    monkeypatch.setattr("app.verification.extract_label_fields", fake_extract)
    monkeypatch.setattr("app.verification.settings.max_batch_size", 3)

    uploads = [upload() for _ in range(3)]
    submissions = [submission() for _ in range(3)]

    response = asyncio.run(verify_items(uploads, json.dumps(submissions)))
    assert response["image_count"] == 3
    assert len(response["results"]) == 3
    assert response["status"] == "pass"
