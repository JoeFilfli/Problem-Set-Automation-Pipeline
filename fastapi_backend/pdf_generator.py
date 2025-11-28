"""
PDF generator for exam papers with proper equation rendering.
Uses reportlab for PDF generation and matplotlib for equation rendering.
"""
from typing import List, Dict, Any
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Flowable
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Agg')  # Use non-interactive backend
from matplotlib import mathtext
import re
import os


def normalize_equation(equation: str) -> str:
    """
    Normalize an equation string to proper LaTeX format.
    Converts common patterns to LaTeX syntax that matplotlib can render.
    
    Args:
        equation: Equation string (may be in various formats)
        
    Returns:
        Normalized LaTeX equation string
    """
    eq = equation.strip()
    
    # Remove any existing delimiters
    eq = eq.strip('$`')
    
    # Handle LaTeX commands that matplotlib's mathtext doesn't support well
    # Replace \text{...} with just the text (matplotlib doesn't support \text)
    eq = re.sub(r'\\text\{([^}]+)\}', r'\1', eq)
    
    # Unescape LaTeX commands (JSON stores \\frac as \frac)
    # This should already be done by JSON parsing, but just in case
    eq = eq.replace('\\\\', '\\')
    
    # Fix escaped percent signs - matplotlib mathtext handles \% correctly
    # But make sure we have proper escaping
    eq = eq.replace('\\%', r'\%')
    
    # Fix common issues with parentheses in function notation
    # e.g., (P/A, i, n) should be (P/A, i, n) - no special handling needed
    
    # Ensure proper spacing around operators
    # Add space around = if missing (but not inside subscripts/superscripts)
    eq = re.sub(r'([a-zA-Z0-9])=([a-zA-Z0-9])', r'\1 = \2', eq)
    
    # Fix spacing around commas in function notation like (P/A, i, n)
    # But be careful not to break subscripts/superscripts
    # This is tricky, so we'll be conservative
    
    return eq


def render_equation_to_image(equation: str, dpi: int = 150) -> BytesIO:
    """
    Render a LaTeX equation to an image using matplotlib.
    
    Args:
        equation: LaTeX equation string (without $ delimiters)
        dpi: Resolution for the image
        
    Returns:
        BytesIO object containing PNG image
    """
    # Normalize the equation to proper LaTeX format
    equation = normalize_equation(equation)
    
    # Create a figure with white background
    # Adjust figure size based on equation length - keep it reasonable
    # For longer equations, we'll scale the image later
    fig_width = min(8, max(4, len(equation) * 0.15))
    fig_height = 0.8  # Reasonable height
    fig = plt.figure(figsize=(fig_width, fig_height), facecolor='white', dpi=dpi)
    fig.patch.set_alpha(1.0)  # White background
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_facecolor('white')
    
    # Render the equation with retry logic
    rendered = False
    eq_to_render = equation
    
    # Wrap in $ delimiters if not already present
    if not (equation.startswith('$') and equation.endswith('$')):
        eq_to_render = f'${equation}$'
    
    # Try rendering with original equation
    try:
        ax.text(0.5, 0.5, eq_to_render, 
                fontsize=16,
                ha='center', 
                va='center',
                transform=ax.transAxes,
                usetex=False,  # Use mathtext, not full LaTeX
                color='black')
        rendered = True
    except Exception as e1:
        print(f"[PDF] First render attempt failed for '{equation}': {e1}")
        
        # Try fixing common issues and retry
        try:
            # Fix common LaTeX issues
            fixed_eq = equation
            
            # Remove any remaining \text{} commands
            fixed_eq = re.sub(r'\\text\{([^}]+)\}', r'\1', fixed_eq)
            
            # Ensure proper escaping of special characters
            # But preserve LaTeX commands
            fixed_eq = fixed_eq.replace('\\\\', '\\')
            
            # Try without $ delimiters first, then add them
            if not (fixed_eq.startswith('$') and fixed_eq.endswith('$')):
                fixed_eq_to_render = f'${fixed_eq}$'
            else:
                fixed_eq_to_render = fixed_eq
            
            ax.text(0.5, 0.5, fixed_eq_to_render, 
                    fontsize=16,
                    ha='center', 
                    va='center',
                    transform=ax.transAxes,
                    usetex=False,
                    color='black')
            rendered = True
            print(f"[PDF] ✓ Successfully rendered after fix: '{fixed_eq}'")
        except Exception as e2:
            print(f"[PDF] ✗ Second render attempt also failed for '{equation}': {e2}")
            import traceback
            print(f"[PDF] Traceback: {traceback.format_exc()}")
            
            # Try one more time with a simplified version
            try:
                # Strip all LaTeX commands and just render the basic math
                simple_eq = re.sub(r'\\[a-zA-Z]+\{?[^}]*\}?', '', equation)
                simple_eq = re.sub(r'[{}]', '', simple_eq)
                if simple_eq.strip():
                    simple_eq_to_render = f'${simple_eq}$'
                    ax.text(0.5, 0.5, simple_eq_to_render, 
                            fontsize=16,
                            ha='center', 
                            va='center',
                            transform=ax.transAxes,
                            usetex=False,
                            color='black')
                    rendered = True
                    print(f"[PDF] ✓ Rendered simplified version: '{simple_eq}'")
                else:
                    raise RuntimeError(f"Equation '{equation}' could not be simplified")
            except Exception as e3:
                print(f"[PDF] ✗ All render attempts failed for '{equation}'")
                # Raise the error - don't create an image with plain text
                raise RuntimeError(f"Failed to render equation '{equation}': {e3}")
    
    # Save to BytesIO
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=dpi, bbox_inches='tight', 
                pad_inches=0.2, facecolor='white', edgecolor='none')
    plt.close(fig)
    img_buffer.seek(0)
    
    return img_buffer


def extract_equations(text: str) -> List[tuple]:
    """
    Extract LaTeX equations from text.
    Handles both LaTeX format ($...$ or $$...$$) and markdown code format (`...`).
    Returns list of (start, end, equation_text) tuples.
    Skips single-character equations (like $r$, $m$) as they should be rendered as text.
    """
    equations = []
    
    # First, find all potential equation patterns
    # Match LaTeX: $...$ or $$...$$
    latex_pattern = r'\$\$?([^\$]+)\$\$?'
    for match in re.finditer(latex_pattern, text):
        start, end = match.span()
        eq_text = match.group(1).strip()
        # Skip single-character equations - they should be rendered as regular text
        if eq_text and not (len(eq_text) == 1 and eq_text.isalnum()):
            equations.append((start, end, eq_text))
    
    # Match markdown code format: `...` (but only if it looks like a formula)
    # Look for patterns like `EAR = ...`, `F = ...`, etc.
    code_pattern = r'`([^`]+)`'
    for match in re.finditer(code_pattern, text):
        start, end = match.span()
        eq_text = match.group(1).strip()
        
        # Check if it looks like a mathematical formula
        # Contains =, ^, /, *, +, -, or common math symbols
        # Also check for common formula patterns like "= ...", "^", "/", etc.
        is_formula = (
            re.search(r'[=+\-*/^()\[\]{}]', eq_text) and len(eq_text) > 2
        ) or (
            # Also match if it starts with a capital letter followed by = (like "EAR =", "F =")
            re.match(r'^[A-Z]+\s*=', eq_text)
        )
        
        if is_formula:
            # Check if this range overlaps with an existing LaTeX equation
            overlaps = False
            for (l_start, l_end, _) in equations:
                if not (end <= l_start or start >= l_end):
                    overlaps = True
                    break
            
            if not overlaps:
                equations.append((start, end, eq_text))
    
    # Sort by start position
    equations.sort(key=lambda x: x[0])
    return equations


def create_equation_flowable(eq_text: str) -> Image:
    """
    Create a ReportLab Image flowable for a LaTeX equation string.
    Keeps the width reasonable so equations sit neatly next to option labels.
    """
    print(f"[PDF] Rendering inline equation: '{eq_text}'")
    try:
        eq_img = render_equation_to_image(eq_text)
        img = Image(eq_img)
        
        # Width scaled by equation length but keep consistent minimum for readability
        target_width_inches = min(4.0, max(2.2, len(eq_text) * 0.12))
        max_width_points = target_width_inches * inch
        img_width = float(getattr(img, "imageWidth", max_width_points))
        img_height = float(getattr(img, "imageHeight", 1))
        if img_width <= 0:
            img_width = max_width_points
        aspect_ratio = img_height / img_width if img_width else 1
        draw_width = min(max_width_points, img_width)
        img.drawWidth = draw_width
        img.drawHeight = draw_width * aspect_ratio
        img.hAlign = 'LEFT'
        print(f"[PDF] ✓ Successfully created equation flowable for: '{eq_text}'")
        return img
    except Exception as e:
        print(f"[PDF] ✗ Failed to create equation flowable for '{eq_text}': {e}")
        import traceback
        print(f"[PDF] Traceback: {traceback.format_exc()}")
        # Re-raise so the caller can handle it
        raise


def build_flowables_for_text(text: str, paragraph_style: ParagraphStyle) -> List[Any]:
    """
    Build flowables for a text block that may contain equations.
    Returns a list of Paragraph/Image objects that respect the provided style.
    """
    flowables: List[Any] = []
    equations = extract_equations(text)
    
    if not equations:
        flowables.append(Paragraph(text.replace('\n', '<br/>'), paragraph_style))
        return flowables
    
    last_end = 0
    for start, end, eq_text in equations:
        if start > last_end:
            before_text = text[last_end:start].replace('\n', '<br/>')
            if before_text.strip():
                flowables.append(Paragraph(before_text, paragraph_style))
        try:
            flowables.append(create_equation_flowable(eq_text))
        except Exception as exc:
            print(f"[PDF] ✗ Failed to create equation image '{eq_text}': {exc}")
            import traceback
            print(f"[PDF] Traceback: {traceback.format_exc()}")
            # Don't show the raw LaTeX - show a cleaned version
            # Remove $ delimiters and \text{} for display
            display_text = eq_text.replace('\\text{', '').replace('}', '')
            display_text = display_text.replace('\\frac', 'frac').replace('\\', '')
            fallback = f'<font face="Courier" size="10">{display_text}</font>'
            flowables.append(Paragraph(fallback, paragraph_style))
        last_end = end
    
    if last_end < len(text):
        after_text = text[last_end:].replace('\n', '<br/>')
        if after_text.strip():
            flowables.append(Paragraph(after_text, paragraph_style))
    
    return flowables


def is_equation_only_text(text: str) -> bool:
    """
    Determine if text consists solely of a single LaTeX equation.
    """
    stripped = text.strip()
    if not stripped:
        return False
    
    equations = extract_equations(stripped)
    if len(equations) != 1:
        return False
    
    start, end, _ = equations[0]
    return start == 0 and end == len(stripped)


class IndentedImage(Flowable):
    """
    Flowable wrapper that draws an image with a configurable left indent.
    Useful for displaying equation images under option labels.
    """
    def __init__(self, image_flowable: Flowable, left_indent: float, space_after: float):
        super().__init__()
        self.image = image_flowable
        self.left_indent = left_indent
        self.spaceAfter = space_after
        self._size = (0.0, 0.0)
    
    def wrap(self, availWidth, availHeight):
        usable_width = max(0.0, availWidth - self.left_indent)
        w, h = self.image.wrap(usable_width, availHeight)
        self._size = (w, h)
        return self.left_indent + w, h
    
    def draw(self):
        w, h = self._size
        self.image.drawOn(self.canv, self.left_indent, 0)




def process_text_with_equations(
    text: str,
    story: list,
    styles: Any,
    paragraph_style: ParagraphStyle = None
):
    """
    Process text and replace equations with images.
    
    Args:
        text: Text that may contain LaTeX equations
        story: List to append story elements to
        styles: ReportLab styles
        paragraph_style: Optional style override
    """
    # Debug: print the raw text first
    print(f"[PDF] Processing text: {repr(text[:200])}")
    style = paragraph_style or styles['Normal']
    flowables = build_flowables_for_text(text, style)
    print(f"[PDF] --> Flowables generated: {len(flowables)}")
    story.extend(flowables)


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
        leftIndent=30,
        spaceAfter=6,
        spaceBefore=0
    )
    
    option_label_style = ParagraphStyle(
        'OptionLabel',
        parent=option_style,
        leftIndent=option_style.leftIndent,
        spaceBefore=0,
        spaceAfter=0
    )
    
    metadata_style = ParagraphStyle(
        'Metadata',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#555555'),
        spaceAfter=4,
        leftIndent=20
    )
    
    # Add title
    story.append(Paragraph(exam_title, title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Add instructions
    instructions = """
    <b>Instructions:</b><br/>
    - Please answer all questions<br/>
    - Choose the best answer for each question<br/>
    - Mark your answers clearly<br/>
    """
    story.append(Paragraph(instructions, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Add each MCQ
    for i, mcq in enumerate(mcqs, 1):
        print(f"\n[PDF] Processing MCQ {i}")
        print(f"[PDF] Question: {repr(mcq.get('question', '')[:100])}")
        print(f"[PDF] Options: {list(mcq.get('options', {}).keys())}")
        
        metadata_bits = []
        difficulty = mcq.get('difficulty')
        if difficulty:
            metadata_bits.append(difficulty.title())
        topic = mcq.get('topic')
        if topic:
            metadata_bits.append(topic)
        question_type = mcq.get('question_type')
        if question_type:
            metadata_bits.append(question_type.title())
        
        if metadata_bits:
            story.append(Paragraph(" | ".join(metadata_bits), metadata_style))
        
        # Question number and text
        question_text = f"<b>Question {i}:</b> {mcq.get('question', '')}"
        process_text_with_equations(question_text, story, styles, question_style)
        story.append(Spacer(1, 0.1*inch))
        
        # Options
        options = mcq.get('options', {})
        for option_key in ['A', 'B', 'C', 'D']:
            if option_key not in options:
                continue
            
            option_value = options[option_key]
            print(f"[PDF] Option {option_key}: {repr(option_value[:100])}")
            
            if is_equation_only_text(option_value):
                eq_text = extract_equations(option_value.strip())[0][2]
                eq_flowable = create_equation_flowable(eq_text)
                label_para = Paragraph(f"<b>{option_key}.</b>", option_label_style)
                story.append(label_para)
                story.append(
                    IndentedImage(
                        image_flowable=eq_flowable,
                        left_indent=option_style.leftIndent + 10,
                        space_after=option_style.spaceAfter
                    )
                )
            else:
                option_text = f"<b>{option_key}.</b> {option_value}"
                process_text_with_equations(option_text, story, styles, option_style)
        
        story.append(Spacer(1, 0.2*inch))
        
        # Add page break every 3 questions (optional)
        if i % 3 == 0 and i < len(mcqs):
            story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

