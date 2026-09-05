import json
from pathlib import Path

import pytest

from callgen.cli import main
from callgen.lexicon import (
    LexiconError,
    apply_corrections,
    build_profile,
    flag_unlike_speaker,
    load_profile,
    suggest_corrections,
)

PROFILES = Path(__file__).parent.parent / "profiles"

VOCAB = [
    "FAISS",
    "Cognee",
    "LangGraph",
    "BM25",
    "ChromaDB",
    "SQLite",
    "Pinecone",
    "reciprocal rank fusion",
    "embeddings",
    "reranker",
]

WRITING = """
We keep the retrieval stack small. A dense index answers most of the questions,
and a sparse index catches the rest. Pinecone was the first thing we tried.
We store embeddings on disk and load them once at start up. The reranker runs
last, and only on the top fifty rows. Reciprocal rank fusion blends the two
lists before that. It is boring and it works.
"""

MANGLED = """[00:01:10] Speaker:
    We started with a Pinecone index and then moved the whole thing local.
    The fate face index was fast enough once we tuned it, and we kept the
    embeddings on disk.

[00:03:40] Speaker:
    For retrieval we combined a dense search with abeam 25 and blended the
    two lists with rank reciprocal factor before the reranker saw them.

[00:05:02] Speaker:
    We tried cockney for the knowledge store and land graph for the agent
    loop, and the whole thing wrote its state to SQL light.

[00:07:15] Speaker:
    Chrome IDB was the first vector store we used, before Pinecone.
"""

EXPECTED = {
    "fate face": "FAISS",
    "abeam 25": "BM25",
    "rank reciprocal factor": "reciprocal rank fusion",
    "cockney": "Cognee",
    "land graph": "LangGraph",
    "SQL light": "SQLite",
    "Chrome IDB": "ChromaDB",
}


@pytest.fixture
def profile():
    return build_profile([WRITING], name="test-engineer", terms=VOCAB)


# --- profile building ------------------------------------------------------


def test_profile_extracts_terms_acronyms_and_identifiers():
    p = build_profile(
        ["We run FAISS and BM25 behind FastAPI on Fly.io, with easyOCR for the scans."],
        name="t",
    )
    for term in ("FAISS", "BM25", "FastAPI", "Fly.io", "easyOCR"):
        assert term in p["terms"], f"{term} missing from {sorted(p['terms'])}"


def test_profile_extracts_a_repeated_multiword_phrase():
    text = (
        "Reciprocal rank fusion blends the lists. "
        "We tuned reciprocal rank fusion until the ordering stopped moving."
    )
    p = build_profile([text], name="t")
    assert "reciprocal rank fusion" in {t.lower() for t in p["terms"]}


def test_profile_records_ngrams_of_ordinary_phrasing(profile):
    assert any(len(k.split()) == 2 for k in profile["ngrams"])
    assert any(len(k.split()) == 3 for k in profile["ngrams"])
    assert "we store" in profile["ngrams"]


def test_profile_records_corpus_size_and_schema_version(profile):
    assert profile["schema"] == 1
    assert profile["name"] == "test-engineer"
    assert profile["corpus"]["documents"] == 1
    assert profile["corpus"]["words"] > 50


def test_profile_holds_no_pii():
    corpus = (
        "Reach me at ada.sterling@example.com or on +1 (415) 555-0132. "
        "Mail goes to 742 Elm Street, Springfield, 94040. "
        "See https://user:secret@internal.example.com/notes for the rest. "
        "We shipped the FAISS index that week."
    )
    blob = json.dumps(build_profile([corpus], name="t"))
    for leak in (
        "ada.sterling",
        "example.com",
        "555-0132",
        "5550132",
        "415",
        "742",
        "Elm",
        "Springfield",
        "94040",
        "secret",
        "internal",
    ):
        assert leak not in blob, f"profile leaked {leak!r}"
    assert "FAISS" in blob


def test_profile_stores_no_long_verbatim_spans(profile):
    assert max(len(k.split()) for k in profile["ngrams"]) <= 3
    assert max(len(k.split()) for k in profile["terms"]) <= 3


def test_load_profile_rejects_a_foreign_schema(tmp_path):
    bad = tmp_path / "p.json"
    bad.write_text(json.dumps({"schema": 99, "terms": {}, "ngrams": {}}))
    with pytest.raises(LexiconError):
        load_profile(bad)


# --- recovery --------------------------------------------------------------


def test_recovers_every_real_mangled_term(profile):
    found = suggest_corrections(MANGLED, profile)
    assert {c.suggestion for c in found} == set(EXPECTED.values())
    for mangled, want in EXPECTED.items():
        hit = [c for c in found if c.suggestion == want]
        assert len(hit) == 1, f"{want} recovered {len(hit)} times"
        c = hit[0]
        assert c.span in mangled, f"{c.span!r} is not inside {mangled!r}"
        assert MANGLED[c.start_char : c.end_char] == c.span
        assert 0.0 < c.score <= 1.0
        assert c.reason


def test_does_not_rewrite_ordinary_english(profile):
    plain = "The colony was cold that winter, and the fate of the crops was decided early."
    assert suggest_corrections(plain, profile) == []


def test_a_transcript_without_profile_terms_yields_nothing(profile):
    plain = (
        "She left the house before dawn and walked to the river. "
        "The light was flat and the water moved slowly under the bridge."
    )
    assert suggest_corrections(plain, profile) == []


def test_corrections_are_ranked_and_never_overlap(profile):
    found = suggest_corrections(MANGLED, profile)
    assert [c.score for c in found] == sorted((c.score for c in found), reverse=True)
    spans = sorted((c.start_char, c.end_char) for c in found)
    for (_, end), (start, _) in zip(spans, spans[1:], strict=False):
        assert end <= start


def test_apply_corrections_rewrites_only_the_spans(profile):
    found = suggest_corrections(MANGLED, profile)
    out = apply_corrections(MANGLED, found)
    for want in EXPECTED.values():
        assert want in out
    assert "cockney" not in out
    assert "[00:05:02] Speaker:" in out


def test_apply_corrections_of_nothing_changes_nothing(profile):
    assert apply_corrections(MANGLED, []) == MANGLED


# --- suspicion -------------------------------------------------------------


def test_flags_a_florid_insertion_and_leaves_plain_sentences_alone():
    p = build_profile([WRITING], name="t", terms=VOCAB)
    text = (
        "We store embeddings on disk and load them once at start up. "
        "The resplendent tapestry of computational endeavour unfurled "
        "magnificently across the luminous firmament of possibility. "
        "The reranker runs last, and only on the top fifty rows."
    )
    flags = flag_unlike_speaker(text, p)
    assert len(flags) == 1
    assert "resplendent" in flags[0].span
    assert text[flags[0].start_char : flags[0].end_char] == flags[0].span
    assert flags[0].why
    assert 0.0 < flags[0].confidence <= 1.0


def test_plain_writing_is_not_flagged_against_itself():
    p = build_profile([WRITING], name="t")
    assert flag_unlike_speaker(WRITING, p) == []


# --- the shipped profile ---------------------------------------------------


def test_example_profile_ships_and_recovers_the_mangled_terms():
    p = load_profile(PROFILES / "example-engineer.json")
    assert p["corpus"]["documents"] >= 1
    for term in ("FAISS", "BM25", "LangGraph", "reciprocal rank fusion", "diarization"):
        assert term in p["terms"]
    found = {c.suggestion for c in suggest_corrections(MANGLED, p)}
    assert set(EXPECTED.values()) <= found


# --- cli -------------------------------------------------------------------


@pytest.fixture
def corpus(tmp_path):
    d = tmp_path / "corpus"
    d.mkdir()
    (d / "notes.md").write_text(WRITING)
    (d / "more.txt").write_text("We reach for SQLite before Postgres, and ChromaDB never.")
    (d / "logo.bin").write_bytes(b"\x00\x01\x02binary junk\x00")
    return d


@pytest.fixture
def built(tmp_path, corpus):
    out = tmp_path / "profile.json"
    assert main(["lexicon", "build", "--from", str(corpus), "--name", "eng", "-o", str(out)]) == 0
    return out


def test_cli_build_reads_a_directory_skips_binaries_and_reports(tmp_path, corpus, capsys):
    out = tmp_path / "p.json"
    assert main(["lexicon", "build", "--from", str(corpus), "--name", "eng", "-o", str(out)]) == 0
    assert "2 documents" in capsys.readouterr().out
    p = load_profile(out)
    assert p["name"] == "eng"
    assert p["corpus"]["documents"] == 2
    assert "SQLite" in p["terms"]


def test_cli_build_accepts_a_glob(tmp_path, corpus, capsys):
    out = tmp_path / "g.json"
    pattern = str(corpus / "*.md")
    assert main(["lexicon", "build", "--from", pattern, "--name", "eng", "-o", str(out)]) == 0
    assert load_profile(out)["corpus"]["documents"] == 1


def test_cli_build_with_a_terms_file(tmp_path, corpus):
    terms = tmp_path / "terms.txt"
    terms.write_text("FAISS\nreciprocal rank fusion\n\n")
    out = tmp_path / "t.json"
    argv = ["lexicon", "build", "--from", str(corpus), "--name", "e", "-o", str(out)]
    assert main([*argv, "--terms", str(terms)]) == 0
    assert "reciprocal rank fusion" in load_profile(out)["terms"]


def test_cli_check_is_quiet_and_zero_on_a_clean_transcript(tmp_path, built, capsys):
    t = tmp_path / "clean.txt"
    t.write_text("She left the house before dawn and walked down to the river.")
    assert main(["lexicon", "check", str(t), "--profile", str(built)]) == 0
    assert "no corrections" in capsys.readouterr().out


def test_cli_check_is_nonzero_and_reports_offsets_on_a_dirty_transcript(tmp_path, capsys):
    prof = tmp_path / "p.json"
    prof.write_text(json.dumps(build_profile([WRITING], name="t", terms=VOCAB)))
    t = tmp_path / "dirty.txt"
    t.write_text(MANGLED)
    assert main(["lexicon", "check", str(t), "--profile", str(prof)]) == 1
    said = capsys.readouterr().out
    assert "SQLite" in said
    assert str(MANGLED.index("SQL light")) in said


def test_cli_check_writes_a_review_file(tmp_path, capsys):
    prof = tmp_path / "p.json"
    prof.write_text(json.dumps(build_profile([WRITING], name="t", terms=VOCAB)))
    t = tmp_path / "dirty.txt"
    t.write_text(MANGLED)
    report = tmp_path / "report.md"
    argv = ["lexicon", "check", str(t), "--profile", str(prof), "-o", str(report)]
    assert main(argv) == 1
    body = report.read_text()
    assert "ChromaDB" in body and "Chrome IDB" in body


def test_cli_apply_needs_the_write_flag(tmp_path, capsys):
    prof = tmp_path / "p.json"
    prof.write_text(json.dumps(build_profile([WRITING], name="t", terms=VOCAB)))
    t = tmp_path / "dirty.txt"
    t.write_text(MANGLED)
    assert main(["lexicon", "apply", str(t), "--profile", str(prof)]) == 1
    assert t.read_text() == MANGLED
    assert not (tmp_path / "dirty.txt.corrections.json").exists()


def test_cli_apply_writes_the_text_and_an_audit_beside_it(tmp_path, capsys):
    prof = tmp_path / "p.json"
    prof.write_text(json.dumps(build_profile([WRITING], name="t", terms=VOCAB)))
    t = tmp_path / "dirty.txt"
    t.write_text(MANGLED)
    argv = ["lexicon", "apply", str(t), "--profile", str(prof), "--write"]
    assert main(argv) == 0
    assert "SQLite" in t.read_text()
    audit = json.loads((tmp_path / "dirty.txt.corrections.json").read_text())
    assert {c["suggestion"] for c in audit["corrections"]} <= set(EXPECTED.values())
    assert audit["profile"] == "t"


# --- a profile is vocabulary, not documentation debris -----------------------


def test_a_capitalised_ordinary_word_is_not_a_term():
    p = build_profile(
        ["Bands of colour sit above the line. We grouped bands by speaker, one band each."],
        name="t",
    )
    assert not {t for t in p["terms"] if t.lower().startswith("band")}


def test_format_placeholders_and_paths_are_not_terms():
    p = build_profile(
        [
            "Stamps read [HH:MM:SS] and dates read YYYY-MM-DD. "
            "Chunks land in work/chunk1.txt and the spec is SKILL.md. "
            "The CI/CD job reads content.json from src/callgen."
        ],
        name="t",
    )
    for junk in ("HH", "MM", "SS", "YYYY", "HH MM", "HH MM SS", "work/chunk1", "SKILL.md",
                 "content.json", "src/callgen"):
        assert junk not in p["terms"], f"{junk!r} was kept as a term"
    assert "CI/CD" in p["terms"]


def test_a_short_span_never_matches_a_short_term():
    p = build_profile([WRITING], name="t", terms=["Ada", "MIT", "FAISS", "Pinecone"])
    text = "We add the file to Pinecone and we might ship it, and the face index is fast."
    found = {(c.span.lower(), c.suggestion) for c in suggest_corrections(text, p)}
    assert ("add", "Ada") not in found
    assert ("might", "MIT") not in found
    assert ("face", "FAISS") in found


def test_the_same_mangling_twice_is_one_reviewable_row():
    p = build_profile([WRITING], name="t", terms=VOCAB)
    text = (
        "We tried cockney first, on Pinecone. Cockney held the graph. "
        "Later we moved off cockney entirely, back to the embeddings store."
    )
    found = [c for c in suggest_corrections(text, p) if c.suggestion == "Cognee"]
    assert len(found) == 1
    assert found[0].count == 3
    assert len(found[0].offsets) == 3
    out = apply_corrections(text, found)
    assert out.count("Cognee") == 3
    assert "ockney" not in out


REAL = """[00:04:12] Speaker:
    We started on pine cone for the vector store, then moved to chroma DB
    when the bill got high. The whole thing is deployed behind cloud flare
    and the API is fast API on FlyIO. Nothing said here is controversial.

[00:11:30] Speaker:
    The pipeline is a Graph RAC index over the docs, and we lower the
    reranker cut when recall drops. We add a Whisper pass first. The CICD
    job runs on every push, and the fixes land the same day.

[00:19:45] Speaker:
    Storage was Chrome IDB at first, then SQL item, then Postgres for real.
    Cockney holds the entity graph. We were working with data bricks for
    the batch side, and Open CV plus a bit of clawed for the vision rack.

[00:27:03] Speaker:
    Redis holds the queue, Terraform owns the infra, and I might turn the
    short retry off. It was a sad month, but him and I got it out. The
    embeddings never moved.
"""

REAL_RECOVERIES = {
    "pine cone": "Pinecone",
    "chroma DB": "ChromaDB",
    "cloud flare": "Cloudflare",
    "fast API": "FastAPI",
    "FlyIO": "Fly.io",
    "Graph RAC": "GraphRAG",
    "CICD": "CI/CD",
    "Chrome IDB": "ChromaDB",
    "SQL item": "SQLite",
    "Cockney": "Cognee",
    "data bricks": "Databricks",
    "Open CV": "OpenCV",
    "clawed": "Claude",
}

ORDINARY = ["high", "said", "lower", "add", "fixes", "working", "rack", "might", "turn",
            "short", "sad", "him", "whole", "first", "real", "bit", "day", "bill"]


def test_a_real_transcript_recovers_terms_and_leaves_ordinary_words_alone():
    p = load_profile(PROFILES / "example-engineer.json")
    found = suggest_corrections(REAL, p)
    got = {c.suggestion for c in found}
    missing = {want for want in REAL_RECOVERIES.values() if want not in got}
    assert not missing, f"not recovered: {sorted(missing)}"
    touched = {c.span.lower() for c in found}
    assert not (touched & set(ORDINARY)), f"ordinary words rewritten: {touched & set(ORDINARY)}"
    assert len(found) <= len(set(REAL_RECOVERIES.values())) + 2, [
        (c.span, c.suggestion, c.score) for c in found
    ]


def test_cli_check_caps_the_list_and_says_what_it_withheld(tmp_path, capsys):
    prof = tmp_path / "p.json"
    prof.write_text(json.dumps(build_profile([WRITING], name="t", terms=VOCAB)))
    t = tmp_path / "dirty.txt"
    t.write_text(MANGLED)
    argv = ["lexicon", "check", str(t), "--profile", str(prof), "--max", "2"]
    assert main(argv) == 1
    said = capsys.readouterr().out
    assert "withheld" in said
    assert said.count(" -> ") == 2


# --- precision on real-shaped input -------------------------------------
# These came from running the shipped profile against a real 74-minute
# transcript, where it proposed 228 corrections that were mostly noise.

REAL_ISH = """
    so we're running the whole thing on flyio, and the front end sits on vercel.
    i coded most of it myself before the models were any good, so i don't just
    ship slop. i said that already. we had to fix the scraper twice. support
    tickets come in through salesforce and might get routed wrong, and then
    somebody's add-on never shows up. he got banned from the repo for a day.
    the sell was easy once they saw it. i'm lower on the stack than you'd think.
    we use chroma DB for vectors, cloud flare in front, data bricks for the
    warehouse, pine cone earlier on, fast API for the service, and open CV plus
    SQL item for the local checks. the cockney library does graph RAC.
"""

RECOVERABLE = {
    "chroma DB": "ChromaDB", "cloud flare": "Cloudflare", "data bricks": "Databricks",
    "pine cone": "Pinecone", "fast API": "FastAPI", "open CV": "OpenCV",
}
ORDINARY_WORDS = [
    "coded", "said", "support", "might", "add", "banned", "sell", "lower", "fix", "fixes",
]


def test_ordinary_english_words_are_not_mined_as_terms():
    """A capitalised word that also appears lowercased is an ordinary word."""
    corpus = [
        "Bands of colour across the chart. We use grouped bands for this.",
        "Said the reviewer. She said it twice. Code review. we review the code.",
        "Fix the importer. We had to fix it again.",
    ]
    profile = build_profile(corpus, name="t")
    for junk in ("Bands", "BAND", "Said", "Code", "Fix"):
        assert junk not in profile["terms"], f"{junk} was mined as a term"


def test_short_spans_need_near_exact_agreement():
    """Three- and four-letter spans match anything phonetically; hold them higher."""
    profile = build_profile(["We deploy with Ada and MIT licences."], name="t",
                            terms=["Ada", "MIT"])
    found = suggest_corrections("please add the item, it might work", profile)
    assert [c.suggestion for c in found] == []


def test_precision_on_a_realistic_transcript():
    """Recover the real mangled tool names without touching ordinary speech."""
    profile = build_profile([" ".join(RECOVERABLE.values())], name="t",
                            terms=list(RECOVERABLE.values()))
    found = suggest_corrections(REAL_ISH, profile)
    suggestions = {c.suggestion for c in found}
    for expected in RECOVERABLE.values():
        assert expected in suggestions, f"lost a real recovery: {expected}"
    touched = {c.span.lower() for c in found}
    for ordinary in ORDINARY_WORDS:
        assert ordinary not in touched, f"rewrote ordinary English: {ordinary}"
