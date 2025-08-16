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
        
        # Enhanced regex patterns with contextual detection
        self.custom_patterns = {
            'credit_card': [
                re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),  # Standard format
                re.compile(r'\b\d{13,19}\b'),  # Generic long number
                re.compile(r'(?i)(?:card|cc|credit)\s*:?\s*(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})', re.IGNORECASE),
            ],
            'phone': [
                re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),  # Standard
                re.compile(r'\(\d{3}\)\s?\d{3}-?\d{4}'),  # (555) 123-4567 format
                re.compile(r'(?i)(?:phone|tel|mobile|cell)\s*:?\s*(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', re.IGNORECASE),
                re.compile(r'(?i)(?:contact|call)\s*:?\s*(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', re.IGNORECASE),
            ],
            'ssn': [
                re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # Standard SSN
                re.compile(r'\b\d{3}\s\d{2}\s\d{4}\b'),  # Space separated
                re.compile(r'\b\d{9}\b'),  # No separators
                re.compile(r'(?i)(?:ssn|social\s*security)\s*:?\s*(\d{3}[-\s]?\d{2}[-\s]?\d{4})', re.IGNORECASE),
            ],
            'email': [
                re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                re.compile(r'(?i)(?:email|e-mail)\s*:?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', re.IGNORECASE),
            ],
            'address': [
                re.compile(r'\b\d{1,5}\s+[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Ct|Court|Circle|Cir|Place|Pl)\b', re.IGNORECASE),
                re.compile(r'(?i)(?:address|addr)\s*:?\s*(\d{1,5}\s+[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd))', re.IGNORECASE),
            ],
            'name_context': [
                re.compile(r'(?i)(?:name|employee|person|contact)\s*:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', re.IGNORECASE),
                re.compile(r'(?i)(?:from|to|by|signed)\s*:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', re.IGNORECASE),
            ]
        }
        
        logger.info("Azure AI Redactor initialized", 
                   threshold=self.confidence_threshold,
                   categories=self.config.pii_categories)
    
    def detect_pii_entities(self, text: str) -> List[PIIEntity]:
        """
        Detect PII entities using hybrid approach: Azure Text Analytics + enhanced regex
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected PII entities from both Azure and regex
        """
        all_entities = []
        
        try:
            # First, try Azure Text Analytics
            max_chars = 5000
            chunks = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
            
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
            
            logger.info("Azure PII detection completed", 
                       azure_entities=len(all_entities))
            
        except Exception as e:
            logger.error("Azure PII detection failed", error=str(e))
        
        # ALWAYS run enhanced regex patterns as well (hybrid approach)
        regex_entities = self._fallback_detection(text)
        logger.info("Regex PII detection completed", 
                   regex_entities=len(regex_entities))
        
        # Combine and deduplicate entities
        combined_entities = all_entities + regex_entities
        
        # Remove duplicates and overlaps (keep highest confidence)
        unique_entities = []
        processed_ranges = []
        
        # Sort by confidence score (highest first)
        for entity in sorted(combined_entities, key=lambda x: -x.confidence_score):
            entity_range = range(entity.offset, entity.offset + entity.length)
            
            # Check for overlap with existing entities
            overlap = any(
                len(set(entity_range) & set(range(start, end))) > 0
                for start, end in processed_ranges
            )
            
            if not overlap:
                unique_entities.append(entity)
                processed_ranges.append((entity.offset, entity.offset + entity.length))
        
        logger.info("Hybrid PII detection completed", 
                   total_unique_entities=len(unique_entities),
                   azure_found=len(all_entities),
                   regex_found=len(regex_entities))
        
        return unique_entities
    
    def _fallback_detection(self, text: str) -> List[PIIEntity]:
        """
        Enhanced fallback PII detection using contextual regex patterns
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected entities using regex with context awareness
        """
        entities = []
        
        for category, pattern_list in self.custom_patterns.items():
            for pattern in pattern_list:
                matches = pattern.finditer(text)
                for match in matches:
                    # For contextual patterns, extract the actual PII from the capture group
                    if match.groups():
                        # Use the captured group (the actual PII data)
                        pii_text = match.group(1)
                        # Find the position of the PII text within the full match
                        full_match = match.group(0)
                        pii_start = full_match.find(pii_text)
                        offset = match.start() + pii_start
                        length = len(pii_text)
                    else:
                        # Use the full match
                        pii_text = match.group(0)
                        offset = match.start()
                        length = len(pii_text)
                    
                    # Map internal categories to Azure categories
                    azure_category = {
                        'credit_card': 'CreditCardNumber',
                        'phone': 'PhoneNumber', 
                        'ssn': 'USPersonalIdentificationNumber',
                        'email': 'Email',
                        'address': 'Address',
                        'name_context': 'Person'
                    }.get(category, category)
                    
                    entity = PIIEntity(
                        text=pii_text,
                        category=azure_category,
                        subcategory=None,
                        confidence_score=0.95,  # High confidence for contextual matches
                        offset=offset,
                        length=length
                    )
                    entities.append(entity)
        
        # Remove duplicates (same text at overlapping positions)
        unique_entities = []
        seen_positions = set()
        
        for entity in sorted(entities, key=lambda x: (x.offset, -x.confidence_score)):
            # Check for overlap with existing entities
            entity_range = range(entity.offset, entity.offset + entity.length)
            overlap = any(
                pos in entity_range 
                for existing_start, existing_end in seen_positions
                for pos in range(existing_start, existing_end)
            )
            
            if not overlap:
                unique_entities.append(entity)
                seen_positions.add((entity.offset, entity.offset + entity.length))
        
        logger.info("Enhanced fallback detection completed", 
                   entities=len(unique_entities),
                   categories=[e.category for e in unique_entities])
        return unique_entities
    
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
