"""
Azure OpenAI Configuration for LLM-based Document Redaction
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import structlog

logger = structlog.get_logger(__name__)

class LLMConfig:
    """Configuration manager for Azure OpenAI LLM redaction"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize LLM configuration
        
        Args:
            env_file: Path to .env file (optional)
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        # Azure OpenAI configuration
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01')
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o-mini')
        
        # Model parameters - directly from .env file
        self.temperature = float(os.getenv('MODEL_TEMPERATURE', '0.1'))
        self.max_tokens = int(os.getenv('MAX_TOKENS', '4000'))
        self.chunk_size = int(os.getenv('CHUNK_SIZE', '3000'))
        self.overlap_size = int(os.getenv('OVERLAP_SIZE', '200'))
        
        # Processing settings
        self.confidence_threshold = float(os.getenv('CONFIDENCE_THRESHOLD', '0.8'))
        self.redaction_style = os.getenv('REDACTION_STYLE', 'standard')
        self.batch_size = int(os.getenv('BATCH_SIZE', '5'))
        self.enable_caching = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
        
        # Cost tracking
        self.enable_cost_tracking = os.getenv('ENABLE_COST_TRACKING', 'true').lower() == 'true'
        self.cost_alert_threshold = float(os.getenv('COST_ALERT_THRESHOLD', '1.00'))
        
        # PII categories
        categories_str = os.getenv('PII_CATEGORIES', 'names,phone_numbers,emails,addresses,ssn,credit_cards')
        self.pii_categories = [cat.strip() for cat in categories_str.split(',')]
        
        logger.info("LLM configuration loaded", 
                   endpoint=self.endpoint,
                   deployment=self.deployment_name,
                   categories=self.pii_categories)
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI client configuration"""
        return {
            'api_key': self.api_key,
            'api_version': self.api_version,
            'azure_endpoint': self.endpoint
        }
    
    def get_model_params(self) -> Dict[str, Any]:
        """Get model parameters for API calls"""
        return {
            'model': self.deployment_name,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }
    
    def validate_configuration(self) -> bool:
        """
        Validate that required configuration is present
        
        Returns:
            True if configuration is valid, False otherwise
        """
        required_fields = [
            ('AZURE_OPENAI_API_KEY', self.api_key),
            ('AZURE_OPENAI_ENDPOINT', self.endpoint),
            ('AZURE_OPENAI_DEPLOYMENT_NAME', self.deployment_name)
        ]
        
        missing_fields = [field for field, value in required_fields if not value]
        
        if missing_fields:
            logger.error("Missing required configuration", fields=missing_fields)
            return False
        
        # Validate endpoint format
        if not self.endpoint.startswith('https://'):
            logger.error("Invalid endpoint format", endpoint=self.endpoint)
            return False
        
        logger.info("Configuration validation passed")
        return True
    
    def get_redaction_patterns(self) -> Dict[str, str]:
        """Get redaction patterns based on style"""
        if self.redaction_style == 'detailed':
            return {
                'names': '[PERSON_NAME_REDACTED]',
                'phone_numbers': '[PHONE_NUMBER_REDACTED]',
                'emails': '[EMAIL_ADDRESS_REDACTED]',
                'addresses': '[PHYSICAL_ADDRESS_REDACTED]',
                'ssn': '[SSN_REDACTED]',
                'credit_cards': '[CREDIT_CARD_NUMBER_REDACTED]',
                'dates': '[DATE_REDACTED]',
                'ip_addresses': '[IP_ADDRESS_REDACTED]'
            }
        elif self.redaction_style == 'minimal':
            return {
                'names': '[REDACTED]',
                'phone_numbers': '[REDACTED]',
                'emails': '[REDACTED]',
                'addresses': '[REDACTED]',
                'ssn': '[REDACTED]',
                'credit_cards': '[REDACTED]',
                'dates': '[REDACTED]',
                'ip_addresses': '[REDACTED]'
            }
        else:  # standard
            return {
                'names': '[NAME_REDACTED]',
                'phone_numbers': '[PHONE_REDACTED]',
                'emails': '[EMAIL_REDACTED]',
                'addresses': '[ADDRESS_REDACTED]',
                'ssn': '[SSN_REDACTED]',
                'credit_cards': '[CREDIT_CARD_REDACTED]',
                'dates': '[DATE_REDACTED]',
                'ip_addresses': '[IP_REDACTED]'
            }
