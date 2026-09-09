from pathlib import Path

from gway_sound import recording


class FakeProcess:
    def __init__(self, pid: int = 4242) -> None:
        self.pid = pid
        self.terminated = False
        self.wait_calls: list[float | None] = []

    def wait(self, timeout: float | None = None) -> int:
        self.wait_calls.append(timeout)
        if timeout is not None:
            import subprocess

            raise subprocess.TimeoutExpired("capture", timeout)
        return 0

    def terminate(self) -> None:
        self.terminated = True


def test_record_without_seconds_runs_in_background(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GWAY_SOUND_DATA_DIR", str(tmp_path))
    process = FakeProcess()
    monkeypatch.setattr(recording.capture, "start", lambda *args, **kwargs: process)

    result = recording.record(source="mic.one", name="inspection")

    assert result["pid"] == 4242
    assert result["source"] == "mic.one"
    assert result["recording"] is True
    assert str(result["path"]).endswith("-inspection.wav")


def test_finite_recording_terminates_after_duration(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GWAY_SOUND_DATA_DIR", str(tmp_path))
    process = FakeProcess()
    cleared: list[int | None] = []
    monkeypatch.setattr(recording.capture, "start", lambda *args, **kwargs: process)
    monkeypatch.setattr(recording.capture, "clear_state", lambda pid=None: cleared.append(pid))

    result = recording.record(seconds=5)

    assert process.terminated is True
    assert process.wait_calls == [5, None]
    assert cleared == [4242]
    assert result["recording"] is False
    assert result["seconds"] == 5


def test_recordings_lists_newest_paths_first(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GWAY_SOUND_DATA_DIR", str(tmp_path))
    root = tmp_path / "recordings" / "2026" / "09" / "09"
    root.mkdir(parents=True)
    older = root / "20260909T100000.000+0000.wav"
    newer = root / "20260909T110000.000+0000.wav"
    older.write_bytes(b"old")
    newer.write_bytes(b"new")

    assert recording.recordings() == [str(newer), str(older)]
