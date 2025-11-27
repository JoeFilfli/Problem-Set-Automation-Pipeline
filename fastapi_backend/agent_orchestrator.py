"""
Agent-based orchestration system for problem set generation.
Uses multiple specialized agents coordinated by an orchestrator.
"""
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
import json
import re
from vector_store import RAGVectorStore

load_dotenv(override=True)


def fix_latex_formatting(text: str) -> str:
    """
    Fix common LaTeX formatting issues that occur when backslashes are lost
    during JSON serialization/deserialization or LLM generation.
    
    This function fixes malformed LaTeX without influencing the LLM's problem
    generation - it only corrects formatting issues post-generation.
    
    Args:
        text: Text that may contain malformed LaTeX
        
    Returns:
        Text with corrected LaTeX formatting
    """
    if not text:
        return text
    
    # Fix spacing issues around LaTeX delimiters and concatenated text
    # First, protect LaTeX content by temporarily replacing it
    latex_placeholders = []
    placeholder_counter = 0
    
    def replace_latex(match):
        nonlocal placeholder_counter
        placeholder = f"__LATEX_PLACEHOLDER_{placeholder_counter}__"
        latex_placeholders.append((placeholder, match.group(0)))
        placeholder_counter += 1
        return placeholder
    
    # Protect LaTeX blocks (both $...$ and $$...$$)
    text = re.sub(r'\$\$[^$]+\$\$', replace_latex, text)
    text = re.sub(r'\$[^$]+\$', replace_latex, text)
    
    # Fix spacing around $ delimiters (for cases where $ is at boundary)
    text = re.sub(r'([a-zA-Z0-9%])\$', r'\1 $', text)
    text = re.sub(r'\$([a-zA-Z0-9])', r'$ \1', text)
    
    # Fix common concatenated patterns:
    # - Number followed by word (e.g., "200at" -> "200 at")
    text = re.sub(r'(\d+)([a-zA-Z])', r'\1 \2', text)
    # - Common phrases that get concatenated
    # Fix "at" + "a" pattern (e.g., "200at" -> "200 at", but we want "200 at a")
    text = re.sub(r'\bat([a-z])', r'at \1', text, flags=re.IGNORECASE)
    # Fix "of" + number pattern (e.g., "rateof5" -> "rate of 5")
    text = re.sub(r'\bof(\d)', r'of \1', text, flags=re.IGNORECASE)
    # Fix "rate" + "of" pattern (e.g., "interestrateof" -> "interest rate of")
    text = re.sub(r'\brate([a-z])', r'rate \1', text, flags=re.IGNORECASE)
    # Fix "interest" + "rate" pattern (e.g., "nominalinterestrate" -> "nominal interest rate")
    text = re.sub(r'\binterest([a-z])', r'interest \1', text, flags=re.IGNORECASE)
    # Fix "nominal" + "interest" pattern
    text = re.sub(r'\bnominal([a-z])', r'nominal \1', text, flags=re.IGNORECASE)
    # Fix lowercase word followed by uppercase (likely missing space, but not for single letters)
    text = re.sub(r'([a-z]{2,})([A-Z][a-z])', r'\1 \2', text)
    
    # Fix double spaces
    text = re.sub(r' +', ' ', text)
    
    # Restore LaTeX content
    for placeholder, original in latex_placeholders:
        text = text.replace(placeholder, original)
    
    # Fix rac{{...}}{{...}} -> \frac{...}{...}
    # This pattern handles the case where backslashes are lost and we get "rac" instead of "\frac"
    # Pattern: rac{{...}}{{...}} where content can include nested braces, parentheses, operators, etc.
    
    # Use iterative approach to handle nested braces correctly
    max_iterations = 10
    iteration = 0
    while 'rac{{' in text and iteration < max_iterations:
        # Find the first occurrence
        start_idx = text.find('rac{{')
        if start_idx == -1:
            break
        
        # Find the matching braces manually
        # After "rac{{", we're inside the numerator braces, so depth starts at 2
        pos = start_idx + 4  # After "rac{{"
        depth = 2  # We've already seen {{
        num_end = -1
        for i in range(pos, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    num_end = i
                    break
        
        if num_end == -1:
            break  # Malformed, stop
        
        numerator = text[pos:num_end]
        
        # Find denominator start
        denom_start = num_end + 1
        while denom_start < len(text) and text[denom_start] in ' \t\n':
            denom_start += 1
        
        if denom_start >= len(text) or text[denom_start:denom_start+2] != '{{':
            break  # Malformed
        
        # Find denominator end
        # After "{{", we're inside the denominator braces, so depth starts at 2
        denom_pos = denom_start + 2
        depth = 2  # We've already seen {{
        denom_end = -1
        for i in range(denom_pos, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    denom_end = i
                    break
        
        if denom_end == -1:
            break  # Malformed
        
        denominator = text[denom_pos:denom_end]
        
        # Replace the pattern
        replacement = f'\\frac{{{numerator}}}{{{denominator}}}'
        text = text[:start_idx] + replacement + text[denom_end + 1:]
        iteration += 1
    
    # Fix other common LaTeX commands that might have lost backslashes
    # Fix int -> \int (but only if it's part of an integral pattern)
    text = re.sub(r'(?<!\\)\bint\s+', r'\\int ', text)
    
    # Fix sum -> \sum (but only if it's part of a summation pattern)
    text = re.sub(r'(?<!\\)\bsum\s*_', r'\\sum_', text)
    
    # Fix sqrt -> \sqrt
    text = re.sub(r'(?<!\\)\bsqrt\s*\{', r'\\sqrt{', text)
    
    # Fix pi -> \pi (but be careful not to replace words containing "pi")
    text = re.sub(r'(?<!\\)\bpi\b(?!\w)', r'\\pi', text)
    
    # Fix alpha, beta, theta, etc. (common Greek letters)
    greek_letters = ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'theta', 
                     'lambda', 'mu', 'sigma', 'phi', 'omega']
    for letter in greek_letters:
        text = re.sub(rf'(?<!\\)\b{letter}\b(?!\w)', rf'\\{letter}', text)
    
    return text


def fix_mcq_latex(mcq: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fix LaTeX formatting in a single MCQ dictionary.
    
    Args:
        mcq: MCQ dictionary with potentially malformed LaTeX
        
    Returns:
        MCQ dictionary with corrected LaTeX
    """
    fixed_mcq = mcq.copy()
    
    # Fix question
    if 'question' in fixed_mcq:
        fixed_mcq['question'] = fix_latex_formatting(fixed_mcq['question'])
    
    # Fix options
    if 'options' in fixed_mcq and isinstance(fixed_mcq['options'], dict):
        fixed_options = {}
        for key, value in fixed_mcq['options'].items():
            fixed_options[key] = fix_latex_formatting(str(value))
        fixed_mcq['options'] = fixed_options
    
    # Fix explanation
    if 'explanation' in fixed_mcq:
        fixed_mcq['explanation'] = fix_latex_formatting(fixed_mcq['explanation'])
    
    return fixed_mcq


class Agent:
    """Base class for specialized agents."""
    
    def __init__(self, name: str, role: str, model: str = "gpt-4o"):
        self.name = name
        self.role = role
        self.model = model
        self.client = OpenAI()
        
    def run(self, task: str, context: Dict[str, Any] = None, force_json: bool = False, max_tokens: int = 4000) -> str:
        """
        Execute the agent's task.
        
        Args:
            task: The specific task/prompt for this agent
            context: Additional context data
            force_json: Whether to force JSON response format
            max_tokens: Maximum tokens for response
            
        Returns:
            Agent's response as string
        """
        print(f"   [{self.name}] Processing...")
        
        messages = [
            {"role": "system", "content": self.role},
            {"role": "user", "content": task}
        ]
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,  # ✅ Limit response size
            "temperature": 0.7,        # ✅ Slightly faster
            "timeout": 45              # ✅ Fail fast if stuck (45 sec for problem gen)
        }
        
        # Force JSON output when requested
        if force_json:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**kwargs)
        
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
        
        # ⚡ PERFORMANCE FIX: Truncate huge chapter content
        max_content_length = 6000  # chars
        truncated_content = chapter_content[:max_content_length]
        if len(chapter_content) > max_content_length:
            truncated_content += "\n\n[Content truncated for performance...]"
        
        task = f"""Analyze this chapter content and extract key information:

{truncated_content}

Return ONLY valid JSON with the structure specified in your role."""
        
        response = self.run(task, force_json=True, max_tokens=2000)
        
        # Extract JSON from response
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            return json.loads(json_str)
        except Exception as e:
            print(f"   [WARNING] Failed to parse JSON: {e}")
            return {
                "topics": ["General Content"],
                "key_formulas": [],
                "concepts": ["Course Material"],
                "difficulty_areas": {"easy": [], "medium": [], "hard": []}
            }


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
        
        # ⚡ PERFORMANCE FIX: Truncate huge chapter content to prevent slowness
        max_content_length = 8000  # chars
        truncated_content = chapter_content[:max_content_length]
        if len(chapter_content) > max_content_length:
            truncated_content += "\n\n[Content truncated for performance...]"
        
        task = f"""Based on this chapter content and analysis, generate {num_problems} problems.

CHAPTER ANALYSIS:
{json.dumps(analysis, indent=2)}

CHAPTER CONTENT (key excerpts):
{truncated_content}

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
        
        response = self.run(task, force_json=True, max_tokens=3000)
        
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
    
    SOLUTION_TEMPLATE = r"""### 1. Approach & Strategy
- Briefly explain the plan (2-3 bullet points).

### 2. Step-by-step Calculations
#### Step 1: <Descriptive title>
- Explanation sentence(s).
- Bullet list of given/derived values (use **bold** labels).
$$
<math for this step>
$$

#### Step 2: <Next title>
- Continue numbering steps sequentially.
- Include intermediate results in **bold**.
$$
<math or code block>
$$

### 3. Final Answer
- **Answer:** <concise final value(s) with units or justification>.
- **Check:** Optional verification or note if assumptions were made.

> Tips:
> - Keep Markdown tidy (no extra blank lines).
> - Use inline math $like\ this$ for short expressions and display math $$like\ this$$ for longer derivations.
> - Present any tables or comparisons using Markdown tables when helpful."""
    
    def __init__(self):
        super().__init__(
            name="Solution Generator",
            role="""You are an expert at solving and explaining academic problems across all subjects.
Produce polished, classroom-ready solution walkthroughs that:
- Follow the provided Markdown template (Approach, Step-by-step, Final Answer).
- Use numbered step headings (#### Step 1, Step 2, ...).
- Present givens/derived values as short bullet lists with **bold** labels.
- Use LaTeX math for every formula ($...$ for inline, $$...$$ for display).
- Highlight final numerical answers in **bold** and include units or justification.
- Reference formulas or theorems where relevant while keeping the layout clean."""
        )
    
    def generate_solution(
        self,
        problem: Dict[str, Any],
        chapter_content: str
    ) -> str:
        """Generate detailed solution for a problem."""
        
        # ⚡ PERFORMANCE FIX: Truncate chapter content (solutions don't need full chapter)
        max_content_length = 5000  # chars
        truncated_content = chapter_content[:max_content_length]
        if len(chapter_content) > max_content_length:
            truncated_content += "\n\n[Additional content available but not shown for performance...]"
        
        task = f"""Solve this problem with a detailed, step-by-step solution that strictly follows the Markdown template shown below.

PROBLEM:
{json.dumps(problem, indent=2)}

CHAPTER CONTENT (for reference):
{truncated_content}

TEMPLATE TO FOLLOW (replace the angle-bracket placeholders with actual content and keep the section headings exactly as shown):

{self.SOLUTION_TEMPLATE}

Formatting requirements:
- Do not introduce extra top-level sections beyond those in the template.
- Keep exactly one blank line between paragraphs/sections.
- Use inline math for short expressions and display math blocks for derivations.
- When a step involves computations, include the symbolic equation first, then the substituted numbers, then the evaluated result.
- Ensure the Final Answer section summarizes the result in a single bullet plus an optional check."""
        
        return self.run(task, max_tokens=3000)


class MCQGeneratorAgent(Agent):
    """Generates multiple choice questions (MCQ) based on chapter content."""
    
    def __init__(self):
        super().__init__(
            name="MCQ Generator",
            role="""You are an expert at creating multiple choice questions (MCQ) for academic assessments across all subjects.
Generate MCQs that:
- Test understanding of key concepts
- Have one clearly correct answer
- Include 4 plausible options (A, B, C, D)
- Use proper notation (mathematical, chemical, programming, etc. as appropriate)
- Are clear and unambiguous
- Vary in difficulty (easy, medium, hard)

CRITICAL: For all mathematical equations, formulas, and mathematical expressions:
- ALWAYS use LaTeX format for equations
- Use inline math delimiters $...$ for equations within text (e.g., $E = mc^2$)
- Use display math delimiters $$...$$ for standalone equations or complex formulas
- Examples:
  * Simple: $x = 5$ or $f(x) = x^2 + 3x - 2$
  * Complex: $$\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$
  * Formulas: $CR = P(A/P, i, n) + S(A/F, i, n)$
  * Variables: $P$, $i$, $n$, $A$, $F$, etc. should be in math mode when used in equations
- Never write equations in plain text - always use LaTeX delimiters

Format each MCQ with:
- Question statement (with LaTeX equations if needed)
- Four options (A, B, C, D) - each option can contain LaTeX equations
- Correct answer (A, B, C, or D)
- Brief explanation for the correct answer (with LaTeX equations if needed)
- Difficulty level"""
        )
    
    def generate_mcqs(
        self,
        chapter_content: str,
        analysis: Dict[str, Any],
        num_mcqs: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate multiple choice questions based on chapter analysis."""
        
        # ⚡ PERFORMANCE FIX: Truncate huge chapter content
        max_content_length = 7000  # chars
        truncated_content = chapter_content[:max_content_length]
        if len(chapter_content) > max_content_length:
            truncated_content += "\n\n[Content truncated for performance...]"
        
        # Build the task string with proper escaping for LaTeX examples
        latex_examples = """- Examples of proper LaTeX formatting:
  * Simple equation: $x = 5$ or $y = mx + b$
  * Formula with subscripts: $A_n = P(1 + i)^n$
  * Complex formula: $$CR = P(A/P, i, n) + S(A/F, i, n)$$
  * Greek letters: $\\alpha$, $\\beta$, $\\pi$, $\\theta$
  * Fractions: $\\frac{{a}}{{b}}$ or $\\frac{{P(A/P, i, n)}}{{S}}$
  * Integrals: $\\int f(x) dx$
  * Summations: $\\sum_{{i=1}}^{{n}} x_i$"""
        
        task = f"""Based on this chapter content and analysis, generate {num_mcqs} multiple choice questions.

CHAPTER ANALYSIS:
{json.dumps(analysis, indent=2)}

CHAPTER CONTENT (key excerpts):
{truncated_content}

Generate {num_mcqs} MCQs covering different topics and difficulty levels.

IMPORTANT FORMATTING REQUIREMENTS:
- ALL mathematical equations, formulas, and expressions MUST be written in LaTeX format
- Use $...$ for inline math (e.g., "The formula $E = mc^2$ shows...")
- Use $$...$$ for display math or complex formulas (e.g., "$$\\int_0^\\infty e^{{-x^2}} dx$$")
- Mathematical variables, symbols, and operators should be in LaTeX math mode
{latex_examples}
- When equations appear in question text or options, wrap them in LaTeX delimiters
- Do NOT write equations in plain text format

Return ONLY valid JSON in this format:
{{
  "mcqs": [
    {{
      "id": 1,
      "difficulty": "easy|medium|hard",
      "topic": "topic name",
      "question": "question statement (use LaTeX $...$ or $$...$$ for equations)",
      "options": {{
        "A": "option A text (use LaTeX for equations)",
        "B": "option B text (use LaTeX for equations)",
        "C": "option C text (use LaTeX for equations)",
        "D": "option D text (use LaTeX for equations)"
      }},
      "correct_answer": "A|B|C|D",
      "explanation": "brief explanation (use LaTeX for equations if needed)"
    }}
  ]
}}"""
        
        response = self.run(task, force_json=True, max_tokens=3500)
        
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            data = json.loads(json_str)
            mcqs = data.get("mcqs", [])
            
            # Fix LaTeX formatting issues post-generation
            # This doesn't influence the LLM's problem generation,
            # it only corrects formatting issues that occur during JSON serialization
            fixed_mcqs = [fix_mcq_latex(mcq) for mcq in mcqs]
            
            return fixed_mcqs
        except Exception as e:
            print(f"   [ERROR] Failed to parse MCQs: {e}")
            return []


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

Assess quality and return your assessment as valid JSON with keys: overall_quality, issues, suggestions."""
        
        response = self.run(task, force_json=True)
        
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
        self.mcq_gen = MCQGeneratorAgent()
        self.quality_checker = QualityCheckerAgent()
    
    def generate_mcq_set(
        self,
        doc_id: str,
        num_mcqs: int = 5
    ) -> Dict[str, Any]:
        """
        Generate a set of multiple choice questions for a specific chapter.
        
        Args:
            doc_id: Document/chapter identifier
            num_mcqs: Number of MCQs to generate
            
        Returns:
            Complete MCQ set with questions and answers
        """
        print(f"\n{'='*70}")
        print(f"GENERATING MCQ SET FOR: {doc_id}")
        print(f"{'='*70}\n")
        
        # Step 1: Retrieve chapter content from vector store
        print("[Step 1] Retrieving chapter content from RAG...")
        results = self.vs.query_by_document(
            query="key concepts formulas examples",
            doc_id=doc_id,
            top_k=20
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
        
        # Step 3: Generate MCQs
        print(f"[Step 3] Generating {num_mcqs} MCQs...")
        mcqs = self.mcq_gen.generate_mcqs(
            chapter_content,
            analysis,
            num_mcqs
        )
        print(f"   ✓ Generated {len(mcqs)} MCQs\n")
        
        result = {
            "doc_id": doc_id,
            "analysis": analysis,
            "num_mcqs": len(mcqs),
            "mcqs": mcqs
        }
        
        print(f"{'='*70}")
        print(f"MCQ SET GENERATION COMPLETE")
        print(f"{'='*70}\n")
        
        return result
        
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
