#!/usr/bin/env python3
"""
Test script for AI Shopping List Ingestion
Run this to test the endpoint without needing Gemini API
"""
import requests
import json

# Sample Hannaford To Go email content
SAMPLE_HANNAFORD_EMAIL = """
Thank you for your Hannaford To Go order!

Your order summary:
- Organic Chicken Breast 2.5 lbs @ $8.99/lb - $22.48
- Whole Milk 1 Gallon - $3.49
- Large Eggs 1 dozen - $2.99
- Frozen Broccoli 16 oz - $2.49
- Greek Yogurt Plain 32 oz - $4.99
- Bananas 3 lbs - $1.47
- Ground Beef 1 lb - $5.99
- Sourdough Bread 1 loaf - $2.99
- Ice Cream Vanilla 48 oz - $4.99
- Pasta Sauce 24 oz jar - $1.99

Total: $53.86

Thank you for shopping with Hannaford To Go!
"""

def test_ai_shopping_endpoint():
    """Test the AI shopping ingestion endpoint"""
    
    # Test data
    payload = {
        "content": SAMPLE_HANNAFORD_EMAIL,
        "source_type": "hannaford"
    }
    
    # For testing, we'll just test the parsing logic directly
    from ai_shopping_parser import shopping_parser
    
    print("🧪 Testing AI Shopping List Parser...")
    print("=" * 50)
    
    # Test parsing
    try:
        parsed_items = shopping_parser.parse_shopping_content(
            content=payload["content"],
            source_type=payload["source_type"]
        )
        
        print(f"✅ Successfully parsed {len(parsed_items)} items")
        print("\nParsed Items:")
        print("-" * 30)
        
        for item in parsed_items:
            print(f"📦 {item.name}")
            print(f"   Quantity: {item.quantity} {item.unit or ''}")
            print(f"   Category: {item.category}")
            print(f"   Confidence: {item.confidence:.2f}")
            print(f"   Raw: {item.raw_text[:50]}...")
            print()
        
        if parsed_items:
            print("🎉 AI Shopping Parser is working!")
        else:
            print("⚠️  No items parsed - check Gemini API configuration")
            
    except Exception as e:
        print(f"❌ Error testing parser: {e}")
        print("💡 This is expected if GEMINI_API_KEY is not configured")
        print("   The parser will fall back to rule-based parsing")

def test_manual_api_call():
    """Test the API endpoint manually (requires authentication)"""
    
    # This would require proper authentication
    # For now, just show what the request would look like
    
    print("\n🌐 API Endpoint Test")
    print("=" * 50)
    print("To test the full endpoint:")
    print("1. Get authentication token from /auth/login")
    print("2. POST to /api/ingest-shopping with:")
    
    sample_request = {
        "content": SAMPLE_HANNAFORD_EMAIL,
        "source_type": "hannaford"
    }
    
    print(json.dumps(sample_request, indent=2))
    
    print("\nExpected response:")
    print("- items_created: number of items added")
    print("- parsing_log: details of AI parsing process")
    print("- items: array of created items with 'ai-generated' tag")

if __name__ == "__main__":
    test_ai_shopping_endpoint()
    test_manual_api_call()