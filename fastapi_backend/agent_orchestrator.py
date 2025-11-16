"""
Agent-based orchestration system for problem set generation.
Uses multiple specialized agents coordinated by an orchestrator.
"""
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
import json
from vector_store import RAGVectorStore

load_dotenv()


class Agent:
    """Base class for specialized agents."""
    
    def __init__(self, name: str, role: str, model: str = "gpt-4o-mini"):
        self.name = name
        self.role = role
        self.model = model
        self.client = OpenAI()
        
    def run(self, task: str, context: Dict[str, Any] = None) -> str:
        """
        Execute the agent's task.
        
        Args:
            task: The specific task/prompt for this agent
            context: Additional context data
            
        Returns:
            Agent's response as string
        """
        print(f"   [{self.name}] Processing...")
        
        messages = [
            {"role": "system", "content": self.role},
            {"role": "user", "content": task}
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
        )
        
        result = response.choices[0].message.content
        print(f"   [{self.name}] ✓ Complete")
        return result


class ChapterAnalyzerAgent(Agent):
    """Analyzes chapter content to extract key topics, concepts, and formulas."""
    
    def __init__(self):
        super().__init__(
            name="Chapter Analyzer",
            role="""You are an expert at analyzing academic course materials across all subjects.
Your task is to identify:
- Key topics and learning objectives
- Important formulas, equations, definitions, or key concepts
- Core ideas that should be tested
- Difficulty levels of different topics

Return your analysis as structured JSON with:
{
  "topics": ["topic1", "topic2", ...],
  "key_formulas": ["formula1", "formula2", ...],
  "concepts": ["concept1", "concept2", ...],
  "difficulty_areas": {"easy": [...], "medium": [...], "hard": [...]}
}"""
        )
    
    def analyze_chapter(self, chapter_content: str) -> Dict[str, Any]:
        """Analyze chapter and return structured topics/concepts."""
        task = f"""Analyze this chapter content and extract key information:

{chapter_content}

Return ONLY valid JSON with the structure specified in your role."""
        
        response = self.run(task)
        
        # Extract JSON from response
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            return json.loads(json_str)
        except:
            print(f"   [WARNING] Failed to parse JSON, returning raw response")
            return {"raw": response}


class ProblemGeneratorAgent(Agent):
    """Generates problems based on chapter topics and difficulty."""
    
    def __init__(self):
        super().__init__(
            name="Problem Generator",
            role="""You are an expert at creating academic problems across all subjects.
Generate problems that:
- Test understanding of key concepts
- Include realistic scenarios and relevant context
- Vary in difficulty (easy, medium, hard)
- Use proper notation (mathematical, chemical, programming, etc. as appropriate)
- Are clear and unambiguous

Format each problem with:
- Problem statement
- Given information
- Required answers
- Difficulty level"""
        )
    
    def generate_problems(
        self,
        chapter_content: str,
        analysis: Dict[str, Any],
        num_problems: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate problems based on chapter analysis."""
        
        task = f"""Based on this chapter content and analysis, generate {num_problems} problems.

CHAPTER ANALYSIS:
{json.dumps(analysis, indent=2)}

CHAPTER CONTENT:
{chapter_content}

Generate {num_problems} problems covering different topics and difficulty levels.

Return ONLY valid JSON in this format:
{{
  "problems": [
    {{
      "id": 1,
      "difficulty": "easy|medium|hard",
      "topic": "topic name",
      "statement": "problem statement",
      "given": ["given info 1", "given info 2"],
      "required": ["what to find 1", "what to find 2"]
    }}
  ]
}}"""
        
        response = self.run(task)
        
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            data = json.loads(json_str)
            return data.get("problems", [])
        except Exception as e:
            print(f"   [ERROR] Failed to parse problems: {e}")
            return []


class SolutionGeneratorAgent(Agent):
    """Generates detailed solutions for problems."""
    
    def __init__(self):
        super().__init__(
            name="Solution Generator",
            role="""You are an expert at solving and explaining academic problems across all subjects.
Provide solutions that:
- Show all steps clearly
- Explain the reasoning
- Use proper notation (LaTeX for math: $...$, $$...$$, code blocks for programming, etc.)
- Include intermediate steps and calculations
- Highlight final answers
- Reference relevant formulas, theorems, or concepts"""
        )
    
    def generate_solution(
        self,
        problem: Dict[str, Any],
        chapter_content: str
    ) -> str:
        """Generate detailed solution for a problem."""
        
        task = f"""Solve this problem with a detailed, step-by-step solution:

PROBLEM:
{json.dumps(problem, indent=2)}

CHAPTER CONTENT (for reference):
{chapter_content}

Provide a complete solution with:
1. Approach/Strategy
2. Step-by-step calculations
3. Final answer(s)

Use LaTeX notation for math: $inline$ and $$display$$"""
        
        return self.run(task)


class QualityCheckerAgent(Agent):
    """Validates problems and solutions for quality and correctness."""
    
    def __init__(self):
        super().__init__(
            name="Quality Checker",
            role="""You are an expert reviewer of academic problems and solutions across all subjects.
Check for:
- Technical correctness (mathematical, logical, conceptual, etc.)
- Clear problem statements
- Complete solutions
- Appropriate difficulty
- Proper notation and formatting
- Realistic and relevant scenarios

Return JSON with:
{
  "overall_quality": "excellent|good|needs_improvement",
  "issues": ["issue1", "issue2", ...],
  "suggestions": ["suggestion1", "suggestion2", ...]
}"""
        )
    
    def check_quality(
        self,
        problem: Dict[str, Any],
        solution: str
    ) -> Dict[str, Any]:
        """Check quality of problem and solution."""
        
        task = f"""Review this problem and solution:

PROBLEM:
{json.dumps(problem, indent=2)}

SOLUTION:
{solution}

Assess quality and return JSON as specified in your role."""
        
        response = self.run(task)
        
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            return json.loads(json_str)
        except:
            return {"overall_quality": "unknown", "issues": [], "suggestions": []}


class ProblemSetOrchestrator:
    """Orchestrates multiple agents to generate complete problem sets."""
    
    def __init__(self, vector_store: RAGVectorStore):
        self.vs = vector_store
        self.analyzer = ChapterAnalyzerAgent()
        self.problem_gen = ProblemGeneratorAgent()
        self.solution_gen = SolutionGeneratorAgent()
        self.quality_checker = QualityCheckerAgent()
        
    def generate_problem_set(
        self,
        doc_id: str,
        num_problems: int = 5,
        check_quality: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a complete problem set for a specific chapter.
        
        Args:
            doc_id: Document/chapter identifier
            num_problems: Number of problems to generate
            check_quality: Whether to run quality checks
            
        Returns:
            Complete problem set with problems and solutions
        """
        print(f"\n{'='*70}")
        print(f"GENERATING PROBLEM SET FOR: {doc_id}")
        print(f"{'='*70}\n")
        
        # Step 1: Retrieve chapter content from vector store
        print("[Step 1] Retrieving chapter content from RAG...")
        results = self.vs.query_by_document(
            query="key concepts formulas examples",
            doc_id=doc_id,
            top_k=20  # Get more chunks for comprehensive coverage
        )
        
        if not results["documents"][0]:
            print(f"   [ERROR] No content found for {doc_id}")
            return None
        
        chapter_content = "\n\n".join(results["documents"][0])
        print(f"   ✓ Retrieved {len(results['documents'][0])} chunks ({len(chapter_content)} chars)\n")
        
        # Step 2: Analyze chapter
        print("[Step 2] Analyzing chapter content...")
        analysis = self.analyzer.analyze_chapter(chapter_content)
        print(f"   ✓ Identified {len(analysis.get('topics', []))} topics\n")
        
        # Step 3: Generate problems
        print(f"[Step 3] Generating {num_problems} problems...")
        problems = self.problem_gen.generate_problems(
            chapter_content,
            analysis,
            num_problems
        )
        print(f"   ✓ Generated {len(problems)} problems\n")
        
        # Step 4: Generate solutions
        print("[Step 4] Generating solutions...")
        problem_set = []
        for i, problem in enumerate(problems, 1):
            print(f"   Working on problem {i}/{len(problems)}...")
            solution = self.solution_gen.generate_solution(problem, chapter_content)
            
            item = {
                "problem": problem,
                "solution": solution
            }
            
            # Optional quality check
            if check_quality:
                quality = self.quality_checker.check_quality(problem, solution)
                item["quality"] = quality
            
            problem_set.append(item)
        
        print(f"   ✓ All solutions generated\n")
        
        result = {
            "doc_id": doc_id,
            "analysis": analysis,
            "num_problems": len(problem_set),
            "problem_set": problem_set
        }
        
        print(f"{'='*70}")
        print(f"PROBLEM SET GENERATION COMPLETE")
        print(f"{'='*70}\n")
        
        return result
