"""
Analytics router - handles data aggregation for professor insights.
"""
from typing import Any, Dict, List, Optional
import json
from pathlib import Path
from collections import Counter

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.dependencies import (
    PROBLEM_SETS_DIR,
    SUBMISSIONS_DIR,
)

router = APIRouter(prefix="/api/py/analytics", tags=["analytics"])


@router.get("/problem-sets")
def get_problem_sets_with_submissions() -> Dict[str, Any]:
    """
    Get list of problem sets that have submissions.
    """
    try:
        problem_sets = []
        
        # Look through all submission files
        for submission_file in SUBMISSIONS_DIR.glob("*.json"):
            try:
                with open(submission_file, 'r', encoding='utf-8') as f:
                    sub_data = json.load(f)
                
                problem_set_id = sub_data.get("problem_set_id")
                if not problem_set_id:
                    continue
                    
                # Get problem set details to get the topic/title
                ps_file = PROBLEM_SETS_DIR / f"{problem_set_id}.json"
                topic = "Unknown Topic"
                if ps_file.exists():
                    with open(ps_file, 'r', encoding='utf-8') as f:
                        ps_data = json.load(f)
                        # Try to find a topic from the first problem
                        if ps_data.get("problem_set") and len(ps_data["problem_set"]) > 0:
                            topic = ps_data["problem_set"][0]["problem"].get("topic", "Unknown Topic")
                
                submission_count = len(sub_data.get("submissions", []))
                
                problem_sets.append({
                    "id": problem_set_id,
                    "topic": topic,
                    "submission_count": submission_count,
                    "last_updated": submission_file.stat().st_mtime
                })
            except Exception as e:
                print(f"[Warning] Error reading {submission_file}: {e}")
                continue
        
        # Sort by last updated desc
        problem_sets.sort(key=lambda x: x["last_updated"], reverse=True)
        
        return {
            "success": True,
            "problem_sets": problem_sets
        }
    except Exception as e:
        print(f"[API] Error getting analytics problem sets: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{problem_set_id}")
def get_problem_set_analytics(problem_set_id: str) -> Dict[str, Any]:
    """
    Get aggregated analytics for a problem set.
    """
    try:
        submissions_file = SUBMISSIONS_DIR / f"{problem_set_id}.json"
        
        if not submissions_file.exists():
            raise HTTPException(status_code=404, detail="No submissions found for this problem set")
        
        with open(submissions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        submissions = data.get("submissions", [])
        graded_submissions = [s for s in submissions if s.get("graded") and s.get("grade")]
        
        if not graded_submissions:
            return {
                "success": True,
                "problem_set_id": problem_set_id,
                "has_data": False,
                "message": "No graded submissions found"
            }
            
        # Load problem set data for curriculum optimization
        problem_set_file = PROBLEM_SETS_DIR / f"{problem_set_id}.json"
        problem_set_data = None
        if problem_set_file.exists():
            with open(problem_set_file, 'r', encoding='utf-8') as f:
                problem_set_data = json.load(f)
            
        # Aggregate stats
        scores = []
        all_errors = []
        all_strengths = []
        grade_counts = Counter()
        problem_scores = {}  # Track scores per problem
        
        student_performance = []
        
        for sub in graded_submissions:
            grade_data = sub.get("grade", {})
            summary = grade_data.get("summary", {})
            evaluation = grade_data.get("evaluation", {})
            problem_id = sub.get("problem_id")
            
            # Score
            score = summary.get("percentage", 0)
            scores.append(score)
            
            # Track per-problem scores
            if problem_id not in problem_scores:
                problem_scores[problem_id] = []
            problem_scores[problem_id].append(score)
            
            # Grade distribution
            letter_grade = summary.get("grade", "N/A")
            grade_counts[letter_grade] += 1
            
            # Common errors and strengths
            if evaluation.get("errors"):
                all_errors.extend(evaluation["errors"])
            if evaluation.get("strengths"):
                all_strengths.extend(evaluation["strengths"])
                
            # Student performance list
            student_performance.append({
                "student_name": sub.get("student_name"),
                "problem_id": problem_id,
                "score": score,
                "grade": letter_grade,
                "submission_id": sub.get("id")
            })
            
        # Calculate stats
        avg_score = sum(scores) / len(scores) if scores else 0
        median_score = sorted(scores)[len(scores)//2] if scores else 0
        min_score = min(scores) if scores else 0
        max_score = max(scores) if scores else 0
        
        # Get top 5 common errors
        common_errors = [
            {"error": error, "count": count} 
            for error, count in Counter(all_errors).most_common(5)
        ]
        
        # Get top 5 strengths
        common_strengths = [
            {"strength": strength, "count": count} 
            for strength, count in Counter(all_strengths).most_common(5)
        ]
        
        # Curriculum Optimization Analysis
        curriculum_insights = _generate_curriculum_insights(
            problem_set_data, 
            problem_scores, 
            common_errors, 
            avg_score
        )
        
        return {
            "success": True,
            "problem_set_id": problem_set_id,
            "has_data": True,
            "stats": {
                "total_submissions": len(submissions),
                "graded_submissions": len(graded_submissions),
                "average_score": avg_score,
                "median_score": median_score,
                "min_score": min_score,
                "max_score": max_score,
                "grade_distribution": dict(grade_counts),
                "common_errors": common_errors,
                "common_strengths": common_strengths
            },
            "student_performance": student_performance,
            "curriculum_optimization": curriculum_insights
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error getting analytics: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_curriculum_insights(
    problem_set_data: Optional[Dict[str, Any]], 
    problem_scores: Dict[int, List[float]],
    common_errors: List[Dict[str, Any]],
    overall_avg: float
) -> Dict[str, Any]:
    """
    Generate curriculum optimization insights based on student performance.
    """
    insights = {
        "problem_difficulty": [],
        "recommendations": [],
        "learning_gaps": []
    }
    
    if not problem_set_data or not problem_scores:
        return insights
    
    # Analyze each problem's difficulty
    for problem_id, scores in problem_scores.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Find problem details
        problem_info = None
        for item in problem_set_data.get("problem_set", []):
            if item.get("problem", {}).get("id") == problem_id:
                problem_info = item.get("problem", {})
                break
        
        topic = problem_info.get("topic", f"Problem {problem_id}") if problem_info else f"Problem {problem_id}"
        
        # Classify difficulty
        if avg_score < 50:
            difficulty = "Too Hard"
            color = "red"
        elif avg_score < 70:
            difficulty = "Challenging"
            color = "orange"
        elif avg_score < 85:
            difficulty = "Appropriate"
            color = "green"
        else:
            difficulty = "Too Easy"
            color = "blue"
        
        insights["problem_difficulty"].append({
            "problem_id": problem_id,
            "topic": topic,
            "avg_score": round(avg_score, 1),
            "difficulty": difficulty,
            "color": color,
            "submission_count": len(scores)
        })
    
    # Sort by avg score (hardest first)
    insights["problem_difficulty"].sort(key=lambda x: x["avg_score"])
    
    # Generate recommendations
    too_hard = [p for p in insights["problem_difficulty"] if p["difficulty"] == "Too Hard"]
    too_easy = [p for p in insights["problem_difficulty"] if p["difficulty"] == "Too Easy"]
    
    if too_hard:
        insights["recommendations"].append({
            "type": "difficulty",
            "severity": "high",
            "title": "Problems Too Difficult",
            "description": f"{len(too_hard)} problem(s) have average scores below 50%. Consider adding prerequisite content or breaking them into smaller steps.",
            "problems": [p["topic"] for p in too_hard[:3]]
        })
    
    if too_easy:
        insights["recommendations"].append({
            "type": "difficulty",
            "severity": "low",
            "title": "Problems Too Easy",
            "description": f"{len(too_easy)} problem(s) have average scores above 85%. Consider increasing complexity or adding extension questions.",
            "problems": [p["topic"] for p in too_easy[:3]]
        })
    
    # Identify learning gaps from common errors
    if common_errors:
        top_error = common_errors[0]
        insights["learning_gaps"].append({
            "concept": "Most Common Mistake",
            "description": top_error["error"],
            "frequency": top_error["count"],
            "recommendation": "Consider adding targeted practice or review material on this concept."
        })
    
    # Overall curriculum health
    if overall_avg < 70:
        insights["recommendations"].append({
            "type": "overall",
            "severity": "high",
            "title": "Overall Low Performance",
            "description": f"Class average is {overall_avg:.1f}%. The material may be too advanced, or students need more foundational preparation.",
            "problems": []
        })
    elif overall_avg > 90:
        insights["recommendations"].append({
            "type": "overall",
            "severity": "medium",
            "title": "High Performance",
            "description": f"Class average is {overall_avg:.1f}%. Students are mastering the material well. Consider adding more challenging problems.",
            "problems": []
        })
    
    return insights
