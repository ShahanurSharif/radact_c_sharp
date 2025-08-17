#!/usr/bin/env python3
"""
Demo script for GPT-4o-mini redaction system
Test the LLM-based document redaction with sample text
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

def test_basic_redaction():
    """Test basic text redaction functionality"""
    
    print("="*60)
    print("GPT-4o-mini Redaction System Demo")
    print("="*60)
    print()
    
    # Sample text with various PII types
    sample_text = """
John Smith works at Acme Corporation. His contact information is as follows:
- Phone: (555) 123-4567
- Email: john.smith@email.com
- Address: 123 Main Street, Anytown, NY 12345

Employee Details:
- SSN: 123-45-6789
- Credit Card: 4532-1234-5678-9012
- Date of Birth: January 15, 1985

For emergency contact, please reach out to:
Jane Doe at (555) 987-6543 or jane.doe@example.org

Additional staff member Sarah Johnson can be reached at:
- Work Phone: (555) 555-5555
- Personal Email: sarah.j@personal.com
- Home Address: 456 Oak Avenue, Somewhere, CA 90210
    """
    
    print("Sample Text to Redact:")
    print("-" * 30)
    print(sample_text.strip())
    print()
    
    try:
        # Import LLM components
        from llm_config import LLMConfig
        from gpt4o_redactor import GPT4oMiniRedactor
        
        print("Initializing GPT-4o-mini redactor...")
        
        # Create configuration
        config = LLMConfig()
        
        if not config.validate_configuration():
            print("❌ Configuration validation failed!")
            print("Please ensure you have set up the following environment variables:")
            print("- AZURE_OPENAI_API_KEY")
            print("- AZURE_OPENAI_ENDPOINT")
            print("- AZURE_OPENAI_DEPLOYMENT (optional, defaults to 'gpt-4o-mini')")
            return False
        
        print(f"✅ Using model: {config.deployment_name}")
        print(f"✅ Confidence threshold: {config.confidence_threshold}")
        print(f"✅ PII categories: {', '.join(config.pii_categories)}")
        print()
        
        # Get cost estimate
        redactor = GPT4oMiniRedactor(config)
        estimate = redactor.get_cost_estimate(sample_text)
        
        print("Cost Estimate:")
        print(f"- Estimated tokens: {estimate['estimated_total_tokens']:,}")
        print(f"- Estimated cost: ${estimate['estimated_cost_usd']:.6f}")
        print(f"- API calls needed: {estimate['api_calls_needed']}")
        print()
        
        # Ask for confirmation
        proceed = input("Proceed with redaction? (y/N): ").strip().lower()
        if proceed not in ['y', 'yes']:
            print("Demo cancelled.")
            return False
        
        print("Processing text with GPT-4o-mini...")
        print("-" * 40)
        
        # Perform redaction
        result = redactor.redact_text(sample_text)
        
        # Display results
        print("\nRedacted Text:")
        print("-" * 30)
        print(result.redacted_text)
        print()
        
        print("Detection Summary:")
        print("-" * 30)
        print(f"Total entities found: {result.total_entities}")
        
        for category, count in result.redaction_summary.items():
            confidence = result.confidence_scores.get(category, 0.0)
            print(f"- {category}: {count} entities (avg confidence: {confidence:.2f})")
        
        print(f"\nProcessing Cost: ${result.processing_cost:.6f}")
        print(f"Tokens used: {result.tokens_used:,}")
        print()
        
        print("Detailed Entities Found:")
        print("-" * 30)
        for entity in result.entities_found:
            print(f"• '{entity.text}' -> {entity.category} "
                  f"(confidence: {entity.confidence:.2f})")
            if entity.reasoning:
                print(f"  Reasoning: {entity.reasoning}")
        
        print()
        print("✅ Demo completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required packages are installed:")
        print("pip install -r requirements.txt")
        return False
    
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        return False

def test_document_processing():
    """Test document processing functionality"""
    
    print("\n" + "="*60)
    print("Document Processing Demo")
    print("="*60)
    
    # Check for sample documents
    docs_dir = Path(__file__).parent.parent.parent / "docs"
    sample_files = []
    
    if docs_dir.exists():
        for pattern in ["*.docx", "*.pdf"]:
            sample_files.extend(docs_dir.glob(pattern))
    
    if not sample_files:
        print("No sample documents found in docs/ directory.")
        print("Skipping document processing demo.")
        return True
    
    print(f"Found {len(sample_files)} sample document(s):")
    for i, file_path in enumerate(sample_files, 1):
        print(f"{i}. {file_path.name}")
    
    try:
        choice = input(f"\nSelect file to process (1-{len(sample_files)}), or press Enter to skip: ").strip()
        
        if not choice:
            print("Document processing demo skipped.")
            return True
        
        file_index = int(choice) - 1
        if file_index < 0 or file_index >= len(sample_files):
            print("Invalid selection.")
            return False
        
        selected_file = sample_files[file_index]
        print(f"\nProcessing: {selected_file}")
        
        # Import document processor
        from llm_config import LLMConfig
        from document_processors import create_processor
        
        config = LLMConfig()
        processor = create_processor(str(selected_file), config)
        
        # Get cost estimate
        print("Getting cost estimate...")
        estimate = processor.get_cost_estimate(str(selected_file))
        
        if 'error' in estimate:
            print(f"❌ Cost estimation failed: {estimate['error']}")
            return False
        
        print(f"Estimated cost: ${estimate['estimated_cost_usd']:.6f}")
        print(f"Estimated tokens: {estimate['estimated_total_tokens']:,}")
        
        proceed = input("Proceed with document redaction? (y/N): ").strip().lower()
        if proceed not in ['y', 'yes']:
            print("Document processing cancelled.")
            return True
        
        # Process document
        print("Processing document...")
        doc_info = processor.process_document(str(selected_file))
        
        print(f"\n✅ Document processed successfully!")
        print(f"Output: {doc_info.file_path}")
        print(f"Risk level: {doc_info.risk_level}")
        print(f"Entities found: {doc_info.entities_found}")
        print(f"Processing cost: ${doc_info.processing_cost:.6f}")
        
        return True
        
    except (ValueError, IndexError):
        print("Invalid selection.")
        return False
    except Exception as e:
        print(f"❌ Document processing error: {e}")
        return False

def main():
    """Run demo script"""
    
    print("GPT-4o-mini Document Redaction System")
    print("Demo & Testing Script")
    print()
    
    # Check environment setup
    required_env_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("Please set these variables in your .env file or environment.")
        print("See .env.template for format.")
        return False
    
    # Run demos
    success = True
    
    # Test 1: Basic text redaction
    success &= test_basic_redaction()
    
    # Test 2: Document processing (optional)
    success &= test_document_processing()
    
    if success:
        print("\n🎉 All demos completed successfully!")
    else:
        print("\n❌ Some demos failed. Please check the error messages above.")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(130)
