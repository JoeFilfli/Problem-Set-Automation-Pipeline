"""
Submissions router - handles student submissions and grading.
"""
from typing import Any, Dict, List, Optional
import json
import traceback
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.dependencies import (
    PROBLEM_SETS_DIR,
    SUBMISSIONS_DIR,
    get_grading_orchestrator,
)

router = APIRouter(prefix="/api/py", tags=["submissions"])


# Request models
class StudentSubmission(BaseModel):
    name: str
    solution: str


class GradeSubmissionsRequest(BaseModel):
    problem: Dict[str, Any]
    correct_solution: str
    student_submissions: List[StudentSubmission]


class StoreSubmissionRequest(BaseModel):
    problem_set_id: str
    problem_id: int
    student_name: str
    solution: str
    images: Optional[List[str]] = []  # List of base64 encoded images


@router.post("/grade-submissions")
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


@router.post("/submissions")
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
            "images": payload.images or [],  # Store images separately
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


@router.get("/submissions/{problem_set_id}")
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


@router.get("/submissions/{problem_set_id}/{student_name}")
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


@router.put("/submissions/{submission_id}/grade")
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


@router.post("/submissions/grade-batch")
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
            {
                "name": s["student_name"], 
                "solution": s["solution"],
                "images": s.get("images", [])  # Include images for vision-based grading
            }
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
