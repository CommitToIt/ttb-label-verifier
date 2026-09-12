import re

from rapidfuzz.fuzz import ratio

from app.models import ApplicationData, FieldResult, LabelFields

REQUIRED_GOVERNMENT_WARNING = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should "
    "not drink alcoholic beverages during pregnancy because of the risk of "
    "birth defects. (2) Consumption of alcoholic beverages impairs your "
    "ability to drive a car or operate machinery, and may cause health "
    "problems."
)
FUZZY_PASS_THRESHOLD = 90
FUZZY_REVIEW_THRESHOLD = 75
ALCOHOL_TOLERANCE = 0.1


def _result(status: str, reason: str | None = None) -> FieldResult:
    return FieldResult(status=status, reason=reason)


def _normalize(value: str | None) -> str:
    return " ".join((value or "").strip().casefold().split())


def _fuzzy_result(field_name: str, extracted: str | None, submitted: str) -> FieldResult:
    if not extracted:
        return _result("needs-review", f"Could not reliably extract {field_name} from the label.")
    score = ratio(_normalize(extracted), _normalize(submitted))
    if score >= FUZZY_PASS_THRESHOLD:
        return _result("pass")
    if score >= FUZZY_REVIEW_THRESHOLD:
        return _result("needs-review", f"{field_name.title()} similarity is borderline ({score:.0f}%).")
    return _result("fail", f"Label {field_name} does not match the submitted value.")


def _alcohol_value(value: str | None) -> float | None:
    if not value:
        return None
    clean_value = value.replace(",", "")
    percent_match = re.search(r"(\d+(?:\.\d+)?)\s*%", clean_value)
    if percent_match:
        return float(percent_match.group(1))
    proof_match = re.search(r"(\d+(?:\.\d+)?)\s*proof", clean_value, re.IGNORECASE)
    if proof_match:
        return float(proof_match.group(1)) / 2
    match = re.search(r"(\d+(?:\.\d+)?)", clean_value)
    if not match:
        return None
    return float(match.group(1))


def _alcohol_result(extracted: str | None, submitted: str) -> FieldResult:
    extracted_value = _alcohol_value(extracted)
    submitted_value = _alcohol_value(submitted)
    if extracted_value is None or submitted_value is None:
        return _result("needs-review", "Could not reliably parse alcohol content.")
    if abs(extracted_value - submitted_value) <= ALCOHOL_TOLERANCE:
        return _result("pass")
    return _result("fail", "Label alcohol content does not match the submitted value.")


def _exact_result(field_name: str, extracted: str | None, submitted: str | None) -> FieldResult:
    if extracted is None or submitted is None:
        return _result("needs-review", f"Could not reliably extract {field_name} from the label.")
    if extracted == submitted:
        return _result("pass")
    return _result("fail", f"Label {field_name} does not exactly match the submitted value.")


def compare_label_fields(
    extracted: LabelFields, submitted: ApplicationData
) -> dict[str, FieldResult]:
    results = {
        "brand_name": _fuzzy_result("brand name", extracted.brand_name, submitted.brand_name),
        "class_type": _fuzzy_result("class/type", extracted.class_type, submitted.class_type),
        "alcohol_content": _alcohol_result(extracted.alcohol_content, submitted.alcohol_content),
        "net_contents": _fuzzy_result("net contents", extracted.net_contents, submitted.net_contents),
        "bottler_name_address": _fuzzy_result(
            "bottler name/address", extracted.bottler_name_address, submitted.bottler_name_address
        ),
        "government_warning_text": _exact_result(
            "government warning text", extracted.government_warning_text, REQUIRED_GOVERNMENT_WARNING
        ),
    }

    if extracted.government_warning_text == REQUIRED_GOVERNMENT_WARNING:
        if extracted.government_warning_is_bold_and_caps is True:
            results["government_warning_is_bold_and_caps"] = _result("pass")
        else:
            results["government_warning_is_bold_and_caps"] = _result(
                "fail", "The GOVERNMENT WARNING heading is not confirmed bold and all caps."
            )
    else:
        results["government_warning_is_bold_and_caps"] = _result(
            "needs-review", "The warning text must match exactly before formatting can be verified."
        )

    if submitted.is_import:
        results["country_of_origin"] = _fuzzy_result(
            "country of origin", extracted.country_of_origin, submitted.country_of_origin
        )

    return results
