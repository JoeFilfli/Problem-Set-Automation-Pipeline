"""Production-ready multi-granularity chunker for technical/educational content."""

# ---------------------------------------------------------------------------
# Original chunker preserved for easy revert
# ---------------------------------------------------------------------------
"""
LLM-based semantic chunker for processing documents with math content.
"""
import json
from typing import List, Tuple
from openai import OpenAI
from dotenv import load_dotenv
from models import Chunk

# Load environment variables
load_dotenv(override=True)


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

# # ---------------------------------------------------------------------------
# # New multi-granularity chunker implementation
# # ---------------------------------------------------------------------------
# import json
# import re
# from typing import List, Dict, Optional
# from dataclasses import dataclass, asdict
# from openai import OpenAI
# from dotenv import load_dotenv
# from models import Chunk as LegacyChunk  # legacy Chunk used by vector_store/api

# load_dotenv(override=True)


# def split_for_llm(
#     text: str,
#     max_chars: int = 15000,   # target per LLM call
#     overlap: int = 500        # shared context between segments
# ) -> List[tuple[str, int]]:
#     """
#     Split a long string into segments of at most max_chars,
#     with 'overlap' characters overlap between neighbors.

#     Returns a list of (segment_text, global_start_index).
#     """
#     segments: List[tuple[str, int]] = []
#     n = len(text)
#     if n == 0:
#         return segments

#     start = 0
#     while start < n:
#         end = min(start + max_chars, n)
#         seg = text[start:end]
#         segments.append((seg, start))

#         if end == n:
#             break
#         start = max(0, end - overlap)

#     return segments


# @dataclass
# class ChunkMetadata:
#     """Rich metadata for each chunk."""
#     chunk_type: str  # definition, theorem, example, derivation, table, etc.
#     topics: List[str]
#     has_formula: bool = False
#     has_code: bool = False
#     has_example: bool = False
#     has_derivation: bool = False
#     difficulty: str = "medium"  # easy, medium, hard
#     prerequisites: List[str] = None
#     learning_objectives: List[str] = None
    
#     def __post_init__(self):
#         if self.prerequisites is None:
#             self.prerequisites = []
#         if self.learning_objectives is None:
#             self.learning_objectives = []


# @dataclass
# class Chunk:
#     """Represents a semantic chunk with metadata."""
#     id: str
#     granularity: str  # atomic, composite, contextual
#     content: str
#     summary: str
#     metadata: ChunkMetadata
#     start_idx: int
#     end_idx: int
#     parent_id: Optional[str] = None
#     child_ids: List[str] = None
    
#     def __post_init__(self):
#         if self.child_ids is None:
#             self.child_ids = []
    
#     def to_vector_db_format(self) -> dict:
#         """Convert to format suitable for vector DB insertion."""
#         return {
#             "id": self.id,
#             "granularity": self.granularity,
#             "content": self.content,
#             "summary": self.summary,
#             "parent_id": self.parent_id,
#             "child_ids": self.child_ids,
#             **asdict(self.metadata),
#             "char_range": f"{self.start_idx}-{self.end_idx}"
#         }


# class MultiGranularityChunker:
#     """Semantic chunker with multi-level granularity for retrieval."""
    
#     def __init__(self, model: str = "gpt-4o-mini"):
#         self.client = OpenAI()
#         self.model = model
#         self.chunk_counter = 0
    
#     def _detect_content_type(self, text: str) -> dict:
#         """Analyze what types of content are present."""
#         return {
#             "has_math": bool(re.search(r"\$.*?\$|\\frac|\\sum|\\int", text)),
#             "has_code": bool(re.search(r"```|def |class |import ", text)),
#             "has_tables": bool(re.search(r"\|.*\|.*\||\t.*\t", text)),
#             "has_lists": bool(re.search(r"^\s*[-*]\s|\d+\.\s", text, re.MULTILINE)),
#         }
    
#     def chunk_atomic(self, text: str, chapter_num: int = None) -> List[Chunk]:
#         """
#         Create atomic chunks: smallest semantic units.
#         Examples: single definition, single formula, single example.
#         Target: 400-800 characters.
#         """
#         content_hints = self._detect_content_type(text)
        
#         prompt = f"""You are an expert educational content analyzer.

# Split this text into ATOMIC chunks - the smallest meaningful units.

# ATOMIC CHUNK = One of:
# - Single definition with its formula
# - Single worked example (complete problem to solution)
# - Single theorem/principle
# - Single data point or fact
# - One row of a table with context

# RULES:
# 1. Each chunk must be self-contained enough to understand in isolation
# 2. Target 400-800 characters per chunk
# 3. DO NOT split formulas or examples mid-calculation
# 4. For each chunk, classify its type and extract metadata

# Content analysis: {json.dumps(content_hints)}

# Return JSON:
# {{
#   "chunks": [
#     {{
#       "content": "...",
#       "summary": "One sentence: what this teaches",
#       "chunk_type": "definition|example|theorem|derivation|table_row|note",
#       "topics": ["topic1", "topic2"],
#       "has_formula": true/false,
#       "has_code": true/false,
#       "difficulty": "easy|medium|hard",
#       "learning_objectives": ["learn X", "apply Y"],
#       "startIndex": 0,
#       "endIndex": 500
#     }}
#   ]
# }}

# Text to chunk:
# \"\"\"
# {text}
# \"\"\"
# """
        
#         response = self.client.chat.completions.create(
#             model=self.model,
#             messages=[{"role": "user", "content": prompt}],
#             response_format={"type": "json_object"},
#             temperature=0.1,
#         )
        
#         data = json.loads(response.choices[0].message.content)
#         chunks = []
        
#         for c in data["chunks"]:
#             self.chunk_counter += 1
#             metadata = ChunkMetadata(
#                 chunk_type=c.get("chunk_type", "unknown"),
#                 topics=c.get("topics", []),
#                 has_formula=c.get("has_formula", False),
#                 has_code=c.get("has_code", False),
#                 has_example=c.get("chunk_type") == "example",
#                 has_derivation=c.get("chunk_type") == "derivation",
#                 difficulty=c.get("difficulty", "medium"),
#                 learning_objectives=c.get("learning_objectives", [])
#             )
            
#             chunk_id = f"atomic_ch{chapter_num}_{self.chunk_counter:03d}"
#             chunks.append(Chunk(
#                 id=chunk_id,
#                 granularity="atomic",
#                 content=c["content"],
#                 summary=c["summary"],
#                 metadata=metadata,
#                 start_idx=c["startIndex"],
#                 end_idx=c["endIndex"]
#             ))
        
#         return chunks
    
#     def chunk_composite(self, text: str, atomic_chunks: List[Chunk], 
#                         chapter_num: int = None) -> List[Chunk]:
#         """
#         Create composite chunks: complete teachable concepts.
#         Examples: definition + formula + example, full derivation.
#         Target: 1000-2000 characters.
#         """
#         prompt = f"""You are an expert educational content structurer.

# Create COMPOSITE chunks - complete teachable concepts that could be:
# - A mini-lesson (definition to formula to example)
# - A complete derivation with all steps
# - A complete worked problem with explanation
# - A related set of formulas with their relationships

# RULES:
# 1. Each chunk should be teachable as a standalone unit
# 2. Target 1000-2000 characters (can go to 2500 for complex derivations)
# 3. Group related atomic concepts together
# 4. Each chunk should have clear learning outcomes

# I'm providing the atomic chunks for reference:
# {json.dumps([{'id': c.id, 'summary': c.summary, 'topics': c.metadata.topics} for c in atomic_chunks], indent=2)}

# Return JSON:
# {{
#   "chunks": [
#     {{
#       "content": "...",
#       "summary": "What concept does this teach?",
#       "topics": ["..."],
#       "child_atomic_ids": ["atomic_ch2_001", "atomic_ch2_002"],
#       "prerequisites": ["prerequisite_topic1"],
#       "learning_objectives": ["Calculate X", "Apply Y to Z"],
#       "has_worked_example": true/false,
#       "difficulty": "easy|medium|hard",
#       "startIndex": 0,
#       "endIndex": 1500
#     }}
#   ]
# }}

# Text to chunk:
# \"\"\"
# {text}
# \"\"\"
# """
        
#         response = self.client.chat.completions.create(
#             model=self.model,
#             messages=[{"role": "user", "content": prompt}],
#             response_format={"type": "json_object"},
#             temperature=0.1,
#         )
        
#         data = json.loads(response.choices[0].message.content)
#         chunks = []
        
#         for c in data["chunks"]:
#             self.chunk_counter += 1
#             chunk_id = f"composite_ch{chapter_num}_{self.chunk_counter:03d}"
            
#             content = c["content"]
#             metadata = ChunkMetadata(
#                 chunk_type="composite_concept",
#                 topics=c.get("topics", []),
#                 has_formula=bool(re.search(r"\$.*?\$", content)),
#                 has_example=c.get("has_worked_example", False),
#                 difficulty=c.get("difficulty", "medium"),
#                 prerequisites=c.get("prerequisites", []),
#                 learning_objectives=c.get("learning_objectives", [])
#             )
            
#             chunks.append(Chunk(
#                 id=chunk_id,
#                 granularity="composite",
#                 content=content,
#                 summary=c["summary"],
#                 metadata=metadata,
#                 start_idx=c["startIndex"],
#                 end_idx=c["endIndex"],
#                 child_ids=c.get("child_atomic_ids", [])
#             ))
        
#         return chunks
    
#     def chunk_contextual(self, text: str, composite_chunks: List[Chunk],
#                          chapter_num: int = None, section_title: str = None) -> Chunk:
#         """
#         Create contextual chunk: full section with complete context.
#         Target: 3000-5000 characters (entire section).
#         """
#         prompt = f"""You are an expert educational content curator.

# Create a CONTEXTUAL summary of this entire section.

# Provide:
# 1. A comprehensive summary (3-5 sentences)
# 2. All key concepts covered
# 3. Prerequisites needed to understand this section
# 4. Learning outcomes after studying this section
# 5. How concepts relate to each other

# Composite chunks in this section:
# {json.dumps([{'id': c.id, 'summary': c.summary} for c in composite_chunks], indent=2)}

# Return JSON:
# {{
#   "summary": "Comprehensive 3-5 sentence summary",
#   "key_concepts": ["concept1", "concept2"],
#   "prerequisites": ["prereq1", "prereq2"],
#   "learning_outcomes": ["outcome1", "outcome2"],
#   "concept_flow": "Brief description of how concepts build on each other",
#   "difficulty": "easy|medium|hard"
# }}

# Text:
# \"\"\"
# {text}
# \"\"\"
# """
        
#         response = self.client.chat.completions.create(
#             model=self.model,
#             messages=[{"role": "user", "content": prompt}],
#             response_format={"type": "json_object"},
#             temperature=0.1,
#         )
        
#         data = json.loads(response.choices[0].message.content)
        
#         chunk_id = f"contextual_ch{chapter_num}_{section_title or 'section'}"
#         metadata = ChunkMetadata(
#             chunk_type="contextual_section",
#             topics=data.get("key_concepts", []),
#             difficulty=data.get("difficulty", "medium"),
#             prerequisites=data.get("prerequisites", []),
#             learning_objectives=data.get("learning_outcomes", [])
#         )
        
#         return Chunk(
#             id=chunk_id,
#             granularity="contextual",
#             content=text,
#             summary=data["summary"],
#             metadata=metadata,
#             start_idx=0,
#             end_idx=len(text),
#             child_ids=[c.id for c in composite_chunks]
#         )
    
#     def process_document(self, text: str, chapter_num: int = None, 
#                          section_title: str = None) -> Dict[str, List[Chunk]]:
#         """
#         Main entry point: processes document at all granularity levels.
        
#         Returns:
#             Dictionary with 'atomic', 'composite', and 'contextual' chunks
#         """
#         print(f"[process] Processing document ({len(text)} chars)...")
        
#         # Step 1: Create atomic chunks
#         print("  -> Creating atomic chunks...")
#         atomic_chunks = self.chunk_atomic(text, chapter_num)
#         print(f"     done: {len(atomic_chunks)} atomic chunks")
        
#         # Step 2: Create composite chunks
#         print("  -> Creating composite chunks...")
#         composite_chunks = self.chunk_composite(text, atomic_chunks, chapter_num)
#         print(f"     done: {len(composite_chunks)} composite chunks")
        
#         # Step 3: Create contextual chunk
#         print("  -> Creating contextual chunk...")
#         contextual_chunk = self.chunk_contextual(text, composite_chunks, 
#                                                  chapter_num, section_title)
#         print("     done: contextual chunk")
        
#         # Link parents to children
#         for composite in composite_chunks:
#             composite.parent_id = contextual_chunk.id
#             for atomic_id in composite.child_ids:
#                 atomic = next((a for a in atomic_chunks if a.id == atomic_id), None)
#                 if atomic:
#                     atomic.parent_id = composite.id
        
#         return {
#             "atomic": atomic_chunks,
#             "composite": composite_chunks,
#             "contextual": [contextual_chunk]
#         }
    
#     def process_large_document(self, text: str, max_section_size: int = 15000,
#                                chapter_num: int = None) -> Dict[str, List[Chunk]]:
#         """
#         Process documents larger than LLM context by splitting into sections.
#         """
#         sections = self._split_into_sections(text, max_section_size)
        
#         all_atomic = []
#         all_composite = []
#         all_contextual = []
        
#         for idx, section_text in enumerate(sections, 1):
#             print(f"\n[process] Processing section {idx}/{len(sections)}...")
#             result = self.process_document(
#                 section_text, 
#                 chapter_num=chapter_num,
#                 section_title=f"section_{idx}"
#             )
#             all_atomic.extend(result["atomic"])
#             all_composite.extend(result["composite"])
#             all_contextual.extend(result["contextual"])
        
#         return {
#             "atomic": all_atomic,
#             "composite": all_composite,
#             "contextual": all_contextual
#         }
    
#     def _split_into_sections(self, text: str, max_size: int) -> List[str]:
#         """Split text into sections, preferring splits at headers."""
#         header_pattern = r"\n#{1,3}\s+.+\n"
#         headers = list(re.finditer(header_pattern, text))
        
#         if not headers:
#             sections = []
#             start = 0
#             while start < len(text):
#                 end = min(start + max_size, len(text))
#                 sections.append(text[start:end])
#                 start = end - 500  # 500 char overlap to preserve context
#             return sections
        
#         sections = []
#         for i in range(len(headers)):
#             start = headers[i].start()
#             end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            
#             section = text[start:end]
#             if len(section) > max_size:
#                 subsections = self._split_into_sections(section, max_size)
#                 sections.extend(subsections)
#             else:
#                 sections.append(section)
        
#         return sections


# class LLMChunker:
#     """
#     Backwards-compatible adapter that maps to MultiGranularityChunker and
#     returns the legacy Chunk objects expected by vector_store/api routes.
#     """

#     def __init__(self, model: str = "gpt-4o-mini", format_mode: str = "markdown"):
#         self.backend = MultiGranularityChunker(model=model)
#         self.format_mode = format_mode

#     def chunk(self, text: str, max_size: int = 1400, overlap: int = 100) -> List[LegacyChunk]:
#         """
#         Simplified wrapper: use atomic chunks and convert to legacy Chunk.
#         """
#         result = self.backend.process_document(text)
#         legacy_chunks: List[LegacyChunk] = []
#         for ch in result["atomic"]:
#             legacy_chunks.append(
#                 LegacyChunk(
#                     formatted=ch.content,
#                     summary=ch.summary,
#                     topics=ch.metadata.topics,
#                     start=ch.start_idx,
#                     end=ch.end_idx,
#                 )
#             )
#         return legacy_chunks

#     def chunk_with_splitting(
#         self,
#         text: str,
#         max_chars: int = 15000,
#         overlap: int = 500,
#         max_size: int = 1400
#     ) -> List[LegacyChunk]:
#         """
#         Roughly mirrors the old API: split large docs and merge atomic chunks.
#         """
#         segments = split_for_llm(text, max_chars=max_chars, overlap=overlap)
#         all_chunks: List[LegacyChunk] = []

#         for seg_text, base_offset in segments:
#             atomic_chunks = self.chunk(seg_text, max_size=max_size, overlap=overlap)
#             # adjust offsets to global positions
#             for chunk in atomic_chunks:
#                 chunk.start += base_offset
#                 chunk.end += base_offset
#                 all_chunks.append(chunk)

#         return all_chunks


# if __name__ == "__main__":
#     chunker = MultiGranularityChunker()
    
#     sample_text = """
#     ## Single Payment Factors
    
#     Recall that P dollars now are equivalent to F dollars after n time periods
#     at an interest rate of i per time period, where F = P(1+i)^n.
    
#     E.g., if you invest $1000 at 5% interest for 3 years, you'll have
#     F = 1000(1.05)^3 = $1157.63
#     """
    
#     result = chunker.process_document(sample_text, chapter_num=2, 
#                                       section_title="single_payment")
    
#     print("\n" + "=" * 60)
#     print("RESULTS:")
#     print(f"  Atomic chunks: {len(result['atomic'])}")
#     print(f"  Composite chunks: {len(result['composite'])}")
#     print(f"  Contextual chunks: {len(result['contextual'])}")
