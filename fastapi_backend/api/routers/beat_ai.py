"""
Beat the AI router - handles challenges where students debug wrong AI solutions.

This feature allows professors to create challenges with intentionally wrong AI solutions.
Students must identify the error, explain it, provide corrected reasoning, and reflect.
"""
from typing import Any, Dict, List, Optional
import json
import traceback
from datetime import datetime
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAI

# Import dependencies for chapter-based generation
from api.dependencies import get_vector_store

# Storage directories
STORAGE_DIR = Path("api_storage")
BEAT_AI_CHALLENGES_DIR = STORAGE_DIR / "beat_ai_challenges"
BEAT_AI_SUBMISSIONS_DIR = STORAGE_DIR / "beat_ai_submissions"

# Create storage directories if they don't exist
BEAT_AI_CHALLENGES_DIR.mkdir(parents=True, exist_ok=True)
BEAT_AI_SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/api/beat-ai", tags=["beat-ai"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class BeatAIChallengeCreate(BaseModel):
    """Schema for creating a Beat the AI challenge."""
    # Chapter-based fields
    chapter_id: str = Field(...)  # Required: which chapter/document to base this on
    topic: Optional[str] = Field(None)  # Optional: specific topic within chapter
    
    # Optional manual fields (if not provided, AI generates them)
    title: Optional[str] = Field(None, max_length=200)
    problem_statement: Optional[str] = Field(None)
    reference_solution: Optional[str] = Field(None)
    
    # Generated fields
    difficulty: str = Field(default="MEDIUM", pattern="^(EASY|MEDIUM|HARD)$")
    tags: List[str] = Field(default_factory=list)
    ai_wrong_solution: str = Field(default="")
    created_by_user_id: str = Field(default="professor")  # Simplified for file-based system


class BeatAIChallengeUpdate(BaseModel):
    """Schema for updating a Beat the AI challenge."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    problem_statement: Optional[str] = Field(None, min_length=10)
    difficulty: Optional[str] = Field(None, pattern="^(EASY|MEDIUM|HARD)$")
    tags: Optional[List[str]] = None
    reference_solution: Optional[str] = Field(None, min_length=10)
    ai_wrong_solution: Optional[str] = None


class BeatAIChallengeOut(BaseModel):
    """Schema for returning challenge data to professors (includes reference solution)."""
    id: str
    title: str
    problem_statement: str
    difficulty: str
    tags: List[str]
    reference_solution: str
    ai_wrong_solution: str
    created_by_user_id: str
    created_at: str
    updated_at: str
    submission_count: int = 0
    avg_score: float = 0.0


class BeatAIChallengeStudentOut(BaseModel):
    """Schema for returning challenge data to students (no reference solution)."""
    id: str
    title: str
    problem_statement: str
    difficulty: str
    tags: List[str]
    ai_wrong_solution: str


class ErrorClassification(BaseModel):
    """Schema for classifying an error."""
    segment_index: int = Field(..., ge=0)
    segment_text: str = Field(..., min_length=1)
    error_type: str = Field(...)  # "incorrect_calculation", "unnecessary_step", "logic_error", "custom"
    custom_description: Optional[str] = None  # Used when error_type is "custom"


class BeatAISubmissionCreate(BaseModel):
    """Schema for creating a submission."""
    challenge_id: str
    student_id: str = Field(default="student")  # Simplified for file-based system
    selected_errors: List[ErrorClassification] = Field(..., min_items=1)
    workflow_suggestion: Optional[str] = Field(None)  # Optional paragraph for better workflow


class BeatAISubmissionOut(BaseModel):
    """Schema for returning submission data."""
    id: str
    challenge_id: str
    student_id: str
    selected_errors: List[ErrorClassification]
    workflow_suggestion: Optional[str] = None
    ai_feedback: Optional[str] = None  # Instant AI feedback after submission
    score: Optional[float] = None
    review_notes: Optional[str] = None
    created_at: str
    updated_at: str


class BeatAISubmissionGradeUpdate(BaseModel):
    """Schema for updating submission grade."""
    score: float = Field(..., ge=0, le=100)
    review_notes: str = Field(default="")


class GenerateWrongSolutionRequest(BaseModel):
    """Schema for requesting AI wrong solution generation."""
    pass  # No additional fields needed, uses challenge data


class GenerateProblemFromChapterRequest(BaseModel):
    """Schema for generating a problem from a chapter."""
    chapter_id: str = Field(..., min_length=1)
    topic: Optional[str] = Field(None)
    difficulty: str = Field(default="MEDIUM", pattern="^(EASY|MEDIUM|HARD)$")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_challenge(challenge_id: str) -> Dict[str, Any]:
    """Load a challenge from storage."""
    challenge_file = BEAT_AI_CHALLENGES_DIR / f"{challenge_id}.json"
    if not challenge_file.exists():
        raise HTTPException(status_code=404, detail=f"Challenge '{challenge_id}' not found")
    
    with open(challenge_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_challenge(challenge_id: str, challenge_data: Dict[str, Any]) -> None:
    """Save a challenge to storage."""
    challenge_file = BEAT_AI_CHALLENGES_DIR / f"{challenge_id}.json"
    with open(challenge_file, 'w', encoding='utf-8') as f:
        json.dump(challenge_data, f, indent=2, ensure_ascii=False)


def get_submission_stats(challenge_id: str) -> Dict[str, Any]:
    """Calculate submission statistics for a challenge."""
    submissions_file = BEAT_AI_SUBMISSIONS_DIR / f"{challenge_id}.json"
    
    if not submissions_file.exists():
        return {"submission_count": 0, "avg_score": 0.0}
    
    with open(submissions_file, 'r', encoding='utf-8') as f:
        submissions_data = json.load(f)
    
    submissions = submissions_data.get("submissions", [])
    submission_count = len(submissions)
    
    # Calculate average score (only for graded submissions)
    graded_submissions = [s for s in submissions if s.get("score") is not None]
    avg_score = 0.0
    if graded_submissions:
        avg_score = sum(s["score"] for s in graded_submissions) / len(graded_submissions)
    
    return {"submission_count": submission_count, "avg_score": avg_score}


def validate_wrong_solution(wrong_solution: str, correct_solution: str) -> bool:
    """
    Validate that the wrong solution is actually different from the correct one.
    Returns True if solutions are sufficiently different, False if too similar.
    """
    # Normalize both solutions for comparison
    wrong_normalized = ' '.join(wrong_solution.lower().split())
    correct_normalized = ' '.join(correct_solution.lower().split())
    
    # Simple similarity check - if more than 95% identical, they're too similar
    if wrong_normalized == correct_normalized:
        return False
    
    # Check for significant differences (at least 5% different)
    similarity_ratio = len(set(wrong_normalized.split()) & set(correct_normalized.split())) / len(set(correct_normalized.split()))
    
    return similarity_ratio < 0.95  # Allow up to 95% similarity


# ============================================================================
# GENERATION ROUTES
# ============================================================================

@router.post("/generate-challenge-from-chapter")
def generate_challenge_from_chapter(payload: GenerateProblemFromChapterRequest) -> Dict[str, Any]:
    """
    Generate a complete Beat the AI challenge from a chapter in one step.
    
    This endpoint:
    1. Generates problem statement and reference solution from chapter
    2. Generates a convincing but wrong AI solution
    3. Creates and saves the complete challenge
    
    Returns the created challenge ready to use.
    """
    try:
        # Get vector store and retrieve context from chapter
        vs = get_vector_store()
        
        # Build query based on topic or general chapter content
        if payload.topic:
            query = f"Explain {payload.topic} and provide an example problem"
        else:
            query = "What are the key concepts and problems in this chapter?"
        
        # Retrieve relevant chunks from the chapter
        results = vs.query_by_document(query, payload.chapter_id, top_k=5)
        
        if not results or not results.get("documents"):
            raise HTTPException(
                status_code=404,
                detail=f"No content found for chapter '{payload.chapter_id}'"
            )
        
        # Extract context from retrieved chunks
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        
        context_parts = []
        for doc, meta in zip(documents, metadatas):
            summary = meta.get("summary", "")
            context_parts.append(f"Summary: {summary}\nContent: {doc}")
        
        chapter_context = "\n\n".join(context_parts)
        
        # Generate problem using AI
        client = OpenAI()
        
        difficulty_guidance = {
            "EASY": "straightforward, basic application of concepts",
            "MEDIUM": "moderate difficulty, requiring some analysis",
            "HARD": "challenging, requiring deep understanding and multiple steps"
        }
        
        topic_instruction = f" focusing on the topic: {payload.topic}" if payload.topic else ""
        
        # Step 1: Generate correct problem and solution
        system_prompt = f"""You are an expert instructor creating educational problems.
Based on the provided chapter content, create a {difficulty_guidance[payload.difficulty]} problem{topic_instruction}.

Your response must be in JSON format with these fields:
- title: A short, descriptive title (max 100 chars)
- problem_statement: Clear problem description with any given information
- reference_solution: Complete, step-by-step solution with explanations (must have multiple clear steps separated by newlines)
- tags: List of 2-4 relevant topic tags

Make the problem realistic and educational. The solution MUST have at least 5-7 distinct steps."""
        
        user_prompt = f"""Chapter: {payload.chapter_id}

Context from chapter:
{chapter_context[:3000]}

Generate a {payload.difficulty} difficulty problem based on this content."""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        # Parse AI response
        import json as json_lib
        generated_content = json_lib.loads(response.choices[0].message.content)
        
        # Step 2: Generate wrong AI solution with improved prompting
        wrong_solution_prompt = """You are simulating a confident but flawed AI assistant that makes ONE subtle error in problem-solving.

Your task: Create a solution that appears professional and correct but contains exactly ONE subtle mistake that students must identify.

ERROR TYPES TO CHOOSE FROM:
1. **Conceptual Misunderstanding** - Misapplying a concept (e.g., confusing correlation with causation)
2. **Calculation Error** - Arithmetic mistake that propagates (e.g., 3×7=24 instead of 21)
3. **Logic Flaw** - Faulty reasoning step (e.g., assuming A→B means B→A)
4. **Sign Error** - Wrong positive/negative (e.g., -5 written as +5)
5. **Formula Misuse** - Using wrong formula or wrong variable in formula
6. **Boundary Condition** - Missing edge case or incorrect domain restriction
7. **Unit Confusion** - Wrong units or missing conversion
8. **Assumption Error** - Making invalid assumption not stated in problem

DIFFICULTY MATCHING:
- EASY problems: Use obvious calculation errors (arithmetic mistakes)
- MEDIUM problems: Use conceptual misunderstandings or formula misuse
- HARD problems: Use subtle logic flaws or boundary condition errors

CRITICAL RULES:
✓ Make EXACTLY ONE error (don't make multiple mistakes)
✓ Error should occur in the MIDDLE steps (not first or last)
✓ 90% of the solution should be perfectly correct
✓ Use the same structure and terminology as correct solution
✓ Write confidently - never hint that something might be wrong
✓ Show all work clearly so error is identifiable
✓ Format in clear numbered steps using markdown
✓ The error should be pedagogically valuable (teaches something important)

AVOID:
✗ Don't make typos or obvious mistakes
✗ Don't contradict yourself
✗ Don't skip steps
✗ Don't use different terminology than the problem
✗ Don't make the error in step 1 or the final answer calculation

EXAMPLE - GOOD SUBTLE ERROR:
Correct: "Since the derivative f'(x) < 0, the function is decreasing"
Wrong: "Since the derivative f'(x) < 0, the function is increasing" ← Conceptual error

EXAMPLE - BAD OBVIOUS ERROR:
Correct: "NPV = $82,025"
Wrong: "NPV = $999,999,999" ← Too obvious, unrealistic"""
        
        wrong_solution_user_prompt = f"""**PROBLEM:**
{generated_content.get('problem_statement', '')}

**CORRECT SOLUTION (for your reference only):**
{generated_content.get('reference_solution', '')}

**YOUR TASK:**
Generate a convincing solution that matches the structure above but contains EXACTLY ONE subtle error appropriate for {payload.difficulty} difficulty.

Choose an error type that would be pedagogically valuable for students to identify.

Write the wrong solution now (using clear markdown formatting with numbered steps):"""
        
        # Generate wrong solution with retry logic for quality
        max_retries = 3
        ai_wrong_solution = None
        
        for attempt in range(max_retries):
            wrong_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": wrong_solution_prompt},
                    {"role": "user", "content": wrong_solution_user_prompt}
                ],
                temperature=0.7 + (attempt * 0.1),  # Increase temperature on retries
                max_tokens=1500
            )
            
            potential_wrong_solution = wrong_response.choices[0].message.content.strip()
            
            # Validate that it's actually different from correct solution
            if validate_wrong_solution(potential_wrong_solution, generated_content.get('reference_solution', '')):
                ai_wrong_solution = potential_wrong_solution
                print(f"[API] Generated valid wrong solution on attempt {attempt + 1}")
                break
            else:
                print(f"[API] Wrong solution too similar to correct one, retrying... (attempt {attempt + 1})")
        
        # If all retries failed, use a fallback
        if not ai_wrong_solution:
            print("[API] Warning: Could not generate sufficiently different wrong solution after retries")
            ai_wrong_solution = generated_content.get('reference_solution', '') + "\n\n*Note: AI solution generation needs manual review*"
        
        # Step 3: Create and save challenge
        challenge_id = f"beatai_{uuid.uuid4().hex[:12]}"
        
        challenge_data = {
            "id": challenge_id,
            "chapter_id": payload.chapter_id,
            "topic": payload.topic,
            "title": generated_content.get("title", "Problem Challenge"),
            "problem_statement": generated_content.get("problem_statement", ""),
            "difficulty": payload.difficulty,
            "tags": generated_content.get("tags", []),
            "reference_solution": generated_content.get("reference_solution", ""),
            "ai_wrong_solution": ai_wrong_solution,
            "created_by_user_id": "professor",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        # Save challenge
        save_challenge(challenge_id, challenge_data)
        
        return {
            "success": True,
            "challenge_id": challenge_id,
            "challenge": challenge_data,
            "message": "Challenge generated and created successfully!"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error generating challenge from chapter: {repr(e)}")
        print(f"[API] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-problem-from-chapter")
def generate_problem_from_chapter(payload: GenerateProblemFromChapterRequest) -> Dict[str, Any]:
    """
    Generate a problem statement and reference solution from a chapter.
    
    Uses RAG to retrieve relevant content from the specified chapter,
    then generates an appropriate problem with solution.
    """
    try:
        # Get vector store and retrieve context from chapter
        vs = get_vector_store()
        
        # Build query based on topic or general chapter content
        if payload.topic:
            query = f"Explain {payload.topic} and provide an example problem"
        else:
            query = "What are the key concepts and problems in this chapter?"
        
        # Retrieve relevant chunks from the chapter
        results = vs.query_by_document(query, payload.chapter_id, top_k=5)
        
        if not results or not results.get("documents"):
            raise HTTPException(
                status_code=404,
                detail=f"No content found for chapter '{payload.chapter_id}'"
            )
        
        # Extract context from retrieved chunks
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        
        context_parts = []
        for doc, meta in zip(documents, metadatas):
            summary = meta.get("summary", "")
            context_parts.append(f"Summary: {summary}\nContent: {doc}")
        
        chapter_context = "\n\n".join(context_parts)
        
        # Generate problem using AI
        client = OpenAI()
        
        difficulty_guidance = {
            "EASY": "straightforward, basic application of concepts",
            "MEDIUM": "moderate difficulty, requiring some analysis",
            "HARD": "challenging, requiring deep understanding and multiple steps"
        }
        
        topic_instruction = f" focusing on the topic: {payload.topic}" if payload.topic else ""
        
        system_prompt = f"""You are an expert instructor creating educational problems.
Based on the provided chapter content, create a {difficulty_guidance[payload.difficulty]} problem{topic_instruction}.

Your response must be in JSON format with these fields:
- title: A short, descriptive title (max 100 chars)
- problem_statement: Clear problem description with any given information
- reference_solution: Complete, step-by-step solution with explanations
- tags: List of 2-4 relevant topic tags

Make the problem realistic and educational."""
        
        user_prompt = f"""Chapter: {payload.chapter_id}

Context from chapter:
{chapter_context[:3000]}

Generate a {payload.difficulty} difficulty problem based on this content."""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        # Parse AI response
        import json as json_lib
        generated_content = json_lib.loads(response.choices[0].message.content)
        
        return {
            "success": True,
            "generated": generated_content,
            "chapter_id": payload.chapter_id
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error generating problem from chapter: {repr(e)}")
        print(f"[API] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROFESSOR ROUTES
# ============================================================================

@router.post("/challenges")
def create_challenge(payload: BeatAIChallengeCreate) -> Dict[str, Any]:
    """
    Create a new Beat the AI challenge.
    
    Requires either pre-filled fields or generates them from the chapter.
    If title, problem_statement, or reference_solution are missing, 
    they must be generated first using /generate-problem-from-chapter.
    """
    try:
        # Validate that required fields are present
        if not payload.title or not payload.problem_statement or not payload.reference_solution:
            raise HTTPException(
                status_code=400,
                detail="title, problem_statement, and reference_solution are required. Use /generate-problem-from-chapter to generate them first."
            )
        
        # Generate challenge ID
        challenge_id = f"beatai_{uuid.uuid4().hex[:12]}"
        
        # Create challenge data
        challenge_data = {
            "id": challenge_id,
            "chapter_id": payload.chapter_id,
            "topic": payload.topic,
            "title": payload.title,
            "problem_statement": payload.problem_statement,
            "difficulty": payload.difficulty,
            "tags": payload.tags,
            "reference_solution": payload.reference_solution,
            "ai_wrong_solution": payload.ai_wrong_solution,
            "created_by_user_id": payload.created_by_user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        # Save challenge
        save_challenge(challenge_id, challenge_data)
        
        return {
            "success": True,
            "challenge_id": challenge_id,
            "challenge": challenge_data
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error creating challenge: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/challenges/{challenge_id}")
def update_challenge(challenge_id: str, payload: BeatAIChallengeUpdate) -> Dict[str, Any]:
    """
    Update an existing Beat the AI challenge.
    
    Professors can update challenge details including the AI wrong solution.
    """
    try:
        # Load existing challenge
        challenge_data = load_challenge(challenge_id)
        
        # Update fields that were provided
        update_data = payload.model_dump(exclude_unset=True)
        challenge_data.update(update_data)
        challenge_data["updated_at"] = datetime.now().isoformat()
        
        # Save updated challenge
        save_challenge(challenge_id, challenge_data)
        
        return {
            "success": True,
            "challenge": challenge_data
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error updating challenge: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/challenges/my")
def get_my_challenges(created_by: str = "professor") -> Dict[str, Any]:
    """
    Get all challenges created by a professor.
    
    Returns challenges with submission count and average score statistics.
    """
    try:
        challenges = []
        
        # Load all challenges
        for challenge_file in BEAT_AI_CHALLENGES_DIR.glob("*.json"):
            try:
                with open(challenge_file, 'r', encoding='utf-8') as f:
                    challenge_data = json.load(f)
                
                # Filter by creator (simplified for file-based system)
                if challenge_data.get("created_by_user_id") == created_by:
                    # Add statistics
                    stats = get_submission_stats(challenge_data["id"])
                    challenge_data["submission_count"] = stats["submission_count"]
                    challenge_data["avg_score"] = stats["avg_score"]
                    
                    challenges.append(challenge_data)
            except Exception as e:
                print(f"[API] Error loading challenge {challenge_file}: {e}")
                continue
        
        # Sort by creation date (newest first)
        challenges.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return {
            "success": True,
            "total": len(challenges),
            "challenges": challenges
        }
    except Exception as e:
        print(f"[API] Error getting challenges: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/challenges/{challenge_id}/professor")
def get_challenge_for_professor(challenge_id: str) -> Dict[str, Any]:
    """
    Get a specific challenge with full details (professor view).
    
    Includes reference solution and all metadata.
    """
    try:
        challenge_data = load_challenge(challenge_id)
        stats = get_submission_stats(challenge_id)
        challenge_data["submission_count"] = stats["submission_count"]
        challenge_data["avg_score"] = stats["avg_score"]
        
        return {
            "success": True,
            "challenge": challenge_data
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error getting challenge: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/submissions/{submission_id}/grade")
def grade_submission(submission_id: str, payload: BeatAISubmissionGradeUpdate) -> Dict[str, Any]:
    """
    Update a submission with a score and review notes.
    
    Professors can manually grade student submissions.
    """
    try:
        # Find the submission across all challenges
        for submissions_file in BEAT_AI_SUBMISSIONS_DIR.glob("*.json"):
            with open(submissions_file, 'r', encoding='utf-8') as f:
                submissions_data = json.load(f)
            
            submissions = submissions_data.get("submissions", [])
            updated = False
            
            for i, sub in enumerate(submissions):
                if sub.get("id") == submission_id:
                    # Update grade and notes
                    submissions[i]["score"] = payload.score
                    submissions[i]["review_notes"] = payload.review_notes
                    submissions[i]["updated_at"] = datetime.now().isoformat()
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
        print(f"[API] Error grading submission: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/challenges/{challenge_id}/generate-wrong-solution")
def generate_wrong_solution(challenge_id: str) -> Dict[str, Any]:
    """
    Generate a convincing but wrong AI solution for a challenge.
    
    Uses OpenAI to create a solution that appears correct but contains
    a subtle conceptual or logical error for students to find.
    """
    try:
        # Load challenge
        challenge_data = load_challenge(challenge_id)
        
        # Get problem and reference solution
        problem_statement = challenge_data.get("problem_statement", "")
        reference_solution = challenge_data.get("reference_solution", "")
        
        if not problem_statement or not reference_solution:
            raise HTTPException(
                status_code=400, 
                detail="Challenge must have problem_statement and reference_solution"
            )
        
        # Create AI prompt with improved instructions
        difficulty = challenge_data.get("difficulty", "MEDIUM")
        
        system_prompt = """You are simulating a confident but flawed AI assistant that makes ONE subtle error in problem-solving.

Your task: Create a solution that appears professional and correct but contains exactly ONE subtle mistake that students must identify.

ERROR TYPES TO CHOOSE FROM:
1. **Conceptual Misunderstanding** - Misapplying a concept (e.g., confusing correlation with causation)
2. **Calculation Error** - Arithmetic mistake that propagates (e.g., 3×7=24 instead of 21)
3. **Logic Flaw** - Faulty reasoning step (e.g., assuming A→B means B→A)
4. **Sign Error** - Wrong positive/negative (e.g., -5 written as +5)
5. **Formula Misuse** - Using wrong formula or wrong variable in formula
6. **Boundary Condition** - Missing edge case or incorrect domain restriction
7. **Unit Confusion** - Wrong units or missing conversion
8. **Assumption Error** - Making invalid assumption not stated in problem

DIFFICULTY MATCHING:
- EASY problems: Use obvious calculation errors (arithmetic mistakes)
- MEDIUM problems: Use conceptual misunderstandings or formula misuse
- HARD problems: Use subtle logic flaws or boundary condition errors

CRITICAL RULES:
✓ Make EXACTLY ONE error (don't make multiple mistakes)
✓ Error should occur in the MIDDLE steps (not first or last)
✓ 90% of the solution should be perfectly correct
✓ Use the same structure and terminology as correct solution
✓ Write confidently - never hint that something might be wrong
✓ Show all work clearly so error is identifiable
✓ Format in clear numbered steps using markdown
✓ The error should be pedagogically valuable (teaches something important)

AVOID:
✗ Don't make typos or obvious mistakes
✗ Don't contradict yourself
✗ Don't skip steps
✗ Don't use different terminology than the problem
✗ Don't make the error in step 1 or the final answer calculation

EXAMPLE - GOOD SUBTLE ERROR:
Correct: "Since the derivative f'(x) < 0, the function is decreasing"
Wrong: "Since the derivative f'(x) < 0, the function is increasing" ← Conceptual error

EXAMPLE - BAD OBVIOUS ERROR:
Correct: "NPV = $82,025"
Wrong: "NPV = $999,999,999" ← Too obvious, unrealistic"""
        
        user_prompt = f"""**PROBLEM:**
{problem_statement}

**CORRECT SOLUTION (for your reference only):**
{reference_solution}

**DIFFICULTY LEVEL:** {difficulty}

**YOUR TASK:**
Generate a convincing solution that matches the structure above but contains EXACTLY ONE subtle error appropriate for {difficulty} difficulty.

Choose an error type that would be pedagogically valuable for students to identify.

Write the wrong solution now (using clear markdown formatting with numbered steps):"""
        
        # Call OpenAI with retry logic for quality
        client = OpenAI()
        max_retries = 3
        ai_wrong_solution = None
        
        for attempt in range(max_retries):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7 + (attempt * 0.1),  # Increase temperature on retries
                max_tokens=1500
            )
            
            potential_wrong_solution = response.choices[0].message.content.strip()
            
            # Validate that it's actually different from correct solution
            if validate_wrong_solution(potential_wrong_solution, reference_solution):
                ai_wrong_solution = potential_wrong_solution
                print(f"[API] Generated valid wrong solution on attempt {attempt + 1}")
                break
            else:
                print(f"[API] Wrong solution too similar to correct one, retrying... (attempt {attempt + 1})")
        
        # If all retries failed, raise an error
        if not ai_wrong_solution:
            raise HTTPException(
                status_code=500,
                detail="Could not generate a sufficiently different wrong solution after multiple attempts. Please try again or manually create the wrong solution."
            )
        
        # Update challenge with generated solution
        challenge_data["ai_wrong_solution"] = ai_wrong_solution
        challenge_data["updated_at"] = datetime.now().isoformat()
        save_challenge(challenge_id, challenge_data)
        
        return {
            "success": True,
            "ai_wrong_solution": ai_wrong_solution,
            "challenge": challenge_data
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error generating wrong solution: {repr(e)}")
        print(f"[API] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/challenges/{challenge_id}/submissions")
def get_challenge_submissions(challenge_id: str) -> Dict[str, Any]:
    """
    Get all submissions for a specific challenge (professor view).
    
    Returns all student submissions with scores and metadata.
    """
    try:
        # Verify challenge exists
        load_challenge(challenge_id)
        
        submissions_file = BEAT_AI_SUBMISSIONS_DIR / f"{challenge_id}.json"
        
        if not submissions_file.exists():
            return {
                "success": True,
                "challenge_id": challenge_id,
                "submissions": []
            }
        
        with open(submissions_file, 'r', encoding='utf-8') as f:
            submissions_data = json.load(f)
        
        submissions = submissions_data.get("submissions", [])
        
        return {
            "success": True,
            "challenge_id": challenge_id,
            "total": len(submissions),
            "submissions": submissions
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error getting challenge submissions: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STUDENT ROUTES
# ============================================================================

@router.get("/challenges/available")
def get_available_challenges() -> Dict[str, Any]:
    """
    Get all available challenges for students.
    
    Returns all challenges without reference solutions.
    """
    try:
        challenges = []
        
        # Load all challenges
        for challenge_file in BEAT_AI_CHALLENGES_DIR.glob("*.json"):
            try:
                with open(challenge_file, 'r', encoding='utf-8') as f:
                    challenge_data = json.load(f)
                
                # Remove reference solution for student view
                student_challenge = {
                    "id": challenge_data["id"],
                    "title": challenge_data["title"],
                    "problem_statement": challenge_data["problem_statement"],
                    "difficulty": challenge_data["difficulty"],
                    "tags": challenge_data.get("tags", []),
                    "ai_wrong_solution": challenge_data.get("ai_wrong_solution", ""),
                    "created_at": challenge_data.get("created_at", "")
                }
                
                challenges.append(student_challenge)
            except Exception as e:
                print(f"[API] Error loading challenge {challenge_file}: {e}")
                continue
        
        # Sort by creation date (newest first)
        challenges.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return {
            "success": True,
            "total": len(challenges),
            "challenges": challenges
        }
    except Exception as e:
        print(f"[API] Error getting available challenges: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/challenges/{challenge_id}")
def get_challenge(challenge_id: str) -> Dict[str, Any]:
    """
    Get a specific challenge (student view).
    
    Returns challenge without reference solution.
    """
    try:
        challenge_data = load_challenge(challenge_id)
        
        # Remove reference solution for student view
        student_challenge = {
            "id": challenge_data["id"],
            "title": challenge_data["title"],
            "problem_statement": challenge_data["problem_statement"],
            "difficulty": challenge_data["difficulty"],
            "tags": challenge_data.get("tags", []),
            "ai_wrong_solution": challenge_data.get("ai_wrong_solution", "")
        }
        
        return {
            "success": True,
            "challenge": student_challenge
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error getting challenge: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def generate_ai_feedback(
    challenge: Dict[str, Any],
    student_errors: List[Dict[str, Any]],
    workflow_suggestion: Optional[str]
) -> str:
    """
    Generate AI feedback for a student submission.
    
    Analyzes the student's error identification and provides constructive feedback.
    """
    try:
        # Get AI wrong solution segments
        ai_solution = challenge.get("ai_wrong_solution", "")
        segments = [line for line in ai_solution.split('\n') if line.strip()]
        
        # Format student's selected errors
        student_errors_text = "\n".join([
            f"- Segment {err['segment_index']}: {err['segment_text'][:100]}... "
            f"(Classified as: {err['error_type']}"
            f"{f', Description: {err['custom_description']}' if err.get('custom_description') else ''})"
            for err in student_errors
        ])
        
        # Generate feedback using AI
        client = OpenAI()
        
        system_prompt = """You are an encouraging educational AI assistant providing feedback to students.
Your role is to analyze how well the student identified errors in an AI's solution and provide constructive feedback.

Be:
- Encouraging and positive
- Specific about what they did well
- Constructive about areas for improvement
- Educational and insightful

Format your feedback in clear sections:
1. What You Did Well
2. Error Analysis
3. Areas for Growth
4. Key Takeaway"""
        
        user_prompt = f"""A student just attempted to find errors in an AI solution to this problem:

PROBLEM:
{challenge.get('problem_statement', '')[:500]}...

AI'S WRONG SOLUTION:
{ai_solution[:1000]}...

REFERENCE SOLUTION (CORRECT):
{challenge.get('reference_solution', '')[:500]}...

STUDENT'S ERROR IDENTIFICATION:
{student_errors_text}

{f"STUDENT'S WORKFLOW SUGGESTION: {workflow_suggestion}" if workflow_suggestion else ""}

Total errors identified by student: {len(student_errors)}

Provide encouraging and constructive feedback on their error identification. 
Be specific about which errors they correctly identified and their classifications.
Keep the feedback concise but meaningful (3-4 paragraphs)."""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[API] Error generating AI feedback: {repr(e)}")
        return "Thank you for your submission! Your professor will review it soon."


@router.post("/challenges/{challenge_id}/submissions")
def create_submission(challenge_id: str, payload: BeatAISubmissionCreate) -> Dict[str, Any]:
    """
    Create a student submission for a challenge.
    
    Students can only submit once per challenge. Subsequent submissions will fail.
    Students select multiple incorrect steps and classify each error type.
    Generates instant AI feedback after submission.
    """
    try:
        # Load challenge data for feedback generation
        challenge_data = load_challenge(challenge_id)
        
        # Load or create submissions file
        submissions_file = BEAT_AI_SUBMISSIONS_DIR / f"{challenge_id}.json"
        
        if submissions_file.exists():
            with open(submissions_file, 'r', encoding='utf-8') as f:
                submissions_data = json.load(f)
        else:
            submissions_data = {"challenge_id": challenge_id, "submissions": []}
        
        # Check if student already submitted
        existing_submissions = submissions_data.get("submissions", [])
        for sub in existing_submissions:
            if sub.get("student_id") == payload.student_id:
                raise HTTPException(
                    status_code=409, 
                    detail="You have already submitted a solution for this challenge"
                )
        
        # Create submission
        submission_id = f"beatai_sub_{uuid.uuid4().hex[:12]}"
        
        # Convert ErrorClassification objects to dicts
        selected_errors_dicts = [
            {
                "segment_index": err.segment_index,
                "segment_text": err.segment_text,
                "error_type": err.error_type,
                "custom_description": err.custom_description
            }
            for err in payload.selected_errors
        ]
        
        # Generate AI feedback
        print(f"[API] Generating AI feedback for submission {submission_id}...")
        ai_feedback = generate_ai_feedback(
            challenge_data,
            selected_errors_dicts,
            payload.workflow_suggestion
        )
        print(f"[API] AI feedback generated successfully")
        
        submission = {
            "id": submission_id,
            "challenge_id": challenge_id,
            "student_id": payload.student_id,
            "selected_errors": selected_errors_dicts,
            "workflow_suggestion": payload.workflow_suggestion,
            "ai_feedback": ai_feedback,
            "score": None,
            "review_notes": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        # Add submission
        existing_submissions.append(submission)
        submissions_data["submissions"] = existing_submissions
        
        # Save to file
        with open(submissions_file, 'w', encoding='utf-8') as f:
            json.dump(submissions_data, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "submission_id": submission_id,
            "submission": submission
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error creating submission: {repr(e)}")
        print(f"[API] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/challenges/{challenge_id}/submissions/my")
def get_my_submission(challenge_id: str, student_id: str = "student") -> Dict[str, Any]:
    """
    Get a student's submission for a specific challenge.
    
    Returns the student's submission if it exists, otherwise returns null.
    """
    try:
        # Verify challenge exists
        load_challenge(challenge_id)
        
        submissions_file = BEAT_AI_SUBMISSIONS_DIR / f"{challenge_id}.json"
        
        if not submissions_file.exists():
            return {
                "success": True,
                "challenge_id": challenge_id,
                "submission": None
            }
        
        with open(submissions_file, 'r', encoding='utf-8') as f:
            submissions_data = json.load(f)
        
        submissions = submissions_data.get("submissions", [])
        
        # Find student's submission
        student_submission = None
        for sub in submissions:
            if sub.get("student_id") == student_id:
                student_submission = sub
                break
        
        return {
            "success": True,
            "challenge_id": challenge_id,
            "submission": student_submission
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error getting student submission: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/challenges/{challenge_id}/reference-solution")
def get_reference_solution(challenge_id: str, student_id: str = "student") -> Dict[str, Any]:
    """
    Get the reference solution for a challenge.
    
    Only accessible after the student has submitted a solution.
    Returns 403 if student has not submitted yet.
    """
    try:
        # Load challenge
        challenge_data = load_challenge(challenge_id)
        
        # Check if student has submitted
        submissions_file = BEAT_AI_SUBMISSIONS_DIR / f"{challenge_id}.json"
        
        has_submitted = False
        if submissions_file.exists():
            with open(submissions_file, 'r', encoding='utf-8') as f:
                submissions_data = json.load(f)
            
            submissions = submissions_data.get("submissions", [])
            for sub in submissions:
                if sub.get("student_id") == student_id:
                    has_submitted = True
                    break
        
        if not has_submitted:
            raise HTTPException(
                status_code=403, 
                detail="You must submit a solution before viewing the reference solution"
            )
        
        return {
            "success": True,
            "reference_solution": challenge_data.get("reference_solution", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error getting reference solution: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UTILITY ROUTES
# ============================================================================

@router.delete("/challenges/{challenge_id}")
def delete_challenge(challenge_id: str) -> Dict[str, Any]:
    """
    Delete a challenge and all its submissions.
    
    This is a utility endpoint for cleanup.
    """
    try:
        # Delete challenge file
        challenge_file = BEAT_AI_CHALLENGES_DIR / f"{challenge_id}.json"
        if not challenge_file.exists():
            raise HTTPException(status_code=404, detail=f"Challenge '{challenge_id}' not found")
        
        challenge_file.unlink()
        
        # Delete associated submissions
        submissions_file = BEAT_AI_SUBMISSIONS_DIR / f"{challenge_id}.json"
        if submissions_file.exists():
            submissions_file.unlink()
        
        return {
            "success": True,
            "message": f"Challenge '{challenge_id}' deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error deleting challenge: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))

