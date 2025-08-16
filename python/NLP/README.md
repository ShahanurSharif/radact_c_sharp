# Azure AI Foundry Document Redaction

🔒 **Intelligent document redaction using Azure AI services for PII detection and removal**

## Overview

This tool leverages Azure AI Foundry services to intelligently detect and redact personally identifiable information (PII) from documents including:

- **Names** (Person, PersonType)
- **Phone Numbers** 
- **Addresses**
- **Credit Card Numbers**
- **Email Addresses**
- **IP Addresses**
- **URLs**
- **Date/Time information**

## Features

### 🤖 AI-Powered Detection
- **Azure Text Analytics**: Advanced PII entity recognition
- **High Accuracy**: Confidence scoring and threshold filtering
- **Multi-language Support**: Built-in language detection
- **Fallback Detection**: Regex patterns for offline capability

### 📄 Document Support
- **DOCX Files**: Full formatting preservation with redaction highlighting
- **PDF Files**: Text extraction and reconstructed redacted PDFs
- **Batch Processing**: Process entire directories
- **Risk Assessment**: Document risk scoring and recommendations

### 🔐 Enterprise Security
- **Azure Integration**: Secure cloud-based processing
- **Configurable Redaction**: Custom redaction patterns
- **Audit Logging**: Comprehensive processing logs
- **Compliance Ready**: Supports GDPR, HIPAA, and other privacy regulations

## Prerequisites

### Azure Services Required

1. **Azure Text Analytics** (Cognitive Services)
   - Create a Text Analytics resource in Azure Portal
   - Note the endpoint URL and access key

2. **Azure OpenAI** (Optional)
   - For advanced language model features
   - Create OpenAI resource and deployment

### Python Requirements
- Python 3.8 or higher
- Virtual environment (recommended)

## Installation

### 1. Quick Setup (Recommended)

```bash
# Navigate to the NLP directory
cd python/NLP

# Run the setup script
python setup.py
```

This will:
- Check Python version compatibility
- Create virtual environment (if needed)
- Install all required packages
- Create configuration files
- Verify installation

### 2. Manual Setup

```bash
# Create and activate virtual environment
python -m venv ../../venv
source ../../venv/bin/activate  # On Windows: ..\\..\\venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Copy configuration template
cp .env.template .env
```

## Configuration

### 1. Azure Credentials

Edit the `.env` file with your Azure credentials:

```env
# Required: Azure Text Analytics
AZURE_TEXT_ANALYTICS_KEY=your_text_analytics_key_here
AZURE_TEXT_ANALYTICS_ENDPOINT=https://your-resource.cognitiveservices.azure.com/

# Optional: Azure OpenAI
AZURE_OPENAI_API_KEY=your_openai_key_here
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

# Optional: Service Principal (for managed identity)
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
```

### 2. Detection Settings

```env
# Confidence threshold (0.0-1.0)
REDACTION_CONFIDENCE_THRESHOLD=0.8

# PII categories to detect (comma-separated)
PII_CATEGORIES=Person,PhoneNumber,Address,CreditCardNumber,Email
```

### 3. Available PII Categories

- `Person` - Names of people
- `PersonType` - Job titles, roles
- `PhoneNumber` - Phone numbers
- `Address` - Physical addresses
- `CreditCardNumber` - Credit card numbers
- `Email` - Email addresses
- `URL` - Web URLs
- `IPAddress` - IP addresses
- `DateTime` - Dates and times
- `Quantity` - Numerical quantities

## Usage

### Command Line Interface

#### Process Single Document

```bash
# Basic redaction
python main.py file document.docx

# Custom output path
python main.py file document.pdf --output redacted_document.pdf

# Custom configuration
python main.py file document.docx --config /path/to/.env
```

#### Batch Process Directory

```bash
# Process all documents in directory
python main.py directory ./documents

# Custom output directory
python main.py directory ./documents --output-dir ./redacted_output
```

#### Analyze Without Redacting

```bash
# Get PII analysis report
python main.py analyze document.docx
```

#### Configuration Management

```bash
# Create sample configuration file
python main.py config
```

### Python API Usage

```python
from azure_config import AzureConfig
from azure_document_processor import AzureDocumentProcessor

# Initialize with configuration
config = AzureConfig('.env')
processor = AzureDocumentProcessor(config)

# Process single file
result = processor.process_file('document.docx', 'redacted.docx')

# Check results
if result['status'] == 'success':
    print(f"Redacted {result['redactions_made']} entities")
    print(f"Risk level: {result['risk_analysis']['risk_level']}")

# Batch processing
batch_result = processor.batch_process('./documents', './redacted')
```

### Direct AI Redactor Usage

```python
from azure_ai_redactor import AzureAIRedactor

# Initialize redactor
redactor = AzureAIRedactor()

# Detect PII entities
entities = redactor.detect_pii_entities("John Smith lives at 123 Main St")

# Redact text
result = redactor.redact_text("Call John at 555-1234")
print(result.redacted_text)  # "Call [NAME_REDACTED] at [PHONE_REDACTED]"

# Risk analysis
risk = redactor.analyze_document_risk(document_text)
print(f"Risk level: {risk['risk_level']}")
```

## Output Examples

### Redacted DOCX
- Original formatting preserved
- Redacted text highlighted in yellow with red font
- Redaction summary added to document header

### Redacted PDF
- Professional layout with redaction header
- Clear indication of redacted content
- Maintains document structure

### Analysis Report
```
📊 Analysis Results:
   • Total characters: 1461
   • PII entities found: 8
   • Risk score: 25
   • Risk level: HIGH
   • Entity breakdown:
     - Person: 3
     - PhoneNumber: 1
     - Address: 1
     - CreditCardNumber: 1
   • Recommendations:
     - Immediate redaction recommended before sharing
     - Credit card numbers detected - ensure PCI compliance
```

## Security & Compliance

### Data Privacy
- **No Data Retention**: Azure Text Analytics doesn't retain your data
- **Encrypted Transit**: All communications use HTTPS/TLS
- **Local Processing**: Option for offline regex fallback

### Compliance Features
- **Audit Logging**: Complete processing logs with timestamps
- **Confidence Scoring**: Transparency in AI decision making
- **Customizable Redaction**: Meet specific compliance requirements
- **Risk Assessment**: Built-in risk scoring for documents

## Troubleshooting

### Common Issues

1. **Azure Authentication Failed**
   ```
   Error: Invalid Azure configuration
   ```
   - Check your Azure credentials in `.env`
   - Verify the endpoint URL format
   - Ensure the service is active in Azure Portal

2. **Import Errors**
   ```
   Import "azure.ai.textanalytics" could not be resolved
   ```
   - Run `pip install -r requirements.txt`
   - Activate your virtual environment
   - Check Python version (3.8+ required)

3. **High Memory Usage**
   - Large documents are processed in chunks
   - Adjust confidence threshold to reduce detected entities
   - Use batch processing with smaller file sets

### Performance Optimization

1. **Confidence Threshold**: Higher values = faster processing
2. **Category Filtering**: Only detect needed PII types
3. **Batch Processing**: More efficient for multiple documents
4. **Chunking**: Large documents automatically split

## Development

### Project Structure
```
NLP/
├── __init__.py                 # Package initialization
├── azure_config.py            # Azure service configuration
├── azure_ai_redactor.py       # Core AI redaction engine
├── azure_document_processor.py # Document processing
├── main.py                     # CLI application
├── setup.py                    # Installation script
├── requirements.txt            # Python dependencies
├── .env.template              # Configuration template
└── README.md                  # This file
```

### Adding Custom Redaction Patterns

```python
# Custom redaction mapping
custom_patterns = {
    'Person': '[EMPLOYEE_NAME]',
    'CreditCardNumber': '[PAYMENT_INFO]',
    'custom_pattern': '[CUSTOM_REDACTED]'
}

result = redactor.redact_text(text, custom_patterns)
```

### Extending Entity Detection

```python
# Add custom regex patterns
redactor.custom_patterns['passport'] = re.compile(r'\b[A-Z]{2}\d{7}\b')
```

## Support & Contributing

### Getting Help
- Check the troubleshooting section
- Review Azure AI documentation
- Check Azure service status

### Contributing
- Follow PEP 8 style guidelines
- Add unit tests for new features
- Update documentation
- Test with various document types

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### v1.0.0
- Initial release with Azure AI integration
- Support for DOCX and PDF documents
- Batch processing capabilities
- Risk assessment features
- Command-line interface
- Python API
