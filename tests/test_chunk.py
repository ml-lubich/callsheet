import pytest

from callsheet.parse import chunks, metrics, parse_transcript

from .conftest import FIXTURES


@pytest.fixture
def transcript():
    return parse_transcript((FIXTURES / "bracket_hms.txt").read_text())


def test_chunks_tile_the_full_duration(transcript):
    cs = chunks(transcript, 3)
    assert cs[0].start_s == 0
    assert cs[-1].end_s == transcript.duration_s
    for a, b in zip(cs, cs[1:], strict=False):
        assert a.end_s == b.start_s


def test_every_turn_lands_in_exactly_one_chunk(transcript):
    cs = chunks(transcript, 3)
    seen = [t["i"] for c in cs for t in c.turns]
    assert sorted(seen) == [t["i"] for t in transcript.turns]
    assert len(seen) == len(set(seen))


def test_chunk_count_degrades_when_n_exceeds_turns(transcript):
    cs = chunks(transcript, 50)
    assert len(cs) == len(transcript.turns)
    assert all(c.turns for c in cs)
    assert cs[-1].end_s == transcript.duration_s


def test_chunk_of_one_is_the_whole_call(transcript):
    (c,) = chunks(transcript, 1)
    assert len(c.turns) == len(transcript.turns)
    assert (c.start_s, c.end_s) == (0, transcript.duration_s)


def test_chunk_n_must_be_positive(transcript):
    with pytest.raises(ValueError):
        chunks(transcript, 0)


def test_chunk_text_carries_timestamps_and_speaker_names(transcript):
    cs = chunks(transcript, 2)
    assert "[00:00:00] Ada Sterling:" in cs[0].text
    assert "01:07:15" in cs[-1].text


def test_metrics_totals_match_the_turns(transcript):
    m = metrics(transcript)
    assert m["turns"] == len(transcript.turns)
    assert m["duration_s"] == transcript.duration_s
    assert len(m["timeline"]) == len(transcript.turns)
    assert sum(v["words"] for v in m["speakers"].values()) == sum(t["w"] for t in transcript.turns)
    assert sum(v["turns"] for v in m["speakers"].values()) == len(transcript.turns)


def test_metrics_timeline_uses_full_names(transcript):
    m = metrics(transcript)
    assert m["timeline"][0]["spk"] == "Ada Sterling"
    assert set(m["speakers"]) == {"Ada Sterling", "Bo Marek"}
