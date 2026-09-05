"""A speaker's own vocabulary, used to catch what the recogniser got wrong.

Local speech recognition has no prior for domain words, so it substitutes the
nearest ordinary English: an index name becomes two common words, a library
becomes a dialect, a ranking method becomes a phrase with the same words in the
wrong order. The damage is quiet. A reader searching the write-up's spelling
finds nothing in the transcript, and a summariser downstream will happily invent
meaning from the garbled form.

Two guardrails, both driven by a profile of how one person actually writes:

``suggest_corrections``   fuzzy-matches transcript spans against the profile's
                          vocabulary and proposes replacements.
``flag_unlike_speaker``   marks phrasing the speaker demonstrably never uses,
                          which is a signal of invention rather than speech.

A profile is derived statistics — term and phrase frequencies — and never source
text: everything that looks like an email address, a phone number, a URL or a
street address is scrubbed before anything is counted.

Corrections are proposed and reviewed. Nothing here rewrites a transcript unless
a caller asks for it in as many words.
"""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

SCHEMA = 1
CONTEXT_CHARS = 400
CERTAIN = 0.92
PHONETIC_FLOOR = 0.82  # below this the two words simply do not sound alike
SINGLE_WORD_FLOOR = 0.95  # one intact word is only wrong if it is a near homophone
SHORTEST_TERM = 4  # one word cannot be corrected to a 3-letter term; too many words match one
SMALL_TARGET = 4  # at this length a term is too small a target for phonetics alone
FILE_SUFFIXES = frozenset(
    "json html htm md txt py js ts css yml yaml sh csv vtt srt m4a bin png svg log toml xml".split()
)

# Enough of a stopword list to keep windows off ordinary phrasing; not linguistics.
STOPWORDS = frozenset(
    """a an and are as at be been but by can could did do does for from had has have he
    her his how i if in into is it its me my not of on or our out she so than that the
    their them then there these they this to was we were what when which who will with
    would you your it's we're don't just get got go going like really very much more
    most some any all one two three no yes now here up down over under before after
    about because while during between own same too own also let us am being does""".split()
)

_URL = re.compile(r"\b(?:https?://|ftp://|www\.)\S+", re.I)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_STREET = re.compile(
    r"\b\d{1,6}\s+(?:[A-Z][\w.'-]*\s+){0,3}"
    r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|"
    r"Place|Pl|Terrace|Parkway|Pkwy|Highway|Hwy)\b\.?"
    r"(?:\s*,\s*[A-Z][A-Za-z]+)*(?:\s*,?\s*\d{5}(?:-\d{4})?)?"
)
_PHONE = re.compile(r"\+?\d[\d\s().-]{6,}\d")
_LONG_NUMBER = re.compile(r"\b\d{5,}\b")

_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9.'/+#-]*[A-Za-z0-9]|[A-Za-z0-9]")
_SENTENCE = re.compile(r"[^.!?\n]+(?:[.!?]+|\n|$)")
_SENTENCE_END = re.compile(r"[.!?]\s*$|\n\s*$")
_CLAUSE_GAP = re.compile(r"^[ \t]*[-–/]?[ \t]*$")


class LexiconError(ValueError):
    """A profile could not be read, or was written by something else."""


@dataclass(frozen=True)
class Correction:
    span: str
    start_char: int
    end_char: int
    suggestion: str
    score: float
    reason: str
    count: int = 1
    offsets: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True)
class Flag:
    span: str
    start_char: int
    end_char: int
    why: str
    confidence: float


# --- scrubbing -------------------------------------------------------------


def scrub(text: str) -> str:
    """Drop everything that identifies a person before anything is counted."""
    for pattern in (_URL, _EMAIL, _STREET, _PHONE, _LONG_NUMBER):
        text = pattern.sub(" ", text)
    return text


# --- phonetics -------------------------------------------------------------

_PAIRS = {"ph": "f", "ch": "k", "sh": "x", "th": "t", "ck": "k", "gh": "", "wh": "w"}
_SINGLE = {
    "b": "b", "c": "k", "d": "t", "f": "f", "g": "k", "j": "k", "k": "k", "l": "l",
    "m": "m", "n": "n", "p": "p", "q": "k", "r": "r", "s": "s", "t": "t", "v": "f",
    "w": "", "x": "ks", "z": "s", "h": "", "y": "",
}  # fmt: skip
_VOWELS = "aeiou"


def phonetic(word: str) -> str:
    """A small metaphone-ish coder: consonant skeleton, digits kept, doubles collapsed.

    The first vowel of each word survives, and it earns its place: without it the
    coder hears "rank" and "wrong", or "state" and "said", as the same word.
    Everything after that is deliberately crude — the coder only has to put a
    mangled word next to its real spelling, and edit distance does the rest.
    """
    w = re.sub(r"[^a-z0-9]", "", word.lower())
    out: list[str] = []
    i = 0
    while i < len(w):
        ch = w[i]
        if ch.isdigit():
            out.append(ch)
            i += 1
            continue
        pair = w[i : i + 2]
        if pair in _PAIRS:
            out.append(_PAIRS[pair])
            i += 2
            continue
        if ch in _VOWELS:
            if not any(c in _VOWELS for c in out):
                out.append(ch)
            i += 1
            continue
        if ch == "c" and i + 1 < len(w) and w[i + 1] in "eiy":
            out.append("s")
            i += 1
            continue
        out.append(_SINGLE.get(ch, ch))
        i += 1
    code = "".join(out)
    return re.sub(r"(.)\1+", r"\1", code)


def _code(phrase: str) -> str:
    return "".join(phonetic(w) for w in phrase.split())


def _similarity(span: str, term: str) -> float:
    """Phonetic agreement, weighted against plain edit distance."""
    literal = SequenceMatcher(None, _flat(span), _flat(term)).ratio()
    return 0.7 * _sounds_like(span, term) + 0.3 * literal


def _sounds_like(span: str, term: str) -> float:
    return SequenceMatcher(None, _code(span), _code(term)).ratio()


def _flat(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _phrase_similarity(span: str, term: str) -> float:
    """Order-insensitive score for multiword terms, so a swapped phrase still matches."""
    span_words, term_words = span.split(), term.split()
    if len(term_words) < 2 or not span_words:
        return 0.0
    spare = list(span_words)
    scores = []
    for word in term_words:
        if not spare:
            break
        best = max(spare, key=lambda s: _similarity(s, word))
        scores.append(_similarity(best, word))
        spare.remove(best)
    if len(scores) < len(term_words):
        return 0.0
    penalty = 0.12 * abs(len(span_words) - len(term_words))
    return max(0.0, statistics.fmean(scores) - penalty)


def _score(span: str, term: str) -> float:
    """Best of a straight near-homophone match and an order-insensitive phrase match.

    The straight path insists the two actually sound alike; without that floor,
    edit distance alone promotes any short word sharing a few letters. A span the
    recogniser left as a single word has to sound like the term almost exactly:
    that is what separates "face" from FAISS, which are the same sounds, from
    "fast" and FastAPI, which is a prefix and an ordinary word besides.
    """
    floor = SINGLE_WORD_FLOOR if " " not in span.strip() else PHONETIC_FLOOR
    direct = _similarity(span, term) if _sounds_like(span, term) >= floor else 0.0
    return max(direct, _phrase_similarity(span, term))


# --- profile ---------------------------------------------------------------


def _tokens(text: str) -> list[tuple[str, int, int]]:
    return [(m.group(0), m.start(), m.end()) for m in _TOKEN.finditer(text)]


def _is_junk_token(word: str) -> bool:
    """Documentation debris that passes a naive capitalisation test.

    Each rejection here is junk a real corpus produced: `HH MM SS` matched "him",
    `work/chunk` matched "working". None of it is vocabulary anyone says.
    """
    runs = [r for r in re.split(r"[^A-Za-z]+", word) if r]
    return (
        len(word) < 2
        or not any(c.isalpha() for c in word)
        or all(len(set(r.lower())) == 1 for r in runs)  # HH, MM, SS, YYYY-MM-DD
        or ("/" in word and not all(p.isupper() for p in word.split("/") if p))  # a path
        or word.rsplit(".", 1)[-1].lower() in FILE_SUFFIXES  # SKILL.md, content.json
    )


def _is_term_token(word: str) -> bool:
    """Does this look like a term rather than a word?"""
    if _is_junk_token(word):
        return False
    body = word[1:]
    return (
        word.isupper() and len(word) >= 2
        or any(c.isupper() for c in body)
        or any(c.isdigit() for c in word)
        or "." in body
        or "/" in word
    )


def _sentence_starts(text: str) -> set[int]:
    starts = set()
    for m in _SENTENCE.finditer(text):
        token = _TOKEN.search(text, m.start(), m.end())
        if token:
            starts.add(token.start())
    return starts


def _extract_terms(text: str) -> Counter:
    """Vocabulary: acronyms, mixed case, dotted or slashed identifiers, adjacent runs."""
    starts = _sentence_starts(text)
    found: Counter = Counter()
    run: list[str] = []
    previous_end = -1
    for word, start, end in _tokens(text):
        plain_capital = (
            not _is_junk_token(word)
            and word[:1].isupper()
            and word.lower() not in STOPWORDS
            and not _is_term_token(word)
        )
        keep = _is_term_token(word) or (plain_capital and start not in starts)
        if keep:
            found[word.strip(".")] += 1
            if start - previous_end <= 1 and run:
                run.append(word.strip("."))
            else:
                run = [word.strip(".")]
            if 2 <= len(run) <= 3:
                found[" ".join(run)] += 1
        else:
            run = []
        previous_end = end
    return found


def _extract_phrases(text: str) -> Counter:
    """Repeated multiword technical phrasing.

    A phrase counts when it is said twice, holds no stopwords or short words, and
    at least one of its words hardly ever appears outside it — which is what
    separates ``reciprocal rank fusion`` from ``every figure``.
    """
    words = [w.lower() for w, _, _ in _tokens(text) if w.isalpha()]
    alone = Counter(words)
    counts: Counter = Counter()
    for n in (2, 3):
        for i in range(len(words) - n + 1):
            gram = words[i : i + n]
            if all(len(w) >= 4 and w not in STOPWORDS for w in gram):
                counts[" ".join(gram)] += 1
    return Counter(
        {
            phrase: n
            for phrase, n in counts.items()
            if n >= 2 and min(alone[w] for w in phrase.split()) <= n
        }
    )


def _extract_ngrams(text: str) -> Counter:
    """Ordinary phrasing: 2- and 3-grams over lowercased words, nothing longer."""
    words = [w.lower() for w, _, _ in _tokens(text) if w.isalpha()]
    counts: Counter = Counter()
    for n in (2, 3):
        for i in range(len(words) - n + 1):
            counts[" ".join(words[i : i + n])] += 1
    return counts


def _sentences(text: str) -> list[tuple[str, int, int]]:
    out = []
    for m in _SENTENCE.finditer(text):
        body = m.group(0)
        lead = len(body) - len(body.lstrip())
        stripped = body.strip()
        if stripped:
            out.append((stripped, m.start() + lead, m.start() + lead + len(stripped)))
    return out


def _register(text: str) -> list[float]:
    lengths = []
    for body, _, _ in _sentences(text):
        words = [w for w, _, _ in _tokens(body) if w.isalpha()]
        if len(words) >= 4:
            lengths.append(statistics.fmean(len(w) for w in words))
    return lengths


def _also_written_lowercase(term: str, lowercase: set[str]) -> bool:
    """A capitalised token the speaker also types in lower case is an ordinary word.

    This is what separates Claude, which never appears lowercased, from BAND, Said,
    Fix and Seal, which are prose the corpus happened to capitalise in a heading.
    Mined lowercase phrases are exempt — being lowercase is the point of them.
    """
    if " " in term:
        return False
    low = term.lower().strip(".")
    return low in lowercase or low.rstrip("s") in lowercase or low + "s" in lowercase


def build_profile(texts, *, name: str, terms=()) -> dict:
    """Count how one person writes: their vocabulary, their phrasing, their register.

    ``terms`` seeds vocabulary that no extractor can find on its own — lowercase
    domain words like ``embeddings`` or ``reciprocal rank fusion``.
    """
    documents = [scrub(t) for t in texts]
    vocabulary: Counter = Counter()
    ngrams: Counter = Counter()
    lengths: list[float] = []
    words = 0
    for doc in documents:
        vocabulary += _extract_terms(doc)
        vocabulary += _extract_phrases(doc)
        ngrams += _extract_ngrams(doc)
        lengths += _register(doc)
        words += len(_tokens(doc))
    lowercase = {w for doc in documents for w, _, _ in _tokens(doc) if w.islower()}
    vocabulary = Counter(
        {t: n for t, n in vocabulary.items() if not _also_written_lowercase(t, lowercase)}
    )
    joined = " ".join(documents).lower()
    for seed in terms:
        seed = seed.strip()
        if seed:
            vocabulary[seed] = max(vocabulary.get(seed, 0), joined.count(seed.lower()), 1)
    return {
        "schema": SCHEMA,
        "name": name,
        "terms": dict(sorted(vocabulary.items())),
        "ngrams": dict(sorted(ngrams.items())),
        "corpus": {"documents": len(documents), "words": words, "sentences": len(lengths)},
        "register": {
            "word_len_mean": round(statistics.fmean(lengths), 3) if lengths else 0.0,
            "word_len_sd": round(statistics.stdev(lengths), 3) if len(lengths) > 1 else 0.0,
        },
    }


def load_profile(path) -> dict:
    """Read a profile, refusing anything this version does not understand."""
    try:
        profile = json.loads(Path(path).read_text())
    except json.JSONDecodeError as e:
        raise LexiconError(f"{path} is not a profile: {e}") from e
    if not isinstance(profile, dict) or profile.get("schema") != SCHEMA:
        raise LexiconError(f"{path}: profile schema {profile.get('schema')!r}, expected {SCHEMA}")
    for key in ("terms", "ngrams"):
        if not isinstance(profile.get(key), dict):
            raise LexiconError(f"{path}: profile has no {key}")
    return profile


# --- recovery --------------------------------------------------------------


def _windows(text: str):
    tokens = _tokens(text)
    for size in (1, 2, 3):
        for i in range(len(tokens) - size + 1):
            group = tokens[i : i + size]
            if any(
                not _CLAUSE_GAP.match(text[a[2] : b[1]])
                for a, b in zip(group, group[1:], strict=False)
            ):
                continue
            start, end = group[0][1], group[-1][2]
            words = [w for w, _, _ in group]
            if len(words[0]) < 3 or words[0].lower() in STOPWORDS:
                continue
            if words[-1].lower() in STOPWORDS or len(words[-1]) < 2:
                continue
            yield text[start:end], start, end


def _anchors(text: str, profile: dict) -> list[tuple[int, int]]:
    """Where the speaker's own vocabulary survived intact — the technical context."""
    spans = []
    for term in profile["terms"]:
        if len(term) < 3:
            continue
        for m in re.finditer(rf"\b{re.escape(term)}\b", text, re.I):
            spans.append((m.start(), m.end()))
    return sorted(spans)


def suggest_corrections(transcript: str, profile: dict, *, threshold: float = 0.72):
    """Spans that sound like the speaker's vocabulary but are not spelled like it.

    Nothing is applied. The result is a review list, ordered strongest first and
    never overlapping, so a person decides what the transcript actually said.
    """
    terms = profile["terms"]
    codes = {term: _code(term) for term in terms}
    known = {term.lower() for term in terms}
    anchors = _anchors(transcript, profile)
    candidates = []
    for span, start, end in _windows(transcript):
        if span.lower() in known or any(a < end and start < b for a, b in anchors):
            continue
        span_code = _code(span)
        single = " " not in span.strip()
        # A short span sounds like half the language; make it earn the correction.
        bar = min(0.97, threshold + 0.04 * max(0, 6 - len(_flat(span))))
        best, best_score = None, 0.0
        for term, code in codes.items():
            if single and len(_flat(term)) < SHORTEST_TERM:
                continue
            if (
                single
                and len(_flat(term)) <= SMALL_TARGET
                and SequenceMatcher(None, _flat(span), _flat(term)).ratio() < 0.9
            ):
                continue  # "lower" is not LoRA; "CICD" is CI/CD
            # ponytail: quick_ratio is an upper bound on the real score, so this
            # prefilter drops nothing; an index over code prefixes is the upgrade
            # if profiles ever get big enough for the scan to show up.
            if " " not in term:
                bound = 0.7 * SequenceMatcher(None, span_code, code).quick_ratio() + 0.3
                if bound < threshold:
                    continue
            score = _score(span, term)
            if score > best_score:
                best, best_score = term, score
        if best and best_score >= bar:
            candidates.append((best_score, start, end, span, best))
    groups: dict[tuple[str, str], list] = {}
    taken: list[tuple[int, int]] = []
    for score, start, end, span, term in sorted(candidates, key=lambda c: (-c[0], c[1])):
        if any(start < b and a < end for a, b in taken):
            continue
        if score < CERTAIN and not _in_context(start, end, anchors):
            continue
        taken.append((start, end))
        groups.setdefault((span.lower(), term), []).append((score, start, end, span))
    kept = []
    for (_, term), hits in groups.items():
        # One term mangled the same way thirty times is one row a person can read.
        score, start, end, span = max(hits)
        kept.append(
            Correction(
                span=span,
                start_char=start,
                end_char=end,
                suggestion=term,
                score=round(score, 3),
                reason=f"sounds like {term!r}, which the speaker uses "
                f"{terms[term]}x in their own writing",
                count=len(hits),
                offsets=tuple(sorted((s, e) for _, s, e, _ in hits)),
            )
        )
    return sorted(kept, key=lambda c: (-c.score, c.start_char))


def _in_context(start: int, end: int, anchors: list[tuple[int, int]]) -> bool:
    """A correction only fires near vocabulary that survived; otherwise it is ordinary English."""
    return any(
        (a >= end or b <= start) and a - end < CONTEXT_CHARS and start - b < CONTEXT_CHARS
        for a, b in anchors
    )


def apply_corrections(transcript: str, corrections) -> str:
    """Splice accepted corrections in. Callers do this on purpose, never by default."""
    edits = [
        (start, end, c.suggestion)
        for c in corrections
        for start, end in (c.offsets or [(c.start_char, c.end_char)])
    ]
    out = transcript
    for start, end, suggestion in sorted(edits, reverse=True):
        out = out[:start] + suggestion + out[end:]
    return out


# --- suspicion -------------------------------------------------------------


def flag_unlike_speaker(transcript: str, profile: dict, *, z: float = 3.0, novelty: float = 0.6):
    """Sentences phrased in a way this speaker's writing never is.

    Two conditions together, because either alone is noise: the sentence's
    two-word phrasings are absent from the profile, *and* its register sits far
    from the speaker's own. That pair is what invented text looks like.
    """
    ngrams = profile["ngrams"]
    mean = profile.get("register", {}).get("word_len_mean", 0.0)
    sd = max(profile.get("register", {}).get("word_len_sd", 0.0), 0.35)
    if not ngrams or not mean:
        return []
    flags = []
    for body, start, end in _sentences(transcript):
        words = [w.lower() for w, _, _ in _tokens(body) if w.isalpha()]
        if len(words) < 5:
            continue
        grams = [" ".join(words[i : i + 2]) for i in range(len(words) - 1)]
        unseen = sum(1 for g in grams if g not in ngrams) / len(grams)
        distance = (statistics.fmean(len(w) for w in words) - mean) / sd
        if unseen < novelty or distance < z:
            continue
        flags.append(
            Flag(
                span=body,
                start_char=start,
                end_char=end,
                why=f"{unseen:.0%} of its two-word phrasings never appear in the profile, "
                f"and its wording runs {distance:.1f} sd from the speaker's register",
                confidence=round(min(1.0, 0.5 * unseen + 0.5 * min(1.0, distance / 6.0)), 2),
            )
        )
    return flags
