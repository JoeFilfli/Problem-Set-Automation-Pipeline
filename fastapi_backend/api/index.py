from typing import Any, Dict, List
import json
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from agent_orchestrator import ProblemSetOrchestrator
from grading_agents import GradingOrchestrator
from vector_store import RAGVectorStore


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


# ---------- Helper factories (avoid re‑creating heavy objects per call) ----------


def get_vector_store() -> RAGVectorStore:
    return RAGVectorStore()


def get_problem_set_orchestrator(vs: RAGVectorStore) -> ProblemSetOrchestrator:
    return ProblemSetOrchestrator(vs)


def get_grading_orchestrator() -> GradingOrchestrator:
    return GradingOrchestrator()


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