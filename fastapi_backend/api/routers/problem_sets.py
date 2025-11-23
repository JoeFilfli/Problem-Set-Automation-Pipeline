"""
Problem sets router - handles generation, storage, and export of problem sets.
"""
from typing import Any, Dict
import json
import traceback
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from api.dependencies import (
    PROBLEM_SETS_DIR,
    get_vector_store,
    get_problem_set_orchestrator,
)

router = APIRouter(prefix="/api/py", tags=["problem-sets"])


# Request models
class GenerateProblemSetRequest(BaseModel):
    doc_id: str
    num_problems: int = 5
    check_quality: bool = True


class StoreProblemSetRequest(BaseModel):
    problem_set: Dict[str, Any]
    title: str | None = None


class ExportFormat(BaseModel):
    """Request model for exporting problem sets."""
    format: str = "markdown"  # markdown, json, or problems_only


@router.post("/generate-problem-set")
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
        
        # Add the ID to the encoded data
        encoded["id"] = problem_set_id
        encoded["created_at"] = stored_data["created_at"]
        
        return {
            "success": True, 
            "problem_set": encoded,
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


@router.post("/problem-sets")
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


@router.get("/problem-sets")
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


@router.get("/problem-sets/{problem_set_id}")
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


@router.delete("/problem-sets/{problem_set_id}")
def delete_problem_set(problem_set_id: str) -> Dict[str, Any]:
    """
    Delete a problem set and all its submissions.
    
    Args:
        problem_set_id: Problem set ID
        
    Returns:
        Success confirmation
    """
    try:
        from api.dependencies import SUBMISSIONS_DIR
        
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


@router.post("/export-problem-set")
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
