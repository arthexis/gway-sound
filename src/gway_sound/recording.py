"""Recording archive and capture operations."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path

from . import capture
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


def record(
    seconds: float | None = None,
    source: str | None = None,
    name: str | None = None,
    rate: int = 16000,
    channels: int = 1,
) -> dict[str, object]:
    """Record from the default or explicitly selected source into the archive."""
    if seconds is not None and seconds <= 0:
        raise ValueError("seconds must be greater than zero")
    if rate <= 0:
        raise ValueError("rate must be greater than zero")
    if channels <= 0:
        raise ValueError("channels must be greater than zero")

    target = path(source=name)
    process = capture.start(target, source=source, rate=rate, channels=channels)
    result: dict[str, object] = {
        "path": os.fspath(target),
        "pid": process.pid,
        "source": source,
        "rate": rate,
        "channels": channels,
        "recording": True,
    }
    if seconds is None:
        return result

    try:
        process.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait()
    finally:
        capture.clear_state(process.pid)
    result["recording"] = False
    result["seconds"] = seconds
    return result


def stop() -> dict[str, object]:
    """Stop the active recording process, if any."""
    return capture.stop()


def recordings() -> list[str]:
    """List archived recordings newest first."""
    root = recordings_root()
    if not root.is_dir():
        return []
    files = [candidate for candidate in root.rglob("*") if candidate.is_file()]
    return [os.fspath(candidate) for candidate in sorted(files, reverse=True)]


def _safe_source(source: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in "-_" else "-" for character in source
    )
    cleaned = cleaned.strip("-")
    if not cleaned:
        raise ValueError("recording source must contain at least one letter or number")
    return cleaned
