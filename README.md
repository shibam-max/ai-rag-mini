# Evident AI

Evident AI is a local-first, evidence-grounded knowledge workspace. Upload a PDF, Markdown file, or text document, ask a question, and inspect the retrieved passages behind the answer. It is a small but complete RAG product prototype designed to demonstrate applied AI engineering: ingestion, retrieval, provider abstraction, grounded generation, a usable product surface, and a credible path to AWS.

## What This Prototype Demonstrates

- End-to-end RAG: upload, parse, chunk, retrieve, augment, generate, and cite.
- Local operation with Ollama and Llama; no cloud account is required.
- An optional OpenAI provider boundary.
- Evidence snippets and retrieval scores with every answer.
- Useful local fallback answers when no model runtime is available.
- File-type and size validation, randomized upload filenames, and controlled CORS.
- Docker packaging for reproducible local development and future deployment.

## Quick Start

```powershell
cd C:\AI_Solutions\ai-rag-mini
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
ollama pull llama3.1
$env:OLLAMA_MODEL="llama3.1"
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`, add `sample_document.txt`, then ask a question. If Ollama is unavailable, upload and retrieval still work, returning cited local evidence rather than a failed chat response.

## Container Run

With Ollama running on the host:

```powershell
docker compose up --build
```

The app is available at `http://127.0.0.1:8000`. The `data/` and `uploads/` directories are mounted as local volumes so an index survives a container restart.

## Architecture

```text
Browser workspace
        |
        v
FastAPI API + static UI
        |
        +--> upload validation -> text extraction -> chunking -> local retrieval store
        |
        +--> question -> TF-IDF retrieval -> grounded prompt -> Ollama / OpenAI
                                                        |
                                                        v
                                              answer + evidence snippets
```

The first retrieval implementation is intentionally inspectable TF-IDF plus cosine similarity. The first production upgrade is a pluggable embedding adapter backed by `pgvector` or OpenSearch vector search.

## AWS-Native Target

The Docker image keeps the application portable. The recommended AWS production shape is:

```text
CloudFront + WAF -> Application Load Balancer -> ECS Fargate (FastAPI)
                                           |                  |
                                           v                  v
                                      S3 original files   Aurora PostgreSQL + pgvector
                                           |
                              SQS -> ECS worker or Lambda -> Amazon Bedrock

CloudWatch / X-Ray / CloudTrail / Secrets Manager / KMS span the platform.
```

This is a target design, not a claim that the prototype already provisions AWS infrastructure. The current local JSON store and synchronous ingestion are intentionally narrow prototype choices.

## Security Roadmap

1. Prototype now: local-only data, file validation, controlled CORS, no secrets in the repository, grounded prompts, and visible sources.
2. Before a public pilot: Cognito authentication, tenant/workspace isolation, S3 presigned uploads, malware scanning, rate limiting, audit events, structured logs, and prompt-injection evaluations.
3. Production: IAM least privilege, private VPC subnets, KMS encryption, Secrets Manager, WAF, retrieval authorization, data retention/deletion workflows, redaction, threat modeling, and continuous RAG quality checks.

## Next Build Steps

- Semantic embeddings with a local model and a Bedrock provider adapter.
- Page-level citations and retrieval quality evaluation datasets.
- User workspaces and role-based access control.
- Asynchronous ingestion with traces and operational metrics.
- Infrastructure as code for the AWS target after the product contract stabilizes.

## Project Layout

```text
backend/              FastAPI routes, RAG pipeline, local retrieval implementation
frontend/             Product workspace UI
data/                 Local index, created at runtime
uploads/              Local uploaded files, created at runtime
Dockerfile            Portable service image
docker-compose.yml    Local container run
```

See [ARCHITECTURE.md](ARCHITECTURE.md) and [RAG_PIPELINE.md](RAG_PIPELINE.md) for the implementation walkthrough.
