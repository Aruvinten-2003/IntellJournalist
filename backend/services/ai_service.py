"""OpenAI-backed news analysis with a deterministic fallback."""

import logging
from collections.abc import AsyncIterator, Sequence

from openai import AsyncOpenAI

from ..config import settings
from ..models import Article
from .summarizer import Summarizer


logger = logging.getLogger(__name__)


class AIService:
    def __init__(self) -> None:
        self.summarizer = Summarizer()
        self.model = settings.openai_model
        self.client = (
            AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())
            if settings.openai_api_key
            else None
        )

    def build_messages(
        self,
        prompt: str,
        context: Sequence[Article],
    ) -> list[dict[str, str]]:
        context_text = self.summarizer.build_context(context)
        return [
            {
                "role": "system",
                "content": (
                    "You are Intell Journalist, a careful news research assistant. "
                    "Answer only from the supplied reporting. Distinguish confirmed facts "
                    "from uncertainty, stay concise, and cite sources using [1], [2], etc.\n\n"
                    f"Reporting:\n{context_text}"
                ),
            },
            {"role": "user", "content": prompt},
        ]

    def fallback_answer(self, question: str, context: Sequence[Article]) -> str:
        if not context:
            return "No matching reports are available yet. Try a broader news topic."
        summaries = [
            f"{article.title}: {self.summarizer.summarize_article(article, 1)} [{index}]"
            for index, article in enumerate(context[:3], start=1)
        ]
        lead = "Based on the current reports, " if question else "Current briefing: "
        return lead + " ".join(summaries)

    async def answer_question(
        self,
        question: str,
        context: Sequence[Article],
    ) -> str:
        if self.client is None:
            return self.fallback_answer(question, context)
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self.build_messages(question, context),
                temperature=0.2,
            )
            answer = response.choices[0].message.content
            return answer.strip() if answer else self.fallback_answer(question, context)
        except Exception:
            logger.exception("OpenAI answer generation failed; using local fallback")
            return self.fallback_answer(question, context)

    async def stream_answer(
        self,
        question: str,
        context: Sequence[Article],
    ) -> AsyncIterator[str]:
        if self.client is None:
            yield self.fallback_answer(question, context)
            return
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=self.build_messages(question, context),
                temperature=0.2,
                stream=True,
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception:
            logger.exception("OpenAI streaming failed; using local fallback")
            yield self.fallback_answer(question, context)

    async def compare_sources(
        self,
        prompt: str,
        articles: Sequence[Article],
    ) -> str:
        request = (
            f"{prompt}\nCompare how the supplied publishers frame the event. "
            "Identify agreement, differences in emphasis, and missing evidence."
        )
        return await self.answer_question(request, articles)

    @staticmethod
    def suggest_follow_ups(_answer: str) -> list[str]:
        return [
            "What facts do the sources agree on?",
            "Where do the sources differ?",
            "What remains uncertain?",
        ]

    @staticmethod
    def format_citation(article: Article, index: int = 1) -> dict[str, str]:
        return {
            "label": f"[{index}] {article.publisher}",
            "title": article.title,
            "url": str(article.url),
        }


def suggest_follow_ups(answer: str) -> list[str]:
    return AIService.suggest_follow_ups(answer)


def build_messages(prompt: str, context: Sequence[Article]) -> list[dict[str, str]]:
    return AIService().build_messages(prompt, context)


def format_citation(article: Article) -> str:
    return f"{article.title} — {article.publisher}: {article.url}"
