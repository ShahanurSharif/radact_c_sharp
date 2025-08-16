"""
Azure AI Foundry Document Redaction Package
Intelligent PII detection and redaction using Azure AI services
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "Azure AI-powered document redaction tool"

from .azure_config import AzureConfig
from .azure_ai_redactor import AzureAIRedactor, PIIEntity, RedactionResult
from .azure_document_processor import AzureDocumentProcessor, AzureDocxProcessor, AzurePdfProcessor

__all__ = [
    'AzureConfig',
    'AzureAIRedactor',
    'PIIEntity',
    'RedactionResult',
    'AzureDocumentProcessor',
    'AzureDocxProcessor',
    'AzurePdfProcessor'
]
