import liquidity_audit.application.shared.time_utils as time_utils
import liquidity_audit.infrastructure.selected_history_store as selected_history_store
import liquidity_audit.config as app_config
import liquidity_audit.domain.contacts.selection as contact_selection
import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.domain.models as models


def new_low_health_listings(listings: list[models.ListingRecord]) -> list[models.ListingRecord]:
    return [
        listing for listing in listings
        if listing.is_low_health and listing.has_health_metrics()
    ]


def new_low_health_listings_from_store(
    store: listings_store.ListingsStore,
    listing_keys: set[tuple[str, str]],
) -> list[models.ListingRecord]:
    all_records = store.load_all()
    new_low_health = [
        all_records[listing_key]
        for listing_key in listing_keys
        if listing_key in all_records
        and all_records[listing_key].is_low_health
        and all_records[listing_key].has_health_metrics()
    ]
    return sorted(new_low_health, key=lambda listing: (listing.exchange, listing.symbol))


def select_and_record_daily_selections(
    store: listings_store.ListingsStore,
    config: app_config.AppConfig,
    new_listing_keys: set[tuple[str, str]],
) -> list[models.DailyProjectSelection]:
    all_records = store.load_all()
    history_store = selected_history_store.SelectedHistoryStore(
        config.daily_selection.history_csv_path,
    )
    recent_selection_by_key = history_store.load_recent_by_key()
    daily_selections = contact_selection.select_daily_projects(
        all_records,
        new_listing_keys,
        recent_selection_by_key,
        config.daily_selection.max_per_day,
        config.daily_selection.cooldown_days,
    )
    selected_at = time_utils.utc_now_iso()
    history_records = [
        selected_history_store.selected_history_record_from_selection(
            selection,
            selected_at,
        )
        for selection in daily_selections
    ]
    history_store.append(history_records)
    return daily_selections
