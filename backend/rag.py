import json
import math
import os
import re
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - handled at runtime
    PdfReader = None


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
UPLOAD_DIR = ROOT_DIR / "uploads"
STORE_PATH = DATA_DIR / "vector_store.json"

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "with",
}


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)


def _load_store() -> dict[str, Any]:
    _ensure_dirs()
    if not STORE_PATH.exists():
        return {"documents": {}, "chunks": []}
    return json.loads(STORE_PATH.read_text(encoding="utf-8"))


def _save_store(store: dict[str, Any]) -> None:
    _ensure_dirs()
    STORE_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [word for word in words if word not in STOP_WORDS and len(word) > 1]


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks


def _extract_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        if PdfReader is None:
            raise RuntimeError("PDF support requires pypdf. Run: pip install -r requirements.txt")
        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return file_path.read_text(encoding="utf-8", errors="ignore")


def ingest_document(source_path: Path, original_name: str) -> dict[str, Any]:
    text = _extract_text(source_path)
    chunks = _chunk_text(text)
    if not chunks:
        raise ValueError("No readable text found in this file.")

    store = _load_store()
    doc_id = str(uuid.uuid4())
    store["documents"][doc_id] = {
        "id": doc_id,
        "name": original_name,
        "chunk_count": len(chunks),
    }

    for index, chunk in enumerate(chunks):
        store["chunks"].append(
            {
                "id": str(uuid.uuid4()),
                "doc_id": doc_id,
                "doc_name": original_name,
                "chunk_index": index,
                "text": chunk,
                "terms": Counter(_tokens(chunk)),
            }
        )

    _save_store(store)
    return store["documents"][doc_id]


def _idf(chunks: list[dict[str, Any]]) -> dict[str, float]:
    document_frequency: Counter[str] = Counter()
    for chunk in chunks:
        document_frequency.update(chunk["terms"].keys())

    total = max(1, len(chunks))
    return {
        term: math.log((1 + total) / (1 + frequency)) + 1
        for term, frequency in document_frequency.items()
    }


def _tfidf_vector(terms: Counter[str], idf: dict[str, float]) -> dict[str, float]:
    total_terms = sum(terms.values()) or 1
    return {term: (count / total_terms) * idf.get(term, 1.0) for term, count in terms.items()}


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    shared = set(left).intersection(right)
    numerator = sum(left[term] * right[term] for term in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def search(question: str, top_k: int = 4) -> list[dict[str, Any]]:
    store = _load_store()
    chunks = store["chunks"]
    if not chunks:
        return []

    idf = _idf(chunks)
    query_vector = _tfidf_vector(Counter(_tokens(question)), idf)
    ranked = []
    for chunk in chunks:
        chunk_vector = _tfidf_vector(Counter(chunk["terms"]), idf)
        score = _cosine(query_vector, chunk_vector)
        if score > 0:
            ranked.append({**chunk, "score": score})

    ranked.sort(key=lambda item: item["score"], reverse=True)
    if not ranked and _is_generic_document_question(question):
        latest_doc_id = next(reversed(store["documents"]), None)
        fallback_chunks = [
            chunk for chunk in chunks if chunk["doc_id"] == latest_doc_id
        ][:top_k]
        return [
            {
                "doc_name": item["doc_name"],
                "chunk_index": item["chunk_index"],
                "score": 0,
                "text": item["text"],
            }
            for item in fallback_chunks
        ]

    return [
        {
            "doc_name": item["doc_name"],
            "chunk_index": item["chunk_index"],
            "score": round(item["score"], 4),
            "text": item["text"],
        }
        for item in ranked[:top_k]
    ]


def _is_generic_document_question(question: str) -> bool:
    normalized = question.lower()
    generic_phrases = [
        "what is this",
        "what's this",
        "summarize",
        "summary",
        "about this",
        "this document",
        "this pdf",
        "the document",
        "the pdf",
    ]
    return any(phrase in normalized for phrase in generic_phrases)


async def answer_with_llm(question: str, sources: list[dict[str, Any]]) -> str:
    context = "\n\n".join(
        f"Source {index + 1} ({source['doc_name']} chunk {source['chunk_index']}):\n{source['text']}"
        for index, source in enumerate(sources)
    )

    if not sources:
        return (
            "I could not find matching context for that question. "
            "Try asking about a specific topic, name, skill, project, or section from the document."
        )

    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    if provider == "ollama":
        return await _answer_with_ollama(question, context)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return (
            "I found relevant document context, but no LLM API key is configured. "
            "Set LLM_PROVIDER=ollama for local Llama or add OPENAI_API_KEY for OpenAI. "
            "Here are the strongest matching snippets to review."
        )

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise RAG assistant. Answer only from the provided sources. "
                        "If the sources do not contain the answer, say that clearly. "
                        "Cite source numbers in the answer."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nSources:\n{context}",
                },
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or "No answer generated."
    except Exception as exc:  # pragma: no cover - external API behavior
        return f"LLM call failed: {exc}"


async def _answer_with_ollama(question: str, context: str) -> str:
    model = os.getenv("OLLAMA_MODEL", "llama3.1")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    prompt = (
        "You are a precise RAG assistant. Answer only from the provided sources. "
        "If the sources do not contain the answer, say that clearly. "
        "Cite source numbers in the answer.\n\n"
        f"Question: {question}\n\nSources:\n{context}"
    )

    try:
        import httpx

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip() or "No answer generated by Ollama."
    except Exception as exc:  # pragma: no cover - local service behavior
        return (
            f"Ollama/Llama call failed: {exc}. "
            f"Make sure Ollama is running and the model is pulled with: ollama pull {model}"
        )


def list_documents() -> list[dict[str, Any]]:
    store = _load_store()
    return list(store["documents"].values())


def clear_store() -> None:
    _save_store({"documents": {}, "chunks": []})
