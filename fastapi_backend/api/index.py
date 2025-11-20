from typing import Any, Dict, List, Optional
import json
import traceback
import re
import uuid

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from openai import OpenAI

from agent_orchestrator import ProblemSetOrchestrator
from grading_agents import GradingOrchestrator
from vector_store import RAGVectorStore
from chunker import LLMChunker
from pdf_extractor import extract_pdf_text_from_bytes


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


DOC_ID_SANITIZER = re.compile(r"[^a-zA-Z0-9_.-]+")


# ---------- Helper factories (avoid re-creating heavy objects per call) ----------

# ---------- Helper factories (avoid re‑creating heavy objects per call) ----------


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
        
        return {"success": True, "problem_set": encoded}
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
def rag_query(payload: RAGQueryRequest) -> Dict[str, Any]:
    """
    Run a retrieval-augmented question against the vector store and
    return the prompt, retrieved chunks, and final answer.
    """
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    top_k = max(1, min(payload.top_k, 10))
    vs = get_vector_store()

    if payload.doc_id:
        results = vs.query_by_document(query, payload.doc_id, top_k=top_k)
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

    context = "\n\n".join(context_blocks)
    prompt_body = (
        "You are a senior teaching assistant who responds with professional, actionable explanations.\n"
        "Use only the supplied context and cite the relevant document IDs in parentheses (e.g., [doc_id]).\n"
        "If the context does not contain enough information, clearly state that limitation and suggest what is missing.\n"
        "Whenever possible, highlight key steps, definitions, or formulas so the reader can learn from the answer.\n\n"
        f"Context:\n{context}\n\nQuestion: {query}\n\nFinal Answer:"
    )

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
