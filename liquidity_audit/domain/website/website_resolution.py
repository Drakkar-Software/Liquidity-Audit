import dataclasses
import json
import typing

import liquidity_audit.domain.select.selection as select_selection
import liquidity_audit.domain.models as models

COINGECKO_AMBIGUOUS_NAME_MATCH = "coingecko_ambiguous_name_match"
COINGECKO_NAME_MISMATCH = "coingecko_name_mismatch"
COINGECKO_NO_MATCH = "coingecko_no_match"

SELECTABLE_WEBSITE_RESOLUTION_STATUSES = frozenset({
    COINGECKO_AMBIGUOUS_NAME_MATCH,
    COINGECKO_NAME_MISMATCH,
})


@dataclasses.dataclass
class WebsiteResolutionResult:
    website: typing.Optional[str]
    coingecko_id: typing.Optional[str]
    failure_reason: typing.Optional[str] = None
    ambiguous_coingecko_candidates: list[dict] = dataclasses.field(default_factory=list)
    symbol_coingecko_candidates: list[dict] = dataclasses.field(default_factory=list)


def is_selectable_by_website_info(record: models.ListingRecord) -> bool:
    if record.website and record.website.strip():
        return True
    status = record.website_resolution_status
    return status in SELECTABLE_WEBSITE_RESOLUTION_STATUSES


def needs_website_resolution(record: models.ListingRecord) -> bool:
    if record.website and record.website.strip():
        return False
    if record.website_resolution_status and record.website_resolution_status.strip():
        return False
    return True


def should_resolve_website(
    listing: models.ListingRecord,
    new_listing_keys: set[tuple[str, str]],
    recent_selection_by_key: dict[tuple[str, str], models.SelectedHistoryRecord],
    cooldown_days: int,
) -> bool:
    return (
        needs_website_resolution(listing)
        and select_selection.is_website_resolution_candidate(
            listing,
            new_listing_keys,
            recent_selection_by_key,
            cooldown_days,
        )
    )


def apply_resolution_to_listing(
    record: models.ListingRecord,
    resolution: WebsiteResolutionResult,
) -> None:
    record.website = resolution.website
    record.coingecko_id = resolution.coingecko_id
    if resolution.website and resolution.website.strip():
        record.website_resolution_status = None
    elif resolution.failure_reason:
        record.website_resolution_status = resolution.failure_reason
    else:
        record.website_resolution_status = COINGECKO_NO_MATCH
    candidates = resolution.ambiguous_coingecko_candidates or resolution.symbol_coingecko_candidates
    if candidates:
        record.coingecko_candidates_json = json.dumps(candidates)
    else:
        record.coingecko_candidates_json = None
