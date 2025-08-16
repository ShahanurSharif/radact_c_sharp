"""
Azure AI Foundry Document Redaction - Main Application
Command-line interface for intelligent document redaction using Azure AI
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional
import json

# Configure logging first
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Import our Azure AI modules
try:
    from azure_config import AzureConfig
    from azure_document_processor import AzureDocumentProcessor
    from azure_ai_redactor import AzureAIRedactor
except ImportError as e:
    logger.error("Failed to import Azure modules", error=str(e))
    print("❌ Error: Azure AI modules not found. Please ensure all dependencies are installed.")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

class AzureRedactionCLI:
    """Command-line interface for Azure AI document redaction"""
    
    def __init__(self):
        """Initialize the CLI application"""
        self.config = None
        self.processor = None
        
    def setup_azure_config(self, env_file: Optional[str] = None) -> bool:
        """
        Setup Azure configuration
        
        Args:
            env_file: Path to .env file
            
        Returns:
            True if setup successful, False otherwise
        """
        try:
            self.config = AzureConfig(env_file)
            
            if not self.config.validate_configuration():
                logger.error("Invalid Azure configuration")
                return False
            
            self.processor = AzureDocumentProcessor(self.config)
            logger.info("Azure configuration loaded successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to setup Azure configuration", error=str(e))
            return False
    
    def process_single_file(self, input_path: str, output_path: Optional[str] = None) -> None:
        """
        Process a single document file
        
        Args:
            input_path: Path to input document
            output_path: Path to output document (optional)
        """
        print(f"🔍 Processing: {input_path}")
        
        result = self.processor.process_file(input_path, output_path)
        
        if result['status'] == 'success':
            print(f"✅ Successfully processed: {result['output_file']}")
            print(f"📊 Statistics:")
            print(f"   • Entities found: {result['entities_found']}")
            print(f"   • Redactions made: {result['redactions_made']}")
            print(f"   • Risk level: {result['risk_analysis']['risk_level']}")
            
            # Show confidence scores
            if result['confidence_scores']:
                print(f"   • Confidence scores:")
                for category, score in result['confidence_scores'].items():
                    print(f"     - {category}: {score:.2f}")
            
            # Show risk recommendations
            if result['risk_analysis']['recommendations']:
                print(f"   • Recommendations:")
                for rec in result['risk_analysis']['recommendations']:
                    print(f"     - {rec}")
        
        else:
            print(f"❌ Failed to process: {result['error']}")
    
    def process_directory(self, input_dir: str, output_dir: Optional[str] = None) -> None:
        """
        Process all documents in a directory
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path (optional)
        """
        print(f"📁 Batch processing directory: {input_dir}")
        
        result = self.processor.batch_process(input_dir, output_dir)
        
        if result['status'] == 'completed':
            print(f"✅ Batch processing completed")
            print(f"📊 Summary:")
            print(f"   • Documents processed: {result['documents_processed']}")
            print(f"   • Successful: {result['successful']}")
            print(f"   • Failed: {result['failed']}")
            print(f"   • Output directory: {result['output_directory']}")
            
            # Show individual results
            for file_result in result['results']:
                if file_result['status'] == 'success':
                    filename = Path(file_result['input_file']).name
                    print(f"   ✅ {filename}: {file_result['redactions_made']} redactions")
                else:
                    filename = Path(file_result['input_file']).name
                    print(f"   ❌ {filename}: {file_result['error']}")
        else:
            print(f"❌ Batch processing failed: {result['error']}")
    
    def analyze_document(self, input_path: str) -> None:
        """
        Analyze document for PII without redacting
        
        Args:
            input_path: Path to document to analyze
        """
        print(f"🔍 Analyzing document: {input_path}")
        
        try:
            # Extract text based on file type
            file_path = Path(input_path)
            
            if file_path.suffix.lower() == '.docx':
                from docx import Document
                doc = Document(input_path)
                text = "\n".join([para.text for para in doc.paragraphs])
            elif file_path.suffix.lower() == '.pdf':
                import PyPDF2
                with open(input_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = "\n".join([page.extract_text() for page in reader.pages])
            else:
                print("❌ Unsupported file type")
                return
            
            # Analyze with Azure AI
            redactor = AzureAIRedactor(self.config)
            entities = redactor.detect_pii_entities(text)
            risk_analysis = redactor.analyze_document_risk(text)
            
            print(f"📊 Analysis Results:")
            print(f"   • Total characters: {len(text)}")
            print(f"   • PII entities found: {len(entities)}")
            print(f"   • Risk score: {risk_analysis['risk_score']}")
            print(f"   • Risk level: {risk_analysis['risk_level']}")
            
            if entities:
                print(f"   • Entity breakdown:")
                category_counts = {}
                for entity in entities:
                    if entity.category not in category_counts:
                        category_counts[entity.category] = 0
                    category_counts[entity.category] += 1
                
                for category, count in category_counts.items():
                    print(f"     - {category}: {count}")
            
            if risk_analysis['recommendations']:
                print(f"   • Recommendations:")
                for rec in risk_analysis['recommendations']:
                    print(f"     - {rec}")
                    
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
    
    def create_sample_config(self) -> None:
        """Create a sample configuration file"""
        config_path = Path('.env')
        
        if config_path.exists():
            print("⚠️  .env file already exists")
            return
        
        template_path = Path('.env.template')
        if template_path.exists():
            import shutil
            shutil.copy(template_path, config_path)
            print("✅ Sample .env file created from template")
            print("📝 Please edit .env file with your Azure credentials")
        else:
            print("❌ .env.template not found")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Azure AI Foundry Document Redaction Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py file document.docx                    # Redact single file
  python main.py file document.pdf --output redacted.pdf  # Redact with custom output
  python main.py directory ./documents                # Redact directory
  python main.py analyze document.docx               # Analyze without redacting
  python main.py config                              # Create sample config file
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # File processing command
    file_parser = subparsers.add_parser('file', help='Process a single document file')
    file_parser.add_argument('input_path', help='Path to input document')
    file_parser.add_argument('--output', '-o', help='Path to output document')
    file_parser.add_argument('--config', '-c', help='Path to .env configuration file')
    
    # Directory processing command
    dir_parser = subparsers.add_parser('directory', help='Process all documents in a directory')
    dir_parser.add_argument('input_dir', help='Input directory path')
    dir_parser.add_argument('--output-dir', help='Output directory path')
    dir_parser.add_argument('--config', '-c', help='Path to .env configuration file')
    
    # Analysis command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze document for PII (no redaction)')
    analyze_parser.add_argument('input_path', help='Path to document to analyze')
    analyze_parser.add_argument('--config', '-c', help='Path to .env configuration file')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Create sample configuration file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Handle config creation
    if args.command == 'config':
        cli = AzureRedactionCLI()
        cli.create_sample_config()
        return
    
    # Initialize CLI
    cli = AzureRedactionCLI()
    
    # Setup Azure configuration
    config_file = getattr(args, 'config', None)
    if not cli.setup_azure_config(config_file):
        print("❌ Failed to setup Azure configuration")
        print("💡 Run 'python main.py config' to create a sample configuration file")
        sys.exit(1)
    
    # Execute commands
    try:
        if args.command == 'file':
            cli.process_single_file(args.input_path, args.output)
        elif args.command == 'directory':
            cli.process_directory(args.input_dir, args.output_dir)
        elif args.command == 'analyze':
            cli.analyze_document(args.input_path)
    
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        logger.error("Unexpected error", error=str(e))
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
