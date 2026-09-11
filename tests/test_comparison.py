from app.comparison import REQUIRED_GOVERNMENT_WARNING, compare_label_fields
from app.models import ApplicationData, LabelFields


def application(**overrides: str | bool) -> ApplicationData:
    values = {
        "brand_name": "Example Gin",
        "class_type": "Gin",
        "alcohol_content": "45% Alc./Vol.",
        "net_contents": "750 mL",
        "bottler_name_address": "Example Bottler, Austin, TX",
    }
    values.update(overrides)
    return ApplicationData(**values)


def extracted(**overrides: str | bool) -> LabelFields:
    values = {
        "brand_name": "Example Gin",
        "class_type": "Gin",
        "alcohol_content": "45%",
        "net_contents": "750 mL",
        "bottler_name_address": "Example Bottler, Austin, TX",
        "government_warning_text": REQUIRED_GOVERNMENT_WARNING,
        "government_warning_is_bold_and_caps": True,
        "extraction_confidence": 0.95,
    }
    values.update(overrides)
    return LabelFields(**values)


def test_case_only_brand_name_difference_passes() -> None:
    result = compare_label_fields(extracted(brand_name="EXAMPLE GIN"), application())
    assert result["brand_name"].status == "pass"


def test_genuinely_different_brand_name_fails() -> None:
    result = compare_label_fields(extracted(brand_name="Different Vodka"), application())
    assert result["brand_name"].status == "fail"


def test_title_case_warning_statement_fails() -> None:
    result = compare_label_fields(
        extracted(government_warning_text=REQUIRED_GOVERNMENT_WARNING.title()), application()
    )
    assert result["government_warning_text"].status == "fail"


def test_abv_matches_after_formatting_normalization() -> None:
    result = compare_label_fields(extracted(alcohol_content="90 proof"), application())
    assert result["alcohol_content"].status == "pass"
