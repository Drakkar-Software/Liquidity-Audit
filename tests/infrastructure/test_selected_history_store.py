import datetime
import pathlib

import liquidity_audit.domain.contacts.health_issues as contact_health_issues
import liquidity_audit.infrastructure.selected_history_store as selected_history_store
import liquidity_audit.domain.models as models


def _listing(symbol: str) -> models.ListingRecord:
    return models.ListingRecord(
        exchange="mexc",
        symbol=symbol,
        base=symbol.split("/")[0],
        quote="USDT",
        full_name="Test Token",
        bid_levels=2,
        ask_levels=3,
        bid_depth_quote=1.5,
        ask_depth_quote=2.5,
        bid_larger_depth_quote=10.0,
        ask_larger_depth_quote=12.0,
        bid_total_depth_quote=100.0,
        ask_total_depth_quote=120.0,
        volume_quote=5000.0,
        bid_ask_spread_ratio=0.05,
        liquidity_score=0.12,
        is_low_health=True,
        health_label_primary="few_orders",
        health_labels_other=["shallow_liquidity"],
    )


class TestCountHealthIssues:
    def test_counts_primary_and_other_labels(self):
        assert contact_health_issues.count_health_issues(_listing("LOW/USDT")) == 2


class TestIsWithinCooldown:
    def test_returns_true_when_selected_recently(self):
        selected_at = "2026-06-10T12:00:00+00:00"
        now = datetime.datetime(2026, 6, 15, 12, 0, tzinfo=datetime.UTC)
        assert selected_history_store.is_within_cooldown(selected_at, 30, now=now) is True

    def test_returns_false_after_cooldown_elapsed(self):
        selected_at = "2026-05-01T12:00:00+00:00"
        now = datetime.datetime(2026, 6, 15, 12, 0, tzinfo=datetime.UTC)
        assert selected_history_store.is_within_cooldown(selected_at, 30, now=now) is False


class TestSelectedHistoryRecordFromSelection:
    def test_copies_label_input_metrics(self):
        selection = models.DailyProjectSelection(
            record=_listing("LOW/USDT"),
            selection_tier=models.SELECTION_TIER_NEW_LOW_HEALTH,
            is_new_listing=True,
        )
        history_record = selected_history_store.selected_history_record_from_selection(
            selection,
            "2026-06-11T14:30:00+00:00",
        )
        assert history_record.selected_at == "2026-06-11T14:30:00+00:00"
        assert history_record.bid_levels == 2
        assert history_record.liquidity_score == 0.12
        assert history_record.issue_count == 2
        assert history_record.selection_tier == models.SELECTION_TIER_NEW_LOW_HEALTH

    def test_persists_new_listing_tier_for_healthy_new_selection(self):
        healthy_listing = _listing("NEW/USDT")
        healthy_listing.is_low_health = False
        selection = models.DailyProjectSelection(
            record=healthy_listing,
            selection_tier=models.SELECTION_TIER_NEW_LISTING,
            is_new_listing=True,
        )
        history_record = selected_history_store.selected_history_record_from_selection(
            selection,
            "2026-06-11T14:30:00+00:00",
        )
        assert history_record.selection_tier == models.SELECTION_TIER_NEW_LISTING
        assert history_record.is_new_listing is True


class TestSelectedHistoryStore:
    def test_round_trips_all_metric_columns(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "selected_history.csv"
        store = selected_history_store.SelectedHistoryStore(csv_path)
        history_record = selected_history_store.selected_history_record_from_selection(
            models.DailyProjectSelection(
                record=_listing("LOW/USDT"),
                selection_tier=models.SELECTION_TIER_EXISTING_DIVERSIFIED,
                is_new_listing=False,
            ),
            "2026-06-11T14:30:00+00:00",
        )
        store.append([history_record])

        loaded_records = store.load_all()
        assert len(loaded_records) == 1
        loaded_record = loaded_records[0]
        assert loaded_record.selected_at == "2026-06-11T14:30:00+00:00"
        assert loaded_record.health_labels_other == ["shallow_liquidity"]
        assert loaded_record.bid_total_depth_quote == 100.0
        assert loaded_record.volume_quote == 5000.0

    def test_load_recent_by_key_keeps_latest_row(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "selected_history.csv"
        store = selected_history_store.SelectedHistoryStore(csv_path)
        listing = _listing("LOW/USDT")
        store.append([
            selected_history_store.selected_history_record_from_selection(
                models.DailyProjectSelection(
                    record=listing,
                    selection_tier=models.SELECTION_TIER_NEW_LOW_HEALTH,
                    is_new_listing=True,
                ),
                "2026-06-01T10:00:00+00:00",
            ),
            selected_history_store.selected_history_record_from_selection(
                models.DailyProjectSelection(
                    record=listing,
                    selection_tier=models.SELECTION_TIER_EXISTING_FILL,
                    is_new_listing=False,
                ),
                "2026-06-10T10:00:00+00:00",
            ),
        ])

        recent_by_key = store.load_recent_by_key()
        assert recent_by_key[("mexc", "LOW/USDT")].selected_at == "2026-06-10T10:00:00+00:00"
