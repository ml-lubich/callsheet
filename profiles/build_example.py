#!/usr/bin/env python3
"""Regenerate profiles/example-engineer.json.

The shipped profile is derived, not hand-edited. Run this after changing the
extractor so the committed profile always matches the code that reads it:

    python3 profiles/build_example.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from callsheet.lexicon import build_profile  # noqa: E402

# Curated vocabulary. These are authoritative: a term mined from prose must
# never outrank one of these, because these are the words the guardrail exists
# to recover.
SEED = [
    "FAISS", "BM25", "Cognee", "LangGraph", "ChromaDB", "Pinecone", "SQLite",
    "PyTorch", "OpenCV", "easyOCR", "FastAPI", "Cloudflare", "Vercel", "Fly.io",
    "Databricks", "Bedrock", "Salesforce", "ServiceNow", "Freshdesk", "Shopify",
    "RRF", "reciprocal rank fusion", "RAG", "GraphRAG", "VLM", "OCR", "CI/CD",
    "semantic versioning", "monorepo", "Kubernetes", "Terraform", "Postgres",
    "Redis", "gRPC", "OAuth", "webhook", "idempotency", "backpressure", "p99",
    "embeddings", "reranker", "quantization", "LoRA", "vLLM", "Ollama",
    "llama.cpp", "Whisper", "diarization",
    # Agent and model names. Speech recognisers mangle these constantly —
    # "Claude" comes back as "clawed" or "cloud", "DeepSeek" as "deep seek" —
    # and they are exactly the words a write-up will quote.
    "Claude", "Claude Code", "Cursor", "Copilot", "ChatGPT", "OpenAI",
    "Anthropic", "DeepSeek", "Llama", "Mistral", "Gemini", "AgentForce",
]

# Prose corpus: the repo's own documentation, so ordinary English is represented
# and the extractor can tell a term from a capitalised word.
DOCS = sorted(
    [p for p in (ROOT / "skills").rglob("*.md")]
    + [ROOT / "README.md", ROOT / "SKILL.md", ROOT / "profiles" / "README.md"]
)


def main() -> int:
    texts = [p.read_text() for p in DOCS if p.exists()]
    profile = build_profile(texts, name="example-engineer", terms=SEED)
    # The prose corpus is here to teach the profile what ordinary English looks
    # like — its n-grams and register — not to contribute vocabulary. Terms
    # mined from documentation ("return edge", "required gates") are phrases
    # about the tool, not words a speaker would have mangled, and every one of
    # them is a false positive waiting to happen. Ship the curated list only.
    profile["terms"] = {t: profile["terms"][t] for t in SEED if t in profile["terms"]}
    missing = [t for t in SEED if t not in profile["terms"]]
    if missing:
        print(f"seed terms did not survive: {missing}", file=sys.stderr)
        return 1
    out = ROOT / "profiles" / "example-engineer.json"
    out.write_text(json.dumps(profile, indent=1, sort_keys=True) + "\n")
    print(f"{out.relative_to(ROOT)}: {len(profile['terms'])} terms "
          f"from {len(texts)} documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
