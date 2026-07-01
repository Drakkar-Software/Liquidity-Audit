import asyncio
import logging
import typing

import liquidity_audit.application.shared.progress as progress
import liquidity_audit.config as app_config
import liquidity_audit.domain.models as models
import liquidity_audit.domain.website.website_resolution as website_resolution
import liquidity_audit.infrastructure.ccxt_client as ccxt_client
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
        self._queue: asyncio.Queue[typing.Any] = asyncio.Queue()
        self._enqueued_keys: set[tuple[str, str]] = set()
        self._coingecko_lock = asyncio.Lock()
        self._resolved_count = 0
        self._failed_count = 0
        self._website_finder = website_finder.WebsiteFinder()
        self._coingecko_client: typing.Any = None
        self._consumer_task: asyncio.Task[None] | None = None

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
        _LOGGER.info("Starting CoinGecko website resolution worker")
        self._coingecko_client = ccxt_client.create_exchange(
            "coingecko",
            ccxt_options=self._config.ccxt_options,
            options=self._config.coingecko_options,
        )
        await self._website_finder.load_coingecko_index(self._coingecko_client)
        _LOGGER.info("CoinGecko index loaded, website resolution worker ready")
        self._consumer_task = asyncio.create_task(self._consumer_loop())

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
        self._queue.put_nowait(listing)
        total_enqueued = len(self._enqueued_keys)
        enqueue_interval = progress.enrichment_progress_log_interval(
            max(total_enqueued, 10),
        )
        if total_enqueued == 1 or total_enqueued % enqueue_interval == 0:
            _LOGGER.info(
                "CoinGecko website queue: %s listing(s) enqueued, %s pending",
                total_enqueued,
                self._queue.qsize(),
            )

    async def shutdown(self) -> int:
        try:
            await asyncio.wait_for(
                self._queue.join(),
                timeout=SHUTDOWN_QUEUE_DRAIN_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            _LOGGER.warning(
                "CoinGecko website resolution queue drain timed out after %ss "
                "(%s item(s) still in queue, %s resolved, %s failed, %s enqueued)",
                SHUTDOWN_QUEUE_DRAIN_TIMEOUT_SECONDS,
                self._queue.qsize(),
                self._resolved_count,
                self._failed_count,
                len(self._enqueued_keys),
            )
            self._abandon_pending_queue_items()

        await self._queue.put(_SHUTDOWN_SENTINEL)
        if self._consumer_task is not None:
            try:
                await asyncio.wait_for(
                    self._consumer_task,
                    timeout=CONSUMER_STOP_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                _LOGGER.warning(
                    "CoinGecko website resolution consumer did not stop within %ss; cancelling",
                    CONSUMER_STOP_TIMEOUT_SECONDS,
                )
                self._consumer_task.cancel()
                try:
                    await self._consumer_task
                except asyncio.CancelledError:
                    pass
        if self._coingecko_client is not None:
            await self._coingecko_client.close()
        _LOGGER.info(
            "CoinGecko website resolution worker stopped: %s resolved, %s failed, %s enqueued",
            self._resolved_count,
            self._failed_count,
            len(self._enqueued_keys),
        )
        return self._resolved_count

    def _abandon_pending_queue_items(self) -> None:
        abandoned_count = 0
        while True:
            try:
                listing = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            if listing is not _SHUTDOWN_SENTINEL:
                abandoned_count += 1
                _LOGGER.warning(
                    "Skipping CoinGecko website resolution for %s %s (shutdown timeout)",
                    listing.exchange,
                    listing.symbol,
                )
            self._queue.task_done()
        if abandoned_count > 0:
            _LOGGER.warning(
                "Abandoned %s pending CoinGecko website resolution(s) due to shutdown timeout",
                abandoned_count,
            )

    async def _consumer_loop(self) -> None:
        while True:
            listing = await self._queue.get()
            try:
                if listing is _SHUTDOWN_SENTINEL:
                    break
                try:
                    await self._resolve_listing(listing)
                except Exception:
                    self._failed_count += 1
                    _LOGGER.exception(
                        "Website resolution failed for %s %s",
                        listing.exchange,
                        listing.symbol,
                    )
            finally:
                self._queue.task_done()

    async def _resolve_listing(self, listing: models.ListingRecord) -> None:
        if not listing.base:
            base, _quote = listings_store.parse_base_quote_from_symbol(listing.symbol)
            listing.base = base
        async with self._coingecko_lock:
            resolution = await self._website_finder.resolve_website(
                self._coingecko_client,
                listing.full_name,
                listing.base,
            )
        website_resolution.apply_resolution_to_listing(listing, resolution)
        async with self._listings_csv_lock:
            self._store.append_or_update([listing])
        self._resolved_count += 1
        progress.maybe_log_enrichment_progress(
            "CoinGecko website",
            self._resolved_count,
            len(self._enqueued_keys),
        )
        _LOGGER.info(
            "Website resolution for %s %s: website=%s status=%s",
            listing.exchange,
            listing.symbol,
            listing.website or "none",
            listing.website_resolution_status or "resolved",
        )
