import liquidity_audit.domain.select.selection as select_selection
import liquidity_audit.domain.models as models
import liquidity_audit.domain.website.website_resolution as website_resolution


def _listing(
    symbol: str,
    *,
    primary_label: str = "few_orders",
    other_labels: list[str] | None = None,
    liquidity_score: float = 0.1,
    is_low_health: bool = True,
    website: str | None = "https://example.com/",
    website_resolution_status: str | None = None,
) -> models.ListingRecord:
    return models.ListingRecord(
        exchange="mexc",
        symbol=symbol,
        base=symbol.split("/")[0],
        quote="USDT",
        full_name=f"{symbol.split('/')[0]} Token",
        bid_levels=2,
        ask_levels=2,
        liquidity_score=liquidity_score,
        is_low_health=is_low_health,
        health_label_primary=primary_label,
        health_labels_other=other_labels or [],
        website=website,
        website_resolution_status=website_resolution_status,
    )


def _history_record(symbol: str, selected_at: str) -> models.SelectedHistoryRecord:
    return models.SelectedHistoryRecord(
        selected_at=selected_at,
        exchange="mexc",
        symbol=symbol,
        full_name="History Token",
        is_new_listing=False,
        selection_tier=models.SELECTION_TIER_EXISTING_FILL,
        is_low_health=True,
        health_label_primary="few_orders",
        health_labels_other=[],
        issue_count=1,
        bid_levels=1,
        ask_levels=1,
        bid_depth_quote=1.0,
        ask_depth_quote=1.0,
        bid_larger_depth_quote=1.0,
        ask_larger_depth_quote=1.0,
        bid_total_depth_quote=1.0,
        ask_total_depth_quote=1.0,
        volume_quote=1.0,
        bid_ask_spread_ratio=0.1,
        liquidity_score=0.1,
    )


class TestSelectDailyProjects:
    def test_prioritizes_new_low_health_listings(self):
        new_listing = _listing("NEW/USDT", liquidity_score=0.5)
        existing_listing = _listing("OLD/USDT", primary_label="wide_spread", liquidity_score=0.01)
        all_records = {
            new_listing.key(): new_listing,
            existing_listing.key(): existing_listing,
        }
        selections = select_selection.select_daily_projects(
            all_records,
            {new_listing.key()},
            {},
            max_per_day=1,
            cooldown_days=30,
        )
        assert len(selections) == 1
        assert selections[0].record.symbol == "NEW/USDT"
        assert selections[0].selection_tier == models.SELECTION_TIER_NEW_LOW_HEALTH

    def test_excludes_listings_within_cooldown(self):
        listing = _listing("OLD/USDT")
        recent_selection_by_key = {
            listing.key(): _history_record("OLD/USDT", "2026-06-10T12:00:00+00:00"),
        }
        selections = select_selection.select_daily_projects(
            {listing.key(): listing},
            set(),
            recent_selection_by_key,
            max_per_day=5,
            cooldown_days=30,
        )
        assert selections == []

    def test_round_robins_existing_listings_across_label_groups(self):
        few_orders_listing = _listing(
            "FEW/USDT",
            primary_label="few_orders",
            liquidity_score=0.2,
        )
        wide_spread_listing = _listing(
            "WIDE/USDT",
            primary_label="wide_spread",
            liquidity_score=0.15,
        )
        all_records = {
            few_orders_listing.key(): few_orders_listing,
            wide_spread_listing.key(): wide_spread_listing,
        }
        selections = select_selection.select_daily_projects(
            all_records,
            set(),
            {},
            max_per_day=2,
            cooldown_days=30,
        )
        assert len(selections) == 2
        selected_labels = {
            selection.record.health_label_primary for selection in selections
        }
        assert selected_labels == {"few_orders", "wide_spread"}

    def test_includes_all_new_listings_even_when_exceeding_max(self):
        listings = [
            _listing("A/USDT", liquidity_score=0.1),
            _listing("B/USDT", liquidity_score=0.2),
            _listing("C/USDT", liquidity_score=0.3),
        ]
        all_records = {listing.key(): listing for listing in listings}
        new_keys = {listing.key() for listing in listings}
        selections = select_selection.select_daily_projects(
            all_records,
            new_keys,
            {},
            max_per_day=2,
            cooldown_days=30,
        )
        assert len(selections) == 3
        assert all(selection.is_new_listing for selection in selections)

    def test_pads_with_existing_low_health_up_to_max(self):
        new_listing = _listing("NEW/USDT", liquidity_score=0.5)
        existing_listings = [
            _listing("OLD1/USDT", primary_label="few_orders", liquidity_score=0.1),
            _listing("OLD2/USDT", primary_label="wide_spread", liquidity_score=0.05),
        ]
        all_records = {new_listing.key(): new_listing}
        for listing in existing_listings:
            all_records[listing.key()] = listing
        selections = select_selection.select_daily_projects(
            all_records,
            {new_listing.key()},
            {},
            max_per_day=3,
            cooldown_days=30,
        )
        assert len(selections) == 3
        assert sum(1 for selection in selections if selection.is_new_listing) == 1
        assert sum(1 for selection in selections if not selection.is_new_listing) == 2

    def test_includes_healthy_new_listing(self):
        healthy_new_listing = _listing(
            "HEALTHY/USDT",
            liquidity_score=0.9,
            is_low_health=False,
        )
        existing_listing = _listing(
            "OLD/USDT",
            primary_label="wide_spread",
            liquidity_score=0.01,
        )
        all_records = {
            healthy_new_listing.key(): healthy_new_listing,
            existing_listing.key(): existing_listing,
        }
        selections = select_selection.select_daily_projects(
            all_records,
            {healthy_new_listing.key()},
            {},
            max_per_day=1,
            cooldown_days=30,
        )
        assert len(selections) == 1
        assert selections[0].record.symbol == "HEALTHY/USDT"
        assert selections[0].selection_tier == models.SELECTION_TIER_NEW_LISTING
        assert selections[0].is_new_listing is True


class TestWebsiteSelectionGate:
    def test_excludes_listing_without_website_info(self):
        listing = _listing("OLD/USDT", website=None, website_resolution_status=None)
        selections = select_selection.select_daily_projects(
            {listing.key(): listing},
            set(),
            {},
            max_per_day=5,
            cooldown_days=30,
        )
        assert selections == []

    def test_includes_listing_with_name_mismatch_status(self):
        listing = _listing(
            "DATA/USDT",
            website=None,
            website_resolution_status=website_resolution.COINGECKO_NAME_MISMATCH,
        )
        selections = select_selection.select_daily_projects(
            {listing.key(): listing},
            set(),
            {},
            max_per_day=5,
            cooldown_days=30,
        )
        assert len(selections) == 1
        assert selections[0].record.symbol == "DATA/USDT"
