import datetime

import liquidity_audit.domain.models as models


def _parse_iso_timestamp(timestamp: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(timestamp)


def is_within_delisted_retention(delisted_at: str, retention_days: int) -> bool:
    delisted_time = _parse_iso_timestamp(delisted_at)
    age = datetime.datetime.now(datetime.UTC) - delisted_time
    return age < datetime.timedelta(days=retention_days)


def mark_delisted(listing: models.ListingRecord, now: str) -> bool:
    if listing.delisted_at:
        return False
    listing.delisted_at = now
    return True


def clear_delisted_if_relisted(listing: models.ListingRecord) -> bool:
    if not listing.delisted_at:
        return False
    listing.delisted_at = None
    return True
