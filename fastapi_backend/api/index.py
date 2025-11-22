from typing import Any, Dict, List, Optional
import json
import traceback
import re
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI

from agent_orchestrator import ProblemSetOrchestrator
from grading_agents import GradingOrchestrator
from vector_store import RAGVectorStore
from chunker import LLMChunker
from pdf_extractor import extract_pdf_text_from_bytes

# Storage directories
STORAGE_DIR = Path("api_storage")
PROBLEM_SETS_DIR = STORAGE_DIR / "problem_sets"
SUBMISSIONS_DIR = STORAGE_DIR / "submissions"

# Create storage directories
PROBLEM_SETS_DIR.mkdir(parents=True, exist_ok=True)
SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)


### Create FastAPI instance with custom docs and openapi url
app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/py/helloFastApi")
def hello_fast_api():
    return {"message": "Hello from FastAPI"}


# ---------- Request / response models ----------


class GenerateProblemSetRequest(BaseModel):
    doc_id: str
    num_problems: int = 5
    check_quality: bool = True


class StudentSubmission(BaseModel):
    name: str
    solution: str


class GradeSubmissionsRequest(BaseModel):
    problem: Dict[str, Any]
    correct_solution: str
    student_submissions: List[StudentSubmission]


class RAGQueryRequest(BaseModel):
    query: str
    doc_id: Optional[str] = None
    top_k: int = 4


class RAGChatMessage(BaseModel):
    role: str
    content: str


class RAGChatRequest(RAGQueryRequest):
    history: List[RAGChatMessage] = []


class StoreProblemSetRequest(BaseModel):
    problem_set: Dict[str, Any]
    title: Optional[str] = None


class StoreSubmissionRequest(BaseModel):
    problem_set_id: str
    problem_id: int
    student_name: str
    solution: str


DOC_ID_SANITIZER = re.compile(r"[^a-zA-Z0-9_.-]+")


# ---------- Helper factories (avoid re-creating heavy objects per call) ----------

def get_vector_store() -> RAGVectorStore:
    return RAGVectorStore()


def get_problem_set_orchestrator(vs: RAGVectorStore) -> ProblemSetOrchestrator:
    return ProblemSetOrchestrator(vs)


def get_grading_orchestrator() -> GradingOrchestrator:
    return GradingOrchestrator()


def get_chunker() -> LLMChunker:
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


def retrieve_context(query: str, doc_id: Optional[str], top_k: int):
    """
    Run a vector search and return serialized chunks plus a context block.
    Shared by both sync and streaming chat endpoints.
    """
    vs = get_vector_store()

    if doc_id:
        results = vs.query_by_document(query, doc_id, top_k=top_k)
    else:
        results = vs.query(query, top_k=top_k)

    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    ids = (results.get("ids") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    if not documents:
        raise HTTPException(status_code=404, detail="No relevant chunks found.")

    retrieved_chunks = []
    context_blocks = []
    for chunk_id, doc_text, metadata, distance in zip(
        ids, documents, metadatas, distances or [None] * len(documents)
    ):
        similarity = None
        if distance is not None:
            similarity = 1 - float(distance)
        retrieved_chunks.append(
            serialize_chunk_payload(
                chunk_id=chunk_id,
                doc_text=doc_text,
                metadata=metadata,
                score=similarity,
            )
        )
        score_display = f"{similarity:.4f}" if similarity is not None else "n/a"
        context_blocks.append(
            f"[{metadata.get('doc_id', 'unknown')} | {chunk_id} | score={score_display}]\n{doc_text}"
        )

    return retrieved_chunks, "\n\n".join(context_blocks)


def build_rag_prompt(
    query: str,
    context: str,
    history: Optional[List[RAGChatMessage]] = None,
) -> str:
    """Construct the LLM prompt with context and recent history."""
    trimmed_history = history or []
    if len(trimmed_history) > 8:
        trimmed_history = trimmed_history[-8:]

    history_section = ""
    if trimmed_history:
        formatted = []
        for msg in trimmed_history:
            role = "User" if msg.role == "user" else "Assistant"
            formatted.append(f"{role}: {msg.content}")
        history_section = "Conversation so far:\n" + "\n".join(formatted) + "\n\n"

    return (
        "You are a senior teaching assistant who responds with professional, actionable explanations.\n"
        "Use only the supplied context and cite the relevant document IDs in parentheses (e.g., [doc_id]).\n"
        "If the context does not contain enough information, clearly state that limitation and suggest what is missing.\n"
        "Whenever possible, highlight key steps, definitions, or formulas so the reader can learn from the answer.\n\n"
        f"Context:\n{context}\n\n"
        f"{history_section}"
        f"Question: {query}\n\n"
        "Final Answer:"
    )


# ---------- Problem set generation endpoints ----------


@app.get("/api/py/chapters")
def list_chapters() -> Dict[str, List[str]]:
    """
    List all available chapter document IDs from the vector store.
    These IDs typically correspond to PDF filenames that were ingested.
    """
    vs = get_vector_store()
    chapters = vs.get_all_documents()
    # Filter out syllabus-like docs to mirror CLI behaviour
    chapters = [c for c in chapters if "syllabus" not in c.lower()]
    return {"chapters": chapters}


@app.post("/api/py/generate-problem-set")
def generate_problem_set(payload: GenerateProblemSetRequest) -> Dict[str, Any]:
    """
    Generate a problem set for a specific chapter document.

    This wraps ProblemSetOrchestrator.generate_problem_set and returns
    the full problem set JSON (analysis, problems, solutions, quality).
    
    The generated problem set is automatically stored and can be retrieved later.
    """
    try:
        vs = get_vector_store()
        orchestrator = get_problem_set_orchestrator(vs)

        result = orchestrator.generate_problem_set(
            doc_id=payload.doc_id,
            num_problems=payload.num_problems,
            check_quality=payload.check_quality,
        )

        if not result:
            raise HTTPException(
                status_code=404, detail=f"No content found for {payload.doc_id}"
            )

        # Ensure everything is JSON serializable
        try:
            encoded = jsonable_encoder(result)
        except Exception as encode_error:
            print(f"[API] JSON encoding error: {repr(encode_error)}")
            print(f"[API] Error type: {type(encode_error)}")
            print(f"[API] Traceback:\n{traceback.format_exc()}")
            # Try to manually convert problematic fields using json.dumps with default handler
            try:
                # Use json.dumps with default=str to convert any non-serializable types to strings
                json_str = json.dumps(result, default=str, ensure_ascii=False)
                encoded = json.loads(json_str)
            except Exception as fallback_error:
                print(f"[API] Fallback encoding also failed: {repr(fallback_error)}")
                print(f"[API] Fallback traceback:\n{traceback.format_exc()}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to serialize response: {str(encode_error)}"
                )
        
        # Auto-store the generated problem set
        problem_set_id = f"ps_{uuid.uuid4().hex[:12]}"
        stored_data = {
            "id": problem_set_id,
            "doc_id": payload.doc_id,
            "title": f"{payload.doc_id} - Problem Set",
            "num_problems": payload.num_problems,
            "created_at": datetime.now().isoformat(),
            "problem_set": encoded.get("problem_set", []),
            "analysis": encoded.get("analysis", {}),
        }
        
        # Save to file
        problem_set_file = PROBLEM_SETS_DIR / f"{problem_set_id}.json"
        with open(problem_set_file, 'w', encoding='utf-8') as f:
            json.dump(stored_data, f, indent=2, ensure_ascii=False)
        
        print(f"[API] Auto-stored problem set: {problem_set_id}")
        
        return {
            "success": True, 
            "problem_set": encoded,
            "problem_set_id": problem_set_id  # Return the ID so frontend can reference it
        }
    except HTTPException:
        # Re-raise HTTPExceptions as-is so FastAPI can handle them
        raise
    except Exception as e:
        # Log the error server-side with full traceback
        print(f"[API] Error in generate_problem_set: {repr(e)}")
        print(f"[API] Error type: {type(e)}")
        print(f"[API] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Grading endpoints ----------


@app.post("/api/py/grade-submissions")
def grade_submissions(payload: GradeSubmissionsRequest) -> Dict[str, Any]:
    """
    Grade multiple student submissions for a single problem.

    Expects the problem definition and correct solution (for example,
    taken directly from the problem set generation response) as well as
    a list of {name, solution} submissions.
    """
    grader = get_grading_orchestrator()

    # Convert Pydantic models to simple dicts expected by GradingOrchestrator
    student_submissions = [
        {"name": s.name, "solution": s.solution} for s in payload.student_submissions
    ]

    results, stats = grader.grade_batch(
        problem=payload.problem,
        correct_solution=payload.correct_solution,
        student_submissions=student_submissions,
    )

    return {
        "success": True,
        "statistics": stats,
        "results": results,
    }


# ---------- Document ingestion and RAG inspection endpoints ----------


@app.post("/api/py/upload-material")
async def upload_material(
    file: UploadFile = File(...),
    doc_id: Optional[str] = Form(None),
    overwrite: bool = Form(False),
) -> Dict[str, Any]:
    """
    Upload a PDF, chunk it semantically, and store chunks in the vector DB.

    Returns the stored chunk metadata so the frontend can visualize
    exactly what was embedded.
    """
    if not file:
        raise HTTPException(status_code=400, detail="A PDF file is required.")

    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    normalized_id = sanitize_doc_id(doc_id or file.filename)
    vs = get_vector_store()

    if vs.document_exists(normalized_id):
        if overwrite:
            vs.delete_document(normalized_id)
        else:
            normalized_id = f"{normalized_id}-{uuid.uuid4().hex[:4]}"

    text = extract_pdf_text_from_bytes(payload)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Unable to extract text from PDF.")

    chunker = get_chunker()
    chunks = chunker.chunk_with_splitting(text)

    if not chunks:
        raise HTTPException(status_code=500, detail="Chunker returned no content.")

    serialized_chunks: List[Dict[str, Any]] = []
    for idx, chunk in enumerate(chunks):
        chunk_id = f"{normalized_id}_chunk_{idx}"
        vs.add_chunk(chunk, normalized_id, chunk_id)
        metadata = {
            "doc_id": normalized_id,
            "summary": chunk.summary,
            "topics": chunk.topics,
            "start": chunk.start,
            "end": chunk.end,
        }
        serialized_chunks.append(
            serialize_chunk_payload(
                chunk_id=chunk_id,
                doc_text=chunk.formatted,
                metadata=metadata,
            )
        )

    return {
        "success": True,
        "doc_id": normalized_id,
        "chunk_count": len(serialized_chunks),
        "chunks": serialized_chunks,
    }


@app.get("/api/py/documents/{doc_id}/chunks")
def get_document_chunks(doc_id: str) -> Dict[str, Any]:
    """
    Return all stored chunks for a specific document.
    """
    vs = get_vector_store()

    if not vs.document_exists(doc_id):
        raise HTTPException(status_code=404, detail=f"{doc_id} has not been ingested.")

    records = vs.get_chunks_for_document(doc_id)
    ids = records.get("ids") or []
    docs = records.get("documents") or []
    metas = records.get("metadatas") or []

    serialized_chunks: List[Dict[str, Any]] = []
    for chunk_id, doc_text, meta in zip(ids, docs, metas):
        serialized_chunks.append(
            serialize_chunk_payload(chunk_id=chunk_id, doc_text=doc_text, metadata=meta)
        )

    # Sort by the start index if available to mirror ingestion order
    serialized_chunks.sort(key=lambda item: item.get("start") or 0)

    return {
        "doc_id": doc_id,
        "chunk_count": len(serialized_chunks),
        "chunks": serialized_chunks,
    }


@app.post("/api/py/rag-query")
def rag_query(payload: RAGChatRequest) -> Dict[str, Any]:
    """
    Run a retrieval-augmented question against the vector store and
    return the prompt, retrieved chunks, and final answer.
    """
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    top_k = max(1, min(payload.top_k, 10))
    retrieved_chunks, context = retrieve_context(query, payload.doc_id, top_k)
    prompt_body = build_rag_prompt(query, context, payload.history)

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert tutor who must rely strictly on the provided context.",
            },
            {"role": "user", "content": prompt_body},
        ],
        temperature=0.3,
    )

    answer = response.choices[0].message.content

    return {
        "success": True,
        "prompt": prompt_body,
        "answer": answer,
        "retrieved_chunks": retrieved_chunks,
    }


@app.post("/api/py/rag-query/stream")
def rag_query_stream(payload: RAGChatRequest):
    """
    Streaming version of the RAG chat endpoint.
    Emits a metadata event followed by token events so the UI can render progressively.
    """
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    top_k = max(1, min(payload.top_k, 10))
    retrieved_chunks, context = retrieve_context(query, payload.doc_id, top_k)
    prompt_body = build_rag_prompt(query, context, payload.history)
    client = OpenAI()

    def event_stream():
        # First send metadata so the UI can show citations immediately
        yield json.dumps(
            {
                "type": "metadata",
                "prompt": prompt_body,
                "retrieved_chunks": retrieved_chunks,
            }
        ) + "\n"

        accumulated_answer = ""
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert tutor who must rely strictly on the provided context.",
                    },
                    {"role": "user", "content": prompt_body},
                ],
                temperature=0.3,
                stream=True,
            )

            for chunk in completion:
                delta = chunk.choices[0].delta.content
                if delta:
                    accumulated_answer += delta
                    yield json.dumps({"type": "token", "value": delta}) + "\n"

            yield json.dumps({"type": "done", "answer": accumulated_answer}) + "\n"
        except Exception as e:
            print(f"[API] Streaming error: {repr(e)}")
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ---------- Document management endpoints ----------


@app.delete("/api/py/documents/{doc_id}")
def delete_document(doc_id: str) -> Dict[str, Any]:
    """
    Delete a document and all its chunks from the vector store.
    
    Args:
        doc_id: Document identifier to delete
        
    Returns:
        Success confirmation
    """
    vs = get_vector_store()
    
    if not vs.document_exists(doc_id):
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    
    vs.delete_document(doc_id)
    
    return {
        "success": True,
        "message": f"Document '{doc_id}' and all its chunks have been deleted.",
        "doc_id": doc_id
    }


@app.get("/api/py/documents")
def list_all_documents() -> Dict[str, Any]:
    """
    List all documents in the vector store with metadata.
    
    Returns:
        List of documents with chunk counts and statistics
    """
    vs = get_vector_store()
    all_docs = vs.get_all_documents()
    
    # Get metadata for each document
    doc_info = []
    for doc_id in all_docs:
        results = vs.get_chunks_for_document(doc_id)
        num_chunks = len(results.get("ids", []))
        
        # Calculate total characters
        documents = results.get("documents", [])
        total_chars = sum(len(doc) for doc in documents)
        
        doc_info.append({
            "doc_id": doc_id,
            "chunk_count": num_chunks,
            "total_chars": total_chars,
            "avg_chunk_size": total_chars // num_chunks if num_chunks > 0 else 0
        })
    
    return {
        "success": True,
        "total_documents": len(doc_info),
        "documents": doc_info
    }


# ---------- Export endpoints ----------


class ExportFormat(BaseModel):
    """Request model for exporting problem sets."""
    format: str = "markdown"  # markdown, json, or problems_only


@app.post("/api/py/export-problem-set")
def export_problem_set(
    problem_set: Dict[str, Any],
    format_request: ExportFormat
) -> Dict[str, Any]:
    """
    Export a problem set in different formats (Markdown, JSON, problems-only).
    
    Args:
        problem_set: The complete problem set data
        format_request: Desired export format
        
    Returns:
        Formatted content ready for download
    """
    from problem_set_generator import build_markdown, build_markdown_problems_only
    
    export_format = format_request.format.lower()
    
    if export_format == "json":
        return {
            "success": True,
            "format": "json",
            "content": json.dumps(problem_set, indent=2, ensure_ascii=False),
            "filename": f"{problem_set.get('doc_id', 'problem_set')}.json"
        }
    
    elif export_format == "problems_only":
        markdown_content = build_markdown_problems_only(problem_set)
        return {
            "success": True,
            "format": "markdown",
            "content": markdown_content,
            "filename": f"{problem_set.get('doc_id', 'problem_set')}_problems_only.md"
        }
    
    else:  # Default to full markdown with solutions
        markdown_content = build_markdown(problem_set)
        return {
            "success": True,
            "format": "markdown",
            "content": markdown_content,
            "filename": f"{problem_set.get('doc_id', 'problem_set')}_with_solutions.md"
        }


# ---------- Statistics and analytics endpoints ----------


@app.get("/api/py/stats")
def get_system_stats() -> Dict[str, Any]:
    """
    Get overall system statistics.
    
    Returns:
        System-wide statistics including document counts, chunk counts, etc.
    """
    vs = get_vector_store()
    all_docs = vs.get_all_documents()
    
    total_chunks = 0
    total_chars = 0
    chunk_sizes = []
    
    for doc_id in all_docs:
        results = vs.get_chunks_for_document(doc_id)
        chunks = results.get("documents", [])
        total_chunks += len(chunks)
        
        for chunk in chunks:
            chunk_len = len(chunk)
            total_chars += chunk_len
            chunk_sizes.append(chunk_len)
    
    return {
        "success": True,
        "statistics": {
            "total_documents": len(all_docs),
            "total_chunks": total_chunks,
            "total_characters": total_chars,
            "avg_chunk_size": total_chars // total_chunks if total_chunks > 0 else 0,
            "min_chunk_size": min(chunk_sizes) if chunk_sizes else 0,
            "max_chunk_size": max(chunk_sizes) if chunk_sizes else 0,
            "avg_chunks_per_document": total_chunks // len(all_docs) if all_docs else 0
        }
    }


# ---------- Health check and validation endpoints ----------


@app.get("/api/py/health")
def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for the API and its dependencies.
    
    Returns:
        Health status of all system components
    """
    health_status = {
        "api": "healthy",
        "vector_store": "unknown",
        "openai": "unknown"
    }
    
    # Check vector store
    try:
        vs = get_vector_store()
        docs = vs.get_all_documents()
        health_status["vector_store"] = "healthy"
        health_status["vector_store_docs"] = len(docs)
    except Exception as e:
        health_status["vector_store"] = f"unhealthy: {str(e)}"
    
    # Check OpenAI connection
    try:
        client = OpenAI()
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        health_status["openai"] = "healthy"
    except Exception as e:
        health_status["openai"] = f"unhealthy: {str(e)}"
    
    # Determine overall status
    overall_healthy = all(
        status == "healthy" or isinstance(status, int)
        for key, status in health_status.items()
        if key != "vector_store_docs"
    )
    
    return {
        "success": overall_healthy,
        "status": "healthy" if overall_healthy else "degraded",
        "components": health_status,
        "timestamp": json.dumps({"time": "now"})  # Simple timestamp
    }


# ---------- Batch operations endpoints ----------


class BatchGenerateRequest(BaseModel):
    """Request model for batch problem set generation."""
    doc_ids: List[str]
    num_problems: int = 5
    check_quality: bool = True


@app.post("/api/py/batch-generate-problem-sets")
def batch_generate_problem_sets(payload: BatchGenerateRequest) -> Dict[str, Any]:
    """
    Generate problem sets for multiple documents in batch.
    
    Args:
        payload: List of document IDs and generation parameters
        
    Returns:
        Results for each document (success or error)
    """
    vs = get_vector_store()
    orchestrator = get_problem_set_orchestrator(vs)
    
    results = []
    for doc_id in payload.doc_ids:
        try:
            problem_set = orchestrator.generate_problem_set(
                doc_id=doc_id,
                num_problems=payload.num_problems,
                check_quality=payload.check_quality
            )
            
            if problem_set:
                results.append({
                    "doc_id": doc_id,
                    "success": True,
                    "problem_set": problem_set
                })
            else:
                results.append({
                    "doc_id": doc_id,
                    "success": False,
                    "error": "No content found"
                })
        except Exception as e:
            results.append({
                "doc_id": doc_id,
                "success": False,
                "error": str(e)
            })
    
    successful = sum(1 for r in results if r["success"])
    
    return {
        "success": True,
        "total_requested": len(payload.doc_ids),
        "successful": successful,
        "failed": len(payload.doc_ids) - successful,
        "results": results
    }


# ---------- Search and discovery endpoints ----------


class SearchRequest(BaseModel):
    """Request model for searching across documents."""
    query: str
    top_k: int = 10
    doc_ids: Optional[List[str]] = None


@app.post("/api/py/search")
def search_across_documents(payload: SearchRequest) -> Dict[str, Any]:
    """
    Search across all documents or specific documents.
    
    Args:
        payload: Search query and filters
        
    Returns:
        Matching chunks with relevance scores
    """
    vs = get_vector_store()
    
    if payload.doc_ids and len(payload.doc_ids) > 0:
        # Search within specific documents
        all_results = []
        for doc_id in payload.doc_ids:
            try:
                results = vs.query_by_document(
                    payload.query,
                    doc_id,
                    top_k=payload.top_k
                )
                
                documents = (results.get("documents") or [[]])[0]
                metadatas = (results.get("metadatas") or [[]])[0]
                ids = (results.get("ids") or [[]])[0]
                distances = (results.get("distances") or [[]])[0]
                
                for chunk_id, doc_text, metadata, distance in zip(
                    ids, documents, metadatas, distances or [None] * len(documents)
                ):
                    similarity = 1 - float(distance) if distance is not None else None
                    all_results.append(
                        serialize_chunk_payload(
                            chunk_id=chunk_id,
                            doc_text=doc_text,
                            metadata=metadata,
                            score=similarity
                        )
                    )
            except Exception as e:
                print(f"Error searching {doc_id}: {e}")
                continue
        
        # Sort by score
        all_results.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)
        all_results = all_results[:payload.top_k]
    else:
        # Search across all documents
        results = vs.query(payload.query, top_k=payload.top_k)
        
        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        ids = (results.get("ids") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
        
        all_results = []
        for chunk_id, doc_text, metadata, distance in zip(
            ids, documents, metadatas, distances or [None] * len(documents)
        ):
            similarity = 1 - float(distance) if distance is not None else None
            all_results.append(
                serialize_chunk_payload(
                    chunk_id=chunk_id,
                    doc_text=doc_text,
                    metadata=metadata,
                    score=similarity
                )
            )
    
    return {
        "success": True,
        "query": payload.query,
        "total_results": len(all_results),
        "results": all_results
    }


# ---------- Problem Sets Storage endpoints ----------


@app.post("/api/py/problem-sets")
def store_problem_set(payload: StoreProblemSetRequest) -> Dict[str, Any]:
    """
    Store a problem set.
    
    Args:
        payload: Problem set data with optional title
        
    Returns:
        Stored problem set with ID
    """
    try:
        problem_set_id = f"ps_{uuid.uuid4().hex[:12]}"
        
        stored_data = {
            "id": problem_set_id,
            "title": payload.title or "Problem Set",
            "created_at": datetime.now().isoformat(),
            **payload.problem_set
        }
        
        # Save to file
        problem_set_file = PROBLEM_SETS_DIR / f"{problem_set_id}.json"
        with open(problem_set_file, 'w', encoding='utf-8') as f:
            json.dump(stored_data, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "problem_set_id": problem_set_id,
            "problem_set": stored_data
        }
    except Exception as e:
        print(f"[API] Error storing problem set: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/py/problem-sets")
def list_problem_sets() -> Dict[str, Any]:
    """
    List all stored problem sets with metadata.
    
    Returns:
        List of problem sets with basic info
    """
    try:
        problem_sets = []
        
        for problem_set_file in PROBLEM_SETS_DIR.glob("*.json"):
            try:
                with open(problem_set_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Return metadata only
                problem_sets.append({
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "doc_id": data.get("doc_id"),
                    "num_problems": data.get("num_problems", len(data.get("problem_set", []))),
                    "created_at": data.get("created_at"),
                    "topics": data.get("analysis", {}).get("topics", [])
                })
            except Exception as e:
                print(f"[API] Error loading {problem_set_file}: {e}")
                continue
        
        # Sort by creation date (newest first)
        problem_sets.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return {
            "success": True,
            "total": len(problem_sets),
            "problem_sets": problem_sets
        }
    except Exception as e:
        print(f"[API] Error listing problem sets: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/py/problem-sets/{problem_set_id}")
def get_problem_set(problem_set_id: str) -> Dict[str, Any]:
    """
    Get a specific problem set by ID.
    
    Args:
        problem_set_id: Problem set ID
        
    Returns:
        Complete problem set data
    """
    try:
        problem_set_file = PROBLEM_SETS_DIR / f"{problem_set_id}.json"
        
        if not problem_set_file.exists():
            raise HTTPException(status_code=404, detail=f"Problem set '{problem_set_id}' not found")
        
        with open(problem_set_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "success": True,
            "problem_set": data
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error getting problem set: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/py/problem-sets/{problem_set_id}")
def delete_problem_set(problem_set_id: str) -> Dict[str, Any]:
    """
    Delete a problem set and all its submissions.
    
    Args:
        problem_set_id: Problem set ID
        
    Returns:
        Success confirmation
    """
    try:
        problem_set_file = PROBLEM_SETS_DIR / f"{problem_set_id}.json"
        
        if not problem_set_file.exists():
            raise HTTPException(status_code=404, detail=f"Problem set '{problem_set_id}' not found")
        
        # Delete problem set file
        problem_set_file.unlink()
        
        # Delete associated submissions
        submissions_file = SUBMISSIONS_DIR / f"{problem_set_id}.json"
        if submissions_file.exists():
            submissions_file.unlink()
        
        return {
            "success": True,
            "message": f"Problem set '{problem_set_id}' deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error deleting problem set: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Submissions Storage endpoints ----------


@app.post("/api/py/submissions")
def store_submission(payload: StoreSubmissionRequest) -> Dict[str, Any]:
    """
    Store a student submission.
    
    Args:
        payload: Submission data
        
    Returns:
        Stored submission with ID
    """
    try:
        # Load or create submissions file for this problem set
        submissions_file = SUBMISSIONS_DIR / f"{payload.problem_set_id}.json"
        
        if submissions_file.exists():
            with open(submissions_file, 'r', encoding='utf-8') as f:
                submissions_data = json.load(f)
        else:
            submissions_data = {"problem_set_id": payload.problem_set_id, "submissions": []}
        
        # Create submission
        submission_id = f"sub_{uuid.uuid4().hex[:12]}"
        submission = {
            "id": submission_id,
            "problem_id": payload.problem_id,
            "student_name": payload.student_name,
            "solution": payload.solution,
            "submitted_at": datetime.now().isoformat(),
            "graded": False,
            "grade": None
        }
        
        # Check if student already submitted this problem
        existing_submissions = submissions_data.get("submissions", [])
        existing_index = None
        for i, sub in enumerate(existing_submissions):
            if (sub.get("student_name") == payload.student_name and 
                sub.get("problem_id") == payload.problem_id):
                existing_index = i
                break
        
        if existing_index is not None:
            # Update existing submission
            submission["id"] = existing_submissions[existing_index].get("id", submission_id)
            existing_submissions[existing_index] = submission
        else:
            # Add new submission
            existing_submissions.append(submission)
        
        submissions_data["submissions"] = existing_submissions
        
        # Save to file
        with open(submissions_file, 'w', encoding='utf-8') as f:
            json.dump(submissions_data, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "submission_id": submission["id"],
            "submission": submission
        }
    except Exception as e:
        print(f"[API] Error storing submission: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/py/submissions/{problem_set_id}")
def get_submissions(problem_set_id: str, problem_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get all submissions for a problem set.
    
    Args:
        problem_set_id: Problem set ID
        problem_id: Optional problem ID to filter by
        
    Returns:
        List of submissions
    """
    try:
        submissions_file = SUBMISSIONS_DIR / f"{problem_set_id}.json"
        
        if not submissions_file.exists():
            return {
                "success": True,
                "problem_set_id": problem_set_id,
                "submissions": []
            }
        
        with open(submissions_file, 'r', encoding='utf-8') as f:
            submissions_data = json.load(f)
        
        submissions = submissions_data.get("submissions", [])
        
        # Filter by problem_id if provided
        if problem_id is not None:
            submissions = [s for s in submissions if s.get("problem_id") == problem_id]
        
        return {
            "success": True,
            "problem_set_id": problem_set_id,
            "total": len(submissions),
            "submissions": submissions
        }
    except Exception as e:
        print(f"[API] Error getting submissions: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/py/submissions/{problem_set_id}/{student_name}")
def get_student_submissions(problem_set_id: str, student_name: str) -> Dict[str, Any]:
    """
    Get a student's submissions for a problem set.
    
    Args:
        problem_set_id: Problem set ID
        student_name: Student name
        
    Returns:
        List of student's submissions
    """
    try:
        submissions_file = SUBMISSIONS_DIR / f"{problem_set_id}.json"
        
        if not submissions_file.exists():
            return {
                "success": True,
                "problem_set_id": problem_set_id,
                "student_name": student_name,
                "submissions": []
            }
        
        with open(submissions_file, 'r', encoding='utf-8') as f:
            submissions_data = json.load(f)
        
        submissions = submissions_data.get("submissions", [])
        student_submissions = [s for s in submissions if s.get("student_name") == student_name]
        
        return {
            "success": True,
            "problem_set_id": problem_set_id,
            "student_name": student_name,
            "submissions": student_submissions
        }
    except Exception as e:
        print(f"[API] Error getting student submissions: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/py/submissions/{submission_id}/grade")
def update_submission_grade(submission_id: str, grade: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a submission with grading results.
    
    Args:
        submission_id: Submission ID
        grade: Grade data from grading API
        
    Returns:
        Updated submission
    """
    try:
        # Find the submission across all problem sets
        for submissions_file in SUBMISSIONS_DIR.glob("*.json"):
            with open(submissions_file, 'r', encoding='utf-8') as f:
                submissions_data = json.load(f)
            
            submissions = submissions_data.get("submissions", [])
            updated = False
            
            for i, sub in enumerate(submissions):
                if sub.get("id") == submission_id:
                    submissions[i]["graded"] = True
                    submissions[i]["grade"] = grade
                    updated = True
                    break
            
            if updated:
                # Save back to file
                with open(submissions_file, 'w', encoding='utf-8') as f:
                    json.dump(submissions_data, f, indent=2, ensure_ascii=False)
                
                return {
                    "success": True,
                    "submission_id": submission_id,
                    "submission": submissions[i]
                }
        
        raise HTTPException(status_code=404, detail=f"Submission '{submission_id}' not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error updating submission grade: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/py/submissions/grade-batch")
def grade_batch_and_store(
    problem_set_id: str,
    problem_id: int
) -> Dict[str, Any]:
    """
    Grade all submissions for a specific problem and store results.
    
    This is a convenience endpoint that:
    1. Gets the problem set and problem
    2. Gets all submissions for that problem
    3. Grades them using the grading API
    4. Stores the grades back
    
    Args:
        problem_set_id: Problem set ID
        problem_id: Problem ID to grade
        
    Returns:
        Grading results with statistics
    """
    try:
        # Get problem set
        problem_set_file = PROBLEM_SETS_DIR / f"{problem_set_id}.json"
        if not problem_set_file.exists():
            raise HTTPException(status_code=404, detail=f"Problem set '{problem_set_id}' not found")
        
        with open(problem_set_file, 'r', encoding='utf-8') as f:
            problem_set_data = json.load(f)
        
        # Find the problem
        problems = problem_set_data.get("problem_set", [])
        problem_data = None
        for item in problems:
            if item.get("problem", {}).get("id") == problem_id:
                problem_data = item
                break
        
        if not problem_data:
            raise HTTPException(status_code=404, detail=f"Problem {problem_id} not found in problem set")
        
        problem = problem_data["problem"]
        correct_solution = problem_data["solution"]
        
        # Get submissions
        submissions_file = SUBMISSIONS_DIR / f"{problem_set_id}.json"
        if not submissions_file.exists():
            raise HTTPException(status_code=404, detail="No submissions found")
        
        with open(submissions_file, 'r', encoding='utf-8') as f:
            submissions_data = json.load(f)
        
        problem_submissions = [
            s for s in submissions_data.get("submissions", [])
            if s.get("problem_id") == problem_id
        ]
        
        if not problem_submissions:
            raise HTTPException(status_code=404, detail="No submissions for this problem")
        
        # Format for grading
        student_submissions = [
            {"name": s["student_name"], "solution": s["solution"]}
            for s in problem_submissions
        ]
        
        # Grade them
        grader = get_grading_orchestrator()
        results, stats = grader.grade_batch(
            problem=problem,
            correct_solution=correct_solution,
            student_submissions=student_submissions
        )
        
        # Store grades back
        all_submissions = submissions_data.get("submissions", [])
        for result in results:
            student_name = result["student_name"]
            for i, sub in enumerate(all_submissions):
                if (sub.get("student_name") == student_name and 
                    sub.get("problem_id") == problem_id):
                    all_submissions[i]["graded"] = True
                    all_submissions[i]["grade"] = result
                    break
        
        submissions_data["submissions"] = all_submissions
        
        # Save back
        with open(submissions_file, 'w', encoding='utf-8') as f:
            json.dump(submissions_data, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "statistics": stats,
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error in grade_batch_and_store: {repr(e)}")
        print(f"[API] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
