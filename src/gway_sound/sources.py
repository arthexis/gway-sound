"""Generic audio capture source discovery."""

from __future__ import annotations

import shutil
import subprocess


def sources() -> list[str]:
    """Return non-monitor PulseAudio/PipeWire capture source names."""
    if shutil.which("pactl") is None:
        return []
    process = subprocess.run(
        ["pactl", "list", "short", "sources"],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        return []

    result: list[str] = []
    for line in process.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        name = parts[1].strip()
        if name and ".monitor" not in name.lower():
            result.append(name)
    return result
