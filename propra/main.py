"""
FastAPI entry point for the Propra LBO legal advisor.

Exposes POST /query — accepts a user question and optional Bundesland filter,
runs FAISS retrieval via rag.py, passes top chunks to the Anthropic API for
answer synthesis, and returns a structured response with citations.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── path setup ────────────────────────────────────────────────────────────────
# api.py sits at propra/ root; rag.py lives in propra/retrieval/
sys.path.insert(0, str(Path(__file__).resolve().parent / "retrieval"))
import rag  # noqa: E402  (must come after sys.path insert)

# ── env ───────────────────────────────────────────────────────────────────────
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY not set in .env")

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Propra LBO Advisor API",
    description="AI-gestützter Rechtsberater für das deutsche Bauordnungsrecht.",
    version="0.1.0",
)

# Allow Lovable frontend (and localhost for dev) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://*.lovable.app",  # Lovable preview URLs
        "https://*.lovableproject.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── load RAG index once at startup ───────────────────────────────────────────
_RETRIEVAL_DIR = Path(os.path.dirname(__file__)) / "retrieval"
retriever = rag.Retriever(
    index_path=_RETRIEVAL_DIR / "faiss.index",
    chunks_path=_RETRIEVAL_DIR / "chunks.pkl",
)

# ── Anthropic client ─────────────────────────────────────────────────────────
llm = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── Pydantic schemas ─────────────────────────────────────────────────────────


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Die Frage des Nutzers auf Deutsch oder Englisch.",
        examples=["Wie groß darf mein Carport in Bayern sein?"],
    )
    bundesland: Optional[str] = Field(
        default=None,
        description="ISO 3166-2 Länderkürzel, z. B. DE-BY für Bayern. Leer = alle Bundesländer.",
        examples=["DE-BY"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Anzahl der FAISS-Treffer, die an das LLM übergeben werden.",
    )


class Citation(BaseModel):
    paragraph: str
    jurisdiction: str
    text: str
    score: float = Field(description="Cosine similarity score (0–1).")


class QueryResponse(BaseModel):
    answer: str = Field(description="Antwort in einfachem Deutsch mit Quellenangaben.")
    citations: list[Citation]
    bundesland_filter: Optional[str]
    confidence: str = Field(description="HIGH | MEDIUM | LOW")


# ── system prompt (loaded from file per CLAUDE.md) ───────────────────────────
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "rag_answer.txt")


def _load_system_prompt() -> str:
    """Load the RAG answer synthesis prompt from file."""
    try:
        with open(PROMPT_PATH, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback inline prompt so the API works before prompts/ folder is set up.
        # Replace with the file version as soon as prompts/rag_answer.txt exists.
        return (
            "Du bist ein sachkundiger Assistent für deutsches Bauordnungsrecht. "
            "Beantworte die Frage ausschließlich auf Basis der bereitgestellten Gesetzesauszüge. "
            "Schreibe in einfachem Deutsch. "
            "Nenne immer den genauen Paragraphen und das Bundesland als Quelle. "
            "Schließe mit einem konkreten nächsten Schritt für den Nutzer ab. "
            "Wenn die Auszüge keine ausreichende Grundlage bieten, sage das klar — "
            "erfinde keine Regelungen."
        )


SYSTEM_PROMPT = _load_system_prompt()


# ── helper ────────────────────────────────────────────────────────────────────


def _build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block for the LLM."""
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(
            f"[{i}] {c['jurisdiction_label']} ({c['jurisdiction']}) · {c['source_paragraph']}\n{c['text']}"
        )
    return "\n\n".join(parts)


def _infer_confidence(chunks: list[dict], bundesland: Optional[str]) -> str:
    """
    Simple heuristic:
    - HIGH only if top chunk score > 0.72 AND bundesland was specified.
    - LOW  if top chunk score < 0.45.
    - MEDIUM otherwise.
    Never returns HIGH when corpus coverage may be incomplete (CLAUDE.md rule).
    """
    if not chunks:
        return "LOW"
    top_score = chunks[0]["score"]
    if top_score < 0.45:
        return "LOW"
    if top_score > 0.72 and bundesland:
        return "HIGH"
    return "MEDIUM"


# ── routes ────────────────────────────────────────────────────────────────────


@app.get("/health")
def health_check():
    """Liveness probe — returns 200 if the API is up and the index is loaded."""
    try:
        retriever._load()
        vector_count = retriever._index.ntotal
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ok", "vectors": vector_count}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """
    Main endpoint.

    1. FAISS retrieval  → top_k chunks (optionally filtered by Bundesland)
    2. Anthropic synthesis → plain-German answer with citations
    3. Return structured response
    """
    # 1. Retrieve — returns list[dict] with keys:
    #    chunk_id, jurisdiction, jurisdiction_label, source_paragraph, text, score
    try:
        chunks = retriever.retrieve(
            query=request.question,
            k=request.top_k,
            jurisdiction=request.bundesland,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    if not chunks:
        return QueryResponse(
            answer=(
                "Für Ihre Frage konnten keine relevanten Gesetzesauszüge gefunden werden. "
                "Bitte formulieren Sie Ihre Frage spezifischer oder wählen Sie ein Bundesland aus."
            ),
            citations=[],
            bundesland_filter=request.bundesland,
            confidence="LOW",
        )

    # 2. Synthesise with Anthropic
    context = _build_context(chunks)
    user_message = (
        f"Frage: {request.question}\n\n"
        f"Gesetzesauszüge:\n{context}"
    )

    try:
        response = llm.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        answer_text = response.content[0].text
    except anthropic.APIError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM error: {exc}",
        ) from exc

    # 3. Build response
    citations = [
        Citation(
            paragraph=c["source_paragraph"],
            jurisdiction=c["jurisdiction"],
            text=c["text"],
            score=round(c["score"], 4),
        )
        for c in chunks
    ]

    return QueryResponse(
        answer=answer_text,
        citations=citations,
        bundesland_filter=request.bundesland,
        confidence=_infer_confidence(chunks, request.bundesland),
    )
