"""
PDF document processor for Python version
"""

import PyPDF2
import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from main import CommonProcessor


class PdfProcessor(CommonProcessor):
    """PDF document processor"""
    
    def __init__(self, redactor):
        super().__init__(redactor)
    
    def read_content(self, file_path: str) -> str:
        """Read content from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                content = []
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    # Clean up the extracted text
                    cleaned_text = self._clean_extracted_text(text)
                    content.append(cleaned_text)
                
                return '\n'.join(content)
                
        except Exception as e:
            raise Exception(f"Error reading PDF file: {e}")
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean up extracted PDF text"""
        if not text:
            return text
        
        # Replace multiple tabs and spaces with single space
        text = re.sub(r'\t+', ' ', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Fix common character encoding issues
        text = text.replace('ﬁ', 'fi')
        text = text.replace('�', 'fi')
        text = text.replace(''', "'")  # Fix smart quote to regular quote
        
        # Clean up line breaks and spacing
        text = re.sub(r'\r\n|\r|\n', '\n', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def generate_output_path(self, input_file_path: str) -> str:
        """Generate output path for redacted PDF file"""
        file_path = Path(input_file_path)
        file_name = file_path.stem
        output_dir = Path("../docs")
        return str(output_dir / f"redact_{file_name}.pdf")
    
    def save_content(self, input_file_path: str, output_path: str, redacted_content: str):
        """Save redacted content as PDF file"""
        # First, always save as text file (guaranteed to work)
        text_path = output_path.replace(".pdf", "_redacted.txt")
        try:
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(redacted_content)
            print(f"✅ Redacted content saved as text: {text_path}")
        except Exception as e:
            print(f"❌ Error saving text file: {e}")
        
        # Then try to create PDF
        try:
            self._create_simple_pdf(output_path, redacted_content)
            
            # Verify the PDF was created with content
            if Path(output_path).exists() and Path(output_path).stat().st_size > 0:
                print(f"✅ PDF successfully created: {output_path}")
                print(f"📄 PDF file size: {Path(output_path).stat().st_size} bytes")
            else:
                print(f"⚠️ PDF creation failed - file is empty or not created")
                print(f"💾 Using text file instead: {text_path}")
                
        except Exception as e:
            print(f"❌ PDF creation error: {e}")
            print(f"💾 Content available in text file: {text_path}")
    
    def _create_simple_pdf(self, output_path: str, content: str):
        """Create PDF using ReportLab"""
        try:
            # Remove existing file
            if Path(output_path).exists():
                Path(output_path).unlink()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # Center alignment
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=6
            )
            
            # Build content
            story = []
            
            # Add title
            story.append(Paragraph("REDACTED DOCUMENT", title_style))
            story.append(Spacer(1, 12))
            
            # Add content
            lines = content.split('\n')
            for line in lines:
                if line.strip():
                    # Escape special characters for ReportLab
                    escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(escaped_line, normal_style))
                else:
                    story.append(Spacer(1, 6))
            
            # Build PDF
            doc.build(story)
            
            print(f"✅ PDF creation completed. Checking file size...")
            
        except Exception as e:
            print(f"❌ Detailed PDF creation error: {e}")
            raise
