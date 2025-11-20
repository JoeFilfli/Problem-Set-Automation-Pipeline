"""
PDF text extraction utilities.
"""
from typing import Iterable
import fitz  # PyMuPDF


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
