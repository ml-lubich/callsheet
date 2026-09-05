import copy

import pytest

from callgen.schema import SchemaError, validate


def test_valid_content_passes(content):
    validate(content)


def bad(content, mutate):
    c = copy.deepcopy(content)
    mutate(c)
    with pytest.raises(SchemaError) as e:
        validate(c)
    return str(e.value)


def test_missing_required_key_names_the_field(content):
    def drop(c):
        del c["abstract"]

    assert "abstract" in bad(content, drop)


def test_missing_nested_meta_key_names_the_path(content):
    def drop(c):
        del c["meta"]["title"]

    assert "meta.title" in bad(content, drop)


def test_act_gap_is_reported(content):
    def gap(c):
        c["acts"][1]["start_s"] = 1200
        c["acts"][1]["span"] = "00:20:00-00:50:00"

    msg = bad(content, gap)
    assert "acts[1]" in msg
    assert "gap" in msg.lower()


def test_act_overlap_is_reported(content):
    def overlap(c):
        c["acts"][1]["start_s"] = 800
        c["acts"][1]["span"] = "00:13:20-00:50:00"

    msg = bad(content, overlap)
    assert "acts[1]" in msg
    assert "overlap" in msg.lower()


def test_acts_must_start_at_zero(content):
    def shift(c):
        c["acts"][0]["start_s"] = 60
        c["acts"][0]["span"] = "00:01:00-00:16:40"

    assert "acts[0]" in bad(content, shift)


def test_span_string_must_agree_with_seconds(content):
    def lie(c):
        c["acts"][0]["span"] = "00:00:00-00:99:99"

    msg = bad(content, lie)
    assert "acts[0].span" in msg


def test_timestamp_seconds_must_agree_with_the_string(content):
    def lie(c):
        c["evidence"][0]["s"] = 99

    msg = bad(content, lie)
    assert "evidence[0]" in msg
    assert "00:01:02" in msg


def test_quote_without_speaker_is_reported(content):
    def strip(c):
        del c["quotes"][0]["speaker"]

    assert "quotes[0].speaker" in bad(content, strip)


def test_quote_speaker_must_be_a_known_participant(content):
    def wrong(c):
        c["quotes"][1]["speaker"] = "Z"

    msg = bad(content, wrong)
    assert "quotes[1].speaker" in msg
    assert "Z" in msg


def test_unknown_evidence_strength_is_reported(content):
    def wrong(c):
        c["evidence"][0]["strength"] = "quite good"

    msg = bad(content, wrong)
    assert "evidence[0].strength" in msg
    assert "quite good" in msg


def test_all_errors_are_reported_together(content):
    def two(c):
        del c["quotes"][0]["speaker"]
        c["evidence"][0]["strength"] = "nope"

    msg = bad(content, two)
    assert "quotes[0].speaker" in msg
    assert "evidence[0].strength" in msg


def test_participants_need_key_and_name(content):
    def wrong(c):
        del c["meta"]["participants"][0]["name"]

    assert "meta.participants[0].name" in bad(content, wrong)


def test_content_must_be_an_object(content):
    with pytest.raises(SchemaError):
        validate([1, 2, 3])
