"""Datetime parsing helpers for source adapters."""

from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from time import struct_time
from calendar import timegm


def parse_datetime(value: object) -> datetime | None:
    """Best-effort parse of common API / RSS datetime shapes to aware UTC."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if isinstance(value, struct_time):
        return datetime.fromtimestamp(timegm(value), tz=UTC)
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    # ISO-8601 (Qiita / Zenn): allow trailing Z
    iso = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except ValueError:
        pass
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except (TypeError, ValueError, IndexError):
        return None
