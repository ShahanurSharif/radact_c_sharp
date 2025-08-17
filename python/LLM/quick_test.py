#!/usr/bin/env python3
"""Quick test of LLM redaction system"""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.append(str(Path(__file__).parent))

from llm_config import LLMConfig
from gpt4o_redactor import GPT4oMiniRedactor

def main():
    print("Testing GPT-4o-mini redaction...")
    
    # Test configuration
    config = LLMConfig()
    print(f'Config validation: {config.validate_configuration()}')
    print(f'Endpoint: {config.endpoint}')
    print(f'Deployment: {config.deployment_name}')
    print()
    
    # Test basic redaction
    redactor = GPT4oMiniRedactor(config)
    test_text = 'Contact John Smith at (555) 123-4567 or email john.smith@email.com'
    
    print(f'Testing text: {test_text}')
    print("Processing...")
    
    result = redactor.redact_text(test_text)
    
    print(f'Original: {test_text}')
    print(f'Redacted: {result.redacted_text}')
    print(f'Entities found: {result.total_entities}')
    print(f'Cost: ${result.processing_cost:.6f}')
    print(f'Categories: {list(result.redaction_summary.keys())}')
    
    for entity in result.entities_found:
        print(f'  - "{entity.text}" -> {entity.category} (confidence: {entity.confidence:.2f})')

if __name__ == "__main__":
    main()
