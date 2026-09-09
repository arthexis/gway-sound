"""Minimal generic audio capture process helpers."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
from pathlib import Path


def _runtime_root() -> Path:
    root = os.environ.get("XDG_RUNTIME_DIR")
    if root:
        return Path(root) / "gway-sound"
    return Path("/tmp") / f"gway-sound-{os.getuid()}"


def state_path() -> Path:
    """Return the cross-invocation recorder state path."""
    return _runtime_root() / "recorder.json"


def command(target: Path, *, source: str | None, rate: int, channels: int) -> list[str]:
    """Build a capture command using the first supported system recorder."""
    pw_record = shutil.which("pw-record")
    if pw_record:
        result = [pw_record, "--rate", str(rate), "--channels", str(channels)]
        if source:
            result.extend(["--target", source])
        result.append(os.fspath(target))
        return result

    parec = shutil.which("parec")
    if parec:
        result = [
            parec,
            "--file-format=wav",
            f"--rate={rate}",
            f"--channels={channels}",
        ]
        if source:
            result.append(f"--device={source}")
        result.append(os.fspath(target))
        return result

    raise RuntimeError("no supported audio recorder found (pw-record, parec)")


def start(target: Path, *, source: str | None, rate: int, channels: int) -> subprocess.Popen[bytes]:
    """Start recording to target and persist recorder state."""
    target.parent.mkdir(parents=True, exist_ok=True)
    capture_command = command(target, source=source, rate=rate, channels=channels)
    process = subprocess.Popen(capture_command)
    root = _runtime_root()
    root.mkdir(parents=True, exist_ok=True)
    state_path().write_text(
        json.dumps(
            {
                "pid": process.pid,
                "path": os.fspath(target),
                "source": source,
                "rate": rate,
                "channels": channels,
            }
        ),
        encoding="utf-8",
    )
    return process


def clear_state(pid: int | None = None) -> None:
    """Remove recorder state, optionally only when it belongs to pid."""
    state = state_path()
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


def stop() -> dict[str, object]:
    """Stop the current recording process, if any."""
    state = state_path()
    if not state.exists():
        return {"stopped": False}
    try:
        payload = json.loads(state.read_text(encoding="utf-8"))
        pid = int(payload["pid"])
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        clear_state()
        return {"stopped": False}

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        clear_state(pid)
        return {"stopped": False}
    clear_state(pid)
    return {"stopped": True, "pid": pid}
