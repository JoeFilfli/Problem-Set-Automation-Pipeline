"""Production-ready multi-granularity chunker for technical/educational content."""

# ---------------------------------------------------------------------------
# Original chunker preserved for easy revert
# ---------------------------------------------------------------------------
"""
LLM-based semantic chunker for processing documents with math content.
"""
import json
import re
from typing import List, Tuple
from openai import OpenAI
from dotenv import load_dotenv
from models import Chunk

# Load environment variables
load_dotenv(override=True)


def smart_chunk_without_llm(text: str, max_size: int = 2000) -> List[Chunk]:
    """
    Rule-based chunking that preserves ALL content without LLM.
    Chunks based on structural patterns (headers, blank lines, section breaks).
    
    Args:
        text: The document text to chunk
        max_size: Target maximum characters per chunk
        
    Returns:
        List of Chunk objects with all content preserved
    """
    print(f"   [Rule-Based] Chunking {len(text)} chars (max_size={max_size})...")
    
    chunks = []
    lines = text.split('\n')
    
    current_chunk_lines = []
    current_size = 0
    chunk_start_idx = 0
    current_pos = 0
    
    def is_section_boundary(line: str, next_line: str = "") -> bool:
        """Detect natural section boundaries."""
        line_stripped = line.strip()
        
        # Major headers (Chapter, Section, numbered headers)
        if re.match(r'^(Chapter|CHAPTER|Section|SECTION|\d+\.|\d+\.\d+)', line_stripped):
            return True
        
        # Markdown headers
        if line_stripped.startswith('#'):
            return True
        
        # ALL CAPS headers (common in course materials)
        if len(line_stripped) > 5 and line_stripped.isupper() and not line_stripped.endswith('.'):
            return True
        
        # Blank line followed by a header-like line
        if len(line_stripped) == 0 and next_line.strip() and (
            next_line.strip()[0].isupper() or next_line.strip().startswith('#')
        ):
            return True
        
        return False
    
    def extract_topics(text: str) -> List[str]:
        """Extract simple keywords from text."""
        # Remove common words and extract capitalized terms
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        # Get unique, limit to 6
        unique_words = []
        for word in words:
            if word not in unique_words and len(word) > 3:
                unique_words.append(word)
            if len(unique_words) >= 6:
                break
        return unique_words if unique_words else ["General Content"]
    
    def extract_summary(text: str) -> str:
        """Extract first meaningful sentence or create simple summary."""
        sentences = re.split(r'[.!?]\s+', text.strip())
        for sentence in sentences[:3]:
            if len(sentence) > 20:
                return sentence[:200] + "..." if len(sentence) > 200 else sentence
        return text[:150] + "..." if len(text) > 150 else text
    
    for i, line in enumerate(lines):
        next_line = lines[i + 1] if i + 1 < len(lines) else ""
        line_with_newline = line + '\n'
        
        # Check if we should split here
        should_split = (
            is_section_boundary(line, next_line) and 
            current_size > max_size * 0.5  # At least 50% of target size
        )
        
        # Force split if too large
        force_split = current_size > max_size * 1.8
        
        if (should_split or force_split) and current_chunk_lines:
            # Save current chunk
            chunk_text = ''.join(current_chunk_lines)
            chunks.append(Chunk(
                formatted=chunk_text,
                summary=extract_summary(chunk_text),
                topics=extract_topics(chunk_text),
                start=chunk_start_idx,
                end=chunk_start_idx + len(chunk_text)
            ))
            
            # Start new chunk
            current_chunk_lines = [line_with_newline]
            current_size = len(line_with_newline)
            chunk_start_idx = current_pos
        else:
            current_chunk_lines.append(line_with_newline)
            current_size += len(line_with_newline)
        
        current_pos += len(line_with_newline)
    
    # Add final chunk
    if current_chunk_lines:
        chunk_text = ''.join(current_chunk_lines)
        chunks.append(Chunk(
            formatted=chunk_text,
            summary=extract_summary(chunk_text),
            topics=extract_topics(chunk_text),
            start=chunk_start_idx,
            end=chunk_start_idx + len(chunk_text)
        ))
    
    print(f"   [Rule-Based] Created {len(chunks)} chunks")
    return chunks


def split_for_llm(
    text: str,
    max_chars: int = 15000,   # target per LLM call
    overlap: int = 500        # shared context between segments
) -> List[Tuple[str, int]]:
    """
    Split a long string into segments of at most max_chars,
    with 'overlap' characters overlap between neighbors.

    Returns a list of (segment_text, global_start_index).
    """
    segments: List[Tuple[str, int]] = []
    n = len(text)
    if n == 0:
        return segments

    start = 0
    while start < n:
        end = min(start + max_chars, n)
        seg = text[start:end]
        segments.append((seg, start))

        # move start forward with overlap
        if end == n:
            break
        start = max(0, end - overlap)

    return segments


class LLMChunker:
    """Handles semantic chunking of documents using LLM with math awareness."""
    
    def __init__(self, model="gpt-4o-mini", format_mode="markdown"):
        self.client = OpenAI()
        self.model = model
        self.format_mode = format_mode

    def extract_json(self, text: str) -> str:
        """Extract clean JSON object from LLM output."""
        text = text.strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON found in LLM response.")
        return text[start: end + 1]

    def chunk(self, text: str, max_size=1400, overlap=100) -> List[Chunk]:
        """
        Split text into semantic chunks using LLM.
        
        Args:
            text: The document text to chunk
            max_size: Target maximum characters per chunk
            overlap: Overlap between chunks (not used in current implementation)
            
        Returns:
            List of Chunk objects with raw, formatted, summary, topics, and indices
        """
        print(f"   [OpenAI] Chunking request ({len(text)} chars, model={self.model})...")
        prompt = f"""
You are an expert educational chunker for textbooks and technical docs.

Objective: produce subtopic-complete chunks. Each chunk must cover one subtopic end-to-end: the core concept plus every example, derivation, or demonstration that teaches that subtopic. Never separate a concept from the examples that illustrate it.

Chunking principles:
- One subtopic per chunk. Keep concept + examples + short exercises for that subtopic together.
- Respect structure: do not split inside equations, code blocks, tables, bullet lists, or numbered procedures.
- Size: prefer chunks under {max_size} characters, but allow up to roughly 20% more when needed to keep the subtopic intact. Never split mid-subtopic just to hit a size target.
- Boundaries: prefer section/paragraph boundaries or clear topic shifts. Use minimal overlap only when absolutely needed to avoid cutting context.
- Formatting: return clean Markdown; preserve math notation, fenced code, and table rows.
- Completeness: the reader should understand the subtopic from a single chunk without needing neighbors.

Return ONLY JSON:
{{
  "chunks": [
    {{
      "formatted": "cleaned Markdown text for this subtopic, including its examples",
      "summary": "1-3 sentences: what the subtopic is and what the examples show",
      "topics": ["3-6 short keywords"],
      "startIndex": 0,
      "endIndex": 120,
      "includes_example": true/false,
      "content_type": "concept|definition|theorem|procedure|example_combo|derivation|table|code",
      "has_equation": true/false,
      "has_table": true/false,
      "has_code": true/false
    }}
  ]
}}

Text to chunk:
\"\"\"{text}\"\"\"
"""

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        raw_output = resp.choices[0].message.content
        json_str = self.extract_json(raw_output)
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"   [ERROR] JSON parsing failed: {e}")
            print(f"   [DEBUG] Raw JSON string (first 500 chars):\n{json_str[:500]}")
            # Try to use response_format for structured output
            print(f"   [RETRY] Requesting structured JSON output...")
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            raw_output = resp.choices[0].message.content
            json_str = self.extract_json(raw_output)
            data = json.loads(json_str)

        chunks = []
        for c in data["chunks"]:
            chunks.append(
                Chunk(
                    formatted=c["formatted"],
                    summary=c["summary"],
                    topics=c["topics"],
                    start=c["startIndex"],
                    end=c["endIndex"],
                )
            )
        print(f"   [OpenAI] Chunking complete: {len(chunks)} chunks created")
        return chunks

    def chunk_with_splitting(
        self,
        text: str,
        max_chars: int = 15000,
        overlap: int = 500,
        max_size: int = 1400
    ) -> List[Chunk]:
        """
        High-level helper for chunking large documents.
        Splits text into LLM-sized segments, runs semantic chunker on each,
        and adjusts indices to be global.
        
        Args:
            text: The full document text to chunk
            max_chars: Maximum characters per LLM call (default ~3.5k tokens)
            overlap: Overlap between segments to avoid breaking concepts
            max_size: Target maximum characters per semantic chunk
            
        Returns:
            List of Chunk objects with global indices
        """
        segments = split_for_llm(text, max_chars=max_chars, overlap=overlap)
        print(f" -> Split into {len(segments)} segments for LLM processing")
        all_chunks: List[Chunk] = []

        for idx, (seg_text, base_offset) in enumerate(segments, 1):
            print(f" -> Processing segment {idx}/{len(segments)} (offset={base_offset})")
            seg_chunks = self.chunk(seg_text, max_size=max_size)

            # Fix indices to refer to the original text
            for ch in seg_chunks:
                ch.start += base_offset
                ch.end += base_offset
                all_chunks.append(ch)

        return all_chunks