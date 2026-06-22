# RAG Pipeline Project Guide

This guide explains the RAG pipeline as an interview-ready project. The goal is to show that you understand both the architecture and the implementation details behind a Retrieval-Augmented Generation system.

## What We Are Building

AI RAG Mini is a document question-answering system. A user uploads a document, the backend indexes it, and the user can ask questions that are answered using retrieved document context.

The core pipeline is:

```text
Document -> Parse -> Chunk -> Index -> Retrieve -> Augment -> Generate -> Answer with Sources
```

## Why This Project Is Valuable

This project demonstrates practical AI engineering skills:

- Building backend APIs for AI workflows.
- Handling file upload and text extraction.
- Designing chunking and retrieval logic.
- Integrating a local LLM with Ollama and Llama.
- Returning source-grounded answers.
- Explaining tradeoffs between a learning prototype and production RAG.

## Pipeline Stages

### 1. Document Loading

The user uploads a `.txt`, `.md`, or `.pdf` file through the frontend.

Backend route:

```text
POST /api/upload
```

The file is saved under:

```text
uploads/
```

### 2. Parsing

The backend extracts raw text from the uploaded file.

- Text and markdown files are read directly.
- PDF files are parsed using `pypdf`.

This creates plain text that can be chunked and indexed.

### 3. Chunking

The document is split into overlapping chunks.

Current values:

```text
chunk_size = 900 characters
overlap = 150 characters
```

Chunking matters because LLMs cannot always receive an entire document. Retrieval works better when the document is broken into smaller, focused pieces.

### 4. Indexing

Each chunk is converted into a searchable representation.

Current version:

```text
TF-IDF token vector
```

Storage:

```text
data/vector_store.json
```

This is intentionally simple. In a production version, this would become an embedding vector stored in `pgvector`, Chroma, Qdrant, or Pinecone.

### 5. Query Processing

When the user asks a question, the backend normalizes the question and turns it into a query vector.

Backend route:

```text
POST /api/ask
```

### 6. Retrieval

The app compares the question vector with every chunk vector using cosine similarity.

The top matching chunks are selected as sources.

Example output:

```json
{
  "doc_name": "resume.pdf",
  "chunk_index": 3,
  "score": 0.42,
  "text": "..."
}
```

### 7. Augmentation

The selected chunks are inserted into the LLM prompt as source context.

Prompt pattern:

```text
System instruction:
Answer only from the provided sources. Cite source numbers.

User question:
...

Sources:
Source 1: ...
Source 2: ...
```

This is the "augmented" part of Retrieval-Augmented Generation.

### 8. Generation

The backend calls the selected LLM provider.

Default:

```text
Ollama + llama3.1
```

Optional:

```text
OpenAI
```

The model receives the question and retrieved sources, then returns a grounded answer.

### 9. Response With Sources

The frontend displays:

- the answer
- source snippets
- document names
- chunk indexes
- similarity scores

This makes the response explainable.

## Code Mapping

| Pipeline Concept | File | Function/Class |
| --- | --- | --- |
| API routes | `backend/main.py` | `/api/upload`, `/api/ask` |
| Pipeline orchestration | `backend/pipeline.py` | `RagPipeline` |
| Text extraction | `backend/rag.py` | `_extract_text` |
| Chunking | `backend/rag.py` | `_chunk_text` |
| Index storage | `backend/rag.py` | `_load_store`, `_save_store` |
| Retrieval | `backend/rag.py` | `search` |
| LLM generation | `backend/rag.py` | `answer_with_llm` |
| Ollama integration | `backend/rag.py` | `_answer_with_ollama` |
| Browser UI | `frontend/` | `index.html`, `app.js`, `styles.css` |

## API Response Pipeline Trace

The API now returns `pipeline_steps` so the user can see what happened internally.

Example:

```json
{
  "answer": "...",
  "sources": [],
  "pipeline_steps": [
    {
      "name": "query",
      "status": "completed",
      "detail": "Normalized the user question"
    },
    {
      "name": "retrieve",
      "status": "completed",
      "detail": "Retrieved 3 source chunks"
    }
  ]
}
```

This is useful for demos because it shows the RAG system is a pipeline, not just a chatbot.

## Interview Explanation

You can explain the project like this:

```text
I built an end-to-end RAG pipeline that accepts document uploads, extracts text, chunks the document, indexes chunks into a local retrieval store, retrieves relevant context for user questions, and generates grounded answers using Llama through Ollama. The API also returns source snippets and pipeline trace steps so the system is explainable and easy to debug.
```

## Production Upgrade Path

To make this production-grade, upgrade each layer:

| Current Layer | Production Upgrade |
| --- | --- |
| Local JSON store | PostgreSQL + pgvector |
| TF-IDF retrieval | Embeddings with BGE/OpenAI/SentenceTransformers |
| Synchronous upload | Background jobs with Redis/Celery/RQ |
| Shared index | Per-user workspaces and auth |
| Basic citations | Page-level PDF citations |
| No metrics | Latency, token, and retrieval-quality monitoring |
| Manual testing | RAG evaluation test set |

## Showcase Checklist

Before showing this project in interviews, add:

- A clean GitHub README.
- Architecture diagram.
- Demo video.
- Sample documents.
- API examples.
- Explanation of RAG tradeoffs.
- One production upgrade, such as real embeddings or `pgvector`.

## Next Implementation Milestones

1. Add real embeddings.
2. Add a vector database.
3. Add page-aware PDF citations.
4. Add evaluation questions.
5. Add Docker.
6. Deploy the app.
7. Add an agent layer that can decide whether to answer, summarize, or ask for clarification.
