#!/usr/bin/env python3
"""Test different Azure OpenAI configurations"""

import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

def test_deployment(deployment_name, api_version="2024-10-21"):
    """Test a specific deployment configuration"""
    
    print(f"\nTesting deployment: {deployment_name}")
    print(f"API version: {api_version}")
    
    try:
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=api_version,
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        # Test with a simple prompt
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "user", "content": "Say 'Hello' if this works"}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        print(f"✅ SUCCESS: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def main():
    print("Testing Azure OpenAI Deployments")
    print("=" * 40)
    print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    print(f"API Key present: {'Yes' if os.getenv('AZURE_OPENAI_API_KEY') else 'No'}")
    
    # Common deployment names for GPT-4o-mini
    deployment_names = [
        "gpt-4o-mini",
        "gpt-4o-mini-2024-07-18",
        "gpt-4o-mini-deployment",
        "gpt4omini",
        "GPT-4o-mini",
        "GPT4omini"
    ]
    
    # Test different API versions
    api_versions = [
        "2024-10-21",
        "2024-07-18", 
        "2024-06-01",
        "2024-05-01-preview",
        "2024-02-01"
    ]
    
    success_found = False
    
    for deployment in deployment_names:
        for version in api_versions:
            if test_deployment(deployment, version):
                print(f"\n🎉 Working configuration found!")
                print(f"   Deployment: {deployment}")
                print(f"   API Version: {version}")
                success_found = True
                break
        if success_found:
            break
    
    if not success_found:
        print("\n❌ No working configuration found")
        print("\nTroubleshooting suggestions:")
        print("1. Check deployment name in Azure OpenAI Studio")
        print("2. Verify API key and endpoint")
        print("3. Try different API versions")
        print("4. Check Azure OpenAI resource region")

if __name__ == "__main__":
    main()
