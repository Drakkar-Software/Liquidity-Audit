import dataclasses
import typing


@dataclasses.dataclass
class HealthResult:
    bid_levels: int
    ask_levels: int
    bid_depth_quote: float
    ask_depth_quote: float
    bid_larger_depth_quote: float
    ask_larger_depth_quote: float
    bid_total_depth_quote: float
    ask_total_depth_quote: float
    volume_quote: typing.Optional[float]
    bid_ask_spread_ratio: typing.Optional[float]
    liquidity_score: float
    is_low_health: bool
    health_label_primary: str = ""
    health_labels_other: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class FailedListingEnrichment:
    exchange: str
    symbol: str
    error: str


SELECTION_TIER_NEW_LISTING = "new_listing"
SELECTION_TIER_NEW_LOW_HEALTH = "new_low_health"
SELECTION_TIER_EXISTING_DIVERSIFIED = "existing_diversified"
SELECTION_TIER_EXISTING_FILL = "existing_fill"


@dataclasses.dataclass
class RunSummary:
    new_listings_total: int
    new_low_health_count: int
    selections_proposed_total: int
    selections_proposed_new: int
    selections_proposed_existing: int
    failed_enrichments_count: int
    websites_resolved_count: int = 0


@dataclasses.dataclass
class DailyProjectSelection:
    record: "ListingRecord"
    selection_tier: str
    is_new_listing: bool


@dataclasses.dataclass
class SelectedHistoryRecord:
    selected_at: str
    exchange: str
    symbol: str
    full_name: str
    is_new_listing: bool
    selection_tier: str
    is_low_health: bool
    health_label_primary: typing.Optional[str]
    health_labels_other: typing.Optional[list[str]]
    issue_count: int
    bid_levels: typing.Optional[int]
    ask_levels: typing.Optional[int]
    bid_depth_quote: typing.Optional[float]
    ask_depth_quote: typing.Optional[float]
    bid_larger_depth_quote: typing.Optional[float]
    ask_larger_depth_quote: typing.Optional[float]
    bid_total_depth_quote: typing.Optional[float]
    ask_total_depth_quote: typing.Optional[float]
    volume_quote: typing.Optional[float]
    bid_ask_spread_ratio: typing.Optional[float]
    liquidity_score: typing.Optional[float]
    website: typing.Optional[str] = None
    coingecko_id: typing.Optional[str] = None
    website_resolution_status: typing.Optional[str] = None

    def key(self) -> tuple[str, str]:
        return (self.exchange, self.symbol)


@dataclasses.dataclass
class DailyRunResult:
    run_summary: RunSummary
    daily_selections: list[DailyProjectSelection]
    new_listings: list["ListingRecord"]
    failed_enrichments: list[FailedListingEnrichment]


@dataclasses.dataclass
class ListingRecord:
    exchange: str
    symbol: str
    base: str
    quote: str
    full_name: str
    bid_levels: typing.Optional[int] = None
    ask_levels: typing.Optional[int] = None
    bid_depth_quote: typing.Optional[float] = None
    ask_depth_quote: typing.Optional[float] = None
    bid_larger_depth_quote: typing.Optional[float] = None
    ask_larger_depth_quote: typing.Optional[float] = None
    bid_total_depth_quote: typing.Optional[float] = None
    ask_total_depth_quote: typing.Optional[float] = None
    volume_quote: typing.Optional[float] = None
    bid_ask_spread_ratio: typing.Optional[float] = None
    liquidity_score: typing.Optional[float] = None
    is_low_health: bool = False
    health_label_primary: typing.Optional[str] = None
    health_labels_other: typing.Optional[list[str]] = None
    delisting_risk: typing.Optional[list[str]] = None
    first_seen_at: typing.Optional[str] = None
    last_checked_at: typing.Optional[str] = None
    last_analyzed_at: typing.Optional[str] = None
    score_100: typing.Optional[int] = None
    spread_pct: typing.Optional[float] = None
    depth_2pct_quote: typing.Optional[float] = None
    bid_volume_quote: typing.Optional[float] = None
    ask_volume_quote: typing.Optional[float] = None
    max_fillable_buy_quote: typing.Optional[float] = None
    slippage_10k_pct: typing.Optional[float] = None
    analysis_json_path: typing.Optional[str] = None
    delisted_at: typing.Optional[str] = None
    website: typing.Optional[str] = None
    coingecko_id: typing.Optional[str] = None
    website_resolution_status: typing.Optional[str] = None
    coingecko_candidates_json: typing.Optional[str] = None

    def key(self) -> tuple[str, str]:
        return (self.exchange, self.symbol)

    def has_health_metrics(self) -> bool:
        return self.bid_levels is not None
