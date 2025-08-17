# Enhanced PDF Processor - API Reference

## Quick Start

### 1. Simple One-Line Usage
```python
from enhanced_pdf_processor import process_pdf_enhanced

# Basic redaction with default settings
result = process_pdf_enhanced("document.pdf")
print(f"Redacted file: {result['file_path']}")
```

### 2. Specify Output Path
```python
result = process_pdf_enhanced(
    input_path="document.pdf",
    output_path="redacted_document.pdf"
)
```

### 3. Custom Configuration
```python
from llm_config import LLMConfig

config = LLMConfig()
config.confidence_threshold = 0.9  # Higher confidence
config.pii_categories = ['names', 'ssn', 'credit_cards']  # Specific categories

result = process_pdf_enhanced("document.pdf", config=config)
```

## Advanced Usage

### Using the Processor Class

```python
from enhanced_pdf_processor import EnhancedPdfProcessor
from llm_config import LLMConfig

# Create processor
config = LLMConfig()
processor = EnhancedPdfProcessor(config)

# Get cost estimate first
estimate = processor.get_cost_estimate("document.pdf")
print(f"Estimated cost: ${estimate['estimated_cost_usd']:.6f}")

# Process if cost is acceptable
if estimate['estimated_cost_usd'] < 0.01:  # Less than 1 cent
    result = processor.process_pdf("document.pdf")
```

### Batch Processing

```python
import os
from pathlib import Path

pdf_files = Path("documents/").glob("*.pdf")

for pdf_file in pdf_files:
    try:
        result = process_pdf_enhanced(str(pdf_file))
        print(f"✅ {pdf_file.name}: {result['entities_found']} entities")
    except Exception as e:
        print(f"❌ {pdf_file.name}: {e}")
```

## Configuration Options

### LLMConfig Parameters

```python
config = LLMConfig()

# Detection settings
config.confidence_threshold = 0.8  # 0.0 to 1.0
config.pii_categories = [
    'names',           # Person names
    'phone_numbers',   # Phone numbers
    'emails',          # Email addresses  
    'addresses',       # Physical addresses
    'ssn',            # Social Security Numbers
    'credit_cards',    # Credit card numbers
    'dates',          # Personal dates
    'ip_addresses'     # IP addresses
]

# Processing settings
config.chunk_size = 3000      # Text chunk size for large documents
config.overlap_size = 200     # Overlap between chunks
config.temperature = 0.1      # LLM temperature (0.0-1.0)
config.max_tokens = 4000      # Max tokens per request
```

## Return Values

### Result Dictionary

```python
result = process_pdf_enhanced("document.pdf")

# Available fields:
result['file_path']         # Output file path
result['file_type']         # 'pdf'
result['page_count']        # Number of pages
result['word_count']        # Total words
result['character_count']   # Total characters
result['processing_cost']   # Cost in USD
result['entities_found']    # Number of PII entities found
result['risk_level']        # 'LOW', 'MEDIUM', or 'HIGH'
```

### Cost Estimate Dictionary

```python
estimate = processor.get_cost_estimate("document.pdf")

# Available fields:
estimate['file_path']              # Input file path
estimate['file_type']              # '.pdf'
estimate['text_length']            # Characters in document
estimate['word_count']             # Words in document
estimate['chunks_required']        # Number of processing chunks
estimate['api_calls_needed']       # Number of API calls
estimate['estimated_input_tokens'] # Expected input tokens
estimate['estimated_output_tokens'] # Expected output tokens
estimate['estimated_total_tokens'] # Total tokens
estimate['estimated_cost_usd']     # Estimated cost
```

## Error Handling

```python
try:
    result = process_pdf_enhanced("document.pdf")
except FileNotFoundError:
    print("PDF file not found")
except PermissionError:
    print("Cannot write output file")
except Exception as e:
    print(f"Processing failed: {e}")
```

## Features

### ✅ What It Does
- **Preserves original PDF formatting** (fonts, layout, images)
- **Intelligent PII detection** using GPT-4o-mini
- **Precise redaction** with black rectangles over sensitive text
- **Cost optimization** with smart text chunking
- **Risk assessment** based on PII types found
- **Professional output** that looks like original document

### ❌ What It Doesn't Do
- Doesn't modify scanned PDFs (text must be selectable)
- Doesn't redact text in images
- Doesn't handle password-protected PDFs
- Doesn't process very large PDFs (>100MB) efficiently

## Cost Information

### GPT-4o-mini Pricing
- **Input tokens**: $0.150 per 1M tokens
- **Output tokens**: $0.600 per 1M tokens

### Typical Costs
- **1-page PDF**: ~$0.0002 - $0.0005
- **10-page PDF**: ~$0.0015 - $0.0025  
- **100-page PDF**: ~$0.01 - $0.02

### Cost vs Benefits
- **Much cheaper than manual redaction**
- **More accurate than regex-only approaches**
- **Preserves formatting unlike text-recreation methods**

## Troubleshooting

### Common Issues

1. **"Document closed" error**: Usually fixed in latest version
2. **High confidence threshold finds nothing**: Lower `confidence_threshold` to 0.7 or 0.6
3. **Missing PII categories**: Add specific categories to `pii_categories` list
4. **High processing cost**: Use cost estimation before processing large documents

### Environment Setup

```bash
# Required environment variables
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-10-21
```

### Debug Mode

```python
import logging

# Enable debug logging
logging.getLogger().setLevel(logging.DEBUG)

# Process with verbose output
result = process_pdf_enhanced("document.pdf")
```
