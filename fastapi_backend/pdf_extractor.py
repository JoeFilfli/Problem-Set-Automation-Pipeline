"""
PDF text extraction utilities.
"""
import fitz  # PyMuPDF


def extract_pdf_text(path: str) -> str:
    """
    Extract all text from a PDF file.
    
    Args:
        path: Path to the PDF file
        
    Returns:
        Extracted text as a single string
    """
    doc = fitz.open(path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text("text"))
    doc.close()
    return "\n".join(text_parts)
