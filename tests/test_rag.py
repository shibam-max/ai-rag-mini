import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from backend import main, rag


class AskRequestTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_rejects_top_k_outside_supported_range(self):
        with patch.object(main.rag_pipeline, "answer", new_callable=AsyncMock) as answer:
            for top_k in (0, 11):
                with self.subTest(top_k=top_k):
                    response = self.client.post(
                        "/api/ask",
                        json={"question": "What is in this document?", "top_k": top_k},
                    )

                    self.assertEqual(response.status_code, 422)
            answer.assert_not_awaited()

    def test_trims_question_before_processing(self):
        result = SimpleNamespace(answer="Answer", sources=[], pipeline_steps=[])
        with patch.object(
            main.rag_pipeline,
            "answer",
            new_callable=AsyncMock,
            return_value=result,
        ) as answer:
            response = self.client.post(
                "/api/ask",
                json={"question": "  What is in this document?  "},
            )

        self.assertEqual(response.status_code, 200)
        answer.assert_awaited_once_with("What is in this document?", top_k=4)


class OllamaFallbackTests(unittest.IsolatedAsyncioTestCase):
    async def test_unavailable_ollama_returns_extractive_answer(self):
        sources = [{
            "doc_name": "guide.md",
            "chunk_index": 0,
            "text": "The service retries three times before reporting failure.",
        }]

        class UnavailableOllama:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return None

            async def post(self, *_args, **_kwargs):
                raise httpx.ConnectError("Ollama is unavailable")

        with (
            patch.dict("os.environ", {"LLM_PROVIDER": "ollama"}),
            patch("httpx.AsyncClient", return_value=UnavailableOllama()),
        ):
            answer = await rag.answer_with_llm("How many times does it retry?", sources)

        self.assertIn("three times", answer)
        self.assertIn("[Source 1]", answer)
