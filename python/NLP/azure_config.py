"""
Azure AI Foundry Configuration Manager
Handles Azure credentials and service connections
"""

import os
from typing import Optional
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import structlog

logger = structlog.get_logger(__name__)

class AzureConfig:
    """Azure AI services configuration manager"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize Azure configuration
        
        Args:
            env_file: Path to .env file (optional)
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        self.text_analytics_key = os.getenv('AZURE_TEXT_ANALYTICS_KEY')
        self.text_analytics_endpoint = os.getenv('AZURE_TEXT_ANALYTICS_ENDPOINT')
        
        self.openai_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.openai_api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01')
        self.openai_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
        
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        
        self.confidence_threshold = float(os.getenv('REDACTION_CONFIDENCE_THRESHOLD', '0.8'))
        self.pii_categories = os.getenv('PII_CATEGORIES', 'Person,PhoneNumber,Address,CreditCardNumber,Email').split(',')
        
        logger.info("Azure configuration loaded", 
                   endpoint=self.text_analytics_endpoint,
                   categories=self.pii_categories,
                   threshold=self.confidence_threshold)
    
    def get_text_analytics_client(self) -> TextAnalyticsClient:
        """
        Create and return Azure Text Analytics client
        
        Returns:
            TextAnalyticsClient instance
        """
        if not self.text_analytics_endpoint:
            raise ValueError("AZURE_TEXT_ANALYTICS_ENDPOINT not configured")
        
        if self.text_analytics_key:
            # Use API key authentication
            credential = AzureKeyCredential(self.text_analytics_key)
            logger.info("Using API key authentication for Text Analytics")
        else:
            # Use managed identity or service principal
            if all([self.tenant_id, self.client_id, self.client_secret]):
                credential = ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                logger.info("Using service principal authentication")
            else:
                credential = DefaultAzureCredential()
                logger.info("Using default Azure credential")
        
        return TextAnalyticsClient(
            endpoint=self.text_analytics_endpoint,
            credential=credential
        )
    
    def validate_configuration(self) -> bool:
        """
        Validate that required configuration is present
        
        Returns:
            True if configuration is valid, False otherwise
        """
        required_fields = [
            ('AZURE_TEXT_ANALYTICS_ENDPOINT', self.text_analytics_endpoint)
        ]
        
        missing_fields = [field for field, value in required_fields if not value]
        
        if missing_fields:
            logger.error("Missing required configuration", fields=missing_fields)
            return False
        
        # Check that we have at least one authentication method
        has_api_key = bool(self.text_analytics_key)
        has_service_principal = all([self.tenant_id, self.client_id, self.client_secret])
        
        if not (has_api_key or has_service_principal):
            logger.error("No valid authentication method configured")
            return False
        
        logger.info("Configuration validation passed")
        return True
