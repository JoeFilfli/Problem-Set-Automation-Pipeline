"""
Course Feedback router - handles student course feedback and surveys.

Allows students to provide feedback on course quality, difficulty, materials, etc.
Professors can view aggregated feedback data in analytics.
"""
from typing import Any, Dict, List, Optional
import json
from datetime import datetime
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Storage directories
STORAGE_DIR = Path("api_storage")
FEEDBACK_DIR = STORAGE_DIR / "feedback"

# Create storage directories if they don't exist
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class CourseFeedbackCreate(BaseModel):
    """Schema for creating course feedback."""
    student_id: str = Field(default="student")
    student_name: str = Field(default="Anonymous")
    
    # Rating scales (1-5)
    overall_rating: int = Field(..., ge=1, le=5)
    content_quality: int = Field(..., ge=1, le=5)
    difficulty_level: int = Field(..., ge=1, le=5)  # 1=too easy, 3=just right, 5=too hard
    pacing: int = Field(..., ge=1, le=5)  # 1=too slow, 3=just right, 5=too fast
    materials_quality: int = Field(..., ge=1, le=5)
    instructor_effectiveness: int = Field(..., ge=1, le=5)
    
    # Open-ended feedback
    what_worked_well: str = Field(default="")
    what_needs_improvement: str = Field(default="")
    suggestions: str = Field(default="")
    
    # Optional topic-specific feedback
    favorite_topics: List[str] = Field(default_factory=list)
    challenging_topics: List[str] = Field(default_factory=list)
    
    # Metadata
    submission_context: Optional[str] = None  # e.g., "mid-semester", "end-of-course"


class CourseFeedbackOut(BaseModel):
    """Schema for returning feedback data."""
    id: str
    student_id: str
    student_name: str
    overall_rating: int
    content_quality: int
    difficulty_level: int
    pacing: int
    materials_quality: int
    instructor_effectiveness: int
    what_worked_well: str
    what_needs_improvement: str
    suggestions: str
    favorite_topics: List[str]
    challenging_topics: List[str]
    submission_context: Optional[str]
    created_at: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_all_feedback() -> List[Dict[str, Any]]:
    """Load all feedback entries from storage."""
    feedback_file = FEEDBACK_DIR / "course_feedback.json"
    
    if not feedback_file.exists():
        return []
    
    with open(feedback_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get("feedback", [])


def save_feedback(feedback_list: List[Dict[str, Any]]) -> None:
    """Save feedback list to storage."""
    feedback_file = FEEDBACK_DIR / "course_feedback.json"
    
    with open(feedback_file, 'w', encoding='utf-8') as f:
        json.dump({"feedback": feedback_list}, f, indent=2, ensure_ascii=False)


# ============================================================================
# STUDENT ROUTES
# ============================================================================

@router.post("/submit")
def submit_feedback(payload: CourseFeedbackCreate) -> Dict[str, Any]:
    """
    Submit course feedback.
    
    Students can provide ratings and open-ended feedback about the course.
    """
    try:
        # Load existing feedback
        all_feedback = load_all_feedback()
        
        # Create feedback entry
        feedback_id = f"fb_{uuid.uuid4().hex[:12]}"
        
        feedback_entry = {
            "id": feedback_id,
            "student_id": payload.student_id,
            "student_name": payload.student_name,
            "overall_rating": payload.overall_rating,
            "content_quality": payload.content_quality,
            "difficulty_level": payload.difficulty_level,
            "pacing": payload.pacing,
            "materials_quality": payload.materials_quality,
            "instructor_effectiveness": payload.instructor_effectiveness,
            "what_worked_well": payload.what_worked_well,
            "what_needs_improvement": payload.what_needs_improvement,
            "suggestions": payload.suggestions,
            "favorite_topics": payload.favorite_topics,
            "challenging_topics": payload.challenging_topics,
            "submission_context": payload.submission_context,
            "created_at": datetime.now().isoformat(),
        }
        
        # Add to feedback list
        all_feedback.append(feedback_entry)
        
        # Save to file
        save_feedback(all_feedback)
        
        return {
            "success": True,
            "feedback_id": feedback_id,
            "message": "Thank you for your feedback!"
        }
    except Exception as e:
        print(f"[API] Error submitting feedback: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-feedback")
def get_my_feedback(student_id: str = "student") -> Dict[str, Any]:
    """
    Get feedback submitted by a specific student.
    
    Returns all feedback entries from this student.
    """
    try:
        all_feedback = load_all_feedback()
        
        # Filter by student
        student_feedback = [fb for fb in all_feedback if fb.get("student_id") == student_id]
        
        return {
            "success": True,
            "total": len(student_feedback),
            "feedback": student_feedback
        }
    except Exception as e:
        print(f"[API] Error getting student feedback: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROFESSOR ROUTES
# ============================================================================

@router.get("/all")
def get_all_feedback() -> Dict[str, Any]:
    """
    Get all course feedback (professor view).
    
    Returns all feedback entries with student information.
    """
    try:
        all_feedback = load_all_feedback()
        
        # Sort by creation date (newest first)
        all_feedback.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return {
            "success": True,
            "total": len(all_feedback),
            "feedback": all_feedback
        }
    except Exception as e:
        print(f"[API] Error getting all feedback: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
def get_feedback_summary() -> Dict[str, Any]:
    """
    Get aggregated feedback summary with statistics.
    
    Returns average ratings, common themes, and insights.
    """
    try:
        all_feedback = load_all_feedback()
        
        if not all_feedback:
            return {
                "success": True,
                "has_data": False,
                "message": "No feedback submitted yet"
            }
        
        # Calculate average ratings
        total_count = len(all_feedback)
        avg_ratings = {
            "overall_rating": sum(fb["overall_rating"] for fb in all_feedback) / total_count,
            "content_quality": sum(fb["content_quality"] for fb in all_feedback) / total_count,
            "difficulty_level": sum(fb["difficulty_level"] for fb in all_feedback) / total_count,
            "pacing": sum(fb["pacing"] for fb in all_feedback) / total_count,
            "materials_quality": sum(fb["materials_quality"] for fb in all_feedback) / total_count,
            "instructor_effectiveness": sum(fb["instructor_effectiveness"] for fb in all_feedback) / total_count,
        }
        
        # Round to 1 decimal place
        avg_ratings = {k: round(v, 1) for k, v in avg_ratings.items()}
        
        # Count rating distributions
        rating_distribution = {
            "overall_rating": {},
            "content_quality": {},
            "difficulty_level": {},
            "pacing": {},
            "materials_quality": {},
            "instructor_effectiveness": {},
        }
        
        for category in rating_distribution.keys():
            for rating in range(1, 6):
                count = sum(1 for fb in all_feedback if fb.get(category) == rating)
                rating_distribution[category][rating] = count
        
        # Aggregate topics
        from collections import Counter
        favorite_topics_counter = Counter()
        challenging_topics_counter = Counter()
        
        for fb in all_feedback:
            for topic in fb.get("favorite_topics", []):
                favorite_topics_counter[topic] += 1
            for topic in fb.get("challenging_topics", []):
                challenging_topics_counter[topic] += 1
        
        # Get top topics
        top_favorite_topics = [
            {"topic": topic, "count": count}
            for topic, count in favorite_topics_counter.most_common(10)
        ]
        
        top_challenging_topics = [
            {"topic": topic, "count": count}
            for topic, count in challenging_topics_counter.most_common(10)
        ]
        
        # Collect open-ended responses
        positive_comments = [
            {"student": fb.get("student_name", "Anonymous"), "comment": fb.get("what_worked_well", "")}
            for fb in all_feedback
            if fb.get("what_worked_well", "").strip()
        ]
        
        improvement_comments = [
            {"student": fb.get("student_name", "Anonymous"), "comment": fb.get("what_needs_improvement", "")}
            for fb in all_feedback
            if fb.get("what_needs_improvement", "").strip()
        ]
        
        suggestion_comments = [
            {"student": fb.get("student_name", "Anonymous"), "comment": fb.get("suggestions", "")}
            for fb in all_feedback
            if fb.get("suggestions", "").strip()
        ]
        
        # Generate insights
        insights = []
        
        # Check difficulty perception
        if avg_ratings["difficulty_level"] > 4:
            insights.append({
                "type": "warning",
                "title": "Course Perceived as Too Difficult",
                "description": f"Average difficulty rating is {avg_ratings['difficulty_level']}/5. Consider reviewing prerequisite requirements or adding more scaffolding."
            })
        elif avg_ratings["difficulty_level"] < 2:
            insights.append({
                "type": "info",
                "title": "Course Perceived as Too Easy",
                "description": f"Average difficulty rating is {avg_ratings['difficulty_level']}/5. Consider adding more challenging content or advanced topics."
            })
        
        # Check pacing
        if avg_ratings["pacing"] > 4:
            insights.append({
                "type": "warning",
                "title": "Course Pacing Too Fast",
                "description": f"Average pacing rating is {avg_ratings['pacing']}/5. Students may need more time to absorb material."
            })
        elif avg_ratings["pacing"] < 2:
            insights.append({
                "type": "info",
                "title": "Course Pacing Too Slow",
                "description": f"Average pacing rating is {avg_ratings['pacing']}/5. Consider covering more material or adding depth."
            })
        
        # Check materials
        if avg_ratings["materials_quality"] < 3:
            insights.append({
                "type": "warning",
                "title": "Materials Need Improvement",
                "description": f"Average materials rating is {avg_ratings['materials_quality']}/5. Review and update course materials."
            })
        
        # Overall satisfaction
        if avg_ratings["overall_rating"] >= 4:
            insights.append({
                "type": "success",
                "title": "High Student Satisfaction",
                "description": f"Average overall rating is {avg_ratings['overall_rating']}/5. Great job!"
            })
        elif avg_ratings["overall_rating"] < 3:
            insights.append({
                "type": "warning",
                "title": "Low Student Satisfaction",
                "description": f"Average overall rating is {avg_ratings['overall_rating']}/5. Consider addressing key concerns."
            })
        
        return {
            "success": True,
            "has_data": True,
            "total_responses": total_count,
            "average_ratings": avg_ratings,
            "rating_distribution": rating_distribution,
            "top_favorite_topics": top_favorite_topics,
            "top_challenging_topics": top_challenging_topics,
            "positive_comments": positive_comments[:20],  # Limit to 20 most recent
            "improvement_comments": improvement_comments[:20],
            "suggestions": suggestion_comments[:20],
            "insights": insights
        }
    except Exception as e:
        print(f"[API] Error generating feedback summary: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/feedback/{feedback_id}")
def delete_feedback(feedback_id: str) -> Dict[str, Any]:
    """
    Delete a specific feedback entry.
    
    Utility endpoint for cleanup.
    """
    try:
        all_feedback = load_all_feedback()
        
        # Find and remove feedback
        original_count = len(all_feedback)
        all_feedback = [fb for fb in all_feedback if fb.get("id") != feedback_id]
        
        if len(all_feedback) == original_count:
            raise HTTPException(status_code=404, detail=f"Feedback '{feedback_id}' not found")
        
        # Save updated list
        save_feedback(all_feedback)
        
        return {
            "success": True,
            "message": f"Feedback '{feedback_id}' deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error deleting feedback: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))



