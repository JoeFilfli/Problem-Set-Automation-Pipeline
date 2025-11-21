"""
Grade Student Submissions - CLI Tool
Evaluates student work against correct solutions with detailed rubrics and feedback.
"""
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from grading_agents import GradingOrchestrator
from pdf_extractor import extract_pdf_text


def load_problem_set(json_path: str) -> Dict[str, Any]:
    """Load generated problem set from JSON."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_student_submissions_json(json_path: str) -> List[Dict[str, Any]]:
    """
    Load student submissions from JSON file.
    
    Expected format:
    {
      "submissions": [
        {
          "student_name": "John Doe",
          "student_id": "123456",
          "answers": [
            {
              "problem_id": 1,
              "solution": "student's written solution..."
            }
          ]
        }
      ]
    }
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('submissions', [])


def load_student_submission_text(text_path: str, student_name: str) -> str:
    """Load a single student's submission from text file."""
    with open(text_path, 'r', encoding='utf-8') as f:
        return f.read()


def load_student_submission_pdf(pdf_path: str, student_name: str, use_ocr: bool = True) -> str:
    """
    Load a single student's submission from PDF.
    
    Args:
        pdf_path: Path to student's PDF file
        student_name: Name of the student
        use_ocr: If True, automatically uses OCR for handwritten/scanned PDFs
        
    Returns:
        Extracted text from PDF
    """
    from pdf_extractor import extract_pdf_smart, extract_pdf_with_ocr
    
    if use_ocr:
        # Smart extraction: tries text first, falls back to OCR
        return extract_pdf_smart(pdf_path)
    else:
        # Force OCR mode
        return extract_pdf_with_ocr(pdf_path)


def save_grading_report_json(results: List[Dict[str, Any]], output_path: str):
    """Save grading results as JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved grading report (JSON): {output_path}")


def save_grading_report_text(
    results: List[Dict[str, Any]],
    stats: Dict[str, Any],
    output_path: str
):
    """Save grading results as formatted text report."""
    
    report = "="*80 + "\n"
    report += "GRADING REPORT\n"
    report += "="*80 + "\n\n"
    
    # Overall statistics
    report += "OVERALL STATISTICS\n"
    report += "-"*80 + "\n"
    report += f"Total Students: {stats['total_students']}\n"
    report += f"Average Score: {stats['average']:.1f}%\n"
    report += f"Median Score: {stats['median']:.1f}%\n"
    report += f"Score Range: {stats['min']:.1f}% - {stats['max']:.1f}%\n\n"
    
    report += "Grade Distribution:\n"
    for grade, count in sorted(stats['grade_distribution'].items()):
        report += f"  {grade}: {count} students\n"
    
    report += "\n" + "="*80 + "\n\n"
    
    # Individual results
    for i, result in enumerate(results, 1):
        student = result['student_name']
        summary = result['summary']
        evaluation = result['evaluation']
        
        report += f"STUDENT {i}: {student}\n"
        report += "-"*80 + "\n"
        report += f"Score: {summary['score']}/{summary['max_score']} ({summary['percentage']:.1f}%)\n"
        report += f"Grade: {summary['grade']}\n\n"
        
        # Rubric breakdown
        report += "Rubric Breakdown:\n"
        for criterion in evaluation.get('criteria_scores', []):
            status = "✓" if criterion.get('correct', False) else "✗"
            report += f"  {status} {criterion.get('criterion', 'N/A')}: "
            report += f"{criterion.get('earned', 0)}/{criterion.get('possible', 0)} pts\n"
            if criterion.get('notes'):
                report += f"     → {criterion['notes']}\n"
        
        report += "\n"
        
        # Strengths and errors
        if evaluation.get('strengths'):
            report += "Strengths:\n"
            for strength in evaluation['strengths']:
                report += f"  + {strength}\n"
            report += "\n"
        
        if evaluation.get('errors'):
            report += "Areas for Improvement:\n"
            for error in evaluation['errors']:
                report += f"  - {error}\n"
            report += "\n"
        
        # Feedback
        report += "Personalized Feedback:\n"
        report += result['feedback'] + "\n"
        
        report += "\n" + "="*80 + "\n\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✓ Saved grading report (Text): {output_path}")


def save_individual_feedback(results: List[Dict[str, Any]], output_dir: Path):
    """Save individual feedback files for each student."""
    output_dir.mkdir(exist_ok=True)
    
    for result in results:
        student = result['student_name']
        safe_name = "".join(c for c in student if c.isalnum() or c in (' ', '_', '-')).strip()
        
        feedback_path = output_dir / f"{safe_name}_feedback.txt"
        
        content = f"FEEDBACK FOR: {student}\n"
        content += "="*70 + "\n\n"
        
        summary = result['summary']
        content += f"Score: {summary['score']}/{summary['max_score']} ({summary['percentage']:.1f}%)\n"
        content += f"Grade: {summary['grade']}\n\n"
        content += "-"*70 + "\n\n"
        content += result['feedback'] + "\n"
        
        with open(feedback_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"✓ Saved {len(results)} individual feedback files to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Grade student submissions using AI-powered evaluation"
    )
    
    parser.add_argument(
        "--problem-set",
        type=str,
        required=True,
        help="Path to generated problem set JSON file"
    )
    parser.add_argument(
        "--problem-id",
        type=int,
        required=True,
        help="Problem number to grade (1-based index)"
    )
    parser.add_argument(
        "--submissions",
        type=str,
        help="Path to student submissions JSON file"
    )
    parser.add_argument(
        "--student-pdf",
        type=str,
        help="Path to single student PDF submission (requires --student-name)"
    )
    parser.add_argument(
        "--student-name",
        type=str,
        help="Name of student (required when using --student-pdf)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="grading_results",
        help="Directory to save grading results (default: grading_results)"
    )
    parser.add_argument(
        "--individual-feedback",
        action="store_true",
        help="Generate individual feedback files for each student"
    )
    parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Force OCR mode for all PDFs (use for handwritten submissions)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.submissions and not args.student_pdf:
        parser.error("Must specify either --submissions or --student-pdf")
    
    if args.student_pdf and not args.student_name:
        parser.error("--student-name is required when using --student-pdf")
    
    if args.submissions and args.student_pdf:
        parser.error("Cannot use both --submissions and --student-pdf")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load problem set
    print("[INIT] Loading problem set...")
    problem_set = load_problem_set(args.problem_set)
    
    # Get specific problem
    problem_idx = args.problem_id - 1
    if problem_idx < 0 or problem_idx >= len(problem_set['problem_set']):
        print(f"[ERROR] Problem {args.problem_id} not found in problem set")
        return
    
    problem_data = problem_set['problem_set'][problem_idx]
    problem = problem_data['problem']
    correct_solution = problem_data['solution']
    
    print(f"   ✓ Loaded Problem {args.problem_id}: {problem.get('topic', 'N/A')}\n")
    
    # Load student submissions
    if args.student_pdf:
        # Single PDF submission mode
        print(f"[INIT] Loading student PDF submission: {args.student_name}...")
        use_ocr_mode = not args.force_ocr  # Smart mode unless force_ocr is True
        student_solution = load_student_submission_pdf(args.student_pdf, args.student_name, use_ocr=use_ocr_mode)
        
        submissions_data = [{
            'student_name': args.student_name,
            'answers': [{
                'problem_id': args.problem_id,
                'solution': student_solution
            }]
        }]
        print(f"   ✓ Loaded PDF submission ({len(student_solution)} characters extracted)\n")
    else:
        # JSON batch mode
        print("[INIT] Loading student submissions...")
        submissions_data = load_student_submissions_json(args.submissions)
        print(f"   ✓ Loaded {len(submissions_data)} submissions\n")
    
    # Prepare submissions for this specific problem
    student_submissions = []
    for submission in submissions_data:
        student_name = submission.get('student_name', 'Unknown')
        # Find answer for this problem
        answers = submission.get('answers', [])
        problem_answer = None
        for answer in answers:
            if answer.get('problem_id') == args.problem_id:
                problem_answer = answer.get('solution', '')
                break
        
        if problem_answer:
            student_submissions.append({
                'name': student_name,
                'solution': problem_answer
            })
        else:
            print(f"   [WARNING] No answer found for {student_name} on Problem {args.problem_id}")
    
    if not student_submissions:
        print("[ERROR] No valid submissions found for this problem")
        return
    
    print(f"   ✓ Found {len(student_submissions)} answers for Problem {args.problem_id}\n")
    
    # Initialize grading system
    print("[INIT] Initializing grading agents...")
    grader = GradingOrchestrator()
    
    # Grade all submissions
    results, stats = grader.grade_batch(
        problem=problem,
        correct_solution=correct_solution,
        student_submissions=student_submissions
    )
    
    # Save results
    base_name = f"problem_{args.problem_id}_grading"
    
    # JSON report
    json_path = output_dir / f"{base_name}.json"
    save_grading_report_json({
        "problem": problem,
        "statistics": stats,
        "results": results
    }, str(json_path))
    
    # Text report
    text_path = output_dir / f"{base_name}.txt"
    save_grading_report_text(results, stats, str(text_path))
    
    # Individual feedback files
    if args.individual_feedback:
        feedback_dir = output_dir / f"{base_name}_feedback"
        save_individual_feedback(results, feedback_dir)
    
    print(f"\n{'='*70}")
    print(f"GRADING COMPLETE")
    print(f"Results saved to: {output_dir.absolute()}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
