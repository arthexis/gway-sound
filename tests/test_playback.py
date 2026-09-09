from pathlib import Path

from gway_sound import playback


class FakeProcess:
    def __init__(self, pid: int = 4242, returncode: int = 0) -> None:
        self.pid = pid
        self.returncode = returncode

    def wait(self) -> int:
        return self.returncode


def test_play_waits_and_clears_state(monkeypatch, tmp_path: Path) -> None:
    sound = tmp_path / "alert.wav"
    sound.write_bytes(b"audio")
    process = FakeProcess()

    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "run"))
    monkeypatch.setattr(playback, "resolve", lambda value: sound)
    monkeypatch.setattr(playback, "_player_command", lambda value: ["/usr/bin/aplay", str(value)])
    monkeypatch.setattr(playback.subprocess, "Popen", lambda command: process)

    result = playback.play("alert")

    assert result == {"path": str(sound), "pid": 4242, "wait": True}
    assert not playback._state_path().exists()


def test_play_without_wait_persists_state(monkeypatch, tmp_path: Path) -> None:
    sound = tmp_path / "alert.wav"
    sound.write_bytes(b"audio")
    process = FakeProcess()

    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "run"))
    monkeypatch.setattr(playback, "resolve", lambda value: sound)
    monkeypatch.setattr(playback, "_player_command", lambda value: ["/usr/bin/aplay", str(value)])
    monkeypatch.setattr(playback.subprocess, "Popen", lambda command: process)

    playback.play("alert", wait=False)

    assert playback._state_path().exists()


def test_stop_terminates_saved_process(monkeypatch, tmp_path: Path) -> None:
    sound = tmp_path / "alert.wav"
    sound.write_bytes(b"audio")
    process = FakeProcess()
    killed: list[tuple[int, int]] = []

    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "run"))
    monkeypatch.setattr(playback, "resolve", lambda value: sound)
    monkeypatch.setattr(playback, "_player_command", lambda value: ["/usr/bin/aplay", str(value)])
    monkeypatch.setattr(playback.subprocess, "Popen", lambda command: process)
    monkeypatch.setattr(playback.os, "kill", lambda pid, sig: killed.append((pid, sig)))
    playback.play("alert", wait=False)

    result = playback.stop()

    assert result == {"stopped": True, "pid": 4242}
    assert killed and killed[0][0] == 4242
    assert not playback._state_path().exists()
