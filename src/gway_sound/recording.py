"""Recording archive naming helpers.

Capture itself is intentionally outside PR1; this module only defines where a
future recorder should write files.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .storage import recordings_root


def path(
    *,
    when: datetime | None = None,
    source: str | None = None,
    suffix: str = ".wav",
) -> Path:
    """Return a sortable archive path for a new recording without creating it."""
    moment = when or datetime.now().astimezone()
    if moment.tzinfo is None:
        moment = moment.astimezone()

    normalized_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    timestamp = moment.strftime("%Y%m%dT%H%M%S.%f")[:-3]
    offset = moment.strftime("%z") or "+0000"
    source_part = f"-{_safe_source(source)}" if source else ""
    filename = f"{timestamp}{offset}{source_part}{normalized_suffix}"
    return recordings_root() / moment.strftime("%Y/%m/%d") / filename


def _safe_source(source: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in "-_" else "-" for character in source
    )
    cleaned = cleaned.strip("-")
    if not cleaned:
        raise ValueError("recording source must contain at least one letter or number")
    return cleaned
