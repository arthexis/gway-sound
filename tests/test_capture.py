from pathlib import Path

from gway_sound import capture


def test_command_prefers_pw_record(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "out.wav"
    monkeypatch.setattr(
        capture.shutil, "which", lambda name: "/usr/bin/pw-record" if name == "pw-record" else None
    )

    command = capture.command(target, source="mic.source", rate=16000, channels=1)

    assert command == [
        "/usr/bin/pw-record",
        "--rate",
        "16000",
        "--channels",
        "1",
        "--target",
        "mic.source",
        str(target),
    ]


def test_command_falls_back_to_parec(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "out.wav"
    monkeypatch.setattr(
        capture.shutil, "which", lambda name: "/usr/bin/parec" if name == "parec" else None
    )

    command = capture.command(target, source=None, rate=48000, channels=2)

    assert command == [
        "/usr/bin/parec",
        "--file-format=wav",
        "--rate=48000",
        "--channels=2",
        str(target),
    ]
