import logging
from typing import List, Tuple, Dict
from sqlalchemy.orm import Session
from app.models import Product
logger = logging.getLogger(__name__)
class MultiModalSearch:
    def __init__(self):
        self.colors = {
            'black', 'blue', 'brown', 'gold', 'silver', 'gray', 'grey', 
            'red', 'green', 'yellow', 'tortoise', 'transparent', 'clear', 'pink'
        }
        self.materials = {'metal', 'plastic', 'acetate', 'titanium', 'polycarbonate'}
        self.styles = {'aviator', 'wayfarer', 'round', 'cat eye', 'square', 'rimless', 'rectangle', 'oval', 'retro'}
    def parse_modifier(self, text: str) -> Dict[str, str]:
        if not text:
            return {}
        text = text.lower().strip()
        modifiers = {}
        for color in self.colors:
            if color in text:
                modifiers['color'] = color.capitalize()
                if color == 'tortoise': modifiers['color'] = 'Tortoise'
                break
        for material in self.materials:
            if material in text:
                modifiers['material'] = material.capitalize()
                break
        for style in self.styles:
            if style in text:
                modifiers['style'] = style.title()
                break
        logger.info(f"Parsed modifiers from '{text}': {modifiers}")
        return modifiers
    def apply_modifier_filter(self, 
                            search_results: List[Tuple[int, float]], 
                            modifiers: Dict[str, str], 
                            db: Session) -> List[Tuple[int, float]]:
        if not modifiers:
            return search_results
        filtered_results = []
        product_ids = [pid for pid, _ in search_results]
        if not product_ids:
            return []
        products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        product_map = {p.id: p for p in products}
        for pid, score in search_results:
            product = product_map.get(pid)
            if not product:
                continue
            is_match = True
            tags = (product.style_tags or "").lower()
            material = (product.material or "").lower()
            if 'color' in modifiers:
                target_color = modifiers['color'].lower()
                if target_color not in tags and target_color not in material:
                    is_match = False
            if is_match and 'material' in modifiers:
                target_mat = modifiers['material'].lower()
                if target_mat not in material and target_mat not in tags:
                    is_match = False
            if is_match and 'style' in modifiers:
                target_style = modifiers['style'].lower()
                if target_style not in tags:
                    is_match = False
            if is_match:
                filtered_results.append((pid, score * 1.05))
        logger.info(f"Filtered results from {len(search_results)} to {len(filtered_results)}")
        return filtered_results