from gway_sound import control


def test_stop_stops_playback_and_recording(monkeypatch) -> None:
    monkeypatch.setattr(control.playback, "stop", lambda: {"stopped": True, "pid": 10})
    monkeypatch.setattr(control.recording, "stop", lambda: {"stopped": True, "pid": 20})

    result = control.stop()

    assert result == {
        "stopped": True,
        "playback": {"stopped": True, "pid": 10},
        "recording": {"stopped": True, "pid": 20},
    }


def test_stop_reports_false_when_nothing_active(monkeypatch) -> None:
    monkeypatch.setattr(control.playback, "stop", lambda: {"stopped": False})
    monkeypatch.setattr(control.recording, "stop", lambda: {"stopped": False})

    assert control.stop()["stopped"] is False
