from enum import StrEnum

from pydantic import BaseModel, Field


class VerificationStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVIEW = "needs-review"


class LabelFields(BaseModel):
    brand_name: str | None = None
    class_type: str | None = None
    alcohol_content: str | None = None
    net_contents: str | None = None
    bottler_name_address: str | None = None
    country_of_origin: str | None = None
    government_warning_text: str | None = None
    government_warning_is_bold_and_caps: bool | None = None
    extraction_confidence: float | None = Field(default=None, ge=0, le=1)


class ApplicationData(BaseModel):
    brand_name: str
    class_type: str
    alcohol_content: str
    net_contents: str
    bottler_name_address: str
    is_import: bool = False
    country_of_origin: str | None = None


class FieldResult(BaseModel):
    status: VerificationStatus
    reason: str | None = None
    score: float | None = None


class VerificationResult(BaseModel):
    item_index: int
    status: VerificationStatus
    fields: dict[str, FieldResult] = Field(default_factory=dict)


class VerificationSummary(BaseModel):
    results: list[VerificationResult]
