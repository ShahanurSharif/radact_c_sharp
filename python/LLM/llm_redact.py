#!/usr/bin/env python3
"""
GPT-4o-mini Document Redaction CLI
Command-line interface for LLM-powered document redaction
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from llm_config import LLMConfig
from gpt4o_redactor import GPT4oMiniRedactor
from document_processors import create_processor, DocumentInfo

def setup_logging():
    """Setup basic logging"""
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    return logging.getLogger(__name__)

def load_config(config_path: Optional[str] = None) -> LLMConfig:
    """Load LLM configuration"""
    try:
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            return LLMConfig(**config_data)
        else:
            return LLMConfig()
    except Exception as e:
        print(f"Error loading config: {e}")
        return LLMConfig()

def estimate_cost(file_path: str, config: LLMConfig, logger):
    """Estimate processing cost for document"""
    
    logger.info(f"Estimating cost for: {file_path}")
    
    try:
        processor = create_processor(file_path, config)
        estimate = processor.get_cost_estimate(file_path)
        
        if 'error' in estimate:
            logger.error(f"Cost estimation failed: {estimate['error']}")
            return
        
        print("\n" + "="*50)
        print("COST ESTIMATION")
        print("="*50)
        print(f"File: {file_path}")
        print(f"File type: {estimate['file_type']}")
        print(f"Text length: {estimate['text_length']:,} characters")
        print(f"Word count: {estimate['word_count']:,} words")
        print(f"Chunks required: {estimate['chunks_required']}")
        print(f"API calls needed: {estimate['api_calls_needed']}")
        print(f"Estimated input tokens: {estimate['estimated_input_tokens']:,}")
        print(f"Estimated output tokens: {estimate['estimated_output_tokens']:,}")
        print(f"Estimated total tokens: {estimate['estimated_total_tokens']:,}")
        print(f"Estimated cost: ${estimate['estimated_cost_usd']:.6f}")
        print("="*50)
        
        # Ask for confirmation
        proceed = input("\nProceed with redaction? (y/N): ").strip().lower()
        return proceed in ['y', 'yes']
        
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        return False

def redact_document(file_path: str, output_path: Optional[str], config: LLMConfig, logger) -> Optional[DocumentInfo]:
    """Redact document using GPT-4o-mini"""
    
    logger.info(f"Starting redaction: {file_path}")
    
    try:
        processor = create_processor(file_path, config)
        doc_info = processor.process_document(file_path, output_path)
        
        return doc_info
        
    except Exception as e:
        logger.error(f"Redaction failed: {e}")
        return None

def display_results(doc_info: DocumentInfo, logger):
    """Display redaction results"""
    
    print("\n" + "="*50)
    print("REDACTION COMPLETED")
    print("="*50)
    print(f"Output file: {doc_info.file_path}")
    print(f"Document type: {doc_info.file_type.upper()}")
    print(f"Pages: {doc_info.page_count}")
    print(f"Words: {doc_info.word_count:,}")
    print(f"Characters: {doc_info.character_count:,}")
    print(f"PII entities found: {doc_info.entities_found}")
    print(f"Risk level: {doc_info.risk_level}")
    print(f"Processing cost: ${doc_info.processing_cost:.6f}")
    print("="*50)
    
    # Risk level warning
    if doc_info.risk_level == "HIGH":
        print("\n⚠️  HIGH RISK: This document contained sensitive PII (SSN, credit cards, etc.)")
        print("   Please handle the redacted document with appropriate security measures.")
    elif doc_info.risk_level == "MEDIUM":
        print("\n⚠️  MEDIUM RISK: This document contained moderate amounts of PII.")
    else:
        print("\n✅ LOW RISK: Minimal PII detected in this document.")

def main():
    """Main CLI function"""
    
    parser = argparse.ArgumentParser(
        description="GPT-4o-mini Document Redaction Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.docx                    # Redact with default settings
  %(prog)s document.pdf -o redacted.pdf    # Specify output file
  %(prog)s document.docx --estimate-only   # Get cost estimate only
  %(prog)s document.pdf --config my.json  # Use custom configuration
  
Environment Variables:
  AZURE_OPENAI_API_KEY       Azure OpenAI API key
  AZURE_OPENAI_ENDPOINT      Azure OpenAI endpoint URL
  AZURE_OPENAI_DEPLOYMENT    Deployment name (default: gpt-4o-mini)
        """
    )
    
    parser.add_argument(
        'input_file',
        help='Input document file (DOCX or PDF)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: input_file_redacted.ext)'
    )
    
    parser.add_argument(
        '--estimate-only',
        action='store_true',
        help='Only estimate cost, do not perform redaction'
    )
    
    parser.add_argument(
        '--config',
        help='Configuration file path (JSON format)'
    )
    
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.7,
        help='Minimum confidence threshold for PII detection (0.0-1.0)'
    )
    
    parser.add_argument(
        '--categories',
        nargs='+',
        default=['names', 'phone_numbers', 'emails', 'addresses', 'ssn', 'credit_cards'],
        help='PII categories to detect'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input file
    if not Path(args.input_file).exists():
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Check file extension
    file_ext = Path(args.input_file).suffix.lower()
    if file_ext not in ['.docx', '.pdf']:
        logger.error(f"Unsupported file type: {file_ext}")
        sys.exit(1)
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    config.confidence_threshold = args.confidence
    config.pii_categories = args.categories
    
    # Validate configuration
    if not config.validate_configuration():
        logger.error("Invalid configuration. Please check your Azure OpenAI settings.")
        sys.exit(1)
    
    print("GPT-4o-mini Document Redaction Tool")
    print("=" * 40)
    print(f"Model: {config.deployment_name}")
    print(f"Confidence threshold: {config.confidence_threshold}")
    print(f"PII categories: {', '.join(config.pii_categories)}")
    print()
    
    try:
        # Cost estimation
        if not estimate_cost(args.input_file, config, logger):
            logger.info("Redaction cancelled by user")
            sys.exit(0)
        
        if args.estimate_only:
            logger.info("Cost estimation completed")
            sys.exit(0)
        
        # Perform redaction
        doc_info = redact_document(args.input_file, args.output, config, logger)
        
        if doc_info:
            display_results(doc_info, logger)
            logger.info("Redaction completed successfully")
        else:
            logger.error("Redaction failed")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
