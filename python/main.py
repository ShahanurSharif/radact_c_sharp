"""
Radact - Document Redaction Tool (Python Version)

A Python implementation that reads DOCX and PDF files and redacts sensitive information 
such as names, emails, phone numbers, and other personally identifiable information (PII).
"""

import os
import re
from abc import ABC, abstractmethod
from typing import List
from pathlib import Path


def main():
    """Main program entry point"""
    try:
        processor_factory = DocumentProcessorFactory()
        processor_factory.process_document("../docs/1.docx")
        processor_factory.process_document("../docs/1.pdf")
    except Exception as e:
        print(f"Error: {e}")


class DocumentProcessorFactory:
    """Factory class to create appropriate document processors"""
    
    def __init__(self):
        self.redactor = DocumentRedactor()
    
    def process_document(self, input_file_path: str):
        """Process a document based on its file extension"""
        extension = Path(input_file_path).suffix.lower()
        
        if extension == ".docx":
            from docx_processor import DocxProcessor
            processor = DocxProcessor(self.redactor)
        elif extension == ".pdf":
            from pdf_processor import PdfProcessor
            processor = PdfProcessor(self.redactor)
        else:
            raise NotSupportedError(f"File format {extension} is not supported")
        
        processor.process(input_file_path)


class IDocumentProcessor(ABC):
    """Common interface for all document processors"""
    
    @abstractmethod
    def process(self, input_file_path: str):
        pass


class CommonProcessor(IDocumentProcessor):
    """Common base functionality shared by all processors"""
    
    def __init__(self, redactor):
        self.redactor = redactor
    
    def process(self, input_file_path: str):
        """Common workflow for all document types"""
        print(f"\nProcessing: {input_file_path}")
        
        # Read document content
        original_content = self.read_content(input_file_path)
        print("Document content loaded successfully!")
        print(f"Content length: {len(original_content)} characters")
        print("\n--- Original Document Content ---")
        print(original_content)
        
        # Redact sensitive information
        redacted_content = self.redactor.redact_sensitive_information(original_content)
        
        # Save redacted content
        output_path = self.generate_output_path(input_file_path)
        self.save_content(input_file_path, output_path, redacted_content)
        
        print("\n--- Redacted Document Content ---")
        print(redacted_content)
        print(f"\nRedacted content saved to: {output_path}")
    
    @abstractmethod
    def read_content(self, file_path: str) -> str:
        pass
    
    @abstractmethod
    def generate_output_path(self, input_file_path: str) -> str:
        pass
    
    @abstractmethod
    def save_content(self, input_file_path: str, output_path: str, redacted_content: str):
        pass


class DocumentRedactor:
    """Handles redacting sensitive information (shared across all file types)"""
    
    def __init__(self):
        self.redaction_rules = self._initialize_redaction_rules()
    
    def redact_sensitive_information(self, content: str) -> str:
        """Apply all redaction rules to the content"""
        redacted = content
        
        for rule in self.redaction_rules:
            redacted = re.sub(rule.pattern, rule.replacement, redacted, flags=rule.flags)
        
        return redacted
    
    def _initialize_redaction_rules(self) -> List['RedactionRule']:
        """Initialize all redaction rules"""
        return [
            RedactionRule(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),
            RedactionRule(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b', '[PHONE_REDACTED]'),
            RedactionRule(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),
            RedactionRule(r'\b(?:\d{4}[-\s]?){3}\d{4}\b', '[CREDIT_CARD_REDACTED]'),
            RedactionRule(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '[DATE_REDACTED]'),
            RedactionRule(r'\b(?:password|pwd|pass)\s*[:=]\s*\S+', '[PASSWORD_REDACTED]', re.IGNORECASE),
            RedactionRule(r'\b(?:api[_-]?key|apikey)\s*[:=]\s*\S+', '[API_KEY_REDACTED]', re.IGNORECASE),
            RedactionRule(r'\b(?:token|auth[_-]?token)\s*[:=]\s*\S+', '[TOKEN_REDACTED]', re.IGNORECASE),
            RedactionRule(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP_ADDRESS_REDACTED]'),
            RedactionRule(r'\b[A-Z][a-z]+ [A-Z][a-z]+\s*\([^)]*\)', '[NAME_REDACTED] (TITLE_REDACTED)'),
            RedactionRule(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME_REDACTED]')
        ]


class RedactionRule:
    """Represents a redaction rule (shared across all file types)"""
    
    def __init__(self, pattern: str, replacement: str, flags: int = 0):
        self.pattern = pattern
        self.replacement = replacement
        self.flags = flags


class NotSupportedError(Exception):
    """Exception raised when file format is not supported"""
    pass


if __name__ == "__main__":
    main()
