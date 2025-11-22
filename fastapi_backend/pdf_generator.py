"""
PDF generator for exam papers with proper equation rendering.
Uses reportlab for PDF generation and matplotlib for equation rendering.
"""
from typing import List, Dict, Any
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from matplotlib import mathtext
import re
import os


def render_equation_to_image(equation: str, dpi: int = 150) -> BytesIO:
    """
    Render a LaTeX equation to an image using matplotlib.
    
    Args:
        equation: LaTeX equation string (without $ delimiters)
        dpi: Resolution for the image
        
    Returns:
        BytesIO object containing PNG image
    """
    # Clean up the equation
    equation = equation.strip()
    # Remove $ delimiters if present
    equation = equation.strip('$')
    
    # Create a figure with transparent background
    fig = plt.figure(figsize=(6, 0.5))
    fig.patch.set_alpha(0)
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Render the equation
    try:
        ax.text(0.5, 0.5, f'${equation}$', 
                fontsize=14, 
                ha='center', 
                va='center',
                transform=ax.transAxes)
    except:
        # Fallback to plain text if LaTeX fails
        ax.text(0.5, 0.5, equation,
                fontsize=14,
                ha='center',
                va='center',
                transform=ax.transAxes)
    
    # Save to BytesIO
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=dpi, bbox_inches='tight', 
                pad_inches=0.1, transparent=True)
    plt.close(fig)
    img_buffer.seek(0)
    
    return img_buffer


def extract_equations(text: str) -> List[tuple]:
    """
    Extract LaTeX equations from text.
    Returns list of (start, end, equation_text) tuples.
    """
    equations = []
    # Match inline math $...$ and display math $$...$$
    pattern = r'\$\$?([^\$]+)\$\$?'
    for match in re.finditer(pattern, text):
        start, end = match.span()
        eq_text = match.group(1)
        equations.append((start, end, eq_text))
    return equations


def process_text_with_equations(text: str, story: list, styles: Any):
    """
    Process text and replace equations with images.
    
    Args:
        text: Text that may contain LaTeX equations
        story: List to append story elements to
        styles: ReportLab styles
    """
    equations = extract_equations(text)
    
    if not equations:
        # No equations, just add as paragraph
        story.append(Paragraph(text.replace('\n', '<br/>'), styles['Normal']))
        return
    
    # Split text by equations and process each part
    last_end = 0
    for start, end, eq_text in equations:
        # Add text before equation
        if start > last_end:
            before_text = text[last_end:start].replace('\n', '<br/>')
            if before_text.strip():
                story.append(Paragraph(before_text, styles['Normal']))
        
        # Add equation as image
        try:
            eq_img = render_equation_to_image(eq_text)
            from reportlab.platypus import Image
            img = Image(eq_img, width=4*inch, height=0.3*inch)
            story.append(img)
        except Exception as e:
            # Fallback: add equation as plain text
            story.append(Paragraph(f'[{eq_text}]', styles['Normal']))
        
        last_end = end
    
    # Add remaining text
    if last_end < len(text):
        after_text = text[last_end:].replace('\n', '<br/>')
        if after_text.strip():
            story.append(Paragraph(after_text, styles['Normal']))


def generate_exam_pdf(mcqs: List[Dict[str, Any]], exam_title: str = "Exam") -> bytes:
    """
    Generate a PDF exam from MCQ questions.
    
    Args:
        mcqs: List of MCQ dictionaries
        exam_title: Title for the exam
        
    Returns:
        PDF file as bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#8B0000'),  # Dark red
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12,
        spaceBefore=12,
        leftIndent=20
    )
    
    option_style = ParagraphStyle(
        'Option',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        leftIndent=40
    )
    
    # Add title
    story.append(Paragraph(exam_title, title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Add instructions
    instructions = """
    <b>Instructions:</b><br/>
    • Please answer all questions<br/>
    • Choose the best answer for each question<br/>
    • Mark your answers clearly<br/>
    """
    story.append(Paragraph(instructions, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Add each MCQ
    for i, mcq in enumerate(mcqs, 1):
        # Question number and text
        question_text = f"<b>Question {i}:</b> {mcq.get('question', '')}"
        process_text_with_equations(question_text, story, styles)
        story.append(Spacer(1, 0.1*inch))
        
        # Options
        options = mcq.get('options', {})
        for option_key in ['A', 'B', 'C', 'D']:
            if option_key in options:
                option_text = f"{option_key}. {options[option_key]}"
                process_text_with_equations(option_text, story, styles)
        
        story.append(Spacer(1, 0.2*inch))
        
        # Add page break every 3 questions (optional)
        if i % 3 == 0 and i < len(mcqs):
            story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

