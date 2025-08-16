"""
Demo Mode Azure AI Redactor
Demonstrates functionality using regex patterns when Azure credentials are not available
"""

import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class DemoPIIEntity:
    """Demo version of PII entity"""
    text: str
    category: str
    subcategory: Optional[str]
    confidence_score: float
    offset: int
    length: int

@dataclass
class DemoRedactionResult:
    """Demo version of redaction result"""
    original_text: str
    redacted_text: str
    entities_found: List[DemoPIIEntity]
    redaction_count: int
    confidence_scores: Dict[str, float]

class DemoAzureAIRedactor:
    """Demo Azure AI redactor using regex patterns"""
    
    def __init__(self):
        """Initialize demo redactor with regex patterns"""
        self.confidence_threshold = 0.8
        
        # Enhanced regex patterns for demo with contextual awareness
        self.patterns = {
            'Person': [
                re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'),  # First Last
                re.compile(r'\b[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+\b'),  # First M. Last
                re.compile(r'(?i)(?:name|employee|person|contact)\s*:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', re.IGNORECASE),
                re.compile(r'(?i)(?:from|to|by|signed)\s*:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', re.IGNORECASE),
            ],
            'PhoneNumber': [
                re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),
                re.compile(r'\(\d{3}\)\s?\d{3}-?\d{4}'),  # (555) 123-4567 format
                re.compile(r'(?i)(?:phone|tel|mobile|cell)\s*:?\s*(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', re.IGNORECASE),
                re.compile(r'(?i)(?:contact|call)\s*:?\s*(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', re.IGNORECASE),
            ],
            'Address': [
                re.compile(r'\b\d{1,5}\s+[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Ct|Court|Circle|Cir|Place|Pl)\b', re.IGNORECASE),
                re.compile(r'(?i)(?:address|addr)\s*:?\s*(\d{1,5}\s+[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd))', re.IGNORECASE),
            ],
            'CreditCardNumber': [
                re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
                re.compile(r'\b\d{13,19}\b'),  # Generic card number
                re.compile(r'(?i)(?:card|cc|credit)\s*:?\s*(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})', re.IGNORECASE),
            ],
            'Email': [
                re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                re.compile(r'(?i)(?:email|e-mail)\s*:?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', re.IGNORECASE),
            ],
            'IPAddress': [
                re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            ],
            'PersonType': [
                re.compile(r'\b(?:CEO|CFO|CTO|Manager|Director|President|Vice President|Analyst|Engineer|Developer)\b', re.IGNORECASE),
            ],
            'USPersonalIdentificationNumber': [
                re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # Standard SSN
                re.compile(r'\b\d{3}\s\d{2}\s\d{4}\b'),  # Space separated
                re.compile(r'(?i)(?:ssn|social\s*security)\s*:?\s*(\d{3}[-\s]?\d{2}[-\s]?\d{4})', re.IGNORECASE),
            ]
        }
        
        logger.info("Demo Azure AI Redactor initialized with regex patterns")
    
    def detect_pii_entities(self, text: str) -> List[DemoPIIEntity]:
        """Detect PII entities using enhanced regex patterns with context awareness"""
        entities = []
        
        for category, pattern_list in self.patterns.items():
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
                    
                    entity = DemoPIIEntity(
                        text=pii_text,
                        category=category,
                        subcategory=None,
                        confidence_score=0.95 if match.groups() else 0.9,  # Higher confidence for contextual matches
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
        
        logger.info("Enhanced demo PII detection completed", entities_found=len(unique_entities))
        return unique_entities
    
    def redact_text(self, text: str, custom_redaction_map: Optional[Dict[str, str]] = None) -> DemoRedactionResult:
        """Redact PII entities from text"""
        entities = self.detect_pii_entities(text)
        
        # Default redaction patterns
        default_redaction_map = {
            'Person': '[NAME_REDACTED]',
            'PersonType': '[TITLE_REDACTED]',
            'PhoneNumber': '[PHONE_REDACTED]',
            'Address': '[ADDRESS_REDACTED]',
            'CreditCardNumber': '[CREDIT_CARD_REDACTED]',
            'Email': '[EMAIL_REDACTED]',
            'IPAddress': '[IP_ADDRESS_REDACTED]',
        }
        
        # Merge custom redaction map if provided
        redaction_map = default_redaction_map.copy()
        if custom_redaction_map:
            redaction_map.update(custom_redaction_map)
        
        # Sort entities by offset in reverse order
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
        
        result = DemoRedactionResult(
            original_text=text,
            redacted_text=redacted_text,
            entities_found=entities,
            redaction_count=redaction_count,
            confidence_scores=avg_confidence_scores
        )
        
        logger.info("Demo text redaction completed",
                   entities_detected=len(entities),
                   redactions_made=redaction_count)
        
        return result
    
    def analyze_document_risk(self, text: str) -> Dict[str, Any]:
        """Analyze document for PII risk assessment"""
        entities = self.detect_pii_entities(text)
        
        # Count entities by category
        category_counts = {}
        high_risk_entities = []
        
        for entity in entities:
            category = entity.category
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1
            
            # High-risk entities (sensitive categories)
            if entity.category in ['CreditCardNumber', 'PhoneNumber', 'Address']:
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
            'recommendations': self._get_risk_recommendations(risk_level, category_counts),
            'demo_mode': True
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
        
        recommendations.append("🔧 Demo Mode: Using regex patterns - Azure AI would provide higher accuracy")
        
        return recommendations
