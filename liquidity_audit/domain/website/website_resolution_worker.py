import asyncio
import logging
import typing

import aiohttp

import liquidity_audit.application.shared.progress as progress
import liquidity_audit.config as app_config
import liquidity_audit.domain.models as models
import liquidity_audit.domain.website.website_resolution as website_resolution
import liquidity_audit.infrastructure.ccxt_client as ccxt_client
import liquidity_audit.infrastructure.exchange_website_resolvers as exchange_website_resolvers
import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.infrastructure.selected_history_store as selected_history_store
import liquidity_audit.infrastructure.website_finder as website_finder

_LOGGER = logging.getLogger(__name__)

_SHUTDOWN_SENTINEL = object()
SHUTDOWN_QUEUE_DRAIN_TIMEOUT_SECONDS = 1800
CONSUMER_STOP_TIMEOUT_SECONDS = 30


class WebsiteResolutionWorker:
    def __init__(
        self,
        store: listings_store.ListingsStore,
        config: app_config.AppConfig,
        new_listing_keys: set[tuple[str, str]],
        recent_selection_by_key: dict[tuple[str, str], models.SelectedHistoryRecord],
        listings_csv_lock: asyncio.Lock,
    ) -> None:
        self._store = store
        self._config = config
        self._new_listing_keys = new_listing_keys
        self._recent_selection_by_key = recent_selection_by_key
        self._cooldown_days = config.daily_selection.cooldown_days
        self._listings_csv_lock = listings_csv_lock
        self._mexc_queue: asyncio.Queue[typing.Any] = asyncio.Queue()
        self._coinex_queue: asyncio.Queue[typing.Any] = asyncio.Queue()
        self._coingecko_queue: asyncio.Queue[typing.Any] = asyncio.Queue()
        self._enqueued_keys: set[tuple[str, str]] = set()
        self._coingecko_lock = asyncio.Lock()
        self._resolved_count = 0
        self._failed_count = 0
        self._website_finder = website_finder.WebsiteFinder()
        self._coingecko_client: typing.Any = None
        self._mexc_throttle_client: typing.Any = None
        self._coinex_throttle_client: typing.Any = None
        self._mexc_http_session: aiohttp.ClientSession | None = None
        self._coinex_http_session: aiohttp.ClientSession | None = None
        self._consumer_tasks: list[asyncio.Task[None]] = []

    @classmethod
    async def create_and_start(
        cls,
        store: listings_store.ListingsStore,
        config: app_config.AppConfig,
        new_listing_keys: set[tuple[str, str]],
        listings_csv_lock: asyncio.Lock,
    ) -> "WebsiteResolutionWorker":
        history_store = selected_history_store.SelectedHistoryStore(
            config.daily_selection.history_csv_path,
        )
        recent_selection_by_key = history_store.load_recent_by_key()
        worker = cls(
            store,
            config,
            new_listing_keys,
            recent_selection_by_key,
            listings_csv_lock,
        )
        await worker.start()
        return worker

    async def start(self) -> None:
        _LOGGER.info("Starting website resolution workers (mexc, coinex, coingecko)")
        self._coingecko_client = ccxt_client.create_exchange(
            "coingecko",
            ccxt_options=self._config.ccxt_options,
            options=self._config.coingecko_options,
        )
        await self._website_finder.load_coingecko_index(self._coingecko_client)

        self._mexc_throttle_client = ccxt_client.create_exchange(
            "mexc",
            ccxt_options=self._config.ccxt_options,
        )
        self._coinex_throttle_client = ccxt_client.create_exchange(
            "coinex",
            ccxt_options=self._config.ccxt_options,
        )
        self._mexc_throttle_client.open()
        self._coinex_throttle_client.open()
        _LOGGER.info(
            "mexc website throttle rateLimit=%s ms (from CCXT)",
            self._mexc_throttle_client.rateLimit,
        )
        _LOGGER.info(
            "coinex website throttle rateLimit=%s ms (from CCXT)",
            self._coinex_throttle_client.rateLimit,
        )

        self._mexc_http_session = exchange_website_resolvers.create_mexc_http_session()
        self._coinex_http_session = exchange_website_resolvers.create_coinex_http_session()

        _LOGGER.info("Website resolution workers ready")
        self._consumer_tasks = [
            asyncio.create_task(self._mexc_consumer_loop()),
            asyncio.create_task(self._coinex_consumer_loop()),
            asyncio.create_task(self._coingecko_consumer_loop()),
        ]

    def try_enqueue(self, listing: models.ListingRecord) -> None:
        listing_key = listing.key()
        if listing_key in self._enqueued_keys:
            return
        if not website_resolution.should_resolve_website(
            listing,
            self._new_listing_keys,
            self._recent_selection_by_key,
            self._cooldown_days,
        ):
            return
        self._enqueued_keys.add(listing_key)
        exchange_name = listing.exchange.strip().lower()
        if exchange_name == "mexc":
            target_queue = self._mexc_queue
            queue_name = "mexc"
        elif exchange_name == "coinex":
            target_queue = self._coinex_queue
            queue_name = "coinex"
        else:
            target_queue = self._coingecko_queue
            queue_name = "coingecko"
        target_queue.put_nowait(listing)
        self._log_queue_enqueue(queue_name, target_queue)

    def _enqueue_coingecko_fallback(self, listing: models.ListingRecord) -> None:
        self._coingecko_queue.put_nowait(listing)
        self._log_queue_enqueue("coingecko", self._coingecko_queue)

    def _log_queue_enqueue(self, queue_name: str, queue: asyncio.Queue) -> None:
        total_enqueued = len(self._enqueued_keys)
        enqueue_interval = progress.enrichment_progress_log_interval(
            max(total_enqueued, 10),
        )
        if total_enqueued == 1 or total_enqueued % enqueue_interval == 0:
            _LOGGER.info(
                "%s website queue: %s listing(s) enqueued total, %s pending",
                queue_name,
                total_enqueued,
                queue.qsize(),
            )

    async def shutdown(self) -> int:
        all_queues = [
            self._mexc_queue,
            self._coinex_queue,
            self._coingecko_queue,
        ]
        try:
            await asyncio.wait_for(
                asyncio.gather(*(queue.join() for queue in all_queues)),
                timeout=SHUTDOWN_QUEUE_DRAIN_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            pending_counts = {
                "mexc": self._mexc_queue.qsize(),
                "coinex": self._coinex_queue.qsize(),
                "coingecko": self._coingecko_queue.qsize(),
            }
            _LOGGER.warning(
                "Website resolution queue drain timed out after %ss "
                "(pending mexc=%s coinex=%s coingecko=%s, resolved=%s failed=%s enqueued=%s)",
                SHUTDOWN_QUEUE_DRAIN_TIMEOUT_SECONDS,
                pending_counts["mexc"],
                pending_counts["coinex"],
                pending_counts["coingecko"],
                self._resolved_count,
                self._failed_count,
                len(self._enqueued_keys),
            )
            self._abandon_pending_queue_items(all_queues)

        for queue in all_queues:
            await queue.put(_SHUTDOWN_SENTINEL)

        for consumer_task in self._consumer_tasks:
            try:
                await asyncio.wait_for(consumer_task, timeout=CONSUMER_STOP_TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                _LOGGER.warning(
                    "Website resolution consumer did not stop within %ss; cancelling",
                    CONSUMER_STOP_TIMEOUT_SECONDS,
                )
                consumer_task.cancel()
                try:
                    await consumer_task
                except asyncio.CancelledError:
                    pass

        if self._mexc_http_session is not None:
            await self._mexc_http_session.close()
        if self._coinex_http_session is not None:
            await self._coinex_http_session.close()
        if self._mexc_throttle_client is not None:
            await self._mexc_throttle_client.close()
        if self._coinex_throttle_client is not None:
            await self._coinex_throttle_client.close()
        if self._coingecko_client is not None:
            await self._coingecko_client.close()

        _LOGGER.info(
            "Website resolution workers stopped: %s resolved, %s failed, %s enqueued",
            self._resolved_count,
            self._failed_count,
            len(self._enqueued_keys),
        )
        return self._resolved_count

    def _abandon_pending_queue_items(self, queues: list[asyncio.Queue]) -> None:
        abandoned_count = 0
        for queue in queues:
            while True:
                try:
                    listing = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                if listing is not _SHUTDOWN_SENTINEL:
                    abandoned_count += 1
                    _LOGGER.warning(
                        "Skipping website resolution for %s %s (shutdown timeout)",
                        listing.exchange,
                        listing.symbol,
                    )
                queue.task_done()
        if abandoned_count > 0:
            _LOGGER.warning(
                "Abandoned %s pending website resolution(s) due to shutdown timeout",
                abandoned_count,
            )

    async def _mexc_consumer_loop(self) -> None:
        while True:
            listing = await self._mexc_queue.get()
            try:
                if listing is _SHUTDOWN_SENTINEL:
                    break
                try:
                    await self._resolve_via_mexc(listing)
                except Exception:
                    self._failed_count += 1
                    _LOGGER.exception(
                        "mexc website resolution failed for %s %s",
                        listing.exchange,
                        listing.symbol,
                    )
            finally:
                self._mexc_queue.task_done()

    async def _coinex_consumer_loop(self) -> None:
        while True:
            listing = await self._coinex_queue.get()
            try:
                if listing is _SHUTDOWN_SENTINEL:
                    break
                try:
                    await self._resolve_via_coinex(listing)
                except Exception:
                    self._failed_count += 1
                    _LOGGER.exception(
                        "coinex website resolution failed for %s %s",
                        listing.exchange,
                        listing.symbol,
                    )
            finally:
                self._coinex_queue.task_done()

    async def _coingecko_consumer_loop(self) -> None:
        while True:
            listing = await self._coingecko_queue.get()
            try:
                if listing is _SHUTDOWN_SENTINEL:
                    break
                try:
                    await self._resolve_via_coingecko(listing)
                except Exception:
                    self._failed_count += 1
                    _LOGGER.exception(
                        "coingecko website resolution failed for %s %s",
                        listing.exchange,
                        listing.symbol,
                    )
            finally:
                self._coingecko_queue.task_done()

    def _ensure_listing_base(self, listing: models.ListingRecord) -> None:
        if not listing.base:
            base, _quote = listings_store.parse_base_quote_from_symbol(listing.symbol)
            listing.base = base

    async def _resolve_via_mexc(self, listing: models.ListingRecord) -> None:
        self._ensure_listing_base(listing)
        await self._mexc_throttle_client.throttle(1)
        website = await exchange_website_resolvers.resolve_mexc_website(
            listing.base,
            self._mexc_http_session,
        )
        if website:
            resolution = website_resolution.WebsiteResolutionResult(
                website=website,
                coingecko_id=None,
            )
            await self._persist_resolution(listing, resolution, source="mexc")
            return
        self._enqueue_coingecko_fallback(listing)

    async def _resolve_via_coinex(self, listing: models.ListingRecord) -> None:
        self._ensure_listing_base(listing)
        await self._coinex_throttle_client.throttle(1)
        website = await exchange_website_resolvers.resolve_coinex_website(
            listing.base,
            self._coinex_http_session,
        )
        if website:
            resolution = website_resolution.WebsiteResolutionResult(
                website=website,
                coingecko_id=None,
            )
            await self._persist_resolution(listing, resolution, source="coinex")
            return
        self._enqueue_coingecko_fallback(listing)

    async def _resolve_via_coingecko(self, listing: models.ListingRecord) -> None:
        self._ensure_listing_base(listing)
        async with self._coingecko_lock:
            resolution = await exchange_website_resolvers.resolve_coingecko_website(
                listing,
                self._website_finder,
                self._coingecko_client,
            )
        await self._persist_resolution(listing, resolution, source="coingecko")

    async def _persist_resolution(
        self,
        listing: models.ListingRecord,
        resolution: website_resolution.WebsiteResolutionResult,
        source: str,
    ) -> None:
        website_resolution.apply_resolution_to_listing(listing, resolution)
        async with self._listings_csv_lock:
            self._store.append_or_update([listing])
        self._resolved_count += 1
        progress.maybe_log_enrichment_progress(
            f"website-{source}",
            self._resolved_count,
            len(self._enqueued_keys),
        )
        _LOGGER.info(
            "%s website resolution for %s %s: website=%s status=%s",
            source,
            listing.exchange,
            listing.symbol,
            listing.website or "none",
            listing.website_resolution_status or "resolved",
        )
