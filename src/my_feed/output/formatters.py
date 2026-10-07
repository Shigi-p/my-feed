"""Rule-based text helpers for markdown paste templates (no LLM)."""

from __future__ import annotations

import html
import re
from datetime import UTC, datetime

from my_feed.models import Item, ScoredItem, SourceName

_TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)
_WS_RE = re.compile(r"\s+")

# Soft limits for paste-friendly excerpts.
_MAX_SENTENCES = 3
_MAX_CHARS = 280

_SOURCE_HINTS: dict[SourceName, str] = {
    SourceName.ZENN: "Zenn で話題の技術記事",
    SourceName.QIITA: "Qiita でストックされやすい実践知見",
    SourceName.GIGAZINE: "Gigazine の速報・解説系トピック",
    SourceName.GITHUB_TRENDING: "GitHub Trending の注目リポジトリ",
    SourceName.FAKE: "開発用の偽ソース記事",
}

DEFAULT_GEMINI_INTRO = (
    "以下を Gemini / ChatGPT に貼り付けて、気になる記事について深掘り・反論・実践案を壁打ちしてください。"
)


def strip_html(text: str) -> str:
    """Remove HTML tags and unescape entities; collapse whitespace."""
    if not text:
        return ""
    plain = _TAG_RE.sub(" ", text)
    plain = html.unescape(plain)
    return _WS_RE.sub(" ", plain).strip()


def format_excerpt(
    raw: str,
    *,
    max_sentences: int = _MAX_SENTENCES,
    max_chars: int = _MAX_CHARS,
) -> str:
    """HTML-stripped excerpt, capped to a few sentences / characters.

    Returns an empty string when input is empty after stripping (caller may
    show a placeholder).
    """
    plain = strip_html(raw)
    if not plain:
        return ""

    parts = [p.strip() for p in re.split(r"(?<=[。．！？!?])\s*|(?<=\.)\s+", plain) if p.strip()]
    if not parts:
        parts = [plain]

    selected: list[str] = []
    total = 0
    for part in parts:
        if len(selected) >= max_sentences:
            break
        if selected and total + len(part) + 1 > max_chars:
            break
        selected.append(part)
        total += len(part) + (1 if len(selected) > 1 else 0)

    text = " ".join(selected) if len(selected) > 1 else selected[0]
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    return text


def _hours_ago(published_at: datetime | None, now: datetime) -> float | None:
    if published_at is None:
        return None
    ts = published_at
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    ref = now if now.tzinfo else now.replace(tzinfo=UTC)
    return max(0.0, (ref - ts).total_seconds() / 3600.0)


def value_line(scored: ScoredItem, *, now: datetime | None = None) -> str:
    """One-liner: why look at this item now (score / source / recency templates).

    Optionally annotates ``score_breakdown`` (e.g. T-Score keys like
    ``norm_popularity`` / ``recency_factor`` / ``hybrid``). Missing or differently
    named keys just omit the parenthetical — do not hard-fail on scorer shape.
    """
    item = scored.item
    ref = now or datetime.now(UTC)
    hours = _hours_ago(item.published_at, ref)
    source_hint = _SOURCE_HINTS.get(item.source, f"{item.source.value} の記事")

    if hours is None:
        recency_bit = "公開時刻は不明だが、いまのスコア圏に入っている"
    elif hours < 24:
        recency_bit = f"直近 {hours:.0f} 時間以内の新鮮な話題"
    elif hours < 72:
        recency_bit = f"ここ {hours / 24:.1f} 日以内の動き"
    else:
        recency_bit = f"公開から {hours / 24:.0f} 日経過だがスコア上位"

    score = scored.score
    if score >= 0.8:
        score_bit = f"スコア {score:.2f} で上位"
    elif score >= 0.5:
        score_bit = f"スコア {score:.2f} で注目圏"
    else:
        score_bit = f"スコア {score:.2f}（補助枠）"

    breakdown = scored.score_breakdown
    extra = ""
    if breakdown:
        # Keys are scorer-defined strings; take the largest numeric component for a hint.
        top_key, top_val = max(breakdown.items(), key=lambda kv: kv[1])
        extra = f"（内訳トップ: {top_key}={top_val:.2f}）"

    return f"{score_bit}。{source_hint}として、{recency_bit}。{extra}".rstrip("。") + "。"


def brainstorm_prompts(item: Item) -> list[str]:
    """2–3 fixed brainstorming questions for Gemini/ChatGPT paste."""
    title = (item.title or "この記事").strip() or "この記事"
    tags = ", ".join(item.tags[:5]) if item.tags else ""

    summary = f"「{title}」の主張を 3 点で要約し、自分の現プロジェクトに効く / 効かない理由を分けてください。"
    if tags:
        summary = (
            f"「{title}」（タグ: {tags}）の主張を 3 点で要約し、"
            "自分の現プロジェクトに効く / 効かない理由を分けてください。"
        )

    return [
        summary,
        f"「{title}」に対する反論や見落としリスクを 2 つ挙げ、検証手順を短く提案してください。",
        f"「{title}」を来週試すなら、半日で終わる最小実験プランをステップで書いてください。",
    ]


def format_generated_at(dt: datetime) -> str:
    """Stable UTC stamp for bundle headers (YYYY-MM-DD HH:mm)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%d %H:%M")
