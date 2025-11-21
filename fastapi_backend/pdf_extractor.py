"""
PDF text extraction utilities with OCR support.
"""
from typing import Iterable
import fitz  # PyMuPDF
from openai import OpenAI
from dotenv import load_dotenv
import base64

load_dotenv(override=True)


def _concatenate_text(pages: Iterable[fitz.Page]) -> str:
    """Helper to concatenate the text contents of PyMuPDF pages."""
    text_parts = []
    for page in pages:
        text_parts.append(page.get_text("text"))
    return "\n".join(text_parts)


def extract_pdf_text(path: str) -> str:
    """
    Extract all text from a PDF file.
    
    Args:
        path: Path to the PDF file
        
    Returns:
        Extracted text as a single string
    """
    doc = fitz.open(path)
    try:
        return _concatenate_text(doc)
    finally:
        doc.close()


def extract_pdf_text_from_bytes(data: bytes) -> str:
    """
    Extract text directly from raw PDF bytes.
    
    Args:
        data: Raw PDF bytes
        
    Returns:
        Extracted text as a single string
    """
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        return _concatenate_text(doc)
    finally:
        doc.close()


def extract_pdf_with_ocr(path: str, use_gpt4_vision: bool = True) -> str:
    """
    Extract text from PDF using OCR via OpenAI Vision API.
    This works for both typed and handwritten content.
    
    Args:
        path: Path to the PDF file
        use_gpt4_vision: Use GPT-4 Vision for better accuracy (default: True)
        
    Returns:
        Extracted text as a single string
    """
    client = OpenAI()
    doc = fitz.open(path)
    
    all_text = []
    total_pages = len(doc)
    
    try:
        for page_num, page in enumerate(doc, 1):
            # Render page as image (PNG format, high DPI for better OCR)
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            
            # Encode image to base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            print(f"   [OCR] Processing page {page_num}/{total_pages}...")
            
            # Use OpenAI Vision API to extract text
            model = "gpt-4o" if use_gpt4_vision else "gpt-4o-mini"
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Extract all text from this image, including handwritten content.

IMPORTANT for grading accuracy:
- Preserve the structure and layout as much as possible
- Include all mathematical equations, formulas, and calculations
- Represent equations in plain math notation (e.g., F = P(1+i)^n)
- If you see numbered steps, clearly mark them as "Step 1:", "Step 2:", etc.
- If you see calculations, preserve the sequence (formula → substitution → result)
- If the handwriting is unclear, make your best interpretation
- Include any crossed-out work or corrections if legible

Return ONLY the extracted text, no commentary or analysis."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            page_text = response.choices[0].message.content
            all_text.append(f"--- Page {page_num} ---\n{page_text}")
            
    finally:
        doc.close()
    
    print(f"   ✓ OCR complete ({total_pages} pages)")
    return "\n\n".join(all_text)


def _needs_ocr(text: str) -> bool:
    """
    Determine if a PDF needs OCR based on content quality.
    For grading, we must be conservative - better to OCR unnecessarily than miss content.
    """
    if not text.strip():
        return True
    
    # Too few meaningful lines (likely just header/metadata)
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) < 5:
        return True
    
    # Suspicious character density (too short for a real solution)
    if len(text.strip()) < 300:
        return True
    
    # Too many empty/broken lines relative to content
    if text.count("\n") > 50 and len(text.replace("\n", "").strip()) < 200:
        return True
    
    # Check if it looks like just a header/form (common patterns)
    header_keywords = ["name:", "course:", "student id:", "date:", "problem set"]
    text_lower = text.lower()
    keyword_count = sum(1 for kw in header_keywords if kw in text_lower)
    if keyword_count >= 2 and len(text.strip()) < 500:
        return True
    
    return False


def extract_pdf_smart(path: str) -> str:
    """
    Smart PDF extraction: tries text extraction first, falls back to OCR if needed.
    Uses robust content quality checks for grading reliability.
    
    Args:
        path: Path to the PDF file
        
    Returns:
        Extracted text as a single string
    """
    # Try regular text extraction first (fast and free)
    text = extract_pdf_text(path)
    
    # Use content quality checks to determine if OCR needed
    if _needs_ocr(text):
        print("   [INFO] Low-quality text extraction detected, switching to OCR mode...")
        return extract_pdf_with_ocr(path)
    
    return text
