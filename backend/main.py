import os
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .pipeline import RagPipeline, serialize_steps
from .rag import UPLOAD_DIR, clear_store, list_documents


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"

app = FastAPI(title="AI RAG Mini", version="0.1.0")
rag_pipeline = RagPipeline()
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class AskRequest(BaseModel):
    question: str
    top_k: int = 4


@app.get("/")
def home() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "evidence-rag",
        "llm_provider": os.getenv("LLM_PROVIDER", "ollama"),
        "documents": str(len(list_documents())),
    }


@app.get("/api/documents")
def documents() -> dict[str, object]:
    return {"documents": list_documents()}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)) -> dict[str, object]:
    allowed = {".txt", ".md", ".pdf"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="Upload a .txt, .md, or .pdf file.")

    safe_name = Path(file.filename or "document").name
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Files must be 10 MB or smaller for this prototype.")
    destination = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    destination.write_bytes(content)

    try:
        result = rag_pipeline.ingest(destination, safe_name)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "document": result.document,
        "pipeline_steps": serialize_steps(result.pipeline_steps),
    }


@app.post("/api/ask")
async def ask(payload: AskRequest) -> dict[str, object]:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")

    result = await rag_pipeline.answer(question, top_k=payload.top_k)
    return {
        "answer": result.answer,
        "sources": result.sources,
        "pipeline_steps": serialize_steps(result.pipeline_steps),
    }


@app.delete("/api/documents")
def reset_documents() -> dict[str, str]:
    clear_store()
    return {"status": "cleared"}
