"""
Grading agent system for evaluating student problem set submissions.
Uses specialized agents for rubric generation, evaluation, and feedback.
"""
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv(override=True)


class Agent:
    """Base class for grading agents."""
    
    def __init__(self, name: str, role: str, model: str = "gpt-4o-mini"):
        self.name = name
        self.role = role
        self.model = model
        self.client = OpenAI()
        
    def run(self, task: str, context: Dict[str, Any] = None) -> str:
        """Execute the agent's task."""
        print(f"   [{self.name}] Processing...")
        
        messages = [
            {"role": "system", "content": self.role},
            {"role": "user", "content": task}
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,  # Lower temp for consistent grading
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
- Break down problems into scorable steps
- Assign point values based on difficulty and importance
- Include partial credit criteria
- Be objective and measurable
- Cover conceptual understanding, methodology, and accuracy

Return rubrics as JSON:
{
  "total_points": X,
  "criteria": [
    {
      "step": "description",
      "points": X,
      "requirements": ["req1", "req2"],
      "partial_credit": {"description": points}
    }
  ]
}"""
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
            return json.loads(json_str)
        except Exception as e:
            print(f"   [WARNING] Failed to parse rubric JSON: {e}")
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
    
    def evaluate_solution(
        self,
        problem: Dict[str, Any],
        correct_solution: str,
        student_solution: str,
        rubric: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate student's solution against rubric."""
        
        task = f"""Evaluate this student's solution:

PROBLEM:
{json.dumps(problem, indent=2)}

CORRECT SOLUTION:
{correct_solution}

STUDENT SOLUTION:
{student_solution}

GRADING RUBRIC:
{json.dumps(rubric, indent=2)}

Carefully evaluate the student's work against each rubric criterion.
Return ONLY valid JSON as specified in your role."""
        
        response = self.run(task)
        
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            return json.loads(json_str)
        except Exception as e:
            print(f"   [WARNING] Failed to parse evaluation JSON: {e}")
            return {
                "score": 0,
                "max_score": rubric.get("total_points", 10),
                "percentage": 0,
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
        
    def grade_submission(
        self,
        problem: Dict[str, Any],
        correct_solution: str,
        student_solution: str,
        student_name: str = "Student",
        generate_rubric: bool = True,
        existing_rubric: Dict[str, Any] = None
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
            
        Returns:
            Complete grading result with score, evaluation, and feedback
        """
        print(f"\n{'='*70}")
        print(f"GRADING SUBMISSION: {student_name}")
        print(f"{'='*70}\n")
        
        # Step 1: Generate or use existing rubric
        if generate_rubric or existing_rubric is None:
            print("[Step 1] Generating grading rubric...")
            rubric = self.rubric_gen.generate_rubric(problem, correct_solution)
            print(f"   ✓ Rubric created ({rubric.get('total_points', 0)} points)\n")
        else:
            rubric = existing_rubric
            print(f"[Step 1] Using existing rubric ({rubric.get('total_points', 0)} points)\n")
        
        # Step 2: Evaluate student's solution
        print("[Step 2] Evaluating student solution...")
        evaluation = self.evaluator.evaluate_solution(
            problem,
            correct_solution,
            student_solution,
            rubric
        )
        score = evaluation.get('score', 0)
        max_score = evaluation.get('max_score', rubric.get('total_points', 10))
        percentage = evaluation.get('percentage', (score/max_score*100) if max_score > 0 else 0)
        print(f"   ✓ Score: {score}/{max_score} ({percentage:.1f}%)\n")
        
        # Step 3: Generate personalized feedback
        print("[Step 3] Generating feedback...")
        feedback = self.feedback_gen.generate_feedback(
            problem,
            evaluation,
            student_solution
        )
        print(f"   ✓ Feedback generated\n")
        
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
                "grade": self._calculate_letter_grade(percentage)
            }
        }
        
        print(f"{'='*70}")
        print(f"GRADING COMPLETE: {score}/{max_score} ({percentage:.1f}%) - {result['summary']['grade']}")
        print(f"{'='*70}\n")
        
        return result
    
    def grade_batch(
        self,
        problem: Dict[str, Any],
        correct_solution: str,
        student_submissions: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Grade multiple student submissions for the same problem.
        
        Args:
            problem: The problem definition
            correct_solution: The correct solution
            student_submissions: List of {name, solution} dicts
            
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
        
        results = []
        for i, submission in enumerate(student_submissions, 1):
            print(f"Processing {i}/{len(student_submissions)}...")
            result = self.grade_submission(
                problem=problem,
                correct_solution=correct_solution,
                student_solution=submission['solution'],
                student_name=submission['name'],
                generate_rubric=False,
                existing_rubric=rubric
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
