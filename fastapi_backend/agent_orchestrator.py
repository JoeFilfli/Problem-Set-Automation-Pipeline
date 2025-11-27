"""
Agent-based orchestration system for problem set generation.
Uses multiple specialized agents coordinated by an orchestrator.
"""
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
import json
import re
import random
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
        num_mcqs: int = 5,
        specialized_prompt: str = None,
        question_type: str = "mixed"
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple choice questions based on chapter analysis.
        
        Args:
            chapter_content: The chapter content text
            analysis: Chapter analysis dictionary
            num_mcqs: Number of MCQs to generate
            specialized_prompt: Optional specialized prompt for this question type
            question_type: Type of questions ("analytical", "direct", or "mixed")
        """
        
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
        
        # Use specialized prompt if provided, otherwise use default
        if specialized_prompt:
            prompt_instruction = f"""
SPECIALIZED PROMPT FOR THIS QUESTION TYPE:
{specialized_prompt}

Follow the guidelines and requirements specified in the specialized prompt above when generating questions.
"""
        else:
            prompt_instruction = ""
        
        task = f"""Based on this chapter content and analysis, generate {num_mcqs} multiple choice questions.

{prompt_instruction}
CHAPTER ANALYSIS:
{json.dumps(analysis, indent=2)}

CHAPTER CONTENT (key excerpts):
{truncated_content}

Generate {num_mcqs} MCQs covering different topics and difficulty levels.
{"Focus on " + question_type + " questions." if question_type in ["analytical", "direct"] else ""}

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


class PromptBuilderAgent:
    """Builds specialized prompts for MCQ generation based on content analysis."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.name = "Prompt Builder"
        self.model = model
        self.client = OpenAI()

    def build_prompts(
        self,
        chunks: List[str],
        doc_id: str = None,
        chunk_summaries: List[str] = None,
        chunk_topics: List[List[str]] = None,
        max_chunks: int = 10,
        max_chars: int = 15000
    ) -> Dict[str, str]:
        """
        Build two specialized prompts (analytical + direct) from chunks.

        Args:
            chunks: List of chunk text strings from the document
            doc_id: Optional document identifier for context
            chunk_summaries: Optional summaries (preferred over full chunks - more efficient)
            chunk_topics: Optional topics per chunk
            max_chunks: Maximum chunks to analyze
            max_chars: Maximum characters to send to LLM

        Returns:
            {
                "analytical_prompt": "detailed prompt for analytical questions",
                "direct_prompt": "detailed prompt for direct questions",
                "domain": "detected domain",
                "content_type": "formulas|concepts|examples|mixed"
            }
        """
        print(f"   [Prompt Builder] Processing {len(chunks)} chunks...")

        # Prepare content for analysis (use summaries if available)
        if chunk_summaries and len(chunk_summaries) > 0:
            print(f"      Using chunk summaries (more efficient)...")
            content = self._prepare_content_from_summaries(
                chunk_summaries,
                chunk_topics,
                max_chunks,
                max_chars
            )
        else:
            print(f"      Using representative chunk sample...")
            content = self._prepare_content_from_chunks(
                chunks,
                max_chunks,
                max_chars
            )

        # Build detailed prompts
        prompts = self._analyze_and_build_prompts(content, doc_id)

        print(f"   [Prompt Builder] ✓ Built analytical and direct prompts")
        return prompts

    def _prepare_content_from_summaries(
        self,
        summaries: List[str],
        topics: List[List[str]] = None,
        max_chunks: int = 10,
        max_chars: int = 15000
    ) -> str:
        """Prepare content using summaries (preferred method - more efficient)."""
        # Select diverse chunks based on topics
        if topics and len(topics) == len(summaries):
            selected_indices = self._select_diverse_by_topics(topics, max_chunks)
            selected_summaries = [summaries[i] for i in selected_indices]
        else:
            # Simple sampling
            selected_summaries = random.sample(
                summaries,
                min(max_chunks, len(summaries))
            )

        # Combine summaries
        content = "\n\n".join(selected_summaries)

        # Add topic information if available
        if topics:
            all_topics = set()
            for topic_list in topics:
                if isinstance(topic_list, str):
                    # If topics is a string (comma-separated), split it
                    all_topics.update([t.strip() for t in topic_list.split(",")])
                elif isinstance(topic_list, list):
                    all_topics.update(topic_list)

            if all_topics:
                content += f"\n\nKey Topics Identified: {', '.join(list(all_topics)[:20])}"

        # Truncate if too long
        if len(content) > max_chars:
            content = content[:max_chars] + "..."

        return content

    def _prepare_content_from_chunks(
        self,
        chunks: List[str],
        max_chunks: int = 10,
        max_chars: int = 15000
    ) -> str:
        """Prepare content from full chunks (fallback method)."""
        # Sample chunks
        if len(chunks) > max_chunks:
            selected = random.sample(chunks, max_chunks)
        else:
            selected = chunks

        # Truncate each chunk to save tokens
        truncated = []
        chars_used = 0
        for chunk in selected:
            if chars_used >= max_chars:
                break

            # Take first part of chunk (usually has key info)
            remaining = max_chars - chars_used
            chunk_limit = min(500, remaining // max(1, (len(selected) - len(truncated))))

            if len(chunk) > chunk_limit:
                truncated.append(chunk[:chunk_limit] + "...")
            else:
                truncated.append(chunk)

            chars_used += len(truncated[-1])

        return "\n\n".join(truncated)

    def _select_diverse_by_topics(
        self,
        topics: List[List[str]],
        sample_size: int
    ) -> List[int]:
        """Select diverse chunks by sampling from different topics."""
        # Group chunks by their primary topic
        chunks_by_topic = {}
        for i, topic_list in enumerate(topics):
            if topic_list:
                # Handle both list and string formats
                if isinstance(topic_list, str):
                    primary_topic = topic_list.split(",")[0].strip()
                elif isinstance(topic_list, list) and len(topic_list) > 0:
                    primary_topic = topic_list[0]
                else:
                    primary_topic = "Other"

                if primary_topic not in chunks_by_topic:
                    chunks_by_topic[primary_topic] = []
                chunks_by_topic[primary_topic].append(i)
            else:
                if "Other" not in chunks_by_topic:
                    chunks_by_topic["Other"] = []
                chunks_by_topic["Other"].append(i)

        # Sample from each topic group
        selected_indices = []
        per_topic = max(1, sample_size // max(1, len(chunks_by_topic)))

        for topic_chunks in chunks_by_topic.values():
            selected_indices.extend(
                random.sample(topic_chunks, min(per_topic, len(topic_chunks)))
            )

        # Fill remaining slots randomly
        all_indices = list(range(len(topics)))
        remaining = sample_size - len(selected_indices)
        if remaining > 0:
            available = [i for i in all_indices if i not in selected_indices]
            if available:
                selected_indices.extend(
                    random.sample(available, min(remaining, len(available)))
                )

        return selected_indices[:sample_size]

    def _analyze_and_build_prompts(
        self,
        content: str,
        doc_id: str = None
    ) -> Dict[str, str]:
        """Analyze content and build two detailed, specialized prompts."""

        task = f"""You are an expert at analyzing educational content and building highly detailed, specialized prompts for multiple choice question generation.
CONTENT TO ANALYZE:

{content}

DOCUMENT: {doc_id or 'Unknown'}

Your task is to:

1. Identify the SPECIFIC domain/subject with full name (e.g., "engineering economics", "financial accounting", "art history", "organic chemistry", NOT just "engineering", "finance", "art", "chemistry")
   - Be as specific as possible: "engineering economics" not "engineering", "financial accounting" not "finance"
   - Include sub-disciplines when applicable: "mechanical engineering" not "engineering", "microeconomics" not "economics"

2. Identify content characteristics (formulas, concepts, examples, procedures, etc.)

3. Determine the complexity level and appropriate question styles

4. Build TWO highly detailed, specialized prompts for MCQ generation

ANALYTICAL PROMPT REQUIREMENTS:

- Focus on generating "why/how/analyze/evaluate/compare" questions
- Test deeper understanding, reasoning, and analytical thinking
- Require students to apply concepts, not just recall facts
- Include questions that test cause-and-effect relationships
- Test ability to synthesize information
- Examples: "Why does X happen?" "How would you analyze Y?" "What would happen if Z?"
- Should be domain-specific with appropriate terminology
- Should reference specific concepts, formulas, or principles from the content

DIRECT PROMPT REQUIREMENTS:

- Focus on generating "what/which/who/when/where" questions
- Test factual knowledge, definitions, and recall
- Require students to recognize correct information
- Include questions about key terms, formulas, and concepts
- Test basic understanding without requiring deep analysis
- Examples: "What is X?" "Which of the following is Y?" "Who developed Z?"
- Should be domain-specific with appropriate terminology
- Should reference specific facts, definitions, or formulas from the content

Both prompts should:

- Be highly detailed and specific to the detected domain
- Include domain-specific guidelines and examples
- Reference the actual content topics and concepts
- Specify appropriate difficulty levels
- Include formatting requirements (especially for mathematical content)
- Be clear about what makes a good question in this domain

Return ONLY valid JSON in this format:

{{
  "domain": "specific full domain name (e.g., engineering economics, financial accounting, art history - be specific!)",
  "content_type": "formulas|concepts|examples|procedures|mixed",
  "complexity": "simple|moderate|complex",
  "analytical_prompt": "highly detailed prompt for analytical questions (500+ words, very specific)",
  "direct_prompt": "highly detailed prompt for direct questions (500+ words, very specific)",
  "key_characteristics": ["characteristic1", "characteristic2", "characteristic3"],
  "recommended_focus_areas": ["area1", "area2", "area3"]
}}"""

        print(f"   [Prompt Builder] Analyzing content and building prompts...")

        # Store the input prompt for later display
        input_prompt = task

        messages = [
            {
                "role": "system",
                "content": "You are an expert educational content analyst and prompt engineer. You create highly detailed, domain-specific prompts for academic question generation. Always identify the FULL, SPECIFIC domain name (e.g., 'engineering economics' not just 'engineering')."
            },
            {
                "role": "user",
                "content": task
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3
        )

        result = response.choices[0].message.content

        try:
            data = json.loads(result)

            return {
                "analytical_prompt": data.get("analytical_prompt", ""),
                "direct_prompt": data.get("direct_prompt", ""),
                "domain": data.get("domain", "general"),
                "content_type": data.get("content_type", "mixed"),
                "complexity": data.get("complexity", "moderate"),
                "key_characteristics": data.get("key_characteristics", []),
                "recommended_focus_areas": data.get("recommended_focus_areas", []),
                "input_prompt": input_prompt  # Store the full input prompt
            }
        except Exception as e:
            print(f"   [WARNING] Failed to parse prompt builder response: {e}")
            # Return default prompts
            return self._get_default_prompts()

    def _get_default_prompts(self) -> Dict[str, str]:
        """Fallback default prompts if analysis fails."""
        return {
            "analytical_prompt": """Generate analytical multiple choice questions that test deeper understanding, reasoning, and analysis. Focus on "why" and "how" questions that require students to think critically about concepts, apply knowledge, and understand relationships between ideas.""",
            "direct_prompt": """Generate direct multiple choice questions that test factual knowledge and recall. Focus on "what" and "which" questions that require students to recognize correct definitions, facts, and concepts.""",
            "domain": "general",
            "content_type": "mixed",
            "complexity": "moderate",
            "key_characteristics": [],
            "recommended_focus_areas": []
        }


class ProblemSetOrchestrator:
    """Orchestrates multiple agents to generate complete problem sets."""
    
    def __init__(self, vector_store: RAGVectorStore):
        self.vs = vector_store
        self.analyzer = ChapterAnalyzerAgent()
        self.problem_gen = ProblemGeneratorAgent()
        self.solution_gen = SolutionGeneratorAgent()
        self.mcq_gen = MCQGeneratorAgent()
        self.quality_checker = QualityCheckerAgent()
        self.prompt_builder = PromptBuilderAgent()
    
    def generate_mcq_set(
        self,
        doc_id: str,
        num_mcqs: int = 5
    ) -> Dict[str, Any]:
        """
        Generate a set of multiple choice questions for a specific chapter.
        Uses PromptBuilderAgent to create specialized prompts for analytical and direct questions.
        
        Args:
            doc_id: Document/chapter identifier
            num_mcqs: Number of MCQs to generate
            
        Returns:
            Complete MCQ set with questions and answers
        """
        print(f"\n{'='*70}")
        print(f"GENERATING MCQ SET FOR: {doc_id}")
        print(f"{'='*70}\n")
        
        # Step 1: Retrieve all chunks with metadata (summaries and topics)
        print("[Step 1] Retrieving chunks with metadata from RAG...")
        chunk_data = self.vs.get_chunks_for_document(doc_id)
        
        if not chunk_data.get("documents") or len(chunk_data["documents"]) == 0:
            print(f"   [ERROR] No content found for {doc_id}")
            return None
        
        # Extract chunks, summaries, and topics
        chunks = chunk_data["documents"]
        metadatas = chunk_data.get("metadatas", [])
        chunk_summaries = [meta.get("summary", "") for meta in metadatas]
        chunk_topics = []
        for meta in metadatas:
            topics_str = meta.get("topics", "")
            if isinstance(topics_str, str) and topics_str:
                chunk_topics.append([t.strip() for t in topics_str.split(",") if t.strip()])
            elif isinstance(topics_str, list):
                chunk_topics.append(topics_str)
            else:
                chunk_topics.append([])
        
        chapter_content = "\n\n".join(chunks)
        print(f"   ✓ Retrieved {len(chunks)} chunks ({len(chapter_content)} chars)")
        print(f"   ✓ Found {len([s for s in chunk_summaries if s])} summaries\n")
        
        # Step 2: Build specialized prompts using PromptBuilderAgent
        print("[Step 2] Building specialized prompts for MCQ generation...")
        prompt_data = self.prompt_builder.build_prompts(
            chunks=chunks,
            doc_id=doc_id,
            chunk_summaries=chunk_summaries if any(chunk_summaries) else None,
            chunk_topics=chunk_topics if any(chunk_topics) else None,
            max_chunks=10,
            max_chars=15000
        )
        print(f"   ✓ Domain detected: {prompt_data.get('domain', 'general')}")
        print(f"   ✓ Content type: {prompt_data.get('content_type', 'mixed')}\n")
        
        # Step 3: Analyze chapter (for backward compatibility)
        print("[Step 3] Analyzing chapter content...")
        analysis = self.analyzer.analyze_chapter(chapter_content)
        print(f"   ✓ Identified {len(analysis.get('topics', []))} topics\n")
        
        # Step 4: Generate MCQs using both prompts
        # Split MCQs between analytical and direct questions
        num_analytical = max(1, num_mcqs // 2)
        num_direct = num_mcqs - num_analytical
        
        print(f"[Step 4] Generating {num_mcqs} MCQs ({num_analytical} analytical, {num_direct} direct)...")
        
        all_mcqs = []
        
        # Generate analytical questions
        if num_analytical > 0:
            print(f"   Generating {num_analytical} analytical questions...")
            analytical_mcqs = self.mcq_gen.generate_mcqs(
                chapter_content,
                analysis,
                num_analytical,
                specialized_prompt=prompt_data.get("analytical_prompt"),
                question_type="analytical"
            )
            # Add question type to each MCQ
            for mcq in analytical_mcqs:
                mcq["question_type"] = "analytical"
            all_mcqs.extend(analytical_mcqs)
            print(f"   ✓ Generated {len(analytical_mcqs)} analytical MCQs")
        
        # Generate direct questions
        if num_direct > 0:
            print(f"   Generating {num_direct} direct questions...")
            direct_mcqs = self.mcq_gen.generate_mcqs(
                chapter_content,
                analysis,
                num_direct,
                specialized_prompt=prompt_data.get("direct_prompt"),
                question_type="direct"
            )
            # Add question type to each MCQ
            for mcq in direct_mcqs:
                mcq["question_type"] = "direct"
            all_mcqs.extend(direct_mcqs)
            print(f"   ✓ Generated {len(direct_mcqs)} direct MCQs")
        
        print(f"   ✓ Total: {len(all_mcqs)} MCQs generated\n")
        
        result = {
            "doc_id": doc_id,
            "analysis": analysis,
            "prompt_info": {
                "domain": prompt_data.get("domain"),
                "content_type": prompt_data.get("content_type"),
                "complexity": prompt_data.get("complexity"),
                "key_characteristics": prompt_data.get("key_characteristics", []),
                "recommended_focus_areas": prompt_data.get("recommended_focus_areas", [])
            },
            "num_mcqs": len(all_mcqs),
            "mcqs": all_mcqs
        }
        
        print(f"{'='*70}")
        print(f"MCQ SET GENERATION COMPLETE")
        print(f"{'='*70}\n")
        
        return result
    
    def generate_mcq_set_stream(
        self,
        doc_id: str,
        num_mcqs: int = 5
    ):
        """
        Streaming version of generate_mcq_set that yields events as MCQs are generated.
        
        Args:
            doc_id: Document/chapter identifier
            num_mcqs: Number of MCQs to generate
            
        Yields:
            Events with type and data for streaming to frontend
        """
        import json
        
        try:
            # Step 1: Retrieve chunks
            yield json.dumps({
                "type": "status",
                "message": "Retrieving chunks with metadata from RAG...",
                "step": 1
            }) + "\n"
            
            chunk_data = self.vs.get_chunks_for_document(doc_id)
            
            if not chunk_data.get("documents") or len(chunk_data["documents"]) == 0:
                yield json.dumps({
                    "type": "error",
                    "message": f"No content found for {doc_id}"
                }) + "\n"
                return
            
            chunks = chunk_data["documents"]
            metadatas = chunk_data.get("metadatas", [])
            chunk_summaries = [meta.get("summary", "") for meta in metadatas]
            chunk_topics = []
            for meta in metadatas:
                topics_str = meta.get("topics", "")
                if isinstance(topics_str, str) and topics_str:
                    chunk_topics.append([t.strip() for t in topics_str.split(",") if t.strip()])
                elif isinstance(topics_str, list):
                    chunk_topics.append(topics_str)
                else:
                    chunk_topics.append([])
            
            chapter_content = "\n\n".join(chunks)
            
            yield json.dumps({
                "type": "status",
                "message": f"Retrieved {len(chunks)} chunks",
                "step": 1,
                "complete": True
            }) + "\n"
            
            # Step 2: Build prompts
            yield json.dumps({
                "type": "status",
                "message": "Building specialized prompts for MCQ generation...",
                "step": 2
            }) + "\n"
            
            prompt_data = self.prompt_builder.build_prompts(
                chunks=chunks,
                doc_id=doc_id,
                chunk_summaries=chunk_summaries if any(chunk_summaries) else None,
                chunk_topics=chunk_topics if any(chunk_topics) else None,
                max_chunks=10,
                max_chars=15000
            )
            
            yield json.dumps({
                "type": "prompt_info",
                "data": {
                    "domain": prompt_data.get("domain"),
                    "content_type": prompt_data.get("content_type"),
                    "complexity": prompt_data.get("complexity"),
                    "key_characteristics": prompt_data.get("key_characteristics", []),
                    "recommended_focus_areas": prompt_data.get("recommended_focus_areas", [])
                }
            }) + "\n"
            
            yield json.dumps({
                "type": "status",
                "message": f"Domain detected: {prompt_data.get('domain', 'general')}",
                "step": 2,
                "complete": True
            }) + "\n"
            
            # Step 3: Analyze chapter
            yield json.dumps({
                "type": "status",
                "message": "Analyzing chapter content...",
                "step": 3
            }) + "\n"
            
            analysis = self.analyzer.analyze_chapter(chapter_content)
            
            yield json.dumps({
                "type": "analysis",
                "data": analysis
            }) + "\n"
            
            yield json.dumps({
                "type": "status",
                "message": f"Identified {len(analysis.get('topics', []))} topics",
                "step": 3,
                "complete": True
            }) + "\n"
            
            # Step 4: Generate MCQs
            num_analytical = max(1, num_mcqs // 2)
            num_direct = num_mcqs - num_analytical
            
            yield json.dumps({
                "type": "status",
                "message": f"Generating {num_mcqs} MCQs ({num_analytical} analytical, {num_direct} direct)...",
                "step": 4
            }) + "\n"
            
            # Generate analytical questions
            if num_analytical > 0:
                yield json.dumps({
                    "type": "status",
                    "message": f"Generating {num_analytical} analytical questions...",
                    "step": 4,
                    "substep": "analytical"
                }) + "\n"
                
                analytical_mcqs = self.mcq_gen.generate_mcqs(
                    chapter_content,
                    analysis,
                    num_analytical,
                    specialized_prompt=prompt_data.get("analytical_prompt"),
                    question_type="analytical"
                )
                
                # Stream each analytical MCQ as it's ready
                for mcq in analytical_mcqs:
                    mcq["question_type"] = "analytical"
                    yield json.dumps({
                        "type": "mcq",
                        "data": mcq
                    }) + "\n"
            
            # Generate direct questions
            if num_direct > 0:
                yield json.dumps({
                    "type": "status",
                    "message": f"Generating {num_direct} direct questions...",
                    "step": 4,
                    "substep": "direct"
                }) + "\n"
                
                direct_mcqs = self.mcq_gen.generate_mcqs(
                    chapter_content,
                    analysis,
                    num_direct,
                    specialized_prompt=prompt_data.get("direct_prompt"),
                    question_type="direct"
                )
                
                # Stream each direct MCQ as it's ready
                for mcq in direct_mcqs:
                    mcq["question_type"] = "direct"
                    yield json.dumps({
                        "type": "mcq",
                        "data": mcq
                    }) + "\n"
            
            # Final status
            yield json.dumps({
                "type": "status",
                "message": "MCQ generation complete!",
                "step": 4,
                "complete": True
            }) + "\n"
            
            yield json.dumps({
                "type": "done",
                "doc_id": doc_id
            }) + "\n"
            
        except Exception as e:
            import traceback
            yield json.dumps({
                "type": "error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }) + "\n"
        
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
