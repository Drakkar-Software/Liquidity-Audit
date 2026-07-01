import liquidity_audit.domain.models as models


def count_health_issues(record: models.ListingRecord) -> int:
    if not record.health_label_primary:
        return 0
    other_labels = record.health_labels_other or []
    return 1 + len(other_labels)
