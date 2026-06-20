# AI RAG Mini Architecture

This document explains the system design of AI RAG Mini: how the frontend, backend, retrieval layer, document store, and Llama model work together.

## High-Level System

```text
Browser UI
   |
   | upload document / ask question
   v
FastAPI Backend
   |
   | document ingestion
   v
Text Extraction + Chunking
   |
   | chunks + token vectors
   v
Local JSON Retrieval Store
   |
   | question search
   v
Top Matching Chunks
   |
   | prompt with sources
   v
Ollama + Llama
   |
   | grounded answer
   v
Browser UI
```

## Main Components

### 1. Frontend

Files:

```text
frontend/index.html
frontend/styles.css
frontend/app.js
```

Responsibilities:

- Render the upload form.
- Render the document list.
- Render the chat interface.
- Send uploaded files to `POST /api/upload`.
- Send user questions to `POST /api/ask`.
- Display the answer and retrieved source snippets.

The frontend is intentionally built with plain HTML, CSS, and JavaScript. This keeps the first version easy to understand before moving to React, Next.js, or a larger UI framework.

### 2. FastAPI Backend

File:

```text
backend/main.py
```

Responsibilities:

- Serve the frontend.
- Expose API endpoints.
- Accept document uploads.
- Pass uploaded files to the RAG pipeline.
- Accept user questions.
- Return answers and source chunks.

Endpoints:

```text
GET    /
GET    /api/health
GET    /api/documents
POST   /api/upload
POST   /api/ask
DELETE /api/documents
```

### 3. RAG Pipeline

File:

```text
backend/rag.py
```

Responsibilities:

- Extract text from files.
- Split text into chunks.
- Convert chunks into searchable term vectors.
- Search for relevant chunks.
- Build an LLM prompt using retrieved sources.
- Call Ollama or OpenAI.
- Return the final answer.

The RAG pipeline has two major phases: ingestion and question answering.

## Ingestion Flow

```text
User uploads file
   |
   v
POST /api/upload
   |
   v
Save file in uploads/
   |
   v
Extract text
   |
   v
Split text into chunks
   |
   v
Create term-frequency vectors
   |
   v
Save chunks in data/vector_store.json
```

### Text Extraction

The app supports:

- `.txt`
- `.md`
- `.pdf`

Text and markdown files are read directly. PDF files are parsed with `pypdf`.

### Chunking

Documents are split into overlapping chunks.

Current settings:

```text
chunk_size = 900 characters
overlap = 150 characters
```

Overlap helps preserve context when an important sentence is near the boundary between two chunks.

### Local Retrieval Store

The first version stores indexed data in:

```text
data/vector_store.json
```

Each chunk contains:

- chunk id
- document id
- document name
- chunk index
- chunk text
- token frequency map

This is not a production vector database. It is a learning-friendly local store that makes the retrieval process easy to inspect.

## Question Answering Flow

```text
User asks question
   |
   v
POST /api/ask
   |
   v
Convert question to token vector
   |
   v
Compare question vector with chunk vectors
   |
   v
Select top matching chunks
   |
   v
Build prompt with question + sources
   |
   v
Call Ollama/Llama
   |
   v
Return answer + source snippets
```

## Retrieval Design

The current retrieval engine uses:

- tokenization
- stop-word removal
- TF-IDF weighting
- cosine similarity

This is a simple version of vector search. Instead of neural embeddings, it uses word frequency and importance. It is useful for learning because the algorithm is readable and does not require another model.

Production RAG systems usually replace this layer with:

- OpenAI embeddings
- Sentence Transformers
- BGE embeddings
- `pgvector`
- Chroma
- Qdrant
- Pinecone

## Generic Question Handling

Questions like these may not share many exact words with the document:

```text
what is this pdf?
summarize this document
what is this about?
```

For those cases, the app falls back to the latest uploaded document and sends its first chunks to the LLM. This makes summary-style questions work better in the simple TF-IDF version.

## LLM Provider Layer

The app supports two answer providers.

### Ollama + Llama

Default provider:

```text
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

The backend calls:

```text
POST /api/generate
```

on the local Ollama server.

### OpenAI

Optional provider:

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
```

The same retrieved chunks are sent to OpenAI instead of Ollama.

## Prompt Design

The LLM receives:

- a system instruction
- the user question
- retrieved source chunks

The model is instructed to:

- answer only from the provided sources
- say clearly when the answer is not in the sources
- cite source numbers

This reduces hallucination and makes the answer traceable to the uploaded document.

## Data Flow Example

```text
Question:
"What skills are mentioned?"

Retrieved source:
"Python, FastAPI, machine learning, RAG, vector databases..."

Prompt sent to Llama:
"Answer only from the provided sources..."

Final response:
"The document mentions Python, FastAPI, machine learning, RAG, and vector databases. [Source 1]"
```

## Deployment View

Current local setup:

```text
User Browser
   |
   v
FastAPI app on localhost:8000
   |
   v
Local files: uploads/ and data/vector_store.json
   |
   v
Ollama on localhost:11434
```

For production, this could become:

```text
Web Client
   |
   v
Backend API
   |
   +--> Object storage for uploaded files
   +--> PostgreSQL + pgvector for chunks and embeddings
   +--> Redis for background jobs
   +--> Hosted LLM or dedicated model server
```

## Future Production Architecture

Recommended upgrades:

- Replace local JSON with PostgreSQL.
- Replace TF-IDF with embedding vectors.
- Use `pgvector` or Qdrant for similarity search.
- Add background workers for large uploads.
- Add auth and per-user indexes.
- Store file metadata separately from chunk data.
- Add page-level citations for PDFs.
- Add observability for latency, token usage, and failed LLM calls.
- Add RAG evaluation with expected questions and answers.

## Design Tradeoffs

| Decision | Why It Was Chosen | Production Upgrade |
| --- | --- | --- |
| Plain HTML frontend | Easy to understand | Next.js or React |
| Local JSON store | Transparent and simple | PostgreSQL + pgvector |
| TF-IDF retrieval | No embedding dependency | Neural embeddings |
| Ollama default | Local Llama without API cost | Hosted model or managed inference |
| Single shared index | Faster to build | Per-user workspaces |
| Synchronous upload | Simple control flow | Background workers |

## Summary

AI RAG Mini is a learning-first RAG system. It demonstrates the core design pattern used in many production AI applications:

```text
documents -> chunks -> retrieval -> prompt -> LLM answer -> citations
```

Once this foundation is clear, the project can be upgraded into a production-style AI document assistant, resume analyzer, customer support bot, internal knowledge-base agent, or codebase onboarding assistant.
