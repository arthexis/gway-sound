"""GWAY command adapter for core sound operations."""

from __future__ import annotations

import os
from pathlib import Path

from . import control, playback, recording, storage
from .sources import sources as list_sources


def resolve(sound: str) -> str:
    """Resolve a reusable sound name or explicit path to an existing audio file."""
    return os.fspath(storage.resolve(sound))


def path(name: str) -> str:
    """Return the resolved or canonical shared path for a reusable sound name."""
    return os.fspath(storage.path(name))


def sounds() -> list[str]:
    """List reusable sound files currently visible to the resolver."""
    return storage.sounds()


def play(sound: str, wait: bool = True) -> dict[str, object]:
    """Play a reusable sound name or explicit file path."""
    return playback.play(Path(sound), wait=wait)


def record(
    seconds: float | None = None,
    source: str | None = None,
    name: str | None = None,
    rate: int = 16000,
    channels: int = 1,
) -> dict[str, object]:
    """Record from the default or explicitly selected capture source."""
    return recording.record(
        seconds=seconds,
        source=source,
        name=name,
        rate=rate,
        channels=channels,
    )


def recordings() -> list[str]:
    """List archived recordings newest first."""
    return recording.recordings()


def sources() -> list[str]:
    """List available non-monitor capture sources."""
    return list_sources()


def stop() -> dict[str, object]:
    """Stop all active gway-sound playback and recording processes."""
    return control.stop()
