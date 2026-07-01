import liquidity_audit.domain.models as models
import liquidity_audit.domain.website.website_resolution as website_resolution


class TestIsSelectableByWebsiteInfo:
    def test_selectable_when_website_set(self):
        record = models.ListingRecord(
            exchange="mexc",
            symbol="DATA/USDT",
            base="DATA",
            quote="USDT",
            full_name="Data Network",
            website="https://datafdn.org/",
        )
        assert website_resolution.is_selectable_by_website_info(record) is True

    def test_selectable_on_name_mismatch_status(self):
        record = models.ListingRecord(
            exchange="mexc",
            symbol="DATA/USDT",
            base="DATA",
            quote="USDT",
            full_name="Data Network",
            website_resolution_status=website_resolution.COINGECKO_NAME_MISMATCH,
        )
        assert website_resolution.is_selectable_by_website_info(record) is True

    def test_not_selectable_without_website_or_actionable_status(self):
        record = models.ListingRecord(
            exchange="mexc",
            symbol="UNK/USDT",
            base="UNK",
            quote="USDT",
            full_name="Unknown",
            website_resolution_status=website_resolution.COINGECKO_NO_MATCH,
        )
        assert website_resolution.is_selectable_by_website_info(record) is False


class TestNeedsWebsiteResolution:
    def test_needs_resolution_when_unresolved(self):
        record = models.ListingRecord(
            exchange="mexc",
            symbol="DATA/USDT",
            base="DATA",
            quote="USDT",
            full_name="Data Network",
        )
        assert website_resolution.needs_website_resolution(record) is True

    def test_does_not_need_resolution_when_status_set(self):
        record = models.ListingRecord(
            exchange="mexc",
            symbol="DATA/USDT",
            base="DATA",
            quote="USDT",
            full_name="Data Network",
            website_resolution_status=website_resolution.COINGECKO_NAME_MISMATCH,
        )
        assert website_resolution.needs_website_resolution(record) is False


class TestShouldResolveWebsite:
    def test_true_for_new_listing_without_website(self):
        listing = models.ListingRecord(
            exchange="mexc",
            symbol="NEW/USDT",
            base="NEW",
            quote="USDT",
            full_name="New Token",
        )
        new_listing_keys = {listing.key()}
        assert website_resolution.should_resolve_website(
            listing,
            new_listing_keys,
            {},
            cooldown_days=30,
        ) is True

    def test_false_when_website_already_set(self):
        listing = models.ListingRecord(
            exchange="mexc",
            symbol="NEW/USDT",
            base="NEW",
            quote="USDT",
            full_name="New Token",
            website="https://example.com/",
        )
        new_listing_keys = {listing.key()}
        assert website_resolution.should_resolve_website(
            listing,
            new_listing_keys,
            {},
            cooldown_days=30,
        ) is False
