"""
Problem Set Generator - Main Script
Uses agent orchestration + RAG to generate chapter-specific problem sets.
"""
import json
import argparse
import subprocess
import re
from pathlib import Path
from vector_store import RAGVectorStore
from agent_orchestrator import ProblemSetOrchestrator


def save_json(data: dict, output_path: str):
    """Save problem set as JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved JSON to: {output_path}")


def save_markdown(data: dict, output_path: str):
    """Save problem set as formatted Markdown."""
    
    md = f"""# Problem Set: {data['doc_id']}

Generated using AI-powered agent orchestration system.

---

## Chapter Analysis

**Topics Covered:**
"""
    
    # Add topics from analysis
    topics = data['analysis'].get('topics', [])
    for topic in topics:
        md += f"- {topic}\n"
    
    md += "\n**Key Formulas:**\n"
    formulas = data['analysis'].get('key_formulas', [])
    for formula in formulas:
        md += f"- {formula}\n"
    
    md += "\n---\n\n"
    
    # Add problems and solutions
    for i, item in enumerate(data['problem_set'], 1):
        problem = item['problem']
        solution = item['solution']
        
        md += f"## Problem {i}\n\n"
        md += f"**Difficulty:** {problem.get('difficulty', 'N/A').upper()}\n\n"
        md += f"**Topic:** {problem.get('topic', 'N/A')}\n\n"
        
        md += f"### Problem Statement\n\n"
        md += f"{problem.get('statement', '')}\n\n"
        
        if problem.get('given'):
            md += "**Given:**\n"
            for g in problem['given']:
                md += f"- {g}\n"
            md += "\n"
        
        if problem.get('required'):
            md += "**Find:**\n"
            for r in problem['required']:
                md += f"- {r}\n"
            md += "\n"
        
        md += f"### Solution\n\n"
        md += f"{solution}\n\n"
        
        # Add quality feedback if available
        if 'quality' in item:
            quality = item['quality']
            md += f"**Quality Assessment:** {quality.get('overall_quality', 'N/A')}\n\n"
            if quality.get('issues'):
                md += "**Issues:**\n"
                for issue in quality['issues']:
                    md += f"- {issue}\n"
                md += "\n"
        
        md += "---\n\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md)
    
    print(f"✓ Saved Markdown to: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Generate problem sets for course chapters using AI agents"
    )
    parser.add_argument(
        "--chapter",
        type=str,
        help="Specific chapter PDF to generate problems for (e.g., 'INDE301_Ch1_Notes_24.pdf')"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate problem sets for all chapters"
    )
    parser.add_argument(
        "--num-problems",
        type=int,
        default=5,
        help="Number of problems to generate per chapter (default: 5)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="generated_problem_sets",
        help="Directory to save generated problem sets (default: generated_problem_sets)"
    )
    parser.add_argument(
        "--no-quality-check",
        action="store_true",
        help="Skip quality checking step"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "markdown", "latex", "pdf", "all"],
        default="all",
        help="Output format: json, markdown, latex, pdf, or all (default: all)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.chapter and not args.all:
        parser.error("Must specify either --chapter or --all")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Initialize vector store and orchestrator
    print("[INIT] Loading RAG vector store...")
    vs = RAGVectorStore()
    orchestrator = ProblemSetOrchestrator(vs)
    
    # Get list of chapters to process
    if args.all:
        chapters = vs.get_all_documents()
        # Filter out syllabus
        chapters = [c for c in chapters if "syllabus" not in c.lower()]
        print(f"\n[INFO] Found {len(chapters)} chapters to process\n")
    else:
        chapters = [args.chapter]
    
    # Generate problem sets
    for chapter in chapters:
        try:
            # Generate problem set
            problem_set = orchestrator.generate_problem_set(
                doc_id=chapter,
                num_problems=args.num_problems,
                check_quality=not args.no_quality_check
            )
            
            if not problem_set:
                print(f"[WARNING] Failed to generate problem set for {chapter}\n")
                continue
            
            # Save outputs
            base_name = Path(chapter).stem
            
            if args.format in ["json", "all"]:
                json_path = output_dir / f"{base_name}_problems.json"
                save_json(problem_set, str(json_path))
            
            if args.format in ["markdown", "all"]:
                md_path = output_dir / f"{base_name}_problems.md"
                save_markdown(problem_set, str(md_path))
            
            print()
            
        except Exception as e:
            print(f"[ERROR] Failed to process {chapter}: {e}\n")
            continue
    
    print(f"\n{'='*70}")
    print(f"ALL PROBLEM SETS GENERATED")
    print(f"Output directory: {output_dir.absolute()}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
