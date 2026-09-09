"""GWAY command adapter for core sound operations."""

from __future__ import annotations

import os
from pathlib import Path

from . import playback, storage


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


def stop() -> dict[str, object]:
    """Stop the most recently started gway-sound playback process."""
    return playback.stop()
