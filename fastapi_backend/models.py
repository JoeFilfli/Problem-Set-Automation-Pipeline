"""
Data models for RAG pipeline.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class Chunk:
    """Represents a semantic chunk of text from a document."""
    formatted: str
    summary: str
    topics: List[str]
    start: int
    end: int
