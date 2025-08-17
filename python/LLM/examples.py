#!/usr/bin/env python3
"""
Direct usage examples for Enhanced PDF Processor
Shows different ways to use the format-preserving PDF redaction
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment and add path
load_dotenv()
sys.path.append(str(Path(__file__).parent))

from enhanced_pdf_processor import EnhancedPdfProcessor, process_pdf_enhanced
from llm_config import LLMConfig

def example_1_basic_usage():
    """Example 1: Basic PDF redaction with default settings"""
    
    print("="*60)
    print("EXAMPLE 1: Basic PDF Redaction")
    print("="*60)
    
    # Simple one-line usage
    input_pdf = "../../docs/1.pdf"
    
    try:
        result = process_pdf_enhanced(input_pdf)
        
        print(f"✅ Processing completed!")
        print(f"📄 Input: {input_pdf}")
        print(f"📄 Output: {result['file_path']}")
        print(f"🔍 Entities found: {result['entities_found']}")
        print(f"⚠️  Risk level: {result['risk_level']}")
        print(f"💰 Cost: ${result['processing_cost']:.6f}")
        print(f"📊 Pages: {result['page_count']}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def example_2_custom_output():
    """Example 2: Specify custom output path"""
    
    print("="*60)
    print("EXAMPLE 2: Custom Output Path")
    print("="*60)
    
    input_pdf = "../../docs/1.pdf"
    output_pdf = "../../docs/my_custom_redacted.pdf"
    
    try:
        result = process_pdf_enhanced(input_pdf, output_pdf)
        
        print(f"✅ Custom output created!")
        print(f"📄 Output saved to: {result['file_path']}")
        print(f"📊 Document stats: {result['word_count']} words, {result['character_count']} characters")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def example_3_custom_configuration():
    """Example 3: Use custom LLM configuration"""
    
    print("="*60)
    print("EXAMPLE 3: Custom Configuration")
    print("="*60)
    
    # Create custom configuration
    config = LLMConfig()
    config.confidence_threshold = 0.9  # Higher confidence required
    config.pii_categories = ['names', 'ssn', 'credit_cards']  # Only high-risk categories
    
    input_pdf = "../../docs/1.pdf"
    output_pdf = "../../docs/high_confidence_redacted.pdf"
    
    try:
        result = process_pdf_enhanced(input_pdf, output_pdf, config)
        
        print(f"✅ High-confidence redaction completed!")
        print(f"📄 Output: {result['file_path']}")
        print(f"🎯 Confidence threshold: {config.confidence_threshold}")
        print(f"🏷️  Categories: {', '.join(config.pii_categories)}")
        print(f"🔍 Entities found: {result['entities_found']}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def example_4_processor_class():
    """Example 4: Use the processor class directly for advanced control"""
    
    print("="*60)
    print("EXAMPLE 4: Advanced Processor Class Usage")
    print("="*60)
    
    # Create processor instance
    config = LLMConfig()
    processor = EnhancedPdfProcessor(config)
    
    input_pdf = "../../docs/1.pdf"
    
    try:
        # First, get cost estimate
        print("Getting cost estimate...")
        estimate = processor.get_cost_estimate(input_pdf)
        
        print(f"📊 Cost Estimate:")
        print(f"   - Text length: {estimate['text_length']:,} characters")
        print(f"   - Estimated tokens: {estimate['estimated_total_tokens']:,}")
        print(f"   - Estimated cost: ${estimate['estimated_cost_usd']:.6f}")
        print(f"   - API calls needed: {estimate['api_calls_needed']}")
        print()
        
        # Ask for confirmation
        proceed = input("Proceed with processing? (y/N): ").strip().lower()
        if proceed not in ['y', 'yes']:
            print("❌ Processing cancelled")
            return
        
        # Process the PDF
        print("Processing PDF...")
        result = processor.process_pdf(input_pdf)
        
        print(f"✅ Advanced processing completed!")
        print(f"📄 Output: {result['file_path']}")
        print(f"💰 Actual cost: ${result['processing_cost']:.6f}")
        print(f"🔍 Entities found: {result['entities_found']}")
        print(f"⚠️  Risk level: {result['risk_level']}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def example_5_batch_processing():
    """Example 5: Process multiple PDFs"""
    
    print("="*60)
    print("EXAMPLE 5: Batch Processing")
    print("="*60)
    
    # Find all PDFs in docs directory
    docs_dir = Path("../../docs")
    pdf_files = list(docs_dir.glob("*.pdf"))
    
    # Filter out already redacted files
    input_pdfs = [f for f in pdf_files if 'redacted' not in f.name.lower()]
    
    print(f"Found {len(input_pdfs)} PDF files to process:")
    for pdf in input_pdfs:
        print(f"  - {pdf.name}")
    print()
    
    if not input_pdfs:
        print("❌ No PDF files found to process")
        return
    
    proceed = input(f"Process all {len(input_pdfs)} files? (y/N): ").strip().lower()
    if proceed not in ['y', 'yes']:
        print("❌ Batch processing cancelled")
        return
    
    # Process each PDF
    total_cost = 0
    total_entities = 0
    
    for pdf_file in input_pdfs:
        try:
            print(f"\n📄 Processing: {pdf_file.name}")
            
            output_path = str(pdf_file.parent / f"{pdf_file.stem}_batch_redacted{pdf_file.suffix}")
            result = process_pdf_enhanced(str(pdf_file), output_path)
            
            total_cost += result['processing_cost']
            total_entities += result['entities_found']
            
            print(f"   ✅ Success: {result['entities_found']} entities, ${result['processing_cost']:.6f}")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print(f"\n📊 Batch Processing Summary:")
    print(f"   - Files processed: {len(input_pdfs)}")
    print(f"   - Total entities found: {total_entities}")
    print(f"   - Total cost: ${total_cost:.6f}")
    print(f"   - Average cost per file: ${total_cost/len(input_pdfs):.6f}")

def show_comparison():
    """Show comparison between old and new approaches"""
    
    print("="*60)
    print("COMPARISON: Old vs New PDF Processing")
    print("="*60)
    
    docs_dir = Path("../../docs")
    
    # Check for comparison files
    old_file = docs_dir / "1_redacted.pdf"
    new_file = docs_dir / "1_enhanced_redacted.pdf"
    
    if old_file.exists() and new_file.exists():
        old_size = old_file.stat().st_size
        new_size = new_file.stat().st_size
        
        print(f"📄 Old approach (reportlab recreation):")
        print(f"   - File: {old_file.name}")
        print(f"   - Size: {old_size:,} bytes")
        print(f"   - Method: Complete PDF recreation")
        print(f"   - Formatting: ❌ Lost original formatting")
        print()
        
        print(f"📄 New approach (format-preserving):")
        print(f"   - File: {new_file.name}")
        print(f"   - Size: {new_size:,} bytes")
        print(f"   - Method: In-place redaction annotations")
        print(f"   - Formatting: ✅ Preserves original formatting")
        print()
        
        print(f"📊 Size difference: {new_size - old_size:+,} bytes")
        print(f"   The enhanced version is larger because it preserves")
        print(f"   the original PDF structure, fonts, and formatting!")
        
    else:
        print("❌ Comparison files not found. Run basic examples first.")

def main():
    """Main demonstration function"""
    
    print("GPT-4o-mini Enhanced PDF Processor")
    print("Format-Preserving Document Redaction")
    print()
    
    print("Available examples:")
    print("1. Basic usage (simple one-liner)")
    print("2. Custom output path")
    print("3. Custom configuration (confidence, categories)")
    print("4. Advanced processor class usage")
    print("5. Batch processing multiple PDFs")
    print("6. Show comparison (old vs new)")
    print("0. Run all examples")
    print()
    
    try:
        choice = input("Select example (0-6): ").strip()
        
        if choice == "0":
            example_1_basic_usage()
            example_2_custom_output()
            example_3_custom_configuration()
            show_comparison()
        elif choice == "1":
            example_1_basic_usage()
        elif choice == "2":
            example_2_custom_output()
        elif choice == "3":
            example_3_custom_configuration()
        elif choice == "4":
            example_4_processor_class()
        elif choice == "5":
            example_5_batch_processing()
        elif choice == "6":
            show_comparison()
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
