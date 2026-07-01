import csv
import pathlib

import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.domain.models as models


class TestListingsStoreAppendOrUpdate:
    def test_round_trip_and_dedup(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "listings.csv"
        store = listings_store.ListingsStore(csv_path)

        first_record = models.ListingRecord(
            exchange="mexc",
            symbol="BTC/USDT",
            base="BTC",
            quote="USDT",
            full_name="Bitcoin",
            first_seen_at="2026-01-01T00:00:00+00:00",
            last_checked_at="2026-01-01T00:00:00+00:00",
        )
        store.append_or_update([first_record])

        updated_record = models.ListingRecord(
            exchange="mexc",
            symbol="BTC/USDT",
            base="BTC",
            quote="USDT",
            full_name="Bitcoin",
            first_seen_at="2026-01-01T00:00:00+00:00",
            last_checked_at="2026-01-02T00:00:00+00:00",
        )
        second_record = models.ListingRecord(
            exchange="bitmart",
            symbol="ETH/USDT",
            base="ETH",
            quote="USDT",
            full_name="Ethereum",
        )
        store.append_or_update([updated_record, second_record])

        records = store.load_all()
        assert len(records) == 2
        assert records[("mexc", "BTC/USDT")].last_checked_at == "2026-01-02T00:00:00+00:00"
        assert records[("mexc", "BTC/USDT")].quote == "USDT"
        assert store.load_known_keys() == {("mexc", "BTC/USDT"), ("bitmart", "ETH/USDT")}

        with csv_path.open(encoding="utf-8") as csv_file:
            header_line = csv_file.readline().strip()
        assert "base" not in header_line.split(",")
        assert "quote" not in header_line.split(",")
        assert header_line.split(",")[-1] == "coingecko_candidates_json"
        assert "delisted_at" in header_line.split(",")


class TestListingsStoreLoadOldSchema:
    def test_loads_row_with_legacy_depth_quote_column(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "listings.csv"
        csv_path.write_text(
            "exchange,symbol,base,quote,full_name,coingecko_id,website,"
            "bid_levels,ask_levels,depth_quote,volume_quote,is_low_health,"
            "first_seen_at,last_checked_at\n"
            "mexc,BTC/USDT,BTC,USDT,Bitcoin,,,5,5,5000.0,10000.0,false,,",
            encoding="utf-8",
        )
        store = listings_store.ListingsStore(csv_path)
        records = store.load_all()
        record = records[("mexc", "BTC/USDT")]
        assert record.bid_depth_quote is None
        assert record.ask_depth_quote is None
        assert record.bid_ask_spread_ratio is None
        assert record.liquidity_score is None
        assert record.bid_levels == 5
        assert record.ask_levels == 5

    def test_loads_row_without_larger_depth_columns_as_none(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "listings.csv"
        csv_path.write_text(
            "exchange,symbol,base,quote,full_name,coingecko_id,website,"
            "bid_levels,ask_levels,bid_depth_quote,ask_depth_quote,volume_quote,"
            "bid_ask_spread_ratio,liquidity_score,is_low_health,"
            "first_seen_at,last_checked_at\n"
            "mexc,BTC/USDT,BTC,USDT,Bitcoin,,,5,5,500.0,600.0,10000.0,0.001,0.5,false,,",
            encoding="utf-8",
        )
        store = listings_store.ListingsStore(csv_path)
        record = store.load_all()[("mexc", "BTC/USDT")]
        assert record.bid_larger_depth_quote is None
        assert record.ask_larger_depth_quote is None

    def test_round_trips_health_label_columns(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "listings.csv"
        store = listings_store.ListingsStore(csv_path)
        store.append_or_update([
            models.ListingRecord(
                exchange="mexc",
                symbol="LOW/USDT",
                base="LOW",
                quote="USDT",
                full_name="Low Token",
                is_low_health=True,
                health_label_primary="few_orders",
                health_labels_other=["shallow_liquidity", "wide_spread"],
            ),
        ])

        record = store.load_all()[("mexc", "LOW/USDT")]
        assert record.health_label_primary == "few_orders"
        assert record.health_labels_other == ["shallow_liquidity", "wide_spread"]

    def test_round_trips_delisting_risk_column(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "listings.csv"
        store = listings_store.ListingsStore(csv_path)
        store.append_or_update([
            models.ListingRecord(
                exchange="mexc",
                symbol="RISK/USDT",
                base="RISK",
                quote="USDT",
                full_name="Risk Token",
                delisting_risk=["low depth", "low volume"],
            ),
        ])

        record = store.load_all()[("mexc", "RISK/USDT")]
        assert record.delisting_risk == ["low depth", "low volume"]

    def test_round_trips_total_depth_columns(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "listings.csv"
        store = listings_store.ListingsStore(csv_path)
        store.append_or_update([
            models.ListingRecord(
                exchange="mexc",
                symbol="BTC/USDT",
                base="BTC",
                quote="USDT",
                full_name="Bitcoin",
                bid_total_depth_quote=2500.5,
                ask_total_depth_quote=3100.25,
            ),
        ])

        record = store.load_all()[("mexc", "BTC/USDT")]
        assert record.bid_total_depth_quote == 2500.5
        assert record.ask_total_depth_quote == 3100.25

    def test_loads_row_without_total_depth_columns_as_none(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "listings.csv"
        csv_path.write_text(
            "exchange,symbol,base,quote,full_name,coingecko_id,website,"
            "bid_levels,ask_levels,bid_depth_quote,ask_depth_quote,bid_larger_depth_quote,"
            "ask_larger_depth_quote,volume_quote,bid_ask_spread_ratio,liquidity_score,"
            "is_low_health,first_seen_at,last_checked_at\n"
            "mexc,BTC/USDT,BTC,USDT,Bitcoin,,,5,5,500.0,600.0,2000.0,2000.0,"
            "10000.0,0.001,0.5,false,,",
            encoding="utf-8",
        )
        record = listings_store.ListingsStore(csv_path).load_all()[("mexc", "BTC/USDT")]
        assert record.bid_total_depth_quote is None
        assert record.ask_total_depth_quote is None

    def test_loads_row_without_base_quote_columns_from_symbol(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "listings.csv"
        csv_path.write_text(
            "exchange,symbol,full_name,bid_levels,ask_levels,bid_depth_quote,"
            "ask_depth_quote,bid_larger_depth_quote,ask_larger_depth_quote,bid_total_depth_quote,"
            "ask_total_depth_quote,volume_quote,bid_ask_spread_ratio,liquidity_score,is_low_health,"
            "health_label_primary,health_labels_other,first_seen_at,last_checked_at,delisted_at\n"
            "mexc,ETH/USDT,Ethereum,,,,,,,,,,,,false,,,,",
            encoding="utf-8",
        )
        record = listings_store.ListingsStore(csv_path).load_all()[("mexc", "ETH/USDT")]
        assert record.base == "ETH"
        assert record.quote == "USDT"

    def test_loads_row_without_health_label_columns_as_empty(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "listings.csv"
        csv_path.write_text(
            "exchange,symbol,base,quote,full_name,coingecko_id,website,"
            "bid_levels,ask_levels,bid_depth_quote,ask_depth_quote,bid_larger_depth_quote,"
            "ask_larger_depth_quote,volume_quote,bid_ask_spread_ratio,liquidity_score,"
            "is_low_health,first_seen_at,last_checked_at\n"
            "mexc,BTC/USDT,BTC,USDT,Bitcoin,,,5,5,500.0,600.0,2000.0,2000.0,"
            "10000.0,0.001,0.5,false,,",
            encoding="utf-8",
        )
        record = listings_store.ListingsStore(csv_path).load_all()[("mexc", "BTC/USDT")]
        assert record.health_label_primary is None
        assert record.health_labels_other == []



class TestParseOptionalFloat:
    def test_parses_comma_decimal_separator(self):
        assert listings_store._parse_optional_float("0,000001") == 0.000001

    def test_parses_dot_decimal_unchanged(self):
        assert listings_store._parse_optional_float("1.5") == 1.5

    def test_returns_none_for_empty_string(self):
        assert listings_store._parse_optional_float("") is None


class TestLoadCommaDecimalFloat:
    def test_loads_row_with_comma_decimal_bid_volume_quote(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "listings.csv"
        row = {column: "" for column in listings_store.CSV_COLUMNS}
        row.update({
            "exchange": "mexc",
            "symbol": "LOW/USDT",
            "full_name": "Low Token",
            "is_low_health": "true",
            "bid_volume_quote": "0,000001",
        })
        with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=listings_store.CSV_COLUMNS)
            writer.writeheader()
            writer.writerow(row)

        record = listings_store.ListingsStore(csv_path).load_all()[("mexc", "LOW/USDT")]
        assert record.bid_volume_quote == 0.000001
