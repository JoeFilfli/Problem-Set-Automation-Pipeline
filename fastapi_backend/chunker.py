"""
LLM-based semantic chunker for processing documents with math content.
"""
import json
from typing import List, Tuple
from openai import OpenAI
from dotenv import load_dotenv
from models import Chunk

# Load environment variables
load_dotenv()


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
You are a math-aware document chunker.

Split the text into semantic chunks. Requirements:
- Each chunk must represent a complete idea (definition, theorem, example, derivation).
- DO NOT split equations mid-derivation.
- Aim for < {max_size} characters per chunk.
- For each chunk:
  - "formatted" = cleaned Markdown with math ($...$, $$...$$)
  - "summary" = 1–2 sentence explanation
  - "topics" = 2–5 short keywords
  - "startIndex" / "endIndex" = character offsets into the original text

Return ONLY JSON:
{{
  "chunks": [
    {{
      "formatted": "...",
      "summary": "...",
      "topics": ["..."],
      "startIndex": 0,
      "endIndex": 120
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
        print(f"   [OpenAI] ✓ Chunking complete: {len(chunks)} chunks created")
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
        print(f" → Split into {len(segments)} segments for LLM processing")
        all_chunks: List[Chunk] = []

        for idx, (seg_text, base_offset) in enumerate(segments, 1):
            print(f" → Processing segment {idx}/{len(segments)} (offset={base_offset})")
            seg_chunks = self.chunk(seg_text, max_size=max_size)

            # Fix indices to refer to the original text
            for ch in seg_chunks:
                ch.start += base_offset
                ch.end += base_offset
                all_chunks.append(ch)

        return all_chunks
