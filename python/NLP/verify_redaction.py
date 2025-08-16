#!/usr/bin/env python3
"""
Verify what was redacted in the output PDF
"""

import sys
from pathlib import Path
import PyPDF2

def compare_pdfs():
    """Compare original and redacted PDF content"""
    
    original_file = "sample_document.pdf"
    redacted_file = "redact_sample_document.pdf"
    
    if not Path(original_file).exists():
        print(f"❌ {original_file} not found")
        return
    
    if not Path(redacted_file).exists():
        print(f"❌ {redacted_file} not found")
        return
    
    # Extract original text
    print("📄 Original Document Content:")
    print("=" * 50)
    with open(original_file, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        original_text = ""
        for page in reader.pages:
            original_text += page.extract_text()
    
    print(original_text)
    
    # Extract redacted text
    print("\n🔒 Redacted Document Content:")
    print("=" * 50)
    with open(redacted_file, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        redacted_text = ""
        for page in reader.pages:
            redacted_text += page.extract_text()
    
    print(redacted_text)
    
    # Show what was redacted
    print("\n🎯 Redaction Summary:")
    print("=" * 30)
    
    redaction_tokens = [
        "[NAME_REDACTED]",
        "[PHONE_REDACTED]", 
        "[EMAIL_REDACTED]",
        "[ADDRESS_REDACTED]",
        "[CREDIT_CARD_REDACTED]",
        "[USPERSONALIDENTIFICATIONNUMBER_REDACTED]"
    ]
    
    for token in redaction_tokens:
        count = redacted_text.count(token)
        if count > 0:
            print(f"✅ {token}: {count} occurrences")
    
    print(f"\n📊 Statistics:")
    print(f"• Original length: {len(original_text)} characters")
    print(f"• Redacted length: {len(redacted_text)} characters")
    print(f"• Size change: {len(redacted_text) - len(original_text):+d} characters")

if __name__ == "__main__":
    compare_pdfs()
