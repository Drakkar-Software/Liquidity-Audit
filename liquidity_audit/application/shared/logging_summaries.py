import logging

import liquidity_audit.domain.contacts.health_issues as contact_health_issues
import liquidity_audit.domain.models as models

_LOGGER = logging.getLogger(__name__)


def format_health_labels(record: models.ListingRecord) -> str:
    primary = record.health_label_primary or "none"
    other_labels = record.health_labels_other or []
    if not other_labels:
        return f"label={primary}"
    return f"label={primary} (+{','.join(other_labels)})"


def log_failed_enrichments(
    failures: list[models.FailedListingEnrichment],
    exchange_name: str | None = None,
) -> None:
    if not failures:
        return
    if exchange_name is not None:
        _LOGGER.error(
            "%s: failed to register %s listing(s)",
            exchange_name,
            len(failures),
        )
    for failure in failures:
        _LOGGER.error("  %s %s: %s", failure.exchange, failure.symbol, failure.error)


def log_daily_selections_summary(
    daily_selections: list[models.DailyProjectSelection],
    max_per_day: int,
) -> None:
    if not daily_selections:
        _LOGGER.info("Daily selections: 0/%s selected", max_per_day)
        return

    new_count = sum(1 for selection in daily_selections if selection.is_new_listing)
    existing_count = len(daily_selections) - new_count
    diversified_count = sum(
        1 for selection in daily_selections
        if selection.selection_tier == models.SELECTION_TIER_EXISTING_DIVERSIFIED
    )
    _LOGGER.info(
        "Daily selections: %s/%s selected (%s new, %s existing, %s diversified)",
        len(daily_selections),
        max_per_day,
        new_count,
        existing_count,
        diversified_count,
    )
    sorted_selections = sorted(
        daily_selections,
        key=lambda selection: (selection.record.exchange, selection.record.symbol),
    )
    for selection in sorted_selections:
        record = selection.record
        issue_count = contact_health_issues.count_health_issues(record)
        primary_label = record.health_label_primary or "none"
        _LOGGER.info(
            "  %s %s | %s | %s | label=%s | issues=%s",
            record.exchange,
            record.symbol,
            record.full_name,
            selection.selection_tier,
            primary_label,
            issue_count,
        )


def log_new_listings_run_summary(
    new_listings: list[models.ListingRecord],
    failed_enrichments: list[models.FailedListingEnrichment],
) -> None:
    if not new_listings:
        _LOGGER.info("New listings summary: no new listings")
        return

    low_health_listings = [
        listing for listing in new_listings
        if listing.is_low_health and listing.has_health_metrics()
    ]
    healthy_count = sum(
        1 for listing in new_listings
        if listing.has_health_metrics() and not listing.is_low_health
    )
    registration_failed_count = sum(
        1 for listing in new_listings if not listing.has_health_metrics()
    )
    if registration_failed_count != len(failed_enrichments):
        _LOGGER.warning(
            "New listings summary: registration failed count mismatch "
            "(stubs=%s, failures=%s)",
            registration_failed_count,
            len(failed_enrichments),
        )

    _LOGGER.info(
        "New listings summary: %s total (%s low-health, %s healthy, %s registration failed)",
        len(new_listings),
        len(low_health_listings),
        healthy_count,
        registration_failed_count,
    )

    sorted_low_health_listings = sorted(
        low_health_listings,
        key=lambda listing: (listing.exchange, listing.symbol),
    )
    for listing in sorted_low_health_listings:
        _LOGGER.info(
            "  %s %s | %s | low_health | %s | liquidity_score=%s",
            listing.exchange,
            listing.symbol,
            listing.full_name,
            format_health_labels(listing),
            listing.liquidity_score,
        )
