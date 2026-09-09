from pathlib import Path

import pytest

from gway_sound import storage


def test_resolve_prefers_configured_sound_dir(monkeypatch, tmp_path: Path) -> None:
    configured = tmp_path / "configured"
    shared = tmp_path / "data" / "sounds"
    configured.mkdir()
    shared.mkdir(parents=True)
    (configured / "alert.wav").write_bytes(b"configured")
    (shared / "alert.wav").write_bytes(b"shared")

    monkeypatch.setenv("GWAY_SOUND_SOUNDS_DIR", str(configured))
    monkeypatch.setenv("GWAY_SOUND_DATA_DIR", str(tmp_path / "data"))

    assert storage.resolve("alert") == (configured / "alert.wav").resolve()


def test_resolve_accepts_explicit_path(tmp_path: Path) -> None:
    sound = tmp_path / "custom.ogg"
    sound.write_bytes(b"audio")

    assert storage.resolve(sound) == sound.resolve()


def test_path_returns_canonical_wav_target(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GWAY_SOUND_DATA_DIR", str(tmp_path))

    assert storage.path("startup") == tmp_path / "sounds" / "startup.wav"


def test_sounds_lists_supported_files_once(monkeypatch, tmp_path: Path) -> None:
    configured = tmp_path / "configured"
    shared = tmp_path / "data" / "sounds"
    configured.mkdir()
    shared.mkdir(parents=True)
    (configured / "alert.wav").write_bytes(b"configured")
    (shared / "alert.wav").write_bytes(b"shared")
    (shared / "startup.ogg").write_bytes(b"shared")
    (shared / "notes.txt").write_text("ignore", encoding="utf-8")

    monkeypatch.setenv("GWAY_SOUND_SOUNDS_DIR", str(configured))
    monkeypatch.setenv("GWAY_SOUND_DATA_DIR", str(tmp_path / "data"))

    assert storage.sounds() == ["alert.wav", "startup.ogg"]


def test_resolve_missing_name_raises(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GWAY_SOUND_SOUNDS_DIR", str(tmp_path / "configured"))
    monkeypatch.setenv("GWAY_SOUND_DATA_DIR", str(tmp_path / "data"))

    with pytest.raises(FileNotFoundError, match="sound not found"):
        storage.resolve("missing")
