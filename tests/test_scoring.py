"""Unit tests for T-Score normalize helpers and strategies (no network)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from my_feed.config import load_config
from my_feed.models import Item, SourceName
from my_feed.scoring import get_scorer, list_scorers
from my_feed.scoring.base import ScoreStrategy
from my_feed.scoring.hybrid import HybridScoreStrategy
from my_feed.scoring.normalize import (
    extract_popularity,
    normalize_popularity_by_source,
    normalize_values,
)
from my_feed.scoring.popularity import PopularityScoreStrategy
from my_feed.scoring.recency import RecencyScoreStrategy
from my_feed.scoring.recency_math import recency_factor


def _item(
    *,
    source: SourceName,
    oid: str,
    likes: float | int | None = None,
    stars: float | int | None = None,
    published_at: datetime | None = None,
    fetched_at: datetime | None = None,
) -> Item:
    now = fetched_at or datetime(2026, 10, 6, 12, 0, tzinfo=UTC)
    metrics: dict[str, float | int] = {}
    if likes is not None:
        metrics["likes"] = likes
    if stars is not None:
        metrics["stars"] = stars
    return Item(
        id=f"{source.value}:{oid}",
        source=source,
        title=f"{source.value} {oid}",
        url=f"https://example.com/{source.value}/{oid}",
        published_at=published_at,
        metrics=metrics,
        fetched_at=now,
    )


# --- normalize ---


def test_extract_popularity_prefers_likes_then_stars():
    assert extract_popularity({"likes": 10, "stars": 99}) == 10.0
    assert extract_popularity({"stars": 7}) == 7.0
    assert extract_popularity({}) is None


def test_extract_popularity_prefers_stars_today_over_stars():
    assert extract_popularity({"stars_today": 12, "stars": 9999}) == 12.0
    assert extract_popularity({"stars_today": 3}) == 3.0


def test_normalize_minmax_maps_within_cohort():
    assert normalize_values([10.0, 20.0, 30.0], method="minmax") == pytest.approx([0.0, 0.5, 1.0])


def test_normalize_minmax_equal_and_missing():
    assert normalize_values([5.0, 5.0], method="minmax") == pytest.approx([1.0, 1.0])
    assert normalize_values([None, None], neutral=0.5) == pytest.approx([0.5, 0.5])
    out = normalize_values([10.0, None, 30.0], method="minmax", neutral=0.5)
    assert out == pytest.approx([0.0, 0.5, 1.0])


def test_normalize_rank():
    # values 10, 30, 20 → ranks 0, 2, 1 → 0, 1, 0.5
    assert normalize_values([10.0, 30.0, 20.0], method="rank") == pytest.approx([0.0, 1.0, 0.5])


def test_normalize_popularity_by_source_is_independent():
    """Raw likes must not be compared across sources."""
    items = [
        _item(source=SourceName.ZENN, oid="1", likes=100),
        _item(source=SourceName.ZENN, oid="2", likes=50),
        _item(source=SourceName.QIITA, oid="1", likes=3),
        _item(source=SourceName.QIITA, oid="2", likes=1),
    ]
    norms = normalize_popularity_by_source(items, method="minmax")
    assert norms["zenn:1"] == pytest.approx(1.0)
    assert norms["zenn:2"] == pytest.approx(0.0)
    # Qiita's "3 likes" is max within Qiita → 1.0, not crushed by Zenn's 100
    assert norms["qiita:1"] == pytest.approx(1.0)
    assert norms["qiita:2"] == pytest.approx(0.0)


def test_normalize_missing_metrics_get_neutral():
    items = [
        _item(source=SourceName.GIGAZINE, oid="1"),
        _item(source=SourceName.GIGAZINE, oid="2", likes=10),
        _item(source=SourceName.GIGAZINE, oid="3", likes=20),
    ]
    norms = normalize_popularity_by_source(items, method="minmax", neutral=0.5)
    assert norms["gigazine:1"] == pytest.approx(0.5)
    assert norms["gigazine:2"] == pytest.approx(0.0)
    assert norms["gigazine:3"] == pytest.approx(1.0)


# --- recency math ---


def test_recency_factor_half_life():
    now = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)
    assert recency_factor(now, now=now, half_life_hours=36) == pytest.approx(1.0)
    aged = now - timedelta(hours=36)
    assert recency_factor(aged, now=now, half_life_hours=36) == pytest.approx(0.5)
    assert recency_factor(None, now=now) == pytest.approx(0.5)


# --- strategies ---


def test_registry_has_all_scorers():
    names = list_scorers()
    assert names == ["fake", "hybrid", "popularity", "recency"]
    for name in names:
        scorer = get_scorer(name)
        assert isinstance(scorer, ScoreStrategy)
        assert scorer.name == name


def test_popularity_strategy_orders_by_norm_within_source():
    items = [
        _item(source=SourceName.ZENN, oid="low", likes=1),
        _item(source=SourceName.ZENN, oid="high", likes=100),
        _item(source=SourceName.QIITA, oid="mid", likes=5),
    ]
    scored = PopularityScoreStrategy().score(items)
    by_id = {s.item.id: s for s in scored}
    # Each source's top (or sole) item maps to 1.0 — raw 5 vs 100 must not matter.
    assert by_id["zenn:high"].score == pytest.approx(1.0)
    assert by_id["qiita:mid"].score == pytest.approx(1.0)
    assert by_id["zenn:low"].score == pytest.approx(0.0)
    assert scored[-1].item.id == "zenn:low"
    assert scored == sorted(scored, key=lambda s: (-s.score, s.item.id))


def test_recency_strategy_prefers_newer():
    now = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)
    items = [
        _item(
            source=SourceName.ZENN,
            oid="old",
            likes=999,
            published_at=now - timedelta(hours=72),
            fetched_at=now,
        ),
        _item(
            source=SourceName.ZENN,
            oid="new",
            likes=1,
            published_at=now - timedelta(hours=1),
            fetched_at=now,
        ),
    ]
    scored = RecencyScoreStrategy(now=now, half_life_hours=36).score(items)
    assert scored[0].item.id == "zenn:new"
    assert scored[0].score > scored[1].score


def test_hybrid_combines_popularity_and_recency():
    now = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)
    items = [
        # High likes but very old → weaker hybrid
        _item(
            source=SourceName.ZENN,
            oid="stale-hit",
            likes=100,
            published_at=now - timedelta(hours=72),
            fetched_at=now,
        ),
        # Mid likes, fresh → wins (needs a third Zenn item so mid ≠ min→0)
        _item(
            source=SourceName.ZENN,
            oid="fresh-mid",
            likes=70,
            published_at=now - timedelta(hours=1),
            fetched_at=now,
        ),
        _item(
            source=SourceName.ZENN,
            oid="anchor-low",
            likes=40,
            published_at=now - timedelta(hours=1),
            fetched_at=now,
        ),
        # No metrics (gigazine-like): neutral pop × recency
        _item(
            source=SourceName.GIGAZINE,
            oid="fresh",
            published_at=now - timedelta(hours=1),
            fetched_at=now,
        ),
    ]
    scored = HybridScoreStrategy(now=now, half_life_hours=36).score(items)
    by_id = {s.item.id: s for s in scored}
    # stale: pop=1.0 * 0.25 = 0.25; fresh-mid: pop=0.5 * ~0.98 ≈ 0.49
    assert by_id["zenn:fresh-mid"].score > by_id["zenn:stale-hit"].score
    assert by_id["gigazine:fresh"].score_breakdown["norm_popularity"] == pytest.approx(0.5)
    assert scored == sorted(scored, key=lambda s: (-s.score, s.item.id))


def test_scoring_config_keys_load(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        "\n".join(
            [
                "top_n = 10",
                'default_scorer = "hybrid"',
                'enabled_sources = ["fake"]',
                "[scoring.hybrid]",
                "recency_half_life_hours = 24",
                "neutral_popularity_when_missing = 0.4",
                "",
            ]
        ),
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.default_scorer == "hybrid"
    assert config.scoring.hybrid.recency_half_life_hours == 24
    assert config.scoring.hybrid.neutral_popularity_when_missing == 0.4


def test_build_scorer_applies_config_knobs(tmp_path):
    from my_feed.scoring import build_scorer

    path = tmp_path / "config.toml"
    path.write_text(
        "\n".join(
            [
                'default_scorer = "hybrid"',
                'enabled_sources = ["fake"]',
                "[scoring.hybrid]",
                "recency_half_life_hours = 12",
                "neutral_popularity_when_missing = 0.25",
                "",
            ]
        ),
        encoding="utf-8",
    )
    config = load_config(path)
    hybrid = build_scorer("hybrid", config)
    assert isinstance(hybrid, HybridScoreStrategy)
    assert hybrid._half_life_hours == 12
    assert hybrid._neutral_popularity == 0.25
    popularity = build_scorer("popularity", config)
    assert popularity._neutral == 0.25


def test_recency_factor_accepts_naive_published_at():
    now = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)
    naive = datetime(2026, 10, 6, 6, 0)  # treated as UTC
    assert recency_factor(naive, now=now, half_life_hours=6) == pytest.approx(0.5)
