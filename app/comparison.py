from app.models import ApplicationData, FieldResult, LabelFields


def compare_label_fields(
    extracted: LabelFields, submitted: ApplicationData
) -> dict[str, FieldResult]:
    """Apply field-specific comparison rules in the implementation phase."""
    raise NotImplementedError
