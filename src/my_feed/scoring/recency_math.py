"""Time-decay helpers for recency / hybrid scoring."""

from __future__ import annotations

from datetime import UTC, datetime

DEFAULT_HALF_LIFE_HOURS = 36.0
DEFAULT_NEUTRAL_RECENCY = 0.5


def _as_utc(dt: datetime) -> datetime:
    """Normalize naive datetimes to UTC so subtraction against aware ``now`` works.

    Adapters should prefer timezone-aware values; treating naive as UTC is a
    defensive default, not a claim that the upstream clock was UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def recency_factor(
    published_at: datetime | None,
    *,
    now: datetime,
    half_life_hours: float = DEFAULT_HALF_LIFE_HOURS,
    missing: float = DEFAULT_NEUTRAL_RECENCY,
) -> float:
    """Exponential decay from ``published_at``; missing timestamp → ``missing``."""
    if published_at is None:
        return missing
    published = _as_utc(published_at)
    now_utc = _as_utc(now)
    age_seconds = (now_utc - published).total_seconds()
    age_hours = max(0.0, age_seconds / 3600.0)
    if half_life_hours <= 0:
        return 0.0 if age_hours > 0 else 1.0
    return float(0.5 ** (age_hours / half_life_hours))
