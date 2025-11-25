"""
Guided Problem Solving Router - Interactive step-by-step problem solving with AI.
Provides a game-like experience where AI guides students through problems.
"""
from typing import Any, Dict, List, Optional, Tuple
import json
import traceback

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the fastapi_backend directory
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

router = APIRouter(prefix="/api/py/guided", tags=["guided-solve"])

# Initialize OpenAI client lazily to avoid errors at import time
_client: Optional[OpenAI] = None

def get_openai_client() -> OpenAI:
    """Get or create OpenAI client."""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


# ============ Request/Response Models ============

class StartSessionRequest(BaseModel):
    """Request to start a new guided solving session."""
    problem: Dict[str, Any]  # The problem to solve
    difficulty: str = "medium"  # easy, medium, hard


class AnswerRequest(BaseModel):
    """Request to submit an answer for the current step."""
    session_id: str
    step_index: int
    answer: str  # The student's answer (e.g., "A", "B", "C", "D" for MCQ)


class HintRequest(BaseModel):
    """Request a hint for the current step."""
    session_id: str
    step_index: int
    hints_used: int  # How many hints already used for this step


class SessionState(BaseModel):
    """Current state of a guided solving session."""
    session_id: str
    problem: Dict[str, Any]
    steps: List[Dict[str, Any]]
    current_step: int
    total_steps: int
    score: int
    max_score: int
    completed: bool
    summary: Optional[Dict[str, Any]] = None


# In-memory session storage (in production, use Redis or a database)
sessions: Dict[str, Dict[str, Any]] = {}


# ============ Helper Functions ============

def generate_steps_for_problem(problem: Dict[str, Any], difficulty: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Use AI to break down a problem into guided steps with MCQs.
    Returns (steps, final_answer) tuple.
    """
    print(f"[GuidedSolve] Generating steps for problem with difficulty: {difficulty}")
    problem_text = json.dumps(problem, indent=2, default=str)
    
    num_steps = 3 if difficulty == 'easy' else 5 if difficulty == 'medium' else 7
    
    prompt = f"""You are an expert tutor. Break down this problem into {num_steps} guided steps.

PROBLEM:
{problem_text}

For each step, create:
1. A clear explanation of what concept/approach to use
2. A multiple choice question (MCQ) to check understanding
3. The correct answer (A, B, C, or D)
4. A brief explanation of why that answer is correct
5. Explanations for why each WRONG answer is incorrect (this helps students learn from mistakes)
6. Two progressive hints (from subtle to more direct)

Return ONLY valid JSON in this exact format:
{{
  "steps": [
    {{
      "step_number": 1,
      "title": "Step title",
      "explanation": "What we need to do in this step",
      "mcq": {{
        "question": "The MCQ question",
        "options": {{
          "A": "First option",
          "B": "Second option", 
          "C": "Third option",
          "D": "Fourth option"
        }},
        "correct_answer": "A",
        "explanation": "Why A is correct",
        "wrong_explanations": {{
          "B": "Why B is wrong - explain the misconception",
          "C": "Why C is wrong - explain the error in thinking",
          "D": "Why D is wrong - clarify the mistake"
        }}
      }},
      "hints": [
        "Subtle hint that nudges in the right direction",
        "More direct hint that almost gives the answer"
      ],
      "points": 10
    }}
  ],
  "final_answer": "The complete solution/answer to the problem"
}}

Make the MCQs test actual understanding, not just memorization. Include realistic wrong answers that represent common mistakes students make, and provide educational explanations for why each wrong answer is incorrect."""

    try:
        client = get_openai_client()
        print(f"[GuidedSolve] Calling OpenAI API...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert educational tutor who creates engaging, step-by-step problem breakdowns. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        content = response.choices[0].message.content
        print(f"[GuidedSolve] Got response from OpenAI, parsing JSON...")
        
        # Extract JSON from response
        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end == 0:
            print(f"[GuidedSolve] No JSON found in response: {content[:200]}")
            raise ValueError("No JSON found in OpenAI response")
            
        json_str = content[start:end]
        
        data = json.loads(json_str)
        steps = data.get("steps", [])
        final_answer = data.get("final_answer", "")
        
        print(f"[GuidedSolve] Successfully parsed {len(steps)} steps")
        return steps, final_answer
        
    except Exception as e:
        print(f"[GuidedSolve] Error generating steps: {e}")
        print(f"[GuidedSolve] Traceback: {traceback.format_exc()}")
        # Return a fallback single step
        return [{
            "step_number": 1,
            "title": "Solve the Problem",
            "explanation": "Work through this problem step by step.",
            "mcq": {
                "question": "What is the first thing you should identify in this problem?",
                "options": {
                    "A": "The given information",
                    "B": "Random guessing",
                    "C": "Skip to the answer",
                    "D": "Give up"
                },
                "correct_answer": "A",
                "explanation": "Always start by identifying what information is given."
            },
            "hints": [
                "Look at what the problem tells you.",
                "List out all the given values and conditions."
            ],
            "points": 10
        }], "Complete the problem using the given information."


def generate_encouragement(is_correct: bool, attempts: int) -> str:
    """Generate encouraging feedback based on performance."""
    if is_correct:
        if attempts == 1:
            return "🎯 Perfect! You got it on the first try!"
        elif attempts == 2:
            return "✨ Great job! You figured it out!"
        else:
            return "👍 You got it! Persistence pays off!"
    else:
        if attempts == 1:
            return "🤔 Not quite. Think about it a bit more..."
        elif attempts == 2:
            return "💡 Try using a hint if you're stuck."
        else:
            return "📚 Review the explanation and try again."


def calculate_step_score(base_points: int, attempts: int, hints_used: int) -> int:
    """Calculate score for a step based on attempts and hints used."""
    score = base_points
    # Deduct for extra attempts (first attempt is free)
    score -= (attempts - 1) * 2
    # Deduct for hints used
    score -= hints_used * 3
    return max(0, score)


# ============ API Endpoints ============

@router.post("/start-session")
def start_session(payload: StartSessionRequest) -> Dict[str, Any]:
    """
    Start a new guided solving session for a problem.
    
    Args:
        payload: Contains the problem and difficulty level
        
    Returns:
        Session state with the first step
    """
    import uuid
    
    print(f"[GuidedSolve] Starting session for problem: {payload.problem.get('statement', 'unknown')[:50]}...")
    
    session_id = f"gs_{uuid.uuid4().hex[:12]}"
    
    try:
        # Generate steps for this problem
        steps, final_answer = generate_steps_for_problem(payload.problem, payload.difficulty)
        
        if not steps:
            raise HTTPException(status_code=500, detail="Failed to generate problem steps - no steps returned")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[GuidedSolve] Error in start_session: {e}")
        print(f"[GuidedSolve] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to generate problem steps: {str(e)}")
    
    # Calculate max possible score
    max_score = sum(step.get("points", 10) for step in steps)
    
    # Create session state
    session_state = {
        "session_id": session_id,
        "problem": payload.problem,
        "difficulty": payload.difficulty,
        "steps": steps,
        "final_answer": final_answer,
        "current_step": 0,
        "total_steps": len(steps),
        "score": 0,
        "max_score": max_score,
        "completed": False,
        "step_attempts": {},  # Track attempts per step
        "step_hints_used": {},  # Track hints used per step
        "step_results": [],  # Track results for each step
    }
    
    # Store session
    sessions[session_id] = session_state
    
    # Return initial state (without revealing answers)
    first_step = steps[0].copy()
    first_step.pop("mcq", None)
    
    return {
        "success": True,
        "session_id": session_id,
        "problem": payload.problem,
        "current_step": 0,
        "total_steps": len(steps),
        "step": {
            "step_number": steps[0]["step_number"],
            "title": steps[0]["title"],
            "explanation": steps[0]["explanation"],
            "mcq": {
                "question": steps[0]["mcq"]["question"],
                "options": steps[0]["mcq"]["options"]
            },
            "points": steps[0].get("points", 10)
        },
        "score": 0,
        "max_score": max_score
    }


@router.post("/submit-answer")
def submit_answer(payload: AnswerRequest) -> Dict[str, Any]:
    """
    Submit an answer for the current step.
    
    Args:
        payload: Contains session_id, step_index, and answer
        
    Returns:
        Result of the answer check and next step if correct
    """
    session = sessions.get(payload.session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["completed"]:
        raise HTTPException(status_code=400, detail="Session already completed")
    
    if payload.step_index != session["current_step"]:
        raise HTTPException(status_code=400, detail="Invalid step index")
    
    step = session["steps"][payload.step_index]
    correct_answer = step["mcq"]["correct_answer"]
    
    # Track attempts
    step_key = str(payload.step_index)
    session["step_attempts"][step_key] = session["step_attempts"].get(step_key, 0) + 1
    attempts = session["step_attempts"][step_key]
    hints_used = session["step_hints_used"].get(step_key, 0)
    
    is_correct = payload.answer.upper() == correct_answer.upper()
    
    response = {
        "success": True,
        "is_correct": is_correct,
        "attempts": attempts,
        "feedback": generate_encouragement(is_correct, attempts)
    }
    
    if is_correct:
        # Calculate and add score
        step_score = calculate_step_score(step.get("points", 10), attempts, hints_used)
        session["score"] += step_score
        
        # Record step result
        session["step_results"].append({
            "step": payload.step_index,
            "attempts": attempts,
            "hints_used": hints_used,
            "score": step_score
        })
        
        response["score_earned"] = step_score
        response["total_score"] = session["score"]
        response["explanation"] = step["mcq"]["explanation"]
        
        # Move to next step or complete
        next_step_index = payload.step_index + 1
        
        if next_step_index >= session["total_steps"]:
            # Session complete!
            session["completed"] = True
            session["current_step"] = next_step_index
            
            # Generate summary
            summary = {
                "total_score": session["score"],
                "max_score": session["max_score"],
                "percentage": round((session["score"] / session["max_score"]) * 100, 1),
                "steps_completed": session["total_steps"],
                "step_results": session["step_results"],
                "final_answer": session["final_answer"],
                "performance": "Excellent!" if session["score"] >= session["max_score"] * 0.9 else
                              "Great job!" if session["score"] >= session["max_score"] * 0.7 else
                              "Good effort!" if session["score"] >= session["max_score"] * 0.5 else
                              "Keep practicing!"
            }
            session["summary"] = summary
            
            response["completed"] = True
            response["summary"] = summary
        else:
            # Move to next step
            session["current_step"] = next_step_index
            next_step = session["steps"][next_step_index]
            
            response["next_step"] = {
                "step_number": next_step["step_number"],
                "title": next_step["title"],
                "explanation": next_step["explanation"],
                "mcq": {
                    "question": next_step["mcq"]["question"],
                    "options": next_step["mcq"]["options"]
                },
                "points": next_step.get("points", 10)
            }
            response["current_step"] = next_step_index
    else:
        # Wrong answer - provide explanation for why their choice was wrong
        response["correct_answer"] = None  # Don't reveal yet
        
        # Get the explanation for why their answer is wrong
        wrong_explanations = step["mcq"].get("wrong_explanations", {})
        user_answer = payload.answer.upper()
        if user_answer in wrong_explanations:
            response["wrong_explanation"] = wrong_explanations[user_answer]
        else:
            # Fallback if no specific explanation
            response["wrong_explanation"] = "That's not quite right. Think about the concept again and try a different approach."
        
        # After 3 attempts, reveal the answer and move on
        if attempts >= 3:
            response["correct_answer"] = correct_answer
            response["explanation"] = step["mcq"]["explanation"]
            response["feedback"] = "📖 Here's the correct answer. Let's move on and learn from this!"
            
            # Record step result with 0 score
            session["step_results"].append({
                "step": payload.step_index,
                "attempts": attempts,
                "hints_used": hints_used,
                "score": 0,
                "gave_up": True
            })
            
            # Move to next step
            next_step_index = payload.step_index + 1
            
            if next_step_index >= session["total_steps"]:
                session["completed"] = True
                session["current_step"] = next_step_index
                
                summary = {
                    "total_score": session["score"],
                    "max_score": session["max_score"],
                    "percentage": round((session["score"] / session["max_score"]) * 100, 1),
                    "steps_completed": session["total_steps"],
                    "step_results": session["step_results"],
                    "final_answer": session["final_answer"],
                    "performance": "Excellent!" if session["score"] >= session["max_score"] * 0.9 else
                                  "Great job!" if session["score"] >= session["max_score"] * 0.7 else
                                  "Good effort!" if session["score"] >= session["max_score"] * 0.5 else
                                  "Keep practicing!"
                }
                session["summary"] = summary
                
                response["completed"] = True
                response["summary"] = summary
            else:
                session["current_step"] = next_step_index
                next_step = session["steps"][next_step_index]
                
                response["next_step"] = {
                    "step_number": next_step["step_number"],
                    "title": next_step["title"],
                    "explanation": next_step["explanation"],
                    "mcq": {
                        "question": next_step["mcq"]["question"],
                        "options": next_step["mcq"]["options"]
                    },
                    "points": next_step.get("points", 10)
                }
                response["current_step"] = next_step_index
    
    return response


@router.post("/get-hint")
def get_hint(payload: HintRequest) -> Dict[str, Any]:
    """
    Get a hint for the current step.
    
    Args:
        payload: Contains session_id, step_index, and hints already used
        
    Returns:
        The next hint if available
    """
    session = sessions.get(payload.session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if payload.step_index != session["current_step"]:
        raise HTTPException(status_code=400, detail="Invalid step index")
    
    step = session["steps"][payload.step_index]
    hints = step.get("hints", [])
    
    if payload.hints_used >= len(hints):
        return {
            "success": True,
            "hint": None,
            "message": "No more hints available for this step.",
            "hints_remaining": 0
        }
    
    # Track hints used
    step_key = str(payload.step_index)
    session["step_hints_used"][step_key] = payload.hints_used + 1
    
    return {
        "success": True,
        "hint": hints[payload.hints_used],
        "hint_number": payload.hints_used + 1,
        "hints_remaining": len(hints) - payload.hints_used - 1,
        "point_deduction": 3  # Points deducted for using this hint
    }


@router.get("/session/{session_id}")
def get_session(session_id: str) -> Dict[str, Any]:
    """
    Get the current state of a session.
    
    Args:
        session_id: The session ID
        
    Returns:
        Current session state
    """
    session = sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Return safe state (without answers)
    current_step_data = None
    if not session["completed"] and session["current_step"] < len(session["steps"]):
        step = session["steps"][session["current_step"]]
        current_step_data = {
            "step_number": step["step_number"],
            "title": step["title"],
            "explanation": step["explanation"],
            "mcq": {
                "question": step["mcq"]["question"],
                "options": step["mcq"]["options"]
            },
            "points": step.get("points", 10)
        }
    
    return {
        "success": True,
        "session_id": session_id,
        "problem": session["problem"],
        "current_step": session["current_step"],
        "total_steps": session["total_steps"],
        "score": session["score"],
        "max_score": session["max_score"],
        "completed": session["completed"],
        "step": current_step_data,
        "summary": session.get("summary")
    }


@router.delete("/session/{session_id}")
def end_session(session_id: str) -> Dict[str, Any]:
    """
    End and delete a session.
    
    Args:
        session_id: The session ID
        
    Returns:
        Confirmation of deletion
    """
    if session_id in sessions:
        del sessions[session_id]
        return {"success": True, "message": "Session ended"}
    
    raise HTTPException(status_code=404, detail="Session not found")

