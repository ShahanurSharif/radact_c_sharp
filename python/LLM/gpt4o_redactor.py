"""
GPT-4o-mini Redaction Engine
Intelligent PII detection and redaction using Azure OpenAI
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import tiktoken
from openai import AzureOpenAI
import structlog

from llm_config import LLMConfig

logger = structlog.get_logger(__name__)

@dataclass
class PIIEntity:
    """Represents a detected PII entity"""
    text: str
    category: str
    confidence: float
    start_pos: int
    end_pos: int
    context: str
    reasoning: Optional[str] = None

@dataclass
class RedactionResult:
    """Results from LLM-based document redaction"""
    original_text: str
    redacted_text: str
    entities_found: List[PIIEntity]
    total_entities: int
    redaction_summary: Dict[str, int]
    processing_cost: float
    tokens_used: int
    confidence_scores: Dict[str, float]

@dataclass
class CostTracker:
    """Track processing costs"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost: float = 0.0
    requests_made: int = 0

class GPT4oMiniRedactor:
    """GPT-4o-mini powered document redaction engine"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize GPT-4o-mini redactor
        
        Args:
            config: LLM configuration instance
        """
        self.config = config or LLMConfig()
        
        if not self.config.validate_configuration():
            raise ValueError("Invalid LLM configuration")
        
        # Initialize Azure OpenAI client
        openai_config = self.config.get_openai_config()
        self.client = AzureOpenAI(**openai_config)
        
        # Initialize tokenizer for cost calculation
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        
        # Cost tracking
        self.cost_tracker = CostTracker()
        
        # Redaction patterns
        self.redaction_patterns = self.config.get_redaction_patterns()
        
        logger.info("GPT-4o-mini redactor initialized", 
                   deployment=self.config.deployment_name,
                   categories=self.config.pii_categories)
    
    def _create_pii_detection_prompt(self, text: str) -> str:
        """Create optimized prompt for PII detection"""
        
        categories_desc = {
            'names': 'Full names of people (first name + last name)',
            'phone_numbers': 'Phone numbers in any format (xxx-xxx-xxxx, (xxx) xxx-xxxx, etc.)',
            'emails': 'Email addresses',
            'addresses': 'Physical addresses (street addresses, not just city/state)',
            'ssn': 'Social Security Numbers (xxx-xx-xxxx format)',
            'credit_cards': 'Credit card numbers (any format)',
            'dates': 'Specific dates that could identify individuals',
            'ip_addresses': 'IP addresses'
        }
        
        active_categories = [cat for cat in self.config.pii_categories if cat in categories_desc]
        category_list = '\n'.join([f"- {cat}: {categories_desc[cat]}" for cat in active_categories])
        
        prompt = f"""You are an expert PII detection system. Analyze the following text and identify ALL personally identifiable information.

CATEGORIES TO DETECT:
{category_list}

INSTRUCTIONS:
1. Find every instance of PII in the text
2. For each PII found, provide: exact text, category, confidence (0-1), start position, end position, and brief reasoning
3. Be very thorough - don't miss any PII
4. Pay special attention to contextual clues (e.g., "Phone:", "SSN:", "Email:")
5. Include 2-3 words of context around each PII item

RESPONSE FORMAT (JSON):
{{
  "entities": [
    {{
      "text": "exact PII text found",
      "category": "one of the categories above",
      "confidence": 0.95,
      "start_pos": 123,
      "end_pos": 135,
      "context": "surrounding text context",
      "reasoning": "why this is PII"
    }}
  ]
}}

TEXT TO ANALYZE:
{text}

RESPONSE (JSON only):"""
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> List[PIIEntity]:
        """Parse LLM response into PIIEntity objects"""
        entities = []
        
        try:
            # Clean up response - sometimes LLM adds extra text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("No JSON found in LLM response")
                return entities
            
            json_text = response_text[json_start:json_end]
            
            # Parse JSON
            data = json.loads(json_text)
            
            if 'entities' not in data:
                logger.error("No 'entities' key in LLM response")
                return entities
            
            for entity_data in data['entities']:
                entity = PIIEntity(
                    text=entity_data.get('text', ''),
                    category=entity_data.get('category', ''),
                    confidence=float(entity_data.get('confidence', 0.0)),
                    start_pos=int(entity_data.get('start_pos', 0)),
                    end_pos=int(entity_data.get('end_pos', 0)),
                    context=entity_data.get('context', ''),
                    reasoning=entity_data.get('reasoning', '')
                )
                
                # Filter by confidence threshold
                if entity.confidence >= self.config.confidence_threshold:
                    entities.append(entity)
            
            logger.info("Parsed LLM response", entities_found=len(entities))
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM JSON response", error=str(e))
        except Exception as e:
            logger.error("Error parsing LLM response", error=str(e))
        
        return entities
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks for processing"""
        
        if len(text) <= self.config.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.config.chunk_size
            
            # Try to break at a sentence or paragraph
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                search_start = max(end - 100, start)
                sentence_breaks = [m.end() for m in re.finditer(r'[.!?]\s+', text[search_start:end])]
                
                if sentence_breaks:
                    # Use the last sentence break
                    end = search_start + sentence_breaks[-1]
            
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.config.overlap_size if end < len(text) else end
        
        logger.info("Text chunked", total_chunks=len(chunks))
        return chunks
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate processing cost for GPT-4o-mini"""
        
        # GPT-4o-mini pricing
        input_cost_per_1k = 0.000150  # $0.150 per 1M tokens = $0.000150 per 1K
        output_cost_per_1k = 0.000600  # $0.600 per 1M tokens = $0.000600 per 1K
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return input_cost + output_cost
    
    def detect_pii_entities(self, text: str) -> List[PIIEntity]:
        """
        Detect PII entities using GPT-4o-mini
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected PII entities
        """
        all_entities = []
        chunks = self._chunk_text(text)
        
        for i, chunk in enumerate(chunks):
            logger.info("Processing chunk", chunk_num=i+1, total_chunks=len(chunks))
            
            # Create detection prompt
            prompt = self._create_pii_detection_prompt(chunk)
            
            # Count input tokens
            input_tokens = len(self.tokenizer.encode(prompt))
            
            try:
                # Call GPT-4o-mini
                model_params = self.config.get_model_params()
                response = self.client.chat.completions.create(
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    **model_params
                )
                
                # Extract response
                response_text = response.choices[0].message.content
                output_tokens = response.usage.completion_tokens
                
                # Update cost tracking
                chunk_cost = self._calculate_cost(input_tokens, output_tokens)
                self.cost_tracker.input_tokens += input_tokens
                self.cost_tracker.output_tokens += output_tokens
                self.cost_tracker.total_cost += chunk_cost
                self.cost_tracker.requests_made += 1
                
                # Parse entities
                chunk_entities = self._parse_llm_response(response_text)
                
                # Adjust positions for chunked text
                chunk_start = sum(len(chunks[j]) - self.config.overlap_size for j in range(i))
                for entity in chunk_entities:
                    entity.start_pos += chunk_start
                    entity.end_pos += chunk_start
                
                all_entities.extend(chunk_entities)
                
                logger.info("Chunk processed", 
                           entities_found=len(chunk_entities),
                           cost=chunk_cost,
                           tokens_used=input_tokens + output_tokens)
                
            except Exception as e:
                logger.error("Error processing chunk", chunk_num=i+1, error=str(e))
                continue
        
        # Remove duplicates and overlaps
        unique_entities = self._deduplicate_entities(all_entities)
        
        logger.info("PII detection completed", 
                   total_entities=len(unique_entities),
                   total_cost=self.cost_tracker.total_cost,
                   total_tokens=self.cost_tracker.input_tokens + self.cost_tracker.output_tokens)
        
        return unique_entities
    
    def _deduplicate_entities(self, entities: List[PIIEntity]) -> List[PIIEntity]:
        """Remove duplicate and overlapping entities"""
        if not entities:
            return entities
        
        # Sort by position
        sorted_entities = sorted(entities, key=lambda x: x.start_pos)
        unique_entities = []
        
        for entity in sorted_entities:
            # Check for overlap with existing entities
            overlap_found = False
            for existing in unique_entities:
                if (entity.start_pos < existing.end_pos and 
                    entity.end_pos > existing.start_pos):
                    # Overlapping - keep the one with higher confidence
                    if entity.confidence > existing.confidence:
                        unique_entities.remove(existing)
                        unique_entities.append(entity)
                    overlap_found = True
                    break
            
            if not overlap_found:
                unique_entities.append(entity)
        
        return sorted(unique_entities, key=lambda x: x.start_pos)
    
    def redact_text(self, text: str) -> RedactionResult:
        """
        Redact PII from text using GPT-4o-mini detection
        
        Args:
            text: Original text to redact
            
        Returns:
            RedactionResult with original and redacted text
        """
        # Reset cost tracking for this operation
        self.cost_tracker = CostTracker()
        
        # Detect entities
        entities = self.detect_pii_entities(text)
        
        # Sort entities by position (reverse order for replacement)
        sorted_entities = sorted(entities, key=lambda x: x.start_pos, reverse=True)
        
        # Apply redactions
        redacted_text = text
        redaction_summary = {}
        
        for entity in sorted_entities:
            # Get redaction pattern
            redaction_token = self.redaction_patterns.get(
                entity.category, 
                f'[{entity.category.upper()}_REDACTED]'
            )
            
            # Replace in text
            redacted_text = (
                redacted_text[:entity.start_pos] + 
                redaction_token + 
                redacted_text[entity.end_pos:]
            )
            
            # Update summary
            if entity.category not in redaction_summary:
                redaction_summary[entity.category] = 0
            redaction_summary[entity.category] += 1
        
        # Calculate confidence scores by category
        confidence_scores = {}
        for entity in entities:
            if entity.category not in confidence_scores:
                confidence_scores[entity.category] = []
            confidence_scores[entity.category].append(entity.confidence)
        
        # Average confidence per category
        avg_confidence_scores = {
            category: sum(scores) / len(scores)
            for category, scores in confidence_scores.items()
        }
        
        result = RedactionResult(
            original_text=text,
            redacted_text=redacted_text,
            entities_found=entities,
            total_entities=len(entities),
            redaction_summary=redaction_summary,
            processing_cost=self.cost_tracker.total_cost,
            tokens_used=self.cost_tracker.input_tokens + self.cost_tracker.output_tokens,
            confidence_scores=avg_confidence_scores
        )
        
        logger.info("Text redaction completed",
                   entities_redacted=len(entities),
                   categories=list(redaction_summary.keys()),
                   total_cost=self.cost_tracker.total_cost)
        
        return result
    
    def get_cost_estimate(self, text: str) -> Dict[str, Any]:
        """
        Estimate processing cost without actually processing
        
        Args:
            text: Text to estimate cost for
            
        Returns:
            Cost estimation details
        """
        # Estimate tokens
        estimated_tokens = len(self.tokenizer.encode(text))
        
        # Add prompt overhead (approximately 500 tokens per chunk)
        chunks = self._chunk_text(text)
        prompt_overhead = len(chunks) * 500
        
        total_input_tokens = estimated_tokens + prompt_overhead
        estimated_output_tokens = total_input_tokens * 0.1  # Assume 10% output ratio
        
        estimated_cost = self._calculate_cost(total_input_tokens, estimated_output_tokens)
        
        return {
            'estimated_input_tokens': total_input_tokens,
            'estimated_output_tokens': estimated_output_tokens,
            'estimated_total_tokens': total_input_tokens + estimated_output_tokens,
            'estimated_cost_usd': round(estimated_cost, 6),
            'chunks_required': len(chunks),
            'api_calls_needed': len(chunks)
        }
