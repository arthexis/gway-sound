from gway_sound import sources as source_module


class Result:
    returncode = 0
    stdout = (
        "0\tmic.one\tPipeWire\ts16le 1ch 16000Hz\tRUNNING\n"
        "1\tspeaker.monitor\tPipeWire\ts16le 2ch 48000Hz\tIDLE\n"
        "2\tmic.two\tPipeWire\ts16le 1ch 48000Hz\tSUSPENDED\n"
    )


def test_sources_filters_monitors(monkeypatch) -> None:
    monkeypatch.setattr(source_module.shutil, "which", lambda name: "/usr/bin/pactl")
    monkeypatch.setattr(source_module.subprocess, "run", lambda *args, **kwargs: Result())

    assert source_module.sources() == ["mic.one", "mic.two"]
