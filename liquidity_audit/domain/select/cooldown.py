import datetime


def parse_selected_at(selected_at: str) -> datetime.datetime:
    parsed = datetime.datetime.fromisoformat(selected_at)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=datetime.UTC)
    return parsed.astimezone(datetime.UTC)


def is_within_cooldown(
    selected_at: str,
    cooldown_days: int,
    now: datetime.datetime | None = None,
) -> bool:
    if now is None:
        now = datetime.datetime.now(datetime.UTC)
    selected_time = parse_selected_at(selected_at)
    elapsed = now - selected_time
    return elapsed < datetime.timedelta(days=cooldown_days)
