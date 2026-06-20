from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .rag import UPLOAD_DIR, answer_with_llm, clear_store, ingest_document, list_documents, search


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"

app = FastAPI(title="AI RAG Mini", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
    return {"status": "ok"}


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
    destination = UPLOAD_DIR / safe_name
    destination.write_bytes(await file.read())

    try:
        document = ingest_document(destination, safe_name)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"document": document}


@app.post("/api/ask")
async def ask(payload: AskRequest) -> dict[str, object]:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")

    sources = search(question, top_k=payload.top_k)
    answer = await answer_with_llm(question, sources)
    return {"answer": answer, "sources": sources}


@app.delete("/api/documents")
def reset_documents() -> dict[str, str]:
    clear_store()
    return {"status": "cleared"}
