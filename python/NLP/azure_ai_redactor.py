"""
Azure AI Foundry PII Detection and Redaction Engine
Uses Azure Text Analytics for intelligent entity recognition and redaction
"""

import re
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from azure.ai.textanalytics import RecognizePiiEntitiesResult
import structlog

from azure_config import AzureConfig

logger = structlog.get_logger(__name__)

@dataclass
class PIIEntity:
    """Represents a detected PII entity"""
    text: str
    category: str
    subcategory: Optional[str]
    confidence_score: float
    offset: int
    length: int

@dataclass
class RedactionResult:
    """Results from document redaction"""
    original_text: str
    redacted_text: str
    entities_found: List[PIIEntity]
    redaction_count: int
    confidence_scores: Dict[str, float]

class AzureAIRedactor:
    """Azure AI-powered document redaction engine"""
    
    def __init__(self, config: Optional[AzureConfig] = None):
        """
        Initialize the Azure AI redactor
        
        Args:
            config: Azure configuration instance
        """
        self.config = config or AzureConfig()
        
        if not self.config.validate_configuration():
            raise ValueError("Invalid Azure configuration")
        
        self.client = self.config.get_text_analytics_client()
        self.confidence_threshold = self.config.confidence_threshold
        
        # Custom regex patterns for enhanced detection
        self.custom_patterns = {
            'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        }
        
        logger.info("Azure AI Redactor initialized", 
                   threshold=self.confidence_threshold,
                   categories=self.config.pii_categories)
    
    def detect_pii_entities(self, text: str) -> List[PIIEntity]:
        """
        Detect PII entities using Azure Text Analytics
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected PII entities
        """
        try:
            # Split text into chunks if it's too long (Azure has limits)
            max_chars = 5000
            chunks = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
            
            all_entities = []
            offset_adjustment = 0
            
            for chunk in chunks:
                response = self.client.recognize_pii_entities(
                    documents=[chunk],
                    language="en",
                    categories_filter=self.config.pii_categories
                )
                
                if response and response[0].entities:
                    for entity in response[0].entities:
                        pii_entity = PIIEntity(
                            text=entity.text,
                            category=entity.category,
                            subcategory=entity.subcategory,
                            confidence_score=entity.confidence_score,
                            offset=entity.offset + offset_adjustment,
                            length=entity.length
                        )
                        
                        # Only include entities above confidence threshold
                        if pii_entity.confidence_score >= self.confidence_threshold:
                            all_entities.append(pii_entity)
                
                offset_adjustment += len(chunk)
            
            logger.info("PII detection completed", 
                       entities_found=len(all_entities),
                       text_length=len(text))
            
            return all_entities
            
        except Exception as e:
            logger.error("Error in PII detection", error=str(e))
            # Fallback to custom regex patterns
            return self._fallback_detection(text)
    
    def _fallback_detection(self, text: str) -> List[PIIEntity]:
        """
        Fallback PII detection using regex patterns
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected entities using regex
        """
        entities = []
        
        for category, pattern in self.custom_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                entity = PIIEntity(
                    text=match.group(),
                    category=category,
                    subcategory=None,
                    confidence_score=0.9,  # High confidence for regex matches
                    offset=match.start(),
                    length=match.end() - match.start()
                )
                entities.append(entity)
        
        logger.info("Fallback detection completed", entities=len(entities))
        return entities
    
    def redact_text(self, text: str, custom_redaction_map: Optional[Dict[str, str]] = None) -> RedactionResult:
        """
        Redact PII entities from text
        
        Args:
            text: Original text to redact
            custom_redaction_map: Custom redaction patterns for categories
            
        Returns:
            RedactionResult with original and redacted text
        """
        entities = self.detect_pii_entities(text)
        
        # Default redaction patterns
        default_redaction_map = {
            'Person': '[NAME_REDACTED]',
            'PersonType': '[TITLE_REDACTED]',
            'PhoneNumber': '[PHONE_REDACTED]',
            'Address': '[ADDRESS_REDACTED]',
            'CreditCardNumber': '[CREDIT_CARD_REDACTED]',
            'Email': '[EMAIL_REDACTED]',
            'URL': '[URL_REDACTED]',
            'IPAddress': '[IP_ADDRESS_REDACTED]',
            'DateTime': '[DATE_REDACTED]',
            'credit_card': '[CREDIT_CARD_REDACTED]',
            'phone': '[PHONE_REDACTED]',
            'ssn': '[SSN_REDACTED]',
            'email': '[EMAIL_REDACTED]'
        }
        
        # Merge custom redaction map if provided
        redaction_map = default_redaction_map.copy()
        if custom_redaction_map:
            redaction_map.update(custom_redaction_map)
        
        # Sort entities by offset in reverse order to maintain positions during replacement
        sorted_entities = sorted(entities, key=lambda x: x.offset, reverse=True)
        
        redacted_text = text
        redaction_count = 0
        confidence_scores = {}
        
        for entity in sorted_entities:
            redaction_token = redaction_map.get(entity.category, f'[{entity.category.upper()}_REDACTED]')
            
            # Replace the entity in the text
            start = entity.offset
            end = entity.offset + entity.length
            redacted_text = redacted_text[:start] + redaction_token + redacted_text[end:]
            
            redaction_count += 1
            
            # Track confidence scores by category
            if entity.category not in confidence_scores:
                confidence_scores[entity.category] = []
            confidence_scores[entity.category].append(entity.confidence_score)
        
        # Calculate average confidence scores per category
        avg_confidence_scores = {
            category: sum(scores) / len(scores)
            for category, scores in confidence_scores.items()
        }
        
        result = RedactionResult(
            original_text=text,
            redacted_text=redacted_text,
            entities_found=entities,
            redaction_count=redaction_count,
            confidence_scores=avg_confidence_scores
        )
        
        logger.info("Text redaction completed",
                   entities_detected=len(entities),
                   redactions_made=redaction_count,
                   avg_confidence=avg_confidence_scores)
        
        return result
    
    def analyze_document_risk(self, text: str) -> Dict[str, Any]:
        """
        Analyze document for PII risk assessment
        
        Args:
            text: Document text to analyze
            
        Returns:
            Risk analysis report
        """
        entities = self.detect_pii_entities(text)
        
        # Count entities by category
        category_counts = {}
        high_risk_entities = []
        
        for entity in entities:
            category = entity.category
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1
            
            # High-risk entities (low confidence or sensitive categories)
            if (entity.confidence_score < 0.7 or 
                entity.category in ['CreditCardNumber', 'PhoneNumber', 'Address']):
                high_risk_entities.append(entity)
        
        # Calculate risk score
        risk_multipliers = {
            'CreditCardNumber': 5,
            'PhoneNumber': 3,
            'Address': 4,
            'Person': 2,
            'Email': 2
        }
        
        risk_score = sum(
            count * risk_multipliers.get(category, 1)
            for category, count in category_counts.items()
        )
        
        risk_level = 'LOW'
        if risk_score > 20:
            risk_level = 'HIGH'
        elif risk_score > 10:
            risk_level = 'MEDIUM'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'total_entities': len(entities),
            'category_breakdown': category_counts,
            'high_risk_entities': len(high_risk_entities),
            'recommendations': self._get_risk_recommendations(risk_level, category_counts)
        }
    
    def _get_risk_recommendations(self, risk_level: str, categories: Dict[str, int]) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        if risk_level == 'HIGH':
            recommendations.append("Immediate redaction recommended before sharing")
            recommendations.append("Consider additional security measures")
        
        if 'CreditCardNumber' in categories:
            recommendations.append("Credit card numbers detected - ensure PCI compliance")
        
        if 'PhoneNumber' in categories:
            recommendations.append("Phone numbers found - verify consent for data processing")
        
        if 'Address' in categories:
            recommendations.append("Physical addresses detected - consider geographical privacy")
        
        return recommendations
