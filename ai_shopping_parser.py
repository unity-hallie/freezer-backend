"""
AI-powered shopping list parsing using Google Gemini API
Extracts grocery items from email receipts and shopping lists
"""
import google.generativeai as genai
from typing import List, Dict, Optional
from pydantic import BaseModel
import json
import re
from decouple import config
import logging

# Configure Gemini AI
GEMINI_API_KEY = config('GEMINI_API_KEY', default=None)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

logger = logging.getLogger(__name__)

class ParsedItem(BaseModel):
    name: str
    quantity: Optional[float] = 1.0
    unit: Optional[str] = None
    category: str  # freezer, fridge, pantry
    confidence: float  # 0.0 - 1.0
    raw_text: str  # original text matched

class ShoppingListParser:
    """Parse grocery shopping lists and receipts using AI"""
    
    def __init__(self):
        if not GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not configured - AI parsing disabled")
            self.model = None
        else:
            self.model = genai.GenerativeModel('gemini-pro')
    
    def parse_shopping_content(self, content: str, source_type: str = "unknown") -> List[ParsedItem]:
        """
        Parse shopping list content and extract items
        
        Args:
            content: Raw text content (email, receipt, list)
            source_type: hannaford, instacart, amazon_fresh, generic
        """
        if not self.model:
            logger.error("Gemini API not configured")
            return []
        
        try:
            # Create specialized prompt based on source
            prompt = self._create_parsing_prompt(content, source_type)
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            items = self._parse_ai_response(response.text, content)
            
            logger.info(f"Parsed {len(items)} items from {source_type} content")
            return items
            
        except Exception as e:
            logger.error(f"AI parsing failed: {e}")
            # Fallback to rule-based parsing
            return self._fallback_parse(content)
    
    def _create_parsing_prompt(self, content: str, source_type: str) -> str:
        """Create context-aware prompt for different shopping sources"""
        
        base_prompt = f"""
You are a grocery shopping assistant. Parse this {source_type} content and extract food items.

RULES:
1. Only extract actual food/grocery items (no services, fees, bags, etc.)
2. Determine the best storage location: "freezer", "fridge", or "pantry"
3. Extract quantity and unit when clear
4. Provide confidence score 0.0-1.0 based on clarity
5. Return ONLY valid JSON array, no other text

OUTPUT FORMAT:
[
  {{
    "name": "Chicken Breast",
    "quantity": 2.0,
    "unit": "lbs", 
    "category": "freezer",
    "confidence": 0.95,
    "raw_text": "Chicken Breast 2lb"
  }}
]

CONTENT TO PARSE:
{content[:2000]}
"""
        
        # Add source-specific guidance
        if source_type == "hannaford":
            base_prompt += """
HANNAFORD SPECIFIC:
- Items often have store codes/SKUs - ignore these
- Look for quantity patterns like "2 @ $3.99"
- Fresh items go to fridge, frozen to freezer, shelf-stable to pantry
"""
        elif source_type == "instacart":
            base_prompt += """
INSTACART SPECIFIC:
- Items may have replacement notes - focus on actual item purchased
- Quantities often in parentheses
- Check for "Fresh", "Frozen" category indicators
"""
        
        return base_prompt
    
    def _parse_ai_response(self, response_text: str, original_content: str) -> List[ParsedItem]:
        """Parse AI JSON response into ParsedItem objects"""
        try:
            # Clean response - sometimes AI adds extra text
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            else:
                json_str = response_text
            
            # Parse JSON
            items_data = json.loads(json_str)
            
            # Convert to ParsedItem objects
            items = []
            for item_data in items_data:
                try:
                    item = ParsedItem(**item_data)
                    # Validate category
                    if item.category not in ["freezer", "fridge", "pantry"]:
                        item.category = self._infer_category(item.name)
                    items.append(item)
                except Exception as e:
                    logger.warning(f"Skipping invalid item: {item_data}, error: {e}")
            
            return items
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI JSON response: {e}")
            logger.debug(f"Response was: {response_text}")
            return []
    
    def _fallback_parse(self, content: str) -> List[ParsedItem]:
        """Rule-based fallback parsing when AI fails"""
        items = []
        
        # Common grocery item patterns
        food_patterns = [
            r'(\d+\.?\d*)\s*(lbs?|pounds?|oz|ounces?|ct|count|each)?\s+([A-Za-z\s]+(?:chicken|beef|pork|fish|salmon|bread|milk|eggs|cheese|yogurt|butter|apples|bananas|carrots|onions|potatoes|rice|pasta|cereal))',
            r'([A-Za-z\s]+(?:chicken|beef|pork|fish|salmon|bread|milk|eggs|cheese|yogurt|butter|apples|bananas|carrots|onions|potatoes|rice|pasta|cereal))\s+(\d+\.?\d*)\s*(lbs?|pounds?|oz|ounces?|ct|count)?'
        ]
        
        for pattern in food_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    # Extract components
                    if groups[0].replace('.', '').isdigit():  # First group is quantity
                        quantity = float(groups[0]) if groups[0] else 1.0
                        unit = groups[1] if len(groups) > 1 else None
                        name = groups[2].strip() if len(groups) > 2 else "Unknown item"
                    else:  # First group is name
                        name = groups[0].strip()
                        quantity = float(groups[1]) if len(groups) > 1 and groups[1] else 1.0
                        unit = groups[2] if len(groups) > 2 else None
                    
                    item = ParsedItem(
                        name=name.title(),
                        quantity=quantity,
                        unit=unit,
                        category=self._infer_category(name),
                        confidence=0.6,  # Lower confidence for rule-based
                        raw_text=match.group()
                    )
                    items.append(item)
        
        return items[:20]  # Limit to 20 items for fallback
    
    def _infer_category(self, item_name: str) -> str:
        """Infer storage category from item name"""
        name_lower = item_name.lower()
        
        # Freezer items
        if any(word in name_lower for word in [
            'frozen', 'ice cream', 'chicken breast', 'ground beef', 
            'fish', 'salmon', 'shrimp', 'french fries', 'pizza'
        ]):
            return "freezer"
        
        # Fridge items  
        if any(word in name_lower for word in [
            'milk', 'yogurt', 'cheese', 'eggs', 'butter', 'lettuce',
            'carrots', 'fresh', 'produce', 'deli', 'meat'
        ]):
            return "fridge"
        
        # Default to pantry
        return "pantry"
    
    def validate_items(self, items: List[ParsedItem]) -> List[ParsedItem]:
        """Validate and clean parsed items"""
        validated = []
        
        for item in items:
            # Basic validation
            if not item.name or len(item.name.strip()) < 2:
                continue
                
            # Clean name
            item.name = item.name.strip().title()
            
            # Validate quantity
            if item.quantity and item.quantity <= 0:
                item.quantity = 1.0
                
            # Ensure confidence is in range
            item.confidence = max(0.0, min(1.0, item.confidence))
            
            validated.append(item)
        
        return validated

# Global instance
shopping_parser = ShoppingListParser()