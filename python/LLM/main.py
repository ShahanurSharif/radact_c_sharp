#!/usr/bin/env python3
"""
Simple LLM-based Document Redaction Tool
Usage: python main.py <input_file> --output=<output_file>
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from enhanced_pdf_processor import process_pdf_enhanced
from document_processors import create_processor, DocxProcessor
from llm_config import LLMConfig

def main():
    parser = argparse.ArgumentParser(
        description='LLM-based Document Redaction Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py sample_document.pdf --output=redacted_sample.pdf
  python main.py docs/sample_document.docx --output=docs/redacted_sample.docx
        """
    )
    
    parser.add_argument('input_file', help='Input document file (PDF or DOCX)')
    parser.add_argument('--output', required=True, help='Output file path')
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Check file extension
    file_ext = input_path.suffix.lower()
    if file_ext not in ['.pdf', '.docx']:
        print(f"❌ Error: Unsupported file type: {file_ext}")
        print("Supported types: PDF, DOCX")
        sys.exit(1)
    
    output_path = args.output
    
    print(f"🚀 LLM Document Redaction")
    print(f"📄 Input: {args.input_file}")
    print(f"📄 Output: {output_path}")
    print()
    
    try:
        # Process based on file type
        if file_ext == '.pdf':
            print("Processing PDF with format preservation...")
            result = process_pdf_enhanced(str(input_path), output_path)
            
        elif file_ext == '.docx':
            print("Processing DOCX document...")
            config = LLMConfig()
            processor = DocxProcessor(config)
            doc_info = processor.process_document(str(input_path), output_path)
            
            # Convert to result format
            result = {
                'file_path': doc_info.file_path,
                'entities_found': doc_info.entities_found,
                'risk_level': doc_info.risk_level,
                'processing_cost': doc_info.processing_cost,
                'page_count': doc_info.page_count,
                'word_count': doc_info.word_count
            }
        
        # Display results
        print("✅ Redaction completed successfully!")
        print(f"📄 Output saved: {result['file_path']}")
        print(f"🔍 PII entities found: {result['entities_found']}")
        print(f"⚠️  Risk level: {result['risk_level']}")
        print(f"💰 Processing cost: ${result['processing_cost']:.6f}")
        print(f"📊 Document stats: {result.get('page_count', 'N/A')} pages, {result.get('word_count', 'N/A')} words")
        
        # Risk warning
        if result['risk_level'] == 'HIGH':
            print("\n⚠️  HIGH RISK: Document contained sensitive PII (SSN, credit cards, etc.)")
            print("   Handle the redacted document with appropriate security measures.")
        elif result['risk_level'] == 'MEDIUM':
            print("\n⚠️  MEDIUM RISK: Document contained moderate amounts of PII.")
        else:
            print("\n✅ LOW RISK: Minimal PII detected.")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
