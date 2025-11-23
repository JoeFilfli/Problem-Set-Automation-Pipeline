"""
RAG (Retrieval-Augmented Generation) router - handles queries, chat, and search.
"""
from typing import Any, Dict, List, Optional
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI

from api.dependencies import (
    get_vector_store,
    serialize_chunk_payload,
)

router = APIRouter(prefix="/api/py", tags=["rag"])


# Request models
class RAGChatMessage(BaseModel):
    role: str
    content: str


class RAGQueryRequest(BaseModel):
    query: str
    doc_id: Optional[str] = None
    top_k: int = 4


class RAGChatRequest(RAGQueryRequest):
    history: List[RAGChatMessage] = []


class SearchRequest(BaseModel):
    """Request model for searching across documents."""
    query: str
    top_k: int = 10
    doc_ids: Optional[List[str]] = None


# Helper functions
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


@router.post("/rag-query")
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


@router.post("/rag-query/stream")
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


@router.post("/search")
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
