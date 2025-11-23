"""
Shared dependencies, factories, and helper functions for the API.
"""
from typing import Any, Dict, List, Optional
import re
import uuid
from pathlib import Path

from agent_orchestrator import ProblemSetOrchestrator
from grading_agents import GradingOrchestrator
from vector_store import RAGVectorStore
from chunker import LLMChunker

# Storage directories
STORAGE_DIR = Path("api_storage")
PROBLEM_SETS_DIR = STORAGE_DIR / "problem_sets"
SUBMISSIONS_DIR = STORAGE_DIR / "submissions"
SAVED_MCQS_DIR = STORAGE_DIR / "saved_mcqs"
EXAMS_DIR = STORAGE_DIR / "exams"

# Create storage directories
PROBLEM_SETS_DIR.mkdir(parents=True, exist_ok=True)
SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
SAVED_MCQS_DIR.mkdir(parents=True, exist_ok=True)
EXAMS_DIR.mkdir(parents=True, exist_ok=True)

DOC_ID_SANITIZER = re.compile(r"[^a-zA-Z0-9_.-]+")

# Singletons for heavy objects
_vector_store_instance = None
_vector_store_error_logged = False


def get_vector_store() -> RAGVectorStore:
    """Get or create vector store instance with error handling."""
    global _vector_store_instance, _vector_store_error_logged
    
    if _vector_store_instance is None:
        import os
        
        # Check if we should use in-memory mode
        use_memory = os.environ.get("CHROMA_USE_MEMORY", "false").lower() == "true"
        
        if not use_memory:
            try:
                _vector_store_instance = RAGVectorStore()
            except (ValueError, AttributeError) as e:
                # Catch tenant/database errors and switch to in-memory
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in [
                    "tenant", "bindings", "could not connect", "does not exist"
                ]):
                    if not _vector_store_error_logged:
                        print("[API] ChromaDB error detected, automatically switching to in-memory mode")
                        print(f"[API] Error: {str(e)[:200]}")
                        _vector_store_error_logged = True
                    
                    # Force in-memory mode and retry
                    os.environ["CHROMA_USE_MEMORY"] = "true"
                    _vector_store_instance = RAGVectorStore()
                else:
                    raise
            except Exception as e:
                # For any other error, also try in-memory as fallback
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in [
                    "panic", "range", "corrupt"
                ]):
                    if not _vector_store_error_logged:
                        print("[API] ChromaDB corruption detected, switching to in-memory mode")
                        print(f"[API] Error: {str(e)[:200]}")
                        _vector_store_error_logged = True
                    
                    os.environ["CHROMA_USE_MEMORY"] = "true"
                    _vector_store_instance = RAGVectorStore()
                else:
                    raise
        else:
            # Already set to use memory
            _vector_store_instance = RAGVectorStore()
    
    return _vector_store_instance


def get_problem_set_orchestrator(vs: RAGVectorStore) -> ProblemSetOrchestrator:
    """Get problem set orchestrator instance."""
    return ProblemSetOrchestrator(vs)


def get_grading_orchestrator() -> GradingOrchestrator:
    """Get grading orchestrator instance."""
    return GradingOrchestrator()


def get_chunker() -> LLMChunker:
    """Get chunker instance."""
    return LLMChunker()


def sanitize_doc_id(raw: Optional[str]) -> str:
    """Normalize filenames into doc IDs compatible with the vector store."""
    if not raw:
        return f"document-{uuid.uuid4().hex[:6]}"
    cleaned = DOC_ID_SANITIZER.sub("-", raw).strip("-_.")
    cleaned = cleaned or f"document-{uuid.uuid4().hex[:6]}"
    return cleaned[:120]


def parse_topics(value: Optional[Any]) -> List[str]:
    """Convert stored metadata topics into a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def serialize_chunk_payload(
    chunk_id: str,
    doc_text: str,
    metadata: Dict[str, Any],
    score: Optional[float] = None,
) -> Dict[str, Any]:
    """Create a consistent chunk payload for API responses."""
    return {
        "chunk_id": chunk_id,
        "doc_id": metadata.get("doc_id"),
        "formatted": doc_text,
        "summary": metadata.get("summary", ""),
        "topics": parse_topics(metadata.get("topics")),
        "start": metadata.get("start"),
        "end": metadata.get("end"),
        "score": score,
    }
