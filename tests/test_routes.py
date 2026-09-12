import json

from fastapi.testclient import TestClient

from app.comparison import REQUIRED_GOVERNMENT_WARNING
from app.models import LabelFields
from main import app


client = TestClient(app)


def submission(brand_name: str = "Example Gin") -> dict[str, str | bool]:
    return {
        "brand_name": brand_name,
        "class_type": "Gin",
        "alcohol_content": "45%",
        "net_contents": "750 mL",
        "bottler_name_address": "Example Bottler, Austin, TX",
        "is_import": False,
    }


def extracted() -> LabelFields:
    return LabelFields(
        brand_name="Example Gin",
        class_type="Gin",
        alcohol_content="45% Alc./Vol.",
        net_contents="750 mL",
        bottler_name_address="Example Bottler, Austin, TX",
        government_warning_text=REQUIRED_GOVERNMENT_WARNING,
        government_warning_is_bold_and_caps=True,
        extraction_confidence=0.95,
    )


def post_verification(monkeypatch, application: dict[str, str | bool]):
    async def fake_extract(image_bytes: bytes, media_type: str, **kwargs) -> LabelFields:
        return extracted()

    monkeypatch.setattr("app.verification.extract_label_fields", fake_extract)
    return client.post(
        "/api/verify",
        files=[("images", ("label.jpg", b"\xff\xd8\xffimage-bytes", "image/jpeg"))],
        data={"applications": json.dumps([application])},
    )


def test_verify_route_returns_pass_response_shape(monkeypatch) -> None:
    response = post_verification(monkeypatch, submission())
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "pass"
    assert body["image_count"] == 1
    assert body["results"][0]["status"] == "pass"
    assert body["results"][0]["fields"]["brand_name"]["status"] == "pass"
    assert body["results"][0]["fields"]["alcohol_content"]["status"] == "pass"


def test_verify_route_reports_specific_mismatched_field(monkeypatch) -> None:
    response = post_verification(monkeypatch, submission(brand_name="Different Vodka"))
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "fail"
    assert body["results"][0]["status"] == "fail"
    assert body["results"][0]["fields"]["brand_name"]["status"] == "fail"
    assert "does not match" in body["results"][0]["fields"]["brand_name"]["reason"]
    assert body["results"][0]["fields"]["class_type"]["status"] == "pass"
