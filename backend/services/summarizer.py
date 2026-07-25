"""Deterministic text cleanup and summarisation helpers."""

import re
from collections.abc import Sequence
from html import unescape

from ..models import Article


class Summarizer:
    """Prepare concise article context without requiring an external AI service."""

    _tag_pattern = re.compile(r"<[^>]+>")
    _space_pattern = re.compile(r"\s+")
    _sentence_pattern = re.compile(r"(?<=[.!?])\s+")

    def clean_text(self, text: str | None) -> str:
        if not text:
            return ""
        without_tags = self._tag_pattern.sub(" ", unescape(text))
        return self._space_pattern.sub(" ", without_tags).strip()

    def split_sentences(self, text: str) -> list[str]:
        cleaned = self.clean_text(text)
        return [sentence.strip() for sentence in self._sentence_pattern.split(cleaned) if sentence.strip()]

    def extractive_summary(self, text: str, max_sentences: int = 2) -> str:
        sentences = self.split_sentences(text)
        return " ".join(sentences[:max(1, max_sentences)])

    def summarize_article(self, article: Article, max_sentences: int = 2) -> str:
        material = article.content or article.excerpt
        return self.extractive_summary(material, max_sentences) or article.excerpt

    def summarize_articles(self, articles: Sequence[Article], max_sentences: int = 1) -> list[str]:
        return [self.summarize_article(article, max_sentences) for article in articles]

    def build_context(self, articles: Sequence[Article], max_characters: int = 12_000) -> str:
        sections = []
        for index, article in enumerate(articles, start=1):
            sections.append(
                f"[{index}] {article.title}\n"
                f"Publisher: {article.publisher}\n"
                f"Summary: {self.summarize_article(article, 3)}\n"
                f"URL: {article.url}"
            )
        return self.truncate("\n\n".join(sections), max_characters)

    @staticmethod
    def truncate(text: str, max_characters: int) -> str:
        if len(text) <= max_characters:
            return text
        return text[: max(0, max_characters - 1)].rstrip() + "…"
