#!/usr/bin/env python3
"""
Debug the PII detection to see what's being missed
"""

import sys
from pathlib import Path
import PyPDF2

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from azure_config import AzureConfig
from azure_ai_redactor import AzureAIRedactor
from demo_redactor import DemoAzureAIRedactor

def debug_pdf_content():
    """Extract and debug PDF content"""
    
    pdf_path = "sample_document.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ {pdf_path} not found")
        return
    
    # Extract text from PDF
    print("📄 Extracting text from PDF...")
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        full_text = ""
        
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            full_text += page_text + "\n"
            print(f"Page {page_num + 1} text:")
            print("-" * 40)
            print(repr(page_text))  # Show exact characters including formatting
            print("-" * 40)
    
    print(f"\n📊 Full extracted text ({len(full_text)} chars):")
    print("=" * 50)
    print(full_text)
    print("=" * 50)
    
    # Test with Azure AI (if configured)
    try:
        config = AzureConfig()
        if config.validate_configuration():
            print("\n🤖 Testing with Azure Text Analytics...")
            redactor = AzureAIRedactor(config)
            entities = redactor.detect_pii_entities(full_text)
            
            print(f"Azure found {len(entities)} entities:")
            for entity in entities:
                print(f"  - {entity.category}: '{entity.text}' (confidence: {entity.confidence_score:.2f})")
        else:
            print("\n⚠️  Azure not configured, using fallback...")
            
    except Exception as e:
        print(f"\n⚠️  Azure failed: {e}")
    
    # Test with demo patterns
    print("\n🔧 Testing with enhanced demo patterns...")
    demo_redactor = DemoAzureAIRedactor()
    demo_entities = demo_redactor.detect_pii_entities(full_text)
    
    print(f"Demo patterns found {len(demo_entities)} entities:")
    for entity in demo_entities:
        print(f"  - {entity.category}: '{entity.text}' (confidence: {entity.confidence_score:.2f})")
    
    # Specific pattern testing
    print("\n🎯 Testing specific problematic patterns...")
    
    import re
    
    # Test phone patterns
    phone_patterns = [
        re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),
        re.compile(r'\(\d{3}\)\s?\d{3}-?\d{4}'),  # (555) 123-4567 format
        re.compile(r'(?i)(?:phone|tel|mobile|cell)\s*:?\s*(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', re.IGNORECASE),
    ]
    
    print("Phone pattern matches:")
    for i, pattern in enumerate(phone_patterns):
        matches = pattern.findall(full_text)
        if matches:
            print(f"  Pattern {i+1}: {matches}")
        else:
            print(f"  Pattern {i+1}: No matches")
    
    # Test SSN patterns
    ssn_patterns = [
        re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        re.compile(r'(?i)(?:ssn|social\s*security)\s*:?\s*(\d{3}[-\s]?\d{2}[-\s]?\d{4})', re.IGNORECASE),
    ]
    
    print("SSN pattern matches:")
    for i, pattern in enumerate(ssn_patterns):
        matches = pattern.findall(full_text)
        if matches:
            print(f"  Pattern {i+1}: {matches}")
        else:
            print(f"  Pattern {i+1}: No matches")

if __name__ == "__main__":
    debug_pdf_content()
