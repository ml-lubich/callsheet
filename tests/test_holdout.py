import os
import stat

import pytest

from callgen.holdout import (
    HoldoutError,
    ngram_overlap,
    read_manifest,
    seal,
    sealed_guard,
    strip_html,
    verify,
)


@pytest.fixture
def sealed(tmp_path):
    d = tmp_path / "sealed"
    d.mkdir()
    (d / "reference.html").write_text("<p>their answer, written by someone else</p>")
    (d / "notes.txt").write_text("second file")
    seal(d)
    return d


def test_seal_makes_files_read_only(sealed):
    for p in sealed.iterdir():
        mode = stat.S_IMODE(p.stat().st_mode)
        assert not mode & stat.S_IWUSR
        assert not mode & stat.S_IWGRP
        assert not mode & stat.S_IWOTH


def test_seal_records_a_hash_per_file(sealed):
    man = read_manifest(sealed)
    assert set(man) == {"notes.txt", "reference.html"}
    assert all(len(h) == 64 for h in man.values())
    verify(sealed)


def test_tampered_file_fails_verification(sealed):
    victim = sealed / "notes.txt"
    victim.chmod(0o644)
    victim.write_text("second file, quietly edited")
    with pytest.raises(HoldoutError) as e:
        verify(sealed)
    assert "notes.txt" in str(e.value)


def test_removed_file_fails_verification(sealed):
    victim = sealed / "notes.txt"
    victim.chmod(0o644)
    victim.unlink()
    with pytest.raises(HoldoutError) as e:
        verify(sealed)
    assert "notes.txt" in str(e.value)


def test_guard_raises_when_a_sealed_file_is_opened(sealed):
    with pytest.raises(HoldoutError) as e:
        with sealed_guard(sealed):
            (sealed / "reference.html").read_text()
    assert "reference.html" in str(e.value)


def test_guard_raises_on_plain_open_too(sealed):
    with pytest.raises(HoldoutError):
        with sealed_guard(sealed):
            with open(sealed / "notes.txt") as fh:
                fh.read()


def test_guard_allows_everything_outside_the_sealed_directory(sealed, tmp_path):
    other = tmp_path / "work.txt"
    other.write_text("fine")
    with sealed_guard(sealed):
        assert other.read_text() == "fine"


def test_guard_stops_guarding_after_the_block(sealed):
    with sealed_guard(sealed):
        pass
    assert "their answer" in (sealed / "reference.html").read_text()


def test_guard_is_lifted_even_when_the_body_raises(sealed):
    with pytest.raises(ZeroDivisionError):
        with sealed_guard(sealed):
            raise ZeroDivisionError("boom")
    assert (sealed / "notes.txt").read_text() == "second file"


def test_overlap_is_one_for_identical_text():
    t = "the count breaks at the door and not anywhere inside the racks at all"
    assert ngram_overlap(t, t) == 1.0


def test_overlap_is_zero_for_disjoint_text():
    a = "alpha bravo charlie delta echo foxtrot golf hotel india juliet"
    b = "kilo lima mike november oscar papa quebec romeo sierra tango"
    assert ngram_overlap(a, b) == 0.0


def test_overlap_ignores_whitespace_and_case():
    a = "The Count  Breaks\nat the   DOOR and not in the racks"
    b = "the count breaks at the door and not in the racks"
    assert ngram_overlap(a, b) == 1.0


def test_overlap_is_a_share_of_the_reference():
    a = "one two three four five six"
    b = "one two three four five six seven eight nine ten eleven"
    assert 0.0 < ngram_overlap(a, b, n=6) < 1.0


def test_overlap_of_text_shorter_than_n_is_zero():
    assert ngram_overlap("a b c", "a b c", n=6) == 0.0


def test_strip_html_drops_tags_scripts_and_styles():
    markup = "<style>p{color:red}</style><script>var x='hidden'</script><p>kept &amp; seen</p>"
    out = strip_html(markup)
    assert "kept & seen" in out
    assert "hidden" not in out
    assert "color:red" not in out
    assert "<p>" not in out


def test_sealed_directory_must_exist(tmp_path):
    with pytest.raises(HoldoutError):
        seal(tmp_path / "nope")


def test_seal_refuses_an_empty_directory(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    with pytest.raises(HoldoutError):
        seal(d)


def test_manifest_is_written_outside_the_sealed_directory(sealed):
    assert (sealed.parent / "sealed.sha256").exists()
    assert not (sealed / "sealed.sha256").exists()
    assert os.access(sealed.parent / "sealed.sha256", os.R_OK)
