from collections import Counter

from app.models import VerificationResult


def summarize_outcomes(results: list[VerificationResult]) -> Counter[str]:
    """Summarize result statuses for request logging."""
    return Counter(result.status.value for result in results)
