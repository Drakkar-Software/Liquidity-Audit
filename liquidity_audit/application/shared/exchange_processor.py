import logging

import liquidity_audit.application.shared.logging_summaries as logging_summaries
import liquidity_audit.application.shared.progress as progress
import liquidity_audit.application.shared.time_utils as time_utils
import liquidity_audit.infrastructure.ccxt_client as ccxt_client
import liquidity_audit.config as app_config
import liquidity_audit.infrastructure.listing_discovery as listing_discovery
import liquidity_audit.domain.models as models

_LOGGER = logging.getLogger(__name__)


def stub_listing_after_discovery_failure(
    listing: models.ListingRecord,
    now: str,
) -> models.ListingRecord:
    return models.ListingRecord(
        exchange=listing.exchange,
        symbol=listing.symbol,
        base=listing.base,
        quote=listing.quote,
        full_name=listing.full_name,
        first_seen_at=now,
        last_checked_at=now,
    )


def register_new_listing(listing: models.ListingRecord) -> models.ListingRecord:
    now = time_utils.utc_now_iso()
    listing.first_seen_at = now
    listing.last_checked_at = now
    return listing


async def process_exchange(
    exchange_name: str,
    known_keys: set[tuple[str, str]],
    config: app_config.AppConfig,
    identify_only: bool,
) -> tuple[list[models.ListingRecord], list[models.FailedListingEnrichment]]:
    exchange_new_listings: list[models.ListingRecord] = []
    failed_enrichments: list[models.FailedListingEnrichment] = []

    _LOGGER.info("Discovering listings on %s", exchange_name)
    async with ccxt_client.exchange_client(
        exchange_name,
        ccxt_options=config.ccxt_options,
    ) as exchange_client:
        current_listings = await listing_discovery.fetch_exchange_listings(
            exchange_client,
            exchange_name,
        )
        exchange_new_candidates = listing_discovery.filter_new_listings(
            current_listings,
            known_keys,
        )
        if exchange_new_candidates:
            total_to_register = len(exchange_new_candidates)
            _LOGGER.info(
                "Registering %s new listing(s) on %s",
                total_to_register,
                exchange_name,
            )
            for listing_index, listing in enumerate(exchange_new_candidates, start=1):
                try:
                    registered = register_new_listing(listing)
                    if not identify_only:
                        progress.maybe_log_enrichment_progress(
                            exchange_name,
                            listing_index,
                            total_to_register,
                        )
                except Exception as registration_error:
                    _LOGGER.warning(
                        "Failed to register %s %s: %s",
                        listing.exchange,
                        listing.symbol,
                        registration_error,
                    )
                    failed_enrichments.append(models.FailedListingEnrichment(
                        exchange=listing.exchange,
                        symbol=listing.symbol,
                        error=str(registration_error),
                    ))
                    stub_listing = stub_listing_after_discovery_failure(
                        listing,
                        time_utils.utc_now_iso(),
                    )
                    exchange_new_listings.append(stub_listing)
                    continue

                exchange_new_listings.append(registered)

            logging_summaries.log_failed_enrichments(failed_enrichments, exchange_name)
            _LOGGER.info(
                "%s registration complete: %s listing(s) processed, %s failed",
                exchange_name,
                len(exchange_new_listings),
                len(failed_enrichments),
            )
        else:
            _LOGGER.info("No new listings on %s", exchange_name)

    return exchange_new_listings, failed_enrichments
