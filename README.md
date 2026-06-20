# AI RAG Mini

AI RAG Mini is a small end-to-end Retrieval-Augmented Generation application. It lets a user upload a document, ask questions about it, retrieve the most relevant document chunks, and generate an answer using a local Llama model through Ollama.

This project is intentionally simple so the complete AI application flow is easy to understand before upgrading to production tools like real embedding models, `pgvector`, Chroma, Qdrant, authentication, and cloud deployment.

## Problem It Solves

Most documents are hard to search manually. Resumes, reports, policies, PDFs, meeting notes, and technical guides often contain useful information, but users need to read through the whole file to find answers.

AI RAG Mini solves this by:

- Uploading a document.
- Breaking it into searchable chunks.
- Finding the most relevant chunks for a user question.
- Sending only those chunks to an LLM.
- Returning an answer with the supporting source text.

This is the foundation behind real-world AI products like support bots, resume analyzers, legal document assistants, internal knowledge-base chat, and codebase onboarding agents.

## Features

- Upload `.txt`, `.md`, and `.pdf` documents.
- Extract readable text from uploaded files.
- Split documents into overlapping chunks.
- Store chunks in a local JSON-backed retrieval store.
- Search chunks using a simple TF-IDF similarity algorithm.
- Answer questions using local Llama through Ollama.
- Optional OpenAI provider support.
- Show retrieved source snippets in the UI.
- Serve frontend and backend from one FastAPI app.

## Technology Used

| Area | Technology | Why It Is Used |
| --- | --- | --- |
| Backend API | FastAPI | Lightweight Python API framework for upload and chat endpoints |
| Frontend | HTML, CSS, JavaScript | Simple browser UI without extra build tooling |
| PDF Parsing | pypdf | Extracts text from uploaded PDF files |
| Retrieval | TF-IDF + cosine similarity | Simple local retrieval method for learning RAG concepts |
| Local LLM | Ollama + Llama | Runs Llama locally without paid API keys |
| Optional Cloud LLM | OpenAI API | Alternative hosted LLM provider |
| Storage | Local JSON file | Keeps the first version easy to inspect and debug |
| HTTP Client | httpx | Calls Ollama from the backend |

## Project Structure

```text
ai-rag-mini/
  backend/
    __init__.py
    main.py        # FastAPI app and API routes
    rag.py         # document ingestion, retrieval, and LLM calls
  frontend/
    index.html     # app UI
    styles.css     # app styling
    app.js         # upload, chat, and API calls
  data/
    vector_store.json
  uploads/
  requirements.txt
  sample_document.txt
  README.md
  ARCHITECTURE.md
```

## Installation

From the project root:

```cmd
cd C:\AI_Solutions\ai-rag-mini
pip install -r requirements.txt
```

If you prefer a virtual environment:

```cmd
cd C:\AI_Solutions\ai-rag-mini
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Llama Setup With Ollama

Install Ollama:

```text
https://ollama.com
```

Pull the Llama model:

```cmd
ollama pull llama3.1
```

Set the model in Command Prompt:

```cmd
set LLM_PROVIDER=ollama
set OLLAMA_MODEL=llama3.1
```

PowerShell version:

```powershell
$env:LLM_PROVIDER="ollama"
$env:OLLAMA_MODEL="llama3.1"
```

The app defaults to `LLM_PROVIDER=ollama`, so setting `OLLAMA_MODEL` is usually enough.

## Run The App

Command Prompt:

```cmd
cd C:\AI_Solutions\ai-rag-mini
set OLLAMA_MODEL=llama3.1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

PowerShell:

```powershell
cd C:\AI_Solutions\ai-rag-mini
$env:OLLAMA_MODEL="llama3.1"
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open the app:

```text
http://127.0.0.1:8000
```

## Optional OpenAI Setup

To use OpenAI instead of local Llama:

Command Prompt:

```cmd
set LLM_PROVIDER=openai
set OPENAI_API_KEY=your_api_key
set OPENAI_MODEL=gpt-4o-mini
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

PowerShell:

```powershell
$env:LLM_PROVIDER="openai"
$env:OPENAI_API_KEY="your_api_key"
$env:OPENAI_MODEL="gpt-4o-mini"
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

## How To Use

1. Start Ollama and run the FastAPI server.
2. Open `http://127.0.0.1:8000`.
3. Upload a `.txt`, `.md`, or `.pdf` file.
4. Ask a question about the uploaded document.
5. Review the answer and source snippets.

Good starter questions:

```text
summarize this document
what is this pdf about?
what skills are mentioned?
what are the important points?
```

## API Endpoints

```text
GET    /api/health       health check
GET    /api/documents    list indexed documents
POST   /api/upload       upload and index a document
POST   /api/ask          ask a question over indexed documents
DELETE /api/documents    clear local document index
```

## Current Limitations

- Retrieval uses TF-IDF instead of real neural embeddings.
- Storage is local JSON, not a production database.
- There is no user authentication.
- All documents share one local index.
- Large PDFs may be slower because text extraction and indexing are local.
- The app depends on Ollama running locally for Llama answers.

## Roadmap

- Replace TF-IDF with embedding models.
- Add `pgvector`, Chroma, Qdrant, or Pinecone.
- Add user login and per-user document spaces.
- Add chat history.
- Add citations with exact page numbers.
- Add Docker support.
- Add deployment instructions.
- Add evaluation tests for answer quality.
- Add agent tools for actions like ticket creation, database lookup, or report generation.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the system design, request flow, and component-level explanation.
