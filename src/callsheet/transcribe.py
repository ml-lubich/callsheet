"""Local transcription with whisper.cpp. The audio never leaves the machine."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

FORMATS = {"txt": "-otxt", "vtt": "-ovtt", "srt": "-osrt", "json": "-oj", "csv": "-ocsv"}
DEFAULT_BINARY = "whisper-cli"


class TranscribeError(RuntimeError):
    """whisper.cpp could not be run, or produced nothing."""


def whisper_command(
    media,
    model,
    out_prefix,
    threads: int = 8,
    fmt: str = "txt",
    binary: str = DEFAULT_BINARY,
) -> list[str]:
    """The whisper.cpp command line for one transcription."""
    if fmt not in FORMATS:
        raise TranscribeError(f"unknown output format {fmt!r}; choose one of {', '.join(FORMATS)}")
    return [
        binary,
        "-m", str(model),
        "-f", str(media),
        "-of", str(out_prefix),
        "-t", str(threads),
        FORMATS[fmt],
    ]


def transcribe(
    media,
    model,
    out_prefix,
    threads: int = 8,
    fmt: str = "txt",
    binary: str = DEFAULT_BINARY,
) -> Path:
    """Run whisper.cpp locally and return the transcript it wrote."""
    media, model, out_prefix = Path(media), Path(model), Path(out_prefix)
    if shutil.which(binary) is None:
        raise TranscribeError(
            f"{binary} is not on PATH. Install it with: brew install whisper-cpp"
        )
    if not media.is_file():
        raise TranscribeError(f"no such recording: {media}")
    if not model.is_file():
        raise TranscribeError(
            f"no such model: {model}. Download a ggml model, e.g. "
            "curl -L -o ggml-large-v3.bin https://huggingface.co/ggerganov/whisper.cpp"
            "/resolve/main/ggml-large-v3.bin"
        )
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    cmd = whisper_command(media, model, out_prefix, threads=threads, fmt=fmt, binary=binary)
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise TranscribeError(f"{binary} failed with exit {e.returncode}") from e
    produced = out_prefix.with_name(out_prefix.name + "." + fmt)
    if not produced.is_file():
        raise TranscribeError(f"{binary} exited cleanly but wrote no {produced}")
    return produced
