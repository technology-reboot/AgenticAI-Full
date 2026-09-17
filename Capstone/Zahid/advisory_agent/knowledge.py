from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class KnowledgeChunk:
    source: str
    text: str


@dataclass(frozen=True)
class RetrievedChunk:
    source: str
    text: str
    score: int


class KnowledgeRetriever:
    """Small local retriever; replaceable with a vector store later."""

    def __init__(self, knowledge_dir: Path):
        self.chunks = self._load(knowledge_dir)

    @staticmethod
    def _load(knowledge_dir: Path) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []
        for path in sorted(knowledge_dir.glob("*.md")):
            sections = [section.strip() for section in path.read_text(encoding="utf-8").split("\n\n")]
            chunks.extend(KnowledgeChunk(path.name, section) for section in sections if section)
        return chunks

    def search(self, query: str, limit: int = 4) -> list[RetrievedChunk]:
        terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        scored = []
        for chunk in self.chunks:
            words = set(re.findall(r"[a-z0-9]+", chunk.text.lower()))
            score = len(terms & words)
            if score:
                scored.append(RetrievedChunk(chunk.source, chunk.text, score))
        return sorted(scored, key=lambda item: (-item.score, item.source))[:limit]
