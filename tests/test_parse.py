import pytest

from callgen.parse import ParseError, parse_transcript

from .conftest import FIXTURES


def total_words(text):
    return len(text.split())


def test_bracket_hms_turns_and_speakers():
    t = parse_transcript((FIXTURES / "bracket_hms.txt").read_text())
    assert [x["ts"] for x in t.turns] == [
        "00:00:00", "00:00:11", "00:00:48", "00:01:02", "01:04:30", "01:07:15",
    ]
    assert t.speakers == {"A": "Ada Sterling", "B": "Bo Marek"}
    assert [x["spk"] for x in t.turns] == ["A", "B", "A", "B", "A", "B"]
    assert [x["i"] for x in t.turns] == list(range(6))


def test_header_block_is_captured_not_parsed_as_a_turn():
    t = parse_transcript((FIXTURES / "bracket_hms.txt").read_text())
    assert "Warehouse inventory review" in t.header
    assert "Warehouse inventory review" not in t.turns[0]["t"]


def test_timestamps_past_one_hour():
    t = parse_transcript((FIXTURES / "bracket_hms.txt").read_text())
    assert t.turns[-2]["s"] == 3870
    assert t.turns[-1]["s"] == 4035
    assert t.duration_s == 4035


def test_multi_paragraph_turn_is_one_turn():
    t = parse_transcript((FIXTURES / "bracket_hms.txt").read_text())
    second = t.turns[1]
    assert second["t"].startswith("the count breaks at the door")
    assert second["t"].endswith("the floor says we do not.")
    assert "\n" not in second["t"]
    assert second["w"] == len(second["t"].split())


def test_unicode_survives():
    t = parse_transcript((FIXTURES / "bracket_hms.txt").read_text())
    assert "café" in t.turns[3]["t"]
    assert "naïve" in t.turns[3]["t"]


def test_word_counts_round_trip():
    raw = (FIXTURES / "bracket_hms.txt").read_text()
    t = parse_transcript(raw)
    per_speaker = {}
    for turn in t.turns:
        per_speaker[turn["spk"]] = per_speaker.get(turn["spk"], 0) + turn["w"]
    whole = total_words(" ".join(turn["t"] for turn in t.turns))
    assert sum(per_speaker.values()) == whole
    assert sum(per_speaker.values()) == sum(x["w"] for x in t.turns)


def test_short_mmss_stamps_including_minutes_over_sixty():
    t = parse_transcript((FIXTURES / "short_mmss.txt").read_text())
    assert [x["s"] for x in t.turns] == [0, 31, 125, 4520]
    assert t.turns[-1]["ts"] == "01:15:20"


def test_webvtt():
    t = parse_transcript((FIXTURES / "sample.vtt").read_text())
    assert [x["s"] for x in t.turns] == [0, 11, 64]
    assert t.speakers == {"A": "Ada Sterling", "B": "Bo Marek"}
    assert t.turns[0]["t"] == "right, we are recording."


def test_webvtt_voice_tags():
    vtt = (
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:04.000\n<v Ada Sterling>first line\n\n"
        "00:00:05.000 --> 00:00:09.000\n<v Bo Marek>second line\n"
    )
    t = parse_transcript(vtt)
    assert [x["spk"] for x in t.turns] == ["A", "B"]
    assert t.turns[0]["t"] == "first line"


def test_consecutive_same_speaker_cues_merge():
    vtt = (
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:04.000\nAda Sterling: first\n\n"
        "00:00:05.000 --> 00:00:09.000\nAda Sterling: second\n\n"
        "00:00:10.000 --> 00:00:14.000\nBo Marek: third\n"
    )
    t = parse_transcript(vtt)
    assert len(t.turns) == 2
    assert t.turns[0]["t"] == "first second"
    assert t.turns[0]["s"] == 0


def test_plain_speaker_lines_get_estimated_timing():
    t = parse_transcript((FIXTURES / "plain_speaker.txt").read_text())
    assert len(t.turns) == 4
    assert t.estimated_timing is True
    assert t.turns[0]["s"] == 0
    assert [x["s"] for x in t.turns] == sorted(x["s"] for x in t.turns)
    assert t.duration_s > 0


def test_timed_formats_are_not_marked_estimated():
    t = parse_transcript((FIXTURES / "bracket_hms.txt").read_text())
    assert t.estimated_timing is False


def test_malformed_timestamp_raises_naming_the_line():
    raw = (FIXTURES / "malformed.txt").read_text()
    with pytest.raises(ParseError) as e:
        parse_transcript(raw)
    msg = str(e.value)
    assert "line 4" in msg
    assert "00:0X:11" in msg


def test_transcript_with_no_turns_raises():
    with pytest.raises(ParseError) as e:
        parse_transcript("just some prose\nwith no speakers at all\n")
    assert "no turns" in str(e.value).lower()


def test_backwards_timestamp_raises():
    raw = "[00:01:00] Ada Sterling:\n    one\n\n[00:00:30] Bo Marek:\n    two\n"
    with pytest.raises(ParseError) as e:
        parse_transcript(raw)
    assert "line 4" in str(e.value)
