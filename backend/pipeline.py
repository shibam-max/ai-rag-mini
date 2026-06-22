from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .rag import answer_with_llm, ingest_document, search


@dataclass
class PipelineStep:
    name: str
    status: str
    detail: str


@dataclass
class IngestionResult:
    document: dict[str, Any]
    pipeline_steps: list[PipelineStep]


@dataclass
class AnswerResult:
    answer: str
    sources: list[dict[str, Any]]
    pipeline_steps: list[PipelineStep]


class RagPipeline:
    def ingest(self, source_path: Path, original_name: str) -> IngestionResult:
        steps = [
            PipelineStep("load", "completed", f"Received file: {original_name}"),
            PipelineStep("parse", "completed", "Extracted readable document text"),
            PipelineStep("chunk", "completed", "Split text into overlapping chunks"),
            PipelineStep("index", "completed", "Stored chunks in the local retrieval index"),
        ]
        document = ingest_document(source_path, original_name)
        steps[-2].detail = f"Created {document['chunk_count']} chunks"
        return IngestionResult(document=document, pipeline_steps=steps)

    async def answer(self, question: str, top_k: int = 4) -> AnswerResult:
        sources = search(question, top_k=top_k)
        steps = [
            PipelineStep("query", "completed", "Normalized the user question"),
            PipelineStep("retrieve", "completed", f"Retrieved {len(sources)} source chunks"),
            PipelineStep("augment", "completed", "Built an LLM prompt with retrieved context"),
            PipelineStep("generate", "completed", "Generated a grounded answer"),
        ]
        answer = await answer_with_llm(question, sources)
        return AnswerResult(answer=answer, sources=sources, pipeline_steps=steps)


def serialize_steps(steps: list[PipelineStep]) -> list[dict[str, str]]:
    return [asdict(step) for step in steps]
