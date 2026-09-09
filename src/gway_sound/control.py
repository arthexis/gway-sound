"""Cross-cutting sound controls."""

from __future__ import annotations

from . import playback, recording


def stop() -> dict[str, object]:
    """Stop all active gway-sound playback and recording processes."""
    playback_result = playback.stop()
    recording_result = recording.stop()
    return {
        "stopped": bool(playback_result.get("stopped") or recording_result.get("stopped")),
        "playback": playback_result,
        "recording": recording_result,
    }
