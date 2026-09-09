"""Basic reusable sound playback without committing to a long-term backend API."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
from pathlib import Path

from .storage import resolve


def _runtime_root() -> Path:
    root = os.environ.get("XDG_RUNTIME_DIR")
    if root:
        return Path(root) / "gway-sound"
    return Path("/tmp") / f"gway-sound-{os.getuid()}"


def _state_path() -> Path:
    return _runtime_root() / "player.json"


def _player_command(sound_path: Path) -> list[str]:
    suffix = sound_path.suffix.lower()
    candidates: list[list[str]] = []
    if suffix == ".wav":
        candidates.extend(
            [
                ["pw-play", os.fspath(sound_path)],
                ["aplay", "-q", os.fspath(sound_path)],
                ["paplay", os.fspath(sound_path)],
            ]
        )
    candidates.extend(
        [
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", os.fspath(sound_path)],
            ["mpv", "--no-video", "--really-quiet", os.fspath(sound_path)],
            ["play", "-q", os.fspath(sound_path)],
        ]
    )
    for command in candidates:
        executable = shutil.which(command[0])
        if executable:
            command[0] = executable
            return command
    raise RuntimeError(
        "no supported audio player found (pw-play, aplay, paplay, ffplay, mpv, play)"
    )


def _write_state(process: subprocess.Popen[bytes], command: list[str]) -> None:
    root = _runtime_root()
    root.mkdir(parents=True, exist_ok=True)
    payload = {"pid": process.pid, "executable": Path(command[0]).name}
    _state_path().write_text(json.dumps(payload), encoding="utf-8")


def _clear_state(pid: int | None = None) -> None:
    state = _state_path()
    if not state.exists():
        return
    if pid is not None:
        try:
            current = json.loads(state.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            current = {}
        if current.get("pid") != pid:
            return
    state.unlink(missing_ok=True)


def play(value: str | Path, *, wait: bool = True) -> dict[str, object]:
    """Play a reusable sound name or explicit audio file path."""
    sound_path = resolve(value)
    command = _player_command(sound_path)
    process = subprocess.Popen(command)
    _write_state(process, command)
    if wait:
        returncode = process.wait()
        _clear_state(process.pid)
        if returncode:
            raise RuntimeError(f"audio player exited with status {returncode}")
    return {"path": os.fspath(sound_path), "pid": process.pid, "wait": wait}


def stop() -> dict[str, object]:
    """Stop the most recently started gway-sound playback process."""
    state = _state_path()
    if not state.exists():
        return {"stopped": False}
    try:
        payload = json.loads(state.read_text(encoding="utf-8"))
        pid = int(payload["pid"])
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        _clear_state()
        return {"stopped": False}

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        _clear_state(pid)
        return {"stopped": False}
    _clear_state(pid)
    return {"stopped": True, "pid": pid}
