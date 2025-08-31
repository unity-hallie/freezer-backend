#!/usr/bin/env python3
"""
Test fallback parsing without Gemini API
"""
from ai_shopping_parser import ShoppingListParser

# Sample data
SAMPLE_CONTENT = """
- Organic Chicken Breast 2.5 lbs @ $8.99/lb - $22.48
- Whole Milk 1 Gallon - $3.49
- Large Eggs 1 dozen - $2.99
- Frozen Broccoli 16 oz - $2.49
- Greek Yogurt Plain 32 oz - $4.99
- Ground Beef 1 lb - $5.99
- Ice Cream Vanilla 48 oz - $4.99
"""

def test_fallback_parsing():
    parser = ShoppingListParser()
    # Force fallback by calling it directly
    items = parser._fallback_parse(SAMPLE_CONTENT)
    
    print(f"🔧 Fallback parser found {len(items)} items:")
    for item in items:
        print(f"  • {item.name} - {item.quantity} {item.unit} -> {item.category}")

if __name__ == "__main__":
    test_fallback_parsing()