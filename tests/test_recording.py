from datetime import UTC, datetime
from pathlib import Path

from gway_sound import recording


def test_recording_path_is_sortable_and_partitioned(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GWAY_SOUND_DATA_DIR", str(tmp_path))
    when = datetime(2026, 9, 9, 12, 34, 56, 789000, tzinfo=UTC)

    target = recording.path(when=when, source="jabra")

    assert target == (
        tmp_path / "recordings" / "2026" / "09" / "09" / "20260909T123456.789+0000-jabra.wav"
    )


def test_recording_path_sanitizes_source(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GWAY_SOUND_DATA_DIR", str(tmp_path))
    when = datetime(2026, 9, 9, tzinfo=UTC)

    assert recording.path(when=when, source="USB Mic #1").name.endswith("-USB-Mic--1.wav")
