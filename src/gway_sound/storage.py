"""Filesystem layout and reusable sound resolution."""

from __future__ import annotations

import os
from pathlib import Path

_DEFAULT_DATA_ROOT = Path("/var/lib/gway/sound")
_DEFAULT_CONFIG_ROOT = Path("/etc/gway/sound")
_AUDIO_SUFFIXES = (".wav", ".mp3", ".ogg", ".flac")


def data_root() -> Path:
    """Return the canonical mutable data root."""
    return Path(os.environ.get("GWAY_SOUND_DATA_DIR", _DEFAULT_DATA_ROOT))


def sounds_root() -> Path:
    """Return the canonical shared reusable-sound directory."""
    return data_root() / "sounds"


def recordings_root() -> Path:
    """Return the canonical recording archive directory."""
    return data_root() / "recordings"


def _configured_sounds_root() -> Path:
    configured = os.environ.get("GWAY_SOUND_SOUNDS_DIR")
    if configured:
        return Path(configured)
    return _DEFAULT_CONFIG_ROOT / "sounds"


def sound_roots() -> tuple[Path, ...]:
    """Return logical-name lookup roots in precedence order."""
    roots = (_configured_sounds_root(), sounds_root())
    return tuple(dict.fromkeys(roots))


def _candidates(root: Path, name: str) -> tuple[Path, ...]:
    candidate = root / name
    if candidate.suffix:
        return (candidate,)
    return (candidate, *(root / f"{name}{suffix}" for suffix in _AUDIO_SUFFIXES))


def resolve(value: str | Path) -> Path:
    """Resolve an explicit file path or reusable sound name to an existing file."""
    requested = Path(value).expanduser()
    if requested.is_file():
        return requested.resolve()

    text = os.fspath(value)
    if requested.is_absolute() or requested.parent != Path("."):
        raise FileNotFoundError(f"sound file not found: {requested}")

    for root in sound_roots():
        for candidate in _candidates(root, text):
            if candidate.is_file():
                return candidate.resolve()
    raise FileNotFoundError(f"sound not found: {text}")


def path(name: str) -> Path:
    """Return an existing reusable sound path, or its canonical shared target path."""
    try:
        return resolve(name)
    except FileNotFoundError:
        target = sounds_root() / name
        return target if target.suffix else target.with_suffix(".wav")


def sounds() -> list[str]:
    """List reusable sound filenames visible through the logical-name resolver."""
    visible: dict[str, Path] = {}
    for root in reversed(sound_roots()):
        if not root.is_dir():
            continue
        for candidate in root.iterdir():
            if candidate.is_file() and candidate.suffix.lower() in _AUDIO_SUFFIXES:
                visible[candidate.name] = candidate
    return sorted(visible)
