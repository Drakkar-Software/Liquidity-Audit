import liquidity_audit.domain.contacts.cooldown as contact_cooldown
import liquidity_audit.domain.contacts.health_issues as contact_health_issues
import liquidity_audit.domain.models as models
import liquidity_audit.domain.website.website_resolution as website_resolution


def _liquidity_sort_key(record: models.ListingRecord) -> tuple[int, float]:
    issue_count = contact_health_issues.count_health_issues(record)
    liquidity_score = record.liquidity_score if record.liquidity_score is not None else 1.0
    return (-issue_count, liquidity_score)


def _is_within_selection_cooldown(
    record: models.ListingRecord,
    recent_selection_by_key: dict[tuple[str, str], models.SelectedHistoryRecord],
    cooldown_days: int,
) -> bool:
    recent_selection = recent_selection_by_key.get(record.key())
    if recent_selection is None:
        return False
    return contact_cooldown.is_within_cooldown(
        recent_selection.selected_at,
        cooldown_days,
    )


def _is_eligible_for_selection(
    record: models.ListingRecord,
    selected_keys: set[tuple[str, str]],
    recent_selection_by_key: dict[tuple[str, str], models.SelectedHistoryRecord],
    cooldown_days: int,
    *,
    require_website: bool = True,
) -> bool:
    listing_key = record.key()
    if listing_key in selected_keys:
        return False
    if not record.is_low_health or not record.has_health_metrics():
        return False
    if _is_within_selection_cooldown(record, recent_selection_by_key, cooldown_days):
        return False
    if require_website:
        if not website_resolution.is_selectable_by_website_info(record):
            return False
    return True


def _is_eligible_for_new_listing_selection(
    record: models.ListingRecord,
    new_listing_keys: set[tuple[str, str]],
    selected_keys: set[tuple[str, str]],
    recent_selection_by_key: dict[tuple[str, str], models.SelectedHistoryRecord],
    cooldown_days: int,
    *,
    require_website: bool = True,
) -> bool:
    listing_key = record.key()
    if listing_key not in new_listing_keys:
        return False
    if listing_key in selected_keys:
        return False
    if _is_within_selection_cooldown(record, recent_selection_by_key, cooldown_days):
        return False
    if require_website:
        if not website_resolution.is_selectable_by_website_info(record):
            return False
    return True


def is_website_resolution_candidate(
    record: models.ListingRecord,
    new_listing_keys: set[tuple[str, str]],
    recent_selection_by_key: dict[tuple[str, str], models.SelectedHistoryRecord],
    cooldown_days: int,
) -> bool:
    empty_selected_keys: set[tuple[str, str]] = set()
    if record.key() in new_listing_keys:
        return _is_eligible_for_new_listing_selection(
            record,
            new_listing_keys,
            empty_selected_keys,
            recent_selection_by_key,
            cooldown_days,
            require_website=False,
        )
    return _is_eligible_for_selection(
        record,
        empty_selected_keys,
        recent_selection_by_key,
        cooldown_days,
        require_website=False,
    )


def _selection_tier_for_new_listing(record: models.ListingRecord) -> str:
    if record.is_low_health:
        return models.SELECTION_TIER_NEW_LOW_HEALTH
    return models.SELECTION_TIER_NEW_LISTING


def _select_phase_new_listings(
    all_records: dict[tuple[str, str], models.ListingRecord],
    new_listing_keys: set[tuple[str, str]],
    selected_keys: set[tuple[str, str]],
    recent_selection_by_key: dict[tuple[str, str], models.SelectedHistoryRecord],
    cooldown_days: int,
) -> list[models.DailyProjectSelection]:
    candidates = [
        record for record in all_records.values()
        if _is_eligible_for_new_listing_selection(
            record,
            new_listing_keys,
            selected_keys,
            recent_selection_by_key,
            cooldown_days,
        )
    ]
    candidates.sort(key=_liquidity_sort_key)
    selections: list[models.DailyProjectSelection] = []
    for record in candidates:
        selected_keys.add(record.key())
        selections.append(models.DailyProjectSelection(
            record=record,
            selection_tier=_selection_tier_for_new_listing(record),
            is_new_listing=True,
        ))
    return selections


def _select_phase_existing_diversified(
    all_records: dict[tuple[str, str], models.ListingRecord],
    new_listing_keys: set[tuple[str, str]],
    selected_keys: set[tuple[str, str]],
    recent_selection_by_key: dict[tuple[str, str], models.SelectedHistoryRecord],
    cooldown_days: int,
    remaining_slots: int,
) -> list[models.DailyProjectSelection]:
    eligible_existing = [
        record for listing_key, record in all_records.items()
        if listing_key not in new_listing_keys
        and _is_eligible_for_selection(
            record,
            selected_keys,
            recent_selection_by_key,
            cooldown_days,
        )
    ]
    label_groups: dict[str, list[models.ListingRecord]] = {}
    for record in eligible_existing:
        label_group = record.health_label_primary or "unknown"
        label_groups.setdefault(label_group, []).append(record)
    for group_candidates in label_groups.values():
        group_candidates.sort(key=_liquidity_sort_key)

    selections: list[models.DailyProjectSelection] = []
    while remaining_slots > len(selections) and label_groups:
        progressed = False
        for label_group in sorted(label_groups.keys()):
            group_candidates = label_groups[label_group]
            while group_candidates and not _is_eligible_for_selection(
                group_candidates[0],
                selected_keys,
                recent_selection_by_key,
                cooldown_days,
            ):
                group_candidates.pop(0)
            if not group_candidates:
                continue
            picked_record = group_candidates.pop(0)
            if not group_candidates:
                del label_groups[label_group]
            selected_keys.add(picked_record.key())
            selections.append(models.DailyProjectSelection(
                record=picked_record,
                selection_tier=models.SELECTION_TIER_EXISTING_DIVERSIFIED,
                is_new_listing=False,
            ))
            progressed = True
            if remaining_slots <= len(selections):
                break
        if not progressed:
            break
    return selections


def _select_phase_existing_fill(
    all_records: dict[tuple[str, str], models.ListingRecord],
    new_listing_keys: set[tuple[str, str]],
    selected_keys: set[tuple[str, str]],
    recent_selection_by_key: dict[tuple[str, str], models.SelectedHistoryRecord],
    cooldown_days: int,
    remaining_slots: int,
) -> list[models.DailyProjectSelection]:
    candidates = [
        record for listing_key, record in all_records.items()
        if listing_key not in new_listing_keys
        and _is_eligible_for_selection(
            record,
            selected_keys,
            recent_selection_by_key,
            cooldown_days,
        )
    ]
    candidates.sort(key=_liquidity_sort_key)
    selections: list[models.DailyProjectSelection] = []
    for record in candidates[:remaining_slots]:
        selected_keys.add(record.key())
        selections.append(models.DailyProjectSelection(
            record=record,
            selection_tier=models.SELECTION_TIER_EXISTING_FILL,
            is_new_listing=False,
        ))
    return selections


def select_daily_projects(
    all_records: dict[tuple[str, str], models.ListingRecord],
    new_listing_keys: set[tuple[str, str]],
    recent_selection_by_key: dict[tuple[str, str], models.SelectedHistoryRecord],
    max_per_day: int,
    cooldown_days: int,
) -> list[models.DailyProjectSelection]:
    if max_per_day <= 0:
        return []

    selected_keys: set[tuple[str, str]] = set()
    selections: list[models.DailyProjectSelection] = []

    phase_one = _select_phase_new_listings(
        all_records,
        new_listing_keys,
        selected_keys,
        recent_selection_by_key,
        cooldown_days,
    )
    selections.extend(phase_one)

    remaining_slots = max(0, max_per_day - len(selections))
    if remaining_slots > 0:
        phase_two = _select_phase_existing_diversified(
            all_records,
            new_listing_keys,
            selected_keys,
            recent_selection_by_key,
            cooldown_days,
            remaining_slots,
        )
        selections.extend(phase_two)

    remaining_slots = max(0, max_per_day - len(selections))
    if remaining_slots > 0:
        phase_three = _select_phase_existing_fill(
            all_records,
            new_listing_keys,
            selected_keys,
            recent_selection_by_key,
            cooldown_days,
            remaining_slots,
        )
        selections.extend(phase_three)

    return selections
