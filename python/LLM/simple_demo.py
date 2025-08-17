#!/usr/bin/env python3
"""
Simple demonstration of Enhanced PDF Processor
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.append(str(Path(__file__).parent))

from enhanced_pdf_processor import process_pdf_enhanced, EnhancedPdfProcessor
from llm_config import LLMConfig

def simple_demo():
    print("🚀 Enhanced PDF Processor - Direct Usage Demo")
    print("=" * 50)
    
    # Method 1: One-liner (simplest)
    print("\n📄 Method 1: Simple One-liner")
    print("-" * 30)
    
    input_pdf = "../../docs/1.pdf"
    print(f"Processing: {input_pdf}")
    
    try:
        result = process_pdf_enhanced(input_pdf)
        
        print(f"✅ SUCCESS!")
        print(f"   📄 Output: {result['file_path']}")
        print(f"   🔍 Found: {result['entities_found']} PII entities")
        print(f"   ⚠️  Risk: {result['risk_level']}")
        print(f"   💰 Cost: ${result['processing_cost']:.6f}")
        print(f"   📊 Stats: {result['page_count']} pages, {result['word_count']} words")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Method 2: Custom output path
    print("\n📄 Method 2: Custom Output")
    print("-" * 30)
    
    try:
        custom_output = "../../docs/my_redacted_document.pdf"
        result = process_pdf_enhanced(input_pdf, custom_output)
        print(f"✅ Custom output created: {result['file_path']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Method 3: Custom configuration
    print("\n📄 Method 3: Custom Configuration")
    print("-" * 30)
    
    try:
        # Create custom config
        config = LLMConfig()
        config.confidence_threshold = 0.9  # Higher confidence
        config.pii_categories = ['names', 'ssn', 'credit_cards']  # High-risk only
        
        result = process_pdf_enhanced(input_pdf, None, config)
        print(f"✅ High-confidence processing:")
        print(f"   📄 Output: {result['file_path']}")
        print(f"   🎯 Confidence: {config.confidence_threshold}")
        print(f"   🏷️  Categories: {', '.join(config.pii_categories)}")
        print(f"   🔍 Found: {result['entities_found']} entities")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Method 4: Advanced usage with cost estimation
    print("\n📄 Method 4: Advanced with Cost Estimation")
    print("-" * 30)
    
    try:
        processor = EnhancedPdfProcessor()
        
        # Get cost estimate first
        estimate = processor.get_cost_estimate(input_pdf)
        print(f"💰 Cost Estimate:")
        print(f"   - Estimated cost: ${estimate['estimated_cost_usd']:.6f}")
        print(f"   - Text length: {estimate['text_length']:,} chars")
        print(f"   - API calls: {estimate['api_calls_needed']}")
        
        if estimate['estimated_cost_usd'] < 0.01:  # Less than 1 cent
            print("✅ Cost acceptable, processing...")
            result = processor.process_pdf(input_pdf)
            print(f"   📄 Result: {result['file_path']}")
            print(f"   💰 Actual cost: ${result['processing_cost']:.6f}")
        else:
            print("⚠️  Cost too high, skipping processing")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    simple_demo()
