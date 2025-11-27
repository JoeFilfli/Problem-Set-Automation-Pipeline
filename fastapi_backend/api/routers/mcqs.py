"""
MCQs router - handles MCQ generation and exam PDF creation.
"""
from typing import Any, Dict, List, Optional
import json
import traceback
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.dependencies import (
    SAVED_MCQS_DIR,
    get_vector_store,
    get_problem_set_orchestrator,
)

router = APIRouter(prefix="/api/py", tags=["mcqs"])


# Request models
class GenerateMCQRequest(BaseModel):
    doc_id: str
    num_mcqs: int = 5


class SaveMCQRequest(BaseModel):
    mcq: Dict[str, Any]
    chapter: str


class GenerateExamRequest(BaseModel):
    mcq_ids: List[str]
    exam_title: Optional[str] = None


@router.post("/generate-mcqs")
def generate_mcqs(payload: GenerateMCQRequest) -> Dict[str, Any]:
    """
    Generate multiple choice questions for a specific chapter document.
    
    Args:
        payload: Request with doc_id and num_mcqs
        
    Returns:
        Generated MCQ set
    """
    try:
        vs = get_vector_store()
        orchestrator = get_problem_set_orchestrator(vs)
        
        result = orchestrator.generate_mcq_set(
            doc_id=payload.doc_id,
            num_mcqs=payload.num_mcqs
        )
        
        if not result:
            raise HTTPException(
                status_code=404, detail=f"No content found for {payload.doc_id}"
            )
        
        encoded = jsonable_encoder(result)
        
        return {
            "success": True,
            "mcq_set": encoded
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error in generate_mcqs: {repr(e)}")
        print(f"[API] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-mcqs/stream")
def generate_mcqs_stream(payload: GenerateMCQRequest):
    """
    Streaming version of MCQ generation.
    Yields events as MCQs are generated, allowing progressive UI updates.
    
    Args:
        payload: Request with doc_id and num_mcqs
        
    Returns:
        StreamingResponse with Server-Sent Events
    """
    try:
        vs = get_vector_store()
        orchestrator = get_problem_set_orchestrator(vs)
        
        def event_stream():
            try:
                for event in orchestrator.generate_mcq_set_stream(
                    doc_id=payload.doc_id,
                    num_mcqs=payload.num_mcqs
                ):
                    yield event
            except Exception as e:
                import json
                yield json.dumps({
                    "type": "error",
                    "message": str(e)
                }) + "\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        print(f"[API] Error in generate_mcqs_stream: {repr(e)}")
        print(f"[API] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-mcq")
def save_mcq(payload: SaveMCQRequest) -> Dict[str, Any]:
    """
    Save a selected MCQ question for later use in exam generation.
    
    Args:
        payload: MCQ data and chapter info
        
    Returns:
        Saved MCQ with ID
    """
    try:
        mcq_id = f"mcq_{uuid.uuid4().hex[:12]}"
        
        saved_mcq = {
            "id": mcq_id,
            "mcq": payload.mcq,
            "chapter": payload.chapter,
            "saved_at": datetime.now().isoformat()
        }
        
        # Save to file
        mcq_file = SAVED_MCQS_DIR / f"{mcq_id}.json"
        with open(mcq_file, 'w', encoding='utf-8') as f:
            json.dump(saved_mcq, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "mcq_id": mcq_id,
            "mcq": saved_mcq
        }
    except Exception as e:
        print(f"[API] Error saving MCQ: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saved-mcqs")
def list_saved_mcqs() -> Dict[str, Any]:
    """
    List all saved MCQ questions.
    
    Returns:
        List of saved MCQs
    """
    try:
        saved_mcqs = []
        
        for mcq_file in SAVED_MCQS_DIR.glob("*.json"):
            try:
                with open(mcq_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                saved_mcqs.append(data)
            except Exception as e:
                print(f"[API] Error loading {mcq_file}: {e}")
                continue
        
        # Sort by save date (newest first)
        saved_mcqs.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
        
        return {
            "success": True,
            "total": len(saved_mcqs),
            "mcqs": saved_mcqs
        }
    except Exception as e:
        print(f"[API] Error listing saved MCQs: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/saved-mcqs/{mcq_id}")
def delete_saved_mcq(mcq_id: str) -> Dict[str, Any]:
    """
    Delete a saved MCQ.
    
    Args:
        mcq_id: MCQ ID to delete
        
    Returns:
        Success confirmation
    """
    try:
        mcq_file = SAVED_MCQS_DIR / f"{mcq_id}.json"
        
        if not mcq_file.exists():
            raise HTTPException(status_code=404, detail=f"MCQ '{mcq_id}' not found")
        
        mcq_file.unlink()
        
        return {
            "success": True,
            "message": f"MCQ '{mcq_id}' deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error deleting MCQ: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-exam-pdf")
def generate_exam_pdf(payload: GenerateExamRequest) -> StreamingResponse:
    """
    Generate a PDF exam from saved MCQ questions.
    
    Args:
        payload: List of MCQ IDs and optional exam title
        
    Returns:
        PDF file as streaming response
    """
    try:
        # Load all requested MCQs
        mcqs = []
        for mcq_id in payload.mcq_ids:
            mcq_file = SAVED_MCQS_DIR / f"{mcq_id}.json"
            if not mcq_file.exists():
                continue
            with open(mcq_file, 'r', encoding='utf-8') as f:
                mcq_data = json.load(f)
                mcqs.append(mcq_data["mcq"])
        
        if not mcqs:
            raise HTTPException(status_code=404, detail="No valid MCQs found")
        
        # Generate PDF
        try:
            from pdf_generator import generate_exam_pdf as gen_pdf
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="PDF generation module not available. Please install required dependencies."
            )
        
        pdf_bytes = gen_pdf(
            mcqs=mcqs,
            exam_title=payload.exam_title or "Exam"
        )
        
        exam_filename = f"exam_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{exam_filename}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error generating exam PDF: {repr(e)}")
        print(f"[API] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
