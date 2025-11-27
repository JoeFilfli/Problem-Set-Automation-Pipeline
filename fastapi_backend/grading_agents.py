"""
Grading agent system for evaluating student problem set submissions.
Uses specialized agents for rubric generation, evaluation, and feedback.
"""
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
import json
import concurrent.futures
import re

load_dotenv(override=True)


class Agent:
    """Base class for grading agents."""
    
    def __init__(self, name: str, role: str, model: str = "gpt-4o"):
        self.name = name
        self.role = role
        self.model = model
        self.client = OpenAI()
        
    def run(self, task: str, context: Dict[str, Any] = None, max_tokens: int = 2000) -> str:
        """Execute the agent's task."""
        print(f"   [{self.name}] Processing...")
        
        messages = [
            {"role": "system", "content": self.role},
            {"role": "user", "content": task}
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,  # Limit response size
            temperature=0.7,        # Slightly reduce variability for speed
            timeout=30              # Fail fast if stuck
        )
        
        result = response.choices[0].message.content
        print(f"   [{self.name}] ✓ Complete")
        return result


class RubricGeneratorAgent(Agent):
    """Generates detailed grading rubrics for problems."""
    
    def __init__(self):
        super().__init__(
            name="Rubric Generator",
            role="""You are an expert at creating detailed, fair grading rubrics.
Your rubrics should:
- Break down problems into scorable steps based on CONCEPTUAL GOALS, not rigid step sequences
- Assign point values based on difficulty and importance
- Include partial credit criteria
- Be objective and measurable
- Cover conceptual understanding, methodology, and accuracy
- RECOGNIZE ALTERNATIVE VALID METHODS - students may solve problems differently

For each criterion:
- Describe the CONCEPTUAL GOAL (what understanding is being checked)
- Avoid requiring an exact step order unless essential
- Keep descriptions concise

Return rubrics as JSON (keep it concise):
{
  "total_points": X,
  "criteria": [
    {
      "step": "description of conceptual goal",
      "points": X,
      "requirements": ["what must be true conceptually"],
      "partial_credit": {"description": points}
    }
  ]
}

Note: Keep output brief. Focus on core concepts, not exhaustive lists."""
        )
    
    def generate_rubric(
        self,
        problem: Dict[str, Any],
        correct_solution: str
    ) -> Dict[str, Any]:
        """Generate grading rubric for a problem."""
        
        task = f"""Create a detailed grading rubric for this problem:

PROBLEM:
{json.dumps(problem, indent=2)}

CORRECT SOLUTION:
{correct_solution}

Generate a comprehensive rubric that breaks down the solution into gradable steps.
Return ONLY valid JSON as specified in your role."""
        
        response = self.run(task)
        
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            
            # Try to parse directly first
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as je:
                # If JSON has escape issues, try to fix common problems
                print(f"   [WARNING] Initial JSON parse failed: {je}")
                print(f"   [INFO] Attempting to fix JSON formatting...")
                
                # Try using json.JSONDecoder with strict=False
                import json as json_module
                try:
                    # Replace problematic escape sequences
                    fixed_json = json_str.replace('\\', '\\\\')  # Escape backslashes
                    # But don't double-escape already valid ones
                    fixed_json = fixed_json.replace('\\\\n', '\\n')
                    fixed_json = fixed_json.replace('\\\\t', '\\t')
                    fixed_json = fixed_json.replace('\\\\r', '\\r')
                    fixed_json = fixed_json.replace('\\\\\\\\', '\\\\')
                    
                    return json.loads(fixed_json)
                except:
                    # If still failing, ask AI to regenerate with stricter instructions
                    print(f"   [INFO] Requesting corrected JSON from AI...")
                    retry_task = f"""The previous JSON response had formatting errors. Please return ONLY valid JSON with proper escaping.

PROBLEM:
{json.dumps(problem, indent=2)}

CORRECT SOLUTION:
{correct_solution}

Return ONLY a valid JSON rubric. Ensure all strings are properly escaped."""
                    
                    retry_response = self.run(retry_task)
                    retry_start = retry_response.find("{")
                    retry_end = retry_response.rfind("}") + 1
                    retry_json = retry_response[retry_start:retry_end]
                    return json.loads(retry_json)
                    
        except Exception as e:
            print(f"   [WARNING] Failed to parse rubric JSON after retries: {e}")
            return {"total_points": 10, "criteria": [], "error": str(e)}


class SolutionEvaluatorAgent(Agent):
    """Evaluates student solutions against correct answers and rubrics."""
    
    def __init__(self):
        super().__init__(
            name="Solution Evaluator",
            role="""You are an expert at evaluating student work fairly and consistently.
Evaluate solutions by:
- Checking each step against the rubric
- Identifying correct and incorrect work
- Recognizing conceptual understanding vs computational errors
- Assigning appropriate partial credit
- Being fair but rigorous

Return evaluation as JSON:
{
  "score": X,
  "max_score": Y,
  "percentage": Z,
  "criteria_scores": [
    {
      "criterion": "step description",
      "earned": X,
      "possible": Y,
      "correct": true/false,
      "notes": "explanation"
    }
  ],
  "strengths": ["strength1", "strength2"],
  "errors": ["error1", "error2"],
  "overall_assessment": "brief summary"
}"""
        )
    
    def _extract_text_from_images(self, image_urls: List[str], images_dir) -> str:
        """
        Extract text from images using OCR (via OpenAI Vision API).
        This uses a simple text extraction prompt to avoid safety filters.
        """
        import base64
        from pathlib import Path
        
        all_extracted_text = []
        
        for url in image_urls:
            try:
                # Extract image ID from URL
                image_id = url.split('/')[-1]
                matching_files = list(images_dir.glob(f"{image_id}.*"))
                
                if not matching_files:
                    print(f"   [WARNING] Image file not found for OCR: {image_id}")
                    continue
                
                image_path = matching_files[0]
                
                # Read and encode image
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                
                b64 = base64.b64encode(image_bytes).decode("utf-8")
                
                # Determine MIME type
                ext = image_path.suffix.lower()
                mime_types = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".gif": "image/gif",
                    ".webp": "image/webp"
                }
                mime = mime_types.get(ext, "image/png")
                
                # Use simple OCR-focused prompt (similar to pdf_extractor)
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """Extract all text from this image, including handwritten content.

IMPORTANT for accuracy:
- Preserve the structure and layout as much as possible
- Include all mathematical equations, formulas, and calculations
- Represent equations in plain math notation (e.g., F = P(1+i)^n)
- If you see numbered steps, clearly mark them as "Step 1:", "Step 2:", etc.
- If you see calculations, preserve the sequence (formula → substitution → result)
- If the handwriting is unclear, make your best interpretation
- Include any diagrams or drawings described in text form

Return ONLY the extracted text, no commentary or analysis."""
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime};base64,{b64}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=2000
                )
                
                extracted = response.choices[0].message.content
                if extracted and len(extracted.strip()) > 0:
                    all_extracted_text.append(extracted)
                    print(f"   [INFO] OCR extracted {len(extracted)} chars from {image_path.name}")
                
            except Exception as e:
                print(f"   [ERROR] OCR extraction failed for image: {e}")
                continue
        
        return "\n\n".join(all_extracted_text)
    
    def evaluate_solution(
        self,
        problem: Dict[str, Any],
        correct_solution: str,
        student_solution: str,
        rubric: Dict[str, Any],
        image_urls: List[str] = None
    ) -> Dict[str, Any]:
        """Evaluate student's solution against rubric, with optional vision support."""
        
        # Check if student used images
        has_images = image_urls and len(image_urls) > 0
        
        if has_images:
            # OPTIMIZED APPROACH: Go directly to OCR since vision grading consistently fails
            # This is faster, more reliable, and cheaper (fewer API calls)
            print(f"   [Solution Evaluator] Processing {len(image_urls)} image(s) via OCR...")
            
            import base64
            from pathlib import Path
            from api.dependencies import STORAGE_DIR
            
            IMAGES_DIR = STORAGE_DIR / "images"
            
            # Extract text from images using OCR
            extracted_text = self._extract_text_from_images(image_urls, IMAGES_DIR)
            
            if extracted_text and len(extracted_text.strip()) > 20:
                print(f"   [INFO] OCR extracted {len(extracted_text)} characters")
                print(f"   [DEBUG] Extracted text preview: {extracted_text[:300]}...")
                print(f"   [DEBUG] Grading problem: {problem.get('text', problem.get('description', 'N/A'))[:100]}...")
                
                # Combine with any text the student typed
                combined_solution = student_solution + "\n\n[Extracted from image(s)]:\n" + extracted_text
                
                # Grade using text-only evaluation
                task = f"""Evaluate this student's solution:

PROBLEM:
{json.dumps(problem, indent=2)}

CORRECT SOLUTION:
{correct_solution}

STUDENT SOLUTION:
{combined_solution}

GRADING RUBRIC:
{json.dumps(rubric, indent=2)}

CRITICAL GRADING INSTRUCTIONS - READ CAREFULLY:
- The student submitted their work as an image. The text above was extracted using OCR.
- PRIORITIZE conceptual understanding and mathematically correct reasoning above ALL else.
- The rubric is a GUIDE, not a strict template. DO NOT fail students for formatting or step order.

SCORING POLICY (MANDATORY):
- If the student's FINAL ANSWER is CORRECT → Give 80-100% of points regardless of method
- If the student's APPROACH is CORRECT but has minor errors → Give 60-80% of points
- If the student shows UNDERSTANDING but made calculation errors → Give 40-60% of points
- If the student ATTEMPTED the problem with relevant math → Give at least 25-30% of points
- ONLY give below 25% if: completely blank, irrelevant content, or fundamentally wrong concept

WHAT TO REWARD:
- Correct final answers (even with different methods)
- Valid alternative formulas or approaches
- Correct reasoning with calculation mistakes
- Proper identification of problem type and variables
- Any demonstration of relevant mathematical knowledge

DO NOT PENALIZE:
- Different step order than rubric
- Equivalent formulas (e.g., PV = FV/(1+i)^n vs PV = FV(P/F, i%, n))
- Minor algebraic differences
- OCR formatting artifacts
- Notation variations
- Steps combined or split differently

REMEMBER: Your job is to recognize UNDERSTANDING, not to match a template perfectly.
If a student demonstrates they know how to solve this type of problem, REWARD THEM GENEROUSLY.

Return ONLY valid JSON as specified in your role."""
                
                result = self.run(task)
            else:
                # OCR failed or insufficient text extracted
                print(f"   [WARNING] OCR extraction failed or returned insufficient text")
                
                # Check if student provided any meaningful text solution
                import re
                text_only = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', '', student_solution).strip()
                
                if len(text_only) < 20:
                    # No text at all - provide helpful error
                    print(f"   [WARNING] No processable content found")
                    result = json.dumps({
                        "score": 0,
                        "max_score": rubric.get("total_points", 10),
                        "percentage": 0,
                        "criteria_scores": [
                            {
                                "criterion": criterion.get("step", "Unknown"),
                                "earned": 0,
                                "possible": criterion.get("points", 0),
                                "correct": False,
                                "notes": "Image could not be processed by the automated grading system"
                            }
                            for criterion in rubric.get("criteria", [])
                        ],
                        "strengths": [],
                        "errors": ["Automated image processing failed"],
                        "overall_assessment": "The image(s) in your submission could not be processed. Please type your solution as text instead, or request manual grading from your instructor."
                    })
                else:
                    # Grade the typed text
                    task = f"""Evaluate this student's solution:

PROBLEM:
{json.dumps(problem, indent=2)}

CORRECT SOLUTION:
{correct_solution}

STUDENT SOLUTION:
{student_solution}

GRADING RUBRIC:
{json.dumps(rubric, indent=2)}

IMPORTANT CONTEXT:
- Student uploaded images but OCR extraction failed (technical issue, not student's fault).
- Only grade based on any typed text that is present.
- If there is insufficient typed text to evaluate, you must assign a low score,
  BUT include a clear note explaining this is due to technical limitations, not lack of effort.
- DO NOT assume the student did nothing - they may have worked hard on paper but the system couldn't read it.

Return ONLY valid JSON as specified in your role."""
                    
                    result = self.run(task)
            
        else:
            # Use text-only model (original implementation)
            task = f"""Evaluate this student's solution:

PROBLEM:
{json.dumps(problem, indent=2)}

CORRECT SOLUTION:
{correct_solution}

STUDENT SOLUTION:
{student_solution}

GRADING RUBRIC:
{json.dumps(rubric, indent=2)}

CRITICAL GRADING INSTRUCTIONS - READ CAREFULLY:
- PRIORITIZE conceptual understanding and mathematically correct reasoning above ALL else.
- The rubric is a GUIDE, not a strict template. DO NOT fail students for formatting or step order.

SCORING POLICY (MANDATORY):
- If the student's FINAL ANSWER is CORRECT → Give 80-100% of points regardless of method
- If the student's APPROACH is CORRECT but has minor errors → Give 60-80% of points
- If the student shows UNDERSTANDING but made calculation errors → Give 40-60% of points
- If the student ATTEMPTED the problem with relevant math → Give at least 25-30% of points
- ONLY give below 25% if: completely blank, irrelevant content, or fundamentally wrong concept

WHAT TO REWARD:
- Correct final answers (even with different methods)
- Valid alternative formulas or approaches
- Correct reasoning with calculation mistakes
- Proper identification of problem type and variables
- Any demonstration of relevant mathematical knowledge

DO NOT PENALIZE:
- Different step order than rubric
- Equivalent formulas (e.g., PV = FV/(1+i)^n vs PV = FV(P/F, i%, n))
- Minor algebraic differences
- Notation variations
- Steps combined or split differently

REMEMBER: Your job is to recognize UNDERSTANDING, not to match a template perfectly.
If a student demonstrates they know how to solve this type of problem, REWARD THEM GENEROUSLY.

Return ONLY valid JSON as specified in your role."""
            
            result = self.run(task)
        
        # Parse JSON response (same for both paths)
        try:
            # Debug: print the raw response
            print(f"   [DEBUG] Raw AI response length: {len(result)} chars")
            print(f"   [DEBUG] First 200 chars: {result[:200]}")
            
            # Remove markdown code blocks if present (```json ... ```)
            import re
            result_cleaned = re.sub(r'```json\s*', '', result)
            result_cleaned = re.sub(r'```\s*$', '', result_cleaned)
            result_cleaned = result_cleaned.strip()
            
            start = result_cleaned.find("{")
            end = result_cleaned.rfind("}") + 1
            
            if start == -1 or end == 0:
                print(f"   [ERROR] No JSON found in response!")
                print(f"   [DEBUG] Full response:\n{result_cleaned}")
                raise ValueError("No JSON object found in AI response")
            
            json_str = result_cleaned[start:end]
            parsed = json.loads(json_str)
            
            # Ensure required fields exist
            if "criteria_scores" not in parsed:
                parsed["criteria_scores"] = []
            if "strengths" not in parsed:
                parsed["strengths"] = []
            if "errors" not in parsed:
                parsed["errors"] = []
                
            return parsed
        except Exception as e:
            print(f"   [WARNING] Failed to parse evaluation JSON: {e}")
            print(f"   [DEBUG] Full response that failed:\n{result}")
            return {
                "score": 0,
                "max_score": rubric.get("total_points", 10),
                "percentage": 0,
                "criteria_scores": [],
                "strengths": [],
                "errors": ["Failed to parse AI response"],
                "overall_assessment": "Error during grading",
                "error": str(e)
            }


class FeedbackGeneratorAgent(Agent):
    """Generates constructive feedback for students."""
    
    def __init__(self):
        super().__init__(
            name="Feedback Generator",
            role="""You are an encouraging and helpful instructor providing feedback.
Your feedback should:
- Be constructive and supportive
- Explain what was done well
- Clearly identify errors and misconceptions
- Suggest specific improvements
- Guide learning without giving away answers
- Be personalized to the student's work
- Encourage continued effort"""
        )
    
    def generate_feedback(
        self,
        problem: Dict[str, Any],
        evaluation: Dict[str, Any],
        student_solution: str
    ) -> str:
        """Generate personalized feedback for the student."""
        
        task = f"""Generate constructive feedback for this student:

PROBLEM:
{json.dumps(problem, indent=2)}

STUDENT'S SOLUTION:
{student_solution}

EVALUATION RESULTS:
{json.dumps(evaluation, indent=2)}

Write encouraging, specific feedback that helps the student learn.
Focus on both what they did well and how to improve."""
        
        return self.run(task)


class GradingOrchestrator:
    """Orchestrates the grading process using multiple agents."""
    
    def __init__(self):
        self.rubric_gen = RubricGeneratorAgent()
        self.evaluator = SolutionEvaluatorAgent()
        self.feedback_gen = FeedbackGeneratorAgent()
        self._rubric_cache = {}  # Cache rubrics by problem ID to avoid regeneration
        
    def grade_submission(
        self,
        problem: Dict[str, Any],
        correct_solution: str,
        student_solution: str,
        student_name: str = "Student",
        generate_rubric: bool = True,
        existing_rubric: Dict[str, Any] = None,
        image_urls: List[str] = None,
        generate_feedback: bool = True
    ) -> Dict[str, Any]:
        """
        Grade a single student submission.
        
        Args:
            problem: The problem definition
            correct_solution: The correct solution
            student_solution: The student's submitted solution
            student_name: Student identifier
            generate_rubric: Whether to generate a new rubric
            existing_rubric: Pre-existing rubric to use
            image_urls: Optional list of image URLs for vision-based grading
            
        Returns:
            Complete grading result with score, evaluation, and feedback
        """
        print(f"\n{'='*70}")
        print(f"GRADING SUBMISSION: {student_name}")
        print(f"{'='*70}\n")
        
        # Step 1: Generate or use existing rubric (with caching)
        if generate_rubric or existing_rubric is None:
            # Check cache first
            problem_id = problem.get('id', None)
            cache_key = f"{problem_id}_{hash(correct_solution)}" if problem_id else None
            
            if cache_key and cache_key in self._rubric_cache:
                print(f"[Step 1] Using cached rubric ({self._rubric_cache[cache_key].get('total_points', 0)} points)\n")
                rubric = self._rubric_cache[cache_key]
            else:
                print("[Step 1] Generating grading rubric...")
                rubric = self.rubric_gen.generate_rubric(problem, correct_solution)
                print(f"   ✓ Rubric created ({rubric.get('total_points', 0)} points)\n")
                
                # Cache the rubric
                if cache_key:
                    self._rubric_cache[cache_key] = rubric
        else:
            rubric = existing_rubric
            print(f"[Step 1] Using existing rubric ({rubric.get('total_points', 0)} points)\n")
        
        # Step 2: Evaluate student's solution (with images if provided)
        print("[Step 2] Evaluating student solution...")
        evaluation = self.evaluator.evaluate_solution(
            problem,
            correct_solution,
            student_solution,
            rubric,
            image_urls=image_urls  # Pass images to evaluator
        )
        score = evaluation.get('score', 0)
        max_score = evaluation.get('max_score', rubric.get('total_points', 10))
        percentage = evaluation.get('percentage', (score/max_score*100) if max_score > 0 else 0)
        print(f"   ✓ Score: {score}/{max_score} ({percentage:.1f}%)\n")
        
        # Step 2.5: Safety rail - sanity check for extremely low scores
        # This catches cases where valid work gets scored unfairly due to rigid rubric matching
        flagged_for_review = False
        original_score = score
        
        # CRITICAL FIX: Check if score is suspiciously low (less than 20% for any substantial work)
        if percentage < 20 and len(student_solution.strip()) > 30:
            print(f"   [SAFETY CHECK] Very low score ({percentage:.1f}%) detected. Running sanity check...")
            
            # Check if student solution shows mathematical reasoning
            import re
            # Look for mathematical content: numbers, formulas, equals signs, common math symbols, keywords
            has_math_content = bool(re.search(r'[\d\+\-\*\/\=\^\(\)]|formula|calculate|result|answer|value|rate|cost|price|npv|irr|present|future', 
                                              student_solution.lower()))
            
            # FIXED LOGIC: Flag if score is below 20% AND there's any meaningful content
            # Don't require "no partial credit" - even 1/12 (8.3%) should be flagged if work was shown
            if has_math_content:
                print(f"   [WARNING] Student showed mathematical work but received {score}/{max_score} ({percentage:.1f}%).")
                print(f"   [WARNING] This is suspiciously low and may indicate rubric mismatch.")
                print(f"   [ACTION] FLAGGING FOR MANUAL REVIEW - instructor must verify this grade.")
                flagged_for_review = True
                
                # Enforce a minimum floor for students showing meaningful work
                # If they attempted the problem with math content, give at least 25% credit
                min_score = max(int(max_score * 0.25), 3)  # At least 25% or 3 points
                if score < min_score:
                    original_percentage = percentage
                    score = min_score
                    percentage = (score / max_score * 100) if max_score > 0 else 0
                    print(f"   [ADJUSTED] Score raised from {original_score} to {score}/{max_score} ({percentage:.1f}%)")
                    print(f"   [REASON] Student showed meaningful attempt - enforcing minimum credit policy.")
        
        # Step 3: Generate personalized feedback (optional for speed)
        if generate_feedback:
            print("[Step 3] Generating feedback...")
            feedback = self.feedback_gen.generate_feedback(
                problem,
                evaluation,
                student_solution
            )
            print(f"   ✓ Feedback generated\n")
        else:
            print("[Step 3] Skipping feedback generation (deferred for speed)\n")
            feedback = "Feedback will be generated separately. Your score is shown above."
        
        result = {
            "student_name": student_name,
            "problem": problem,
            "rubric": rubric,
            "evaluation": evaluation,
            "feedback": feedback,
            "summary": {
                "score": score,
                "max_score": max_score,
                "percentage": percentage,
                "grade": self._calculate_letter_grade(percentage),
                "flagged_for_review": flagged_for_review,
                "needs_manual_review": flagged_for_review  # For instructor attention
            }
        }
        
        if flagged_for_review:
            result["summary"]["review_reason"] = (
                f"Automatic grading gave very low score ({original_score}/{max_score}) "
                "despite student showing mathematical work. Please review manually."
            )
        
        print(f"{'='*70}")
        status = " [FLAGGED FOR REVIEW]" if flagged_for_review else ""
        print(f"GRADING COMPLETE: {score}/{max_score} ({percentage:.1f}%) - {result['summary']['grade']}{status}")
        print(f"{'='*70}\n")
        
        return result
    
    def grade_batch(
        self,
        problem: Dict[str, Any],
        correct_solution: str,
        student_submissions: List[Dict[str, str]],
        parallel: bool = True,
        generate_feedback: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Grade multiple student submissions for the same problem.
        
        Args:
            problem: The problem definition
            correct_solution: The correct solution
            student_submissions: List of {name, solution} dicts
            parallel: Whether to grade submissions in parallel (faster)
            generate_feedback: Whether to generate feedback (disable for speed)
            
        Returns:
            List of grading results
        """
        print(f"\n{'='*70}")
        print(f"BATCH GRADING: {len(student_submissions)} submissions")
        print(f"{'='*70}\n")
        
        # Generate rubric once for all students
        print("[INIT] Generating shared rubric...")
        rubric = self.rubric_gen.generate_rubric(problem, correct_solution)
        print(f"   ✓ Rubric created ({rubric.get('total_points', 0)} points)\n")
        
        # Extract image URLs for all submissions first
        import re
        submissions_with_images = []
        for submission in student_submissions:
            solution_text = submission['solution']
            image_pattern = r'!\[([^\]]*)\]\((/api/py/images/[^)]+)\)'
            image_urls = re.findall(image_pattern, solution_text)
            image_urls = [url[1] for url in image_urls]  # Extract just the URLs
            
            submissions_with_images.append({
                'submission': submission,
                'image_urls': image_urls if image_urls else None
            })
        
        results = []
        
        if parallel and len(student_submissions) > 1:
            # PARALLEL GRADING - Much faster for multiple students
            print(f"[MODE] Parallel grading enabled (max 5 concurrent)\n")
            import concurrent.futures
            
            def grade_single(sub_data):
                """Helper function for parallel execution"""
                sub = sub_data['submission']
                imgs = sub_data['image_urls']
                return self.grade_submission(
                    problem=problem,
                    correct_solution=correct_solution,
                    student_solution=sub['solution'],
                    student_name=sub['name'],
                    generate_rubric=False,
                    existing_rubric=rubric,
                    image_urls=imgs,
                    generate_feedback=generate_feedback
                )
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # Submit all grading tasks
                futures = {
                    executor.submit(grade_single, sub_data): i 
                    for i, sub_data in enumerate(submissions_with_images, 1)
                }
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(futures):
                    idx = futures[future]
                    try:
                        result = future.result()
                        results.append((idx, result))
                        print(f"   ✓ Completed {idx}/{len(student_submissions)}")
                    except Exception as e:
                        print(f"   ✗ Error grading student {idx}: {e}")
                        # Add error result
                        results.append((idx, {
                            "student_name": submissions_with_images[idx-1]['submission']['name'],
                            "error": str(e),
                            "summary": {"score": 0, "max_score": rubric.get('total_points', 10)}
                        }))
            
            # Sort results by original order
            results = [r[1] for r in sorted(results, key=lambda x: x[0])]
            
        else:
            # SEQUENTIAL GRADING - Original implementation
            print(f"[MODE] Sequential grading\n")
            for i, sub_data in enumerate(submissions_with_images, 1):
                print(f"Processing {i}/{len(student_submissions)}...")
                
                result = self.grade_submission(
                    problem=problem,
                    correct_solution=correct_solution,
                    student_solution=sub_data['submission']['solution'],
                    student_name=sub_data['submission']['name'],
                    generate_rubric=False,
                    existing_rubric=rubric,
                    image_urls=sub_data['image_urls'],
                    generate_feedback=generate_feedback
                )
                results.append(result)
        
        # Calculate statistics
        scores = [r['summary']['percentage'] for r in results]
        stats = {
            "total_students": len(results),
            "average": sum(scores) / len(scores) if scores else 0,
            "median": sorted(scores)[len(scores)//2] if scores else 0,
            "min": min(scores) if scores else 0,
            "max": max(scores) if scores else 0,
            "grade_distribution": self._calculate_grade_distribution(results)
        }
        
        print(f"\n{'='*70}")
        print(f"BATCH GRADING COMPLETE")
        print(f"Average: {stats['average']:.1f}%")
        print(f"Range: {stats['min']:.1f}% - {stats['max']:.1f}%")
        print(f"{'='*70}\n")
        
        return results, stats
    
    def _calculate_letter_grade(self, percentage: float) -> str:
        """Convert percentage to letter grade."""
        if percentage >= 93: return "A"
        elif percentage >= 90: return "A-"
        elif percentage >= 87: return "B+"
        elif percentage >= 83: return "B"
        elif percentage >= 80: return "B-"
        elif percentage >= 77: return "C+"
        elif percentage >= 73: return "C"
        elif percentage >= 70: return "C-"
        elif percentage >= 67: return "D+"
        elif percentage >= 63: return "D"
        elif percentage >= 60: return "D-"
        else: return "F"
    
    def _calculate_grade_distribution(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate distribution of letter grades."""
        distribution = {}
        for result in results:
            grade = result['summary']['grade']
            distribution[grade] = distribution.get(grade, 0) + 1
        return distribution
