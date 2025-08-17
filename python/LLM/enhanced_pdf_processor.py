"""
Enhanced PDF processor that preserves original formatting
Uses PyMuPDF to redact PII while maintaining document structure
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import structlog

from gpt4o_redactor import GPT4oMiniRedactor, RedactionResult, PIIEntity
from llm_config import LLMConfig

logger = structlog.get_logger(__name__)

class EnhancedPdfProcessor:
    """Advanced PDF processor that preserves formatting during redaction"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize enhanced PDF processor
        
        Args:
            config: LLM configuration for redaction
        """
        self.config = config or LLMConfig()
        self.redactor = GPT4oMiniRedactor(self.config)
        
        logger.info("Enhanced PDF processor initialized with formatting preservation")
    
    def _find_text_locations(self, doc: fitz.Document, entities: List[PIIEntity]) -> List[Dict]:
        """
        Find the exact locations of PII text in the PDF
        
        Args:
            doc: PDF document
            entities: List of PII entities to locate
            
        Returns:
            List of text locations with coordinates
        """
        text_locations = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get all text instances with their locations
            text_dict = page.get_text("dict")
            
            for entity in entities:
                search_text = entity.text.strip()
                
                # Search for the text on this page
                text_instances = page.search_for(search_text)
                
                for rect in text_instances:
                    text_locations.append({
                        'page_num': page_num,
                        'rect': rect,
                        'text': search_text,
                        'entity': entity,
                        'category': entity.category
                    })
                    
                    logger.debug("Found text location", 
                               page=page_num, 
                               text=search_text,
                               category=entity.category,
                               coords=f"({rect.x0}, {rect.y0}, {rect.x1}, {rect.y1})")
        
        return text_locations
    
    def _apply_redaction_rectangles(self, doc: fitz.Document, text_locations: List[Dict]):
        """
        Apply text replacements to show [REDACTED] markers instead of black boxes
        
        Args:
            doc: PDF document
            text_locations: List of text locations to redact
        """
        
        for location in text_locations:
            page_num = location['page_num']
            rect = location['rect']
            category = location['category']
            original_text = location['text']
            
            page = doc[page_num]
            
            # Create replacement text based on category
            replacement_text = f"[{category.upper()}_REDACTED]"
            
            try:
                # Get text instances to replace
                text_instances = page.search_for(original_text)
                
                for instance_rect in text_instances:
                    # Add white rectangle to cover original text
                    white_rect = page.new_shape()
                    white_rect.draw_rect(instance_rect)
                    white_rect.finish(fill=(1, 1, 1), color=(1, 1, 1))  # White fill and border
                    white_rect.commit()
                    
                    # Add replacement text
                    page.insert_text((instance_rect.x0, instance_rect.y1 - 2), 
                                    replacement_text, 
                                    fontsize=10, 
                                    color=(0, 0, 0))  # Black text
                
                logger.debug("Applied text replacement", 
                            page=page_num, 
                            category=category,
                            original_text=original_text,
                            replacement=replacement_text,
                            rect_coords=f"({rect.x0}, {rect.y0}, {rect.x1}, {rect.y1})")
                            
            except Exception as e:
                logger.warning("Failed to replace text, using redaction annotation", 
                              page=page_num, category=category, error=str(e))
                
                # Fallback to redaction annotation
                redact_annot = page.add_redact_annot(rect)
                redact_annot.set_info(content=replacement_text)
        
        # Apply any remaining redactions
        for page_num in range(len(doc)):
            page = doc[page_num]
            try:
                page.apply_redactions()
                logger.info("Applied redactions to page", page_num=page_num)
            except Exception as e:
                logger.debug("No redactions to apply on page", page_num=page_num)
    
    def _get_document_info(self, doc: fitz.Document, original_text: str, 
                          redaction_result: RedactionResult) -> Dict:
        """Get document information"""
        
        page_count = len(doc)
        word_count = len(original_text.split())
        char_count = len(original_text)
        
        # Assess risk level
        risk_level = self._assess_risk_level(
            redaction_result.total_entities,
            redaction_result.confidence_scores
        )
        
        return {
            'file_type': 'pdf',
            'page_count': page_count,
            'word_count': word_count,
            'character_count': char_count,
            'processing_cost': redaction_result.processing_cost,
            'entities_found': redaction_result.total_entities,
            'risk_level': risk_level
        }
    
    def _assess_risk_level(self, entities_count: int, confidence_scores: Dict[str, float]) -> str:
        """Assess document risk level based on PII findings"""
        
        if entities_count == 0:
            return "LOW"
        
        # High-risk categories
        high_risk_categories = ['ssn', 'credit_cards']
        has_high_risk = any(cat in confidence_scores for cat in high_risk_categories)
        
        # Risk assessment logic
        if has_high_risk or entities_count >= 10:
            return "HIGH"
        elif entities_count >= 5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def process_pdf(self, input_path: str, output_path: Optional[str] = None) -> Dict:
        """
        Process PDF with format-preserving redaction
        
        Args:
            input_path: Path to input PDF
            output_path: Optional output path
            
        Returns:
            Processing information dictionary
        """
        logger.info("Processing PDF with format preservation", input_path=input_path)
        
        if output_path is None:
            path = Path(input_path)
            output_path = str(path.parent / f"{path.stem}_redacted_enhanced{path.suffix}")
        
        try:
            # Open the PDF
            doc = fitz.open(input_path)
            page_count = len(doc)
            
            # Extract text for LLM analysis
            full_text = ""
            for page_num in range(page_count):
                page = doc[page_num]
                text = page.get_text()
                full_text += text + "\n\n"
            
            logger.info("Extracted text from PDF", 
                       pages=page_count, 
                       text_length=len(full_text))
            
            # Perform LLM-based PII detection
            redaction_result = self.redactor.redact_text(full_text)
            
            if redaction_result.total_entities == 0:
                logger.info("No PII found, copying original document")
                doc.save(output_path)
                doc.close()
                
                # Calculate document stats
                word_count = len(full_text.split())
                char_count = len(full_text)
                
                return {
                    'file_path': output_path,
                    'file_type': 'pdf',
                    'page_count': page_count,
                    'word_count': word_count,
                    'character_count': char_count,
                    'processing_cost': redaction_result.processing_cost,
                    'entities_found': redaction_result.total_entities,
                    'risk_level': 'LOW'
                }
            
            # Find exact locations of PII text in PDF
            text_locations = self._find_text_locations(doc, redaction_result.entities_found)
            
            logger.info("Located PII in document", 
                       total_locations=len(text_locations),
                       entities=redaction_result.total_entities)
            
            # Apply redaction rectangles while preserving formatting
            self._apply_redaction_rectangles(doc, text_locations)
            
            # Calculate document stats before closing
            word_count = len(full_text.split())
            char_count = len(full_text)
            
            # Assess risk level
            risk_level = self._assess_risk_level(
                redaction_result.total_entities,
                redaction_result.confidence_scores
            )
            
            # Save the redacted PDF
            doc.save(output_path)
            doc.close()
            
            # Prepare result
            result_info = {
                'file_path': output_path,
                'file_type': 'pdf',
                'page_count': page_count,
                'word_count': word_count,
                'character_count': char_count,
                'processing_cost': redaction_result.processing_cost,
                'entities_found': redaction_result.total_entities,
                'risk_level': risk_level
            }
            
            logger.info("PDF redaction completed with format preservation",
                       output_path=output_path,
                       entities_redacted=redaction_result.total_entities,
                       cost=redaction_result.processing_cost,
                       risk_level=risk_level)
            
            return result_info
            
        except Exception as e:
            logger.error("PDF processing failed", input_path=input_path, error=str(e))
            raise
    
    def get_cost_estimate(self, file_path: str) -> Dict:
        """
        Get cost estimate for PDF processing
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Cost estimation details
        """
        try:
            doc = fitz.open(file_path)
            
            # Extract text
            full_text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                full_text += text + "\n\n"
            
            doc.close()
            
            # Get LLM cost estimate
            estimate = self.redactor.get_cost_estimate(full_text)
            
            # Add document info
            estimate.update({
                'file_path': file_path,
                'file_type': '.pdf',
                'text_length': len(full_text),
                'word_count': len(full_text.split())
            })
            
            return estimate
            
        except Exception as e:
            logger.error("Failed to estimate PDF cost", file_path=file_path, error=str(e))
            return {'error': str(e)}

# Create a simple function for backward compatibility
def process_pdf_enhanced(input_path: str, output_path: Optional[str] = None, 
                        config: Optional[LLMConfig] = None) -> Dict:
    """
    Process PDF with enhanced formatting preservation
    
    Args:
        input_path: Path to input PDF
        output_path: Optional output path
        config: LLM configuration
        
    Returns:
        Processing information dictionary
    """
    processor = EnhancedPdfProcessor(config)
    return processor.process_pdf(input_path, output_path)
