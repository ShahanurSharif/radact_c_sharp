#!/usr/bin/env python3
"""
Test the enhanced PII detection patterns
"""

import sys
from pathlib import Path

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from demo_redactor import DemoAzureAIRedactor

def test_enhanced_patterns():
    """Test the enhanced PII detection patterns"""
    
    # Sample text with various formatting
    test_text = """
    Employee Record:
    Name: Sarah Johnson
    Phone: (555) 123-4567
    Alternative contact: 555-987-6543
    Email: sarah.johnson@company.com
    SSN: 123-45-6789
    Credit Card: 4532-1234-5678-9012
    Address: 456 Oak Street, Boston, MA
    
    Emergency Contact Information:
    Contact: Michael Johnson (spouse)
    Phone: (617) 555-0123
    Email: m.johnson@email.com
    
    From: John Doe, HR Manager
    """
    
    print("🧪 Testing Enhanced PII Detection Patterns")
    print("=" * 50)
    
    redactor = DemoAzureAIRedactor()
    
    print("📄 Sample Text:")
    print(test_text)
    print("\n🔍 Detecting PII entities...")
    
    entities = redactor.detect_pii_entities(test_text)
    
    print(f"\n📊 Found {len(entities)} PII entities:")
    
    # Group by category
    by_category = {}
    for entity in entities:
        if entity.category not in by_category:
            by_category[entity.category] = []
        by_category[entity.category].append(entity)
    
    for category, entity_list in by_category.items():
        print(f"\n{category}:")
        for entity in entity_list:
            confidence_emoji = "🎯" if entity.confidence_score >= 0.95 else "✅"
            print(f"  {confidence_emoji} '{entity.text}' (confidence: {entity.confidence_score:.2f})")
    
    print("\n🔒 Testing Redaction...")
    result = redactor.redact_text(test_text)
    
    print("📄 Redacted Text:")
    print("-" * 30)
    print(result.redacted_text)
    print("-" * 30)
    
    print(f"\n📊 Redaction Summary:")
    print(f"  • Original length: {len(result.original_text)} characters")
    print(f"  • Redacted length: {len(result.redacted_text)} characters") 
    print(f"  • Entities detected: {len(result.entities_found)}")
    print(f"  • Redactions applied: {result.redaction_count}")
    
    return len(entities) > 0

if __name__ == "__main__":
    success = test_enhanced_patterns()
    if success:
        print("\n✅ Enhanced detection patterns working!")
        print("\n💡 Now test with your document:")
        print("python main.py file sample_document.pdf --output redact_sample_document.pdf")
    else:
        print("\n❌ Pattern testing failed")
