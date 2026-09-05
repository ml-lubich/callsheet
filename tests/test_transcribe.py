import subprocess

import pytest

from callgen import transcribe as tr


@pytest.fixture
def model(tmp_path):
    p = tmp_path / "ggml-large-v3.bin"
    p.write_bytes(b"not really a model")
    return p


def test_command_line_shape(tmp_path, model):
    cmd = tr.whisper_command(
        media=tmp_path / "call.m4a",
        model=model,
        out_prefix=tmp_path / "out" / "call",
        threads=6,
        fmt="txt",
    )
    assert cmd[0] == "whisper-cli"
    assert cmd[cmd.index("-m") + 1] == str(model)
    assert cmd[cmd.index("-f") + 1] == str(tmp_path / "call.m4a")
    assert cmd[cmd.index("-of") + 1] == str(tmp_path / "out" / "call")
    assert cmd[cmd.index("-t") + 1] == "6"
    assert "-otxt" in cmd


@pytest.mark.parametrize("fmt,flag", [("txt", "-otxt"), ("vtt", "-ovtt"), ("srt", "-osrt")])
def test_output_format_flags(tmp_path, model, fmt, flag):
    cmd = tr.whisper_command(tmp_path / "a.wav", model, tmp_path / "a", fmt=fmt)
    assert flag in cmd


def test_unknown_format_raises(tmp_path, model):
    with pytest.raises(tr.TranscribeError) as e:
        tr.whisper_command(tmp_path / "a.wav", model, tmp_path / "a", fmt="pdf")
    assert "pdf" in str(e.value)


def test_custom_binary_name_is_honoured(tmp_path, model):
    cmd = tr.whisper_command(tmp_path / "a.wav", model, tmp_path / "a", binary="whisper-cpp")
    assert cmd[0] == "whisper-cpp"


def test_missing_binary_is_actionable(tmp_path, model, monkeypatch):
    monkeypatch.setattr(tr.shutil, "which", lambda name: None)
    media = tmp_path / "a.wav"
    media.write_bytes(b"x")
    with pytest.raises(tr.TranscribeError) as e:
        tr.transcribe(media, model, tmp_path / "a")
    msg = str(e.value)
    assert "whisper-cli" in msg
    assert "whisper-cpp" in msg


def test_missing_model_is_actionable(tmp_path, monkeypatch):
    monkeypatch.setattr(tr.shutil, "which", lambda name: "/usr/local/bin/whisper-cli")
    media = tmp_path / "a.wav"
    media.write_bytes(b"x")
    with pytest.raises(tr.TranscribeError) as e:
        tr.transcribe(media, tmp_path / "ggml-missing.bin", tmp_path / "a")
    msg = str(e.value)
    assert "ggml-missing.bin" in msg
    assert "model" in msg.lower()


def test_missing_media_is_actionable(tmp_path, model, monkeypatch):
    monkeypatch.setattr(tr.shutil, "which", lambda name: "/usr/local/bin/whisper-cli")
    with pytest.raises(tr.TranscribeError) as e:
        tr.transcribe(tmp_path / "gone.wav", model, tmp_path / "a")
    assert "gone.wav" in str(e.value)


def test_runs_the_command_and_returns_the_output_path(tmp_path, model, monkeypatch):
    media = tmp_path / "a.wav"
    media.write_bytes(b"x")
    seen = {}

    def fake_run(cmd, **kw):
        seen["cmd"] = cmd
        seen["kw"] = kw
        (tmp_path / "a.txt").write_text("[00:00:00]  hello\n")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(tr.shutil, "which", lambda name: "/usr/local/bin/whisper-cli")
    monkeypatch.setattr(tr.subprocess, "run", fake_run)

    out = tr.transcribe(media, model, tmp_path / "a", threads=4)
    assert out == tmp_path / "a.txt"
    assert out.read_text().startswith("[00:00:00]")
    assert seen["cmd"] == tr.whisper_command(media, model, tmp_path / "a", threads=4)
    assert seen["kw"]["check"] is True


def test_non_zero_exit_is_reported(tmp_path, model, monkeypatch):
    media = tmp_path / "a.wav"
    media.write_bytes(b"x")

    def fake_run(cmd, **kw):
        raise subprocess.CalledProcessError(2, cmd)

    monkeypatch.setattr(tr.shutil, "which", lambda name: "/usr/local/bin/whisper-cli")
    monkeypatch.setattr(tr.subprocess, "run", fake_run)
    with pytest.raises(tr.TranscribeError) as e:
        tr.transcribe(media, model, tmp_path / "a")
    assert "exit 2" in str(e.value)


def test_missing_output_after_a_clean_run_is_reported(tmp_path, model, monkeypatch):
    media = tmp_path / "a.wav"
    media.write_bytes(b"x")
    monkeypatch.setattr(tr.shutil, "which", lambda name: "/usr/local/bin/whisper-cli")
    monkeypatch.setattr(
        tr.subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0)
    )
    with pytest.raises(tr.TranscribeError) as e:
        tr.transcribe(media, model, tmp_path / "a")
    assert "a.txt" in str(e.value)
