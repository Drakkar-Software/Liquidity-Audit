import logging

import pytest

import liquidity_audit.application.shared.progress as progress


class TestFormatEnrichmentProgress:
    def test_formats_completed_and_total_with_percentage(self):
        assert progress.format_enrichment_progress(3, 10) == "3/10 (30%)"


class TestMaybeLogEnrichmentProgress:
    def test_logs_first_and_last_completed_items(self, caplog: pytest.LogCaptureFixture):
        with caplog.at_level(logging.INFO, logger=progress.__name__):
            progress.maybe_log_enrichment_progress("CoinGecko", 1, 25)
            progress.maybe_log_enrichment_progress("CoinGecko", 2, 25)
            progress.maybe_log_enrichment_progress("CoinGecko", 25, 25)
        messages = [record.message for record in caplog.records]
        assert messages == [
            "CoinGecko enrichment progress: 1/25 (4%)",
            "CoinGecko enrichment progress: 25/25 (100%)",
        ]
