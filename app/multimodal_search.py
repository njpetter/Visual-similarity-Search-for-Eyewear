"""
Multi-modal search: Combine image search with text modifiers
Example: Upload black frame image + text "but in tortoise shell color"
"""
import re
import logging
from typing import List, Tuple, Dict, Optional
from sqlalchemy.orm import Session

from app.models import Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiModalSearch:
    """
    Processes text modifiers to adjust search results
    Supports color/style modifications like "tortoise shell", "metal", "transparent"
    """
    
    # Color keywords mapping
    COLOR_KEYWORDS = {
        'tortoise': ['tortoise', 'tortoiseshell', 'brown', 'patterned'],
        'black': ['black', 'dark'],
        'brown': ['brown', 'tortoise'],
        'transparent': ['transparent', 'clear', 'see-through'],
        'metal': ['metal', 'metallic', 'silver', 'gold', 'bronze'],
        'colorful': ['colorful', 'colored', 'bright', 'vibrant']
    }
    
    # Style keywords mapping
    STYLE_KEYWORDS = {
        'aviator': ['aviator', 'pilot'],
        'wayfarer': ['wayfarer', 'classic'],
        'round': ['round', 'circular'],
        'square': ['square', 'angular'],
        'cat eye': ['cat eye', 'cat-eye'],
        'rimless': ['rimless', 'rim-less', 'frameless']
    }
    
    def __init__(self):
        """Initialize multi-modal search processor"""
        pass
    
    def parse_modifier(self, text: Optional[str]) -> Dict[str, str]:
        """
        Parse text modifier to extract desired attributes
        
        Args:
            text: Text modifier like "but in tortoise shell color"
            
        Returns:
            Dictionary with extracted attributes (color, style, etc.)
        """
        if not text:
            return {}
        
        text_lower = text.lower()
        modifiers = {}
        
        # Extract color preference
        for color, keywords in self.COLOR_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    modifiers['color'] = color.title()
                    break
            if 'color' in modifiers:
                break
        
        # Extract style preference
        for style, keywords in self.STYLE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    modifiers['style'] = style.title()
                    break
            if 'style' in modifiers:
                break
        
        logger.info(f"Parsed text modifier '{text}' -> {modifiers}")
        return modifiers
    
    def apply_modifier_filter(
        self, 
        results: List[Tuple[int, float]], 
        modifiers: Dict[str, str],
        db: Session
    ) -> List[Tuple[int, float]]:
        """
        Filter and re-rank results based on text modifiers
        
        Args:
            results: List of (product_id, similarity_score) tuples
            modifiers: Dictionary with color/style preferences
            db: Database session
            
        Returns:
            Filtered and re-ranked results
        """
        if not modifiers:
            return results
        
        filtered_results = []
        boosted_results = []
        
        for product_id, similarity_score in results:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                continue
            
            matches_modifier = True
            boost_factor = 1.0
            
            # Check color match
            if 'color' in modifiers:
                desired_color = modifiers['color'].lower()
                product_tags = (product.style_tags or "").lower()
                product_material = (product.material or "").lower()
                
                # Check if product matches desired color
                color_match = (
                    desired_color in product_tags or
                    desired_color in product_material or
                    self._check_color_match(desired_color, product_tags, product_material)
                )
                
                if color_match:
                    boost_factor *= 1.3  # Boost matching products
                else:
                    boost_factor *= 0.7  # Reduce non-matching products
            
            # Check style match
            if 'style' in modifiers:
                desired_style = modifiers['style'].lower()
                product_tags = (product.style_tags or "").lower()
                
                style_match = desired_style in product_tags
                
                if style_match:
                    boost_factor *= 1.2
                else:
                    boost_factor *= 0.9
            
            # Apply boost
            new_score = similarity_score * boost_factor
            
            if boost_factor >= 1.0:
                boosted_results.append((product_id, new_score))
            else:
                filtered_results.append((product_id, new_score))
        
        # Combine: boosted first, then filtered
        boosted_results.sort(key=lambda x: x[1], reverse=True)
        filtered_results.sort(key=lambda x: x[1], reverse=True)
        
        final_results = boosted_results + filtered_results
        return final_results
    
    def _check_color_match(self, desired_color: str, tags: str, material: str) -> bool:
        """Check if product color matches desired color"""
        # Mapping for common color variations
        color_synonyms = {
            'tortoise': ['tortoise', 'tortoiseshell', 'brown', 'patterned', 'acetate'],
            'black': ['black', 'dark'],
            'metal': ['metal', 'metallic', 'titanium', 'steel'],
            'transparent': ['transparent', 'clear', 'acetate']
        }
        
        synonyms = color_synonyms.get(desired_color, [desired_color])
        
        for synonym in synonyms:
            if synonym in tags or synonym in material:
                return True
        
        return False

