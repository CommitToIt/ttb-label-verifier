from app.comparison import REQUIRED_GOVERNMENT_WARNING, compare_label_fields
from app.models import ApplicationData, LabelFields


def application(**overrides: str | bool) -> ApplicationData:
    values = {
        "brand_name": "Example Gin",
        "class_type": "Gin",
        "alcohol_content": "45% Alc./Vol.",
        "net_contents": "750 mL",
        "bottler_name_address": "Example Bottler, Austin, TX",
        "is_import": True,
        "country_of_origin": "India",
    }
    values.update(overrides)
    return ApplicationData(**values)


def extracted(**overrides: str | bool | float) -> LabelFields:
    values: dict[str, str | bool | float] = {
        "brand_name": "Example Gin",
        "class_type": "Gin",
        "alcohol_content": "45%",
        "net_contents": "750 mL",
        "bottler_name_address": "Example Bottler, Austin, TX",
        "country_of_origin": "India",
        "government_warning_text": REQUIRED_GOVERNMENT_WARNING,
        "government_warning_is_bold_and_caps": True,
        "extraction_confidence": 0.95,
    }
    values.update(overrides)
    return LabelFields(**values)


def test_brand_name_identical_values_pass() -> None:
    assert compare_label_fields(extracted(), application())["brand_name"].status == "pass"


def test_brand_name_case_difference_passes() -> None:
    assert compare_label_fields(extracted(brand_name=" EXAMPLE  GIN "), application())["brand_name"].status == "pass"


def test_brand_name_near_miss_returns_needs_review() -> None:
    result = compare_label_fields(
        extracted(brand_name="Old Tom Distillery"),
        application(brand_name="Old Tom Distiller"),
    )
    assert result["brand_name"].status == "needs-review"


def test_genuinely_different_brand_name_fails() -> None:
    assert compare_label_fields(extracted(brand_name="Different Vodka"), application())["brand_name"].status == "fail"


def test_class_type_identical_values_pass() -> None:
    assert compare_label_fields(extracted(), application())["class_type"].status == "pass"


def test_class_type_case_difference_passes() -> None:
    assert compare_label_fields(extracted(class_type=" gIN "), application())["class_type"].status == "pass"


def test_genuinely_different_class_type_fails() -> None:
    assert compare_label_fields(extracted(class_type="Vodka"), application())["class_type"].status == "fail"


def test_alcohol_content_identical_values_pass() -> None:
    assert compare_label_fields(extracted(alcohol_content="45%"), application())["alcohol_content"].status == "pass"


def test_alcohol_content_formatting_difference_passes() -> None:
    assert compare_label_fields(extracted(alcohol_content="90 proof"), application())["alcohol_content"].status == "pass"


def test_alcohol_content_compound_percentage_and_proof_passes() -> None:
    result = compare_label_fields(
        extracted(alcohol_content="45% Alc./Vol. (90 Proof)"), application(alcohol_content="45%")
    )
    assert result["alcohol_content"].status == "pass"


def test_alcohol_content_compound_percentage_and_proof_mismatch_fails() -> None:
    result = compare_label_fields(
        extracted(alcohol_content="45% Alc./Vol. (90 Proof)"), application(alcohol_content="50%")
    )
    assert result["alcohol_content"].status == "fail"


def test_genuinely_different_alcohol_content_fails() -> None:
    assert compare_label_fields(extracted(alcohol_content="40%"), application())["alcohol_content"].status == "fail"


def test_net_contents_identical_values_pass() -> None:
    assert compare_label_fields(extracted(), application())["net_contents"].status == "pass"


def test_net_contents_case_difference_passes() -> None:
    assert compare_label_fields(extracted(net_contents=" 750 ML "), application())["net_contents"].status == "pass"


def test_genuinely_different_net_contents_fails() -> None:
    assert compare_label_fields(extracted(net_contents="1 L"), application())["net_contents"].status == "fail"


def test_net_contents_ml_suffix_no_space_passes() -> None:
    result = compare_label_fields(extracted(net_contents="750ML"), application(net_contents="750"))
    assert result["net_contents"].status == "pass"


def test_net_contents_liters_vs_milliliters_passes() -> None:
    result = compare_label_fields(extracted(net_contents="1.75 L"), application(net_contents="1750 mL"))
    assert result["net_contents"].status == "pass"


def test_net_contents_fluid_ounces_vs_bare_number_passes() -> None:
    result = compare_label_fields(extracted(net_contents="12 FL OZ"), application(net_contents="354.882"))
    assert result["net_contents"].status == "pass"


def test_net_contents_fl_oz_not_misdetected_as_liters() -> None:
    result = compare_label_fields(extracted(net_contents="12 FL OZ"), application(net_contents="354.882 mL"))
    assert result["net_contents"].status == "pass"


def test_net_contents_different_quantity_still_fails() -> None:
    result = compare_label_fields(extracted(net_contents="375 mL"), application(net_contents="750"))
    assert result["net_contents"].status == "fail"


def test_bottler_name_address_identical_values_pass() -> None:
    assert compare_label_fields(extracted(), application())["bottler_name_address"].status == "pass"


def test_bottler_name_address_case_difference_passes() -> None:
    result = compare_label_fields(
        extracted(bottler_name_address=" example bottler,  austin, tx "), application()
    )
    assert result["bottler_name_address"].status == "pass"


def test_genuinely_different_bottler_name_address_fails() -> None:
    result = compare_label_fields(
        extracted(bottler_name_address="Other Bottler, Denver, CO"), application()
    )
    assert result["bottler_name_address"].status == "fail"


def test_bottler_name_address_containment_passes() -> None:
    result = compare_label_fields(
        extracted(
            bottler_name_address="DISTILLED, AGED & BOTTLED BY BUFFALO TRACE DISTILLERY, FRANKFORT, KY"
        ),
        application(bottler_name_address="Buffalo Trace Distillery, Frankfort, KY"),
    )
    assert result["bottler_name_address"].status == "pass"


def test_bottler_name_address_containment_genuinely_different_fails() -> None:
    result = compare_label_fields(
        extracted(
            bottler_name_address="DISTILLED, AGED & BOTTLED BY BUFFALO TRACE DISTILLERY, FRANKFORT, KY"
        ),
        application(bottler_name_address="Heaven Hill Distillery, Bardstown, KY"),
    )
    assert result["bottler_name_address"].status == "fail"


def test_country_of_origin_identical_values_pass() -> None:
    assert compare_label_fields(extracted(), application())["country_of_origin"].status == "pass"


def test_country_of_origin_case_difference_passes() -> None:
    assert compare_label_fields(extracted(country_of_origin=" INDIA "), application())["country_of_origin"].status == "pass"


def test_country_of_origin_containment_passes() -> None:
    result = compare_label_fields(
        extracted(country_of_origin="Product of Scotland"),
        application(country_of_origin="Scotland"),
    )
    assert result["country_of_origin"].status == "pass"


def test_country_of_origin_containment_reverse_passes() -> None:
    result = compare_label_fields(
        extracted(country_of_origin="Scotland"),
        application(country_of_origin="Product of Scotland"),
    )
    assert result["country_of_origin"].status == "pass"


def test_genuinely_different_country_of_origin_fails() -> None:
    assert compare_label_fields(extracted(country_of_origin="Canada"), application())["country_of_origin"].status == "fail"


def test_country_of_origin_containment_mismatch_fails() -> None:
    result = compare_label_fields(
        extracted(country_of_origin="Product of Scotland"),
        application(country_of_origin="France"),
    )
    assert result["country_of_origin"].status == "fail"


def test_country_of_origin_empty_extracted_returns_needs_review() -> None:
    result = compare_label_fields(
        extracted(country_of_origin=""),
        application(country_of_origin="Scotland"),
    )
    assert result["country_of_origin"].status == "needs-review"
    assert result["country_of_origin"].reason == "Could not reliably extract country of origin from the label."


def test_country_of_origin_none_extracted_returns_needs_review() -> None:
    result = compare_label_fields(
        extracted(country_of_origin=None),
        application(country_of_origin="Scotland"),
    )
    assert result["country_of_origin"].status == "needs-review"
    assert result["country_of_origin"].reason == "Could not reliably extract country of origin from the label."


def test_country_of_origin_empty_submitted_returns_needs_review() -> None:
    result = compare_label_fields(
        extracted(country_of_origin="Scotland"),
        application(country_of_origin=""),
    )
    assert result["country_of_origin"].status == "needs-review"
    assert result["country_of_origin"].reason == "No country of origin was submitted to compare against the label."


def test_fuzzy_field_empty_extracted_returns_needs_review() -> None:
    result = compare_label_fields(
        extracted(brand_name=""),
        application(brand_name="Old Tom"),
    )
    assert result["brand_name"].status == "needs-review"
    assert result["brand_name"].reason == "Could not reliably extract brand name from the label."


def test_fuzzy_field_empty_submitted_returns_needs_review() -> None:
    result = compare_label_fields(
        extracted(brand_name="Old Tom"),
        application(brand_name=""),
    )
    assert result["brand_name"].status == "needs-review"
    assert result["brand_name"].reason == "No brand name was submitted to compare against the label."


def test_government_warning_identical_values_pass() -> None:
    assert compare_label_fields(extracted(), application())["government_warning_text"].status == "pass"


def test_government_warning_case_difference_fails() -> None:
    result = compare_label_fields(
        extracted(government_warning_text=REQUIRED_GOVERNMENT_WARNING.title()), application()
    )
    assert result["government_warning_text"].status == "fail"


def test_genuinely_different_government_warning_fails() -> None:
    result = compare_label_fields(extracted(government_warning_text="Different warning"), application())
    assert result["government_warning_text"].status == "fail"


def test_government_warning_formatting_flag_passes() -> None:
    assert compare_label_fields(extracted(), application())["government_warning_is_bold_and_caps"].status == "pass"


def test_government_warning_formatting_flag_fails_when_unconfirmed() -> None:
    result = compare_label_fields(extracted(government_warning_is_bold_and_caps=False), application())
    assert result["government_warning_is_bold_and_caps"].status == "fail"
