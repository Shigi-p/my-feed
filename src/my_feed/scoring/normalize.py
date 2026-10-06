"""Per-source popularity normalization (never compare raw likes across sources)."""

from __future__ import annotations

from collections import defaultdict
from typing import Literal

from my_feed.models import Item

NormalizeMethod = Literal["minmax", "rank"]

# Preferred metric keys in priority order (sources expose different names).
# First hit wins — e.g. an item with both likes and stocks uses likes only.
# Note: GitHub adapters may also expose ``stars_today``; it is intentionally
# NOT in this list today (all-time ``stars`` wins). Promote stars_today only
# after an explicit product decision.
POPULARITY_METRIC_KEYS: tuple[str, ...] = ("likes", "stocks", "stars", "forks")

DEFAULT_NEUTRAL = 0.5


def extract_popularity(metrics: dict[str, float | int]) -> float | None:
    """Return a popularity signal from metrics, or None if absent."""
    for key in POPULARITY_METRIC_KEYS:
        if key in metrics:
            return float(metrics[key])
    return None


def _minmax(values: list[float]) -> list[float]:
    """Map values to 0..1.

    Tied or single-value cohorts → 1.0 for every present member. That means a
    source that contributes only one item to a cross-source Top-N run gets a
    perfect popularity component — known skew; switch to rank or dampen later
    if it dominates hybrid rankings in practice.
    """
    lo = min(values)
    hi = max(values)
    if hi == lo:
        return [1.0] * len(values)
    span = hi - lo
    return [(v - lo) / span for v in values]


def _rank(values: list[float]) -> list[float]:
    """Dense rank mapped to 0..1 (highest value → 1.0). Ties share average rank."""
    n = len(values)
    if n == 1:
        return [1.0]
    # Sort indices by value ascending; average ranks for ties.
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    denom = n - 1
    return [r / denom for r in ranks]


def normalize_values(
    values: list[float | None],
    *,
    method: NormalizeMethod = "minmax",
    neutral: float = DEFAULT_NEUTRAL,
) -> list[float]:
    """Normalize a list that may contain None (missing) entries.

    Present values are normalized among themselves; missing → ``neutral``.
    If every value is missing, all become ``neutral``.
    """
    present_idx = [i for i, v in enumerate(values) if v is not None]
    out = [neutral] * len(values)
    if not present_idx:
        return out
    present = [float(values[i]) for i in present_idx]  # type: ignore[arg-type]
    mapped = _minmax(present) if method == "minmax" else _rank(present)
    for i, score in zip(present_idx, mapped, strict=True):
        out[i] = score
    return out


def normalize_popularity_by_source(
    items: list[Item],
    *,
    method: NormalizeMethod = "minmax",
    neutral: float = DEFAULT_NEUTRAL,
) -> dict[str, float]:
    """Return ``item.id →`` popularity in 0..1, normalized within each source."""
    by_source: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        by_source[item.source.value].append(item)

    result: dict[str, float] = {}
    for group in by_source.values():
        raw = [extract_popularity(item.metrics) for item in group]
        norms = normalize_values(raw, method=method, neutral=neutral)
        for item, score in zip(group, norms, strict=True):
            result[item.id] = score
    return result
