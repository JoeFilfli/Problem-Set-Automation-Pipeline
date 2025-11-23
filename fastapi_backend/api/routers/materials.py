"""
Materials management router - handles document uploads, ingestion, and chunk inspection.
"""
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from api.dependencies import (
    get_vector_store,
    get_chunker,
    sanitize_doc_id,
    serialize_chunk_payload,
)
from pdf_extractor import extract_pdf_text_from_bytes

router = APIRouter(prefix="/api/py", tags=["materials"])


@router.post("/upload-material")
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


@router.get("/chapters")
def list_chapters() -> Dict[str, List[str]]:
    """
    List all available chapter document IDs from the vector store.
    These IDs typically correspond to PDF filenames that were ingested.
    """
    try:
        vs = get_vector_store()
        chapters = vs.get_all_documents()
        # Filter out syllabus-like docs to mirror CLI behaviour
        chapters = [c for c in chapters if "syllabus" not in c.lower()]
        return {"chapters": chapters}
    except (ValueError, AttributeError) as e:
        # ChromaDB error - return empty list
        error_str = str(e).lower()
        if any(kw in error_str for kw in ["tenant", "bindings", "could not connect"]):
            return {"chapters": []}
        raise


@router.get("/documents")
def list_all_documents() -> Dict[str, Any]:
    """
    List all documents in the vector store with metadata.
    
    Returns:
        List of documents with chunk counts and statistics
    """
    try:
        vs = get_vector_store()
        all_docs = vs.get_all_documents()
    except (ValueError, AttributeError) as e:
        # ChromaDB error - return empty list
        error_str = str(e).lower()
        if any(kw in error_str for kw in ["tenant", "bindings", "could not connect"]):
            return {
                "success": True,
                "total_documents": 0,
                "documents": []
            }
        raise
    
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


@router.get("/documents/{doc_id}/chunks")
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


@router.delete("/documents/{doc_id}")
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


@router.get("/stats")
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
