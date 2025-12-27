"""
Feedback loop for learning from user interactions
"""
import logging
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models import Product, Feedback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeedbackSystem:
    """
    Manages feedback collection and product boosting
    """
    
    def __init__(self, db: Session):
        """
        Initialize feedback system
        
        Args:
            db: Database session
        """
        self.db = db
    
    def record_feedback(self, query_image_path: str, product_id: int, is_relevant: bool):
        """
        Record user feedback on a search result
        
        Args:
            query_image_path: Path to the query image
            product_id: Product ID that was clicked
            is_relevant: True if product was relevant, False otherwise
        """
        try:
            feedback = Feedback(
                query_image_path=query_image_path,
                product_id=product_id,
                is_relevant=1 if is_relevant else 0
            )
            self.db.add(feedback)
            
            # Update product statistics
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if product:
                if is_relevant:
                    product.click_count += 1
                    # Boost relevance score (simple moving average)
                    product.relevance_score = (
                        product.relevance_score * 0.9 + 1.0 * 0.1
                    )
                else:
                    # Decrease relevance score
                    product.relevance_score = (
                        product.relevance_score * 0.95 + 0.0 * 0.05
                    )
            
            self.db.commit()
            logger.info(f"Recorded feedback: product_id={product_id}, relevant={is_relevant}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recording feedback: {str(e)}")
            raise
    
    def boost_product(self, product_id: int, boost_factor: float = 1.1):
        """
        Boost a product's relevance score
        
        Args:
            product_id: Product ID to boost
            boost_factor: Multiplier for relevance score
        """
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if product:
                product.relevance_score *= boost_factor
                # Cap at 1.0
                product.relevance_score = min(product.relevance_score, 1.0)
                self.db.commit()
                logger.info(f"Boosted product {product_id} to {product.relevance_score}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error boosting product: {str(e)}")
    
    def apply_relevance_boost(self, results: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """
        Apply relevance boost to search results based on feedback
        
        Args:
            results: List of (product_id, similarity_score) tuples
            
        Returns:
            Re-ranked results with boosted scores
        """
        boosted_results = []
        
        for product_id, similarity_score in results:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if product:
                # Combine similarity score with relevance score
                # Weighted combination: 70% similarity, 30% relevance
                boosted_score = (
                    similarity_score * 0.7 + 
                    product.relevance_score * 0.3
                )
                boosted_results.append((product_id, boosted_score))
            else:
                boosted_results.append((product_id, similarity_score))
        
        # Re-sort by boosted score
        boosted_results.sort(key=lambda x: x[1], reverse=True)
        
        return boosted_results
    
    def get_product_stats(self, product_id: int) -> dict:
        """
        Get feedback statistics for a product
        
        Args:
            product_id: Product ID
            
        Returns:
            Dictionary with statistics
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {}
        
        # Count feedback
        relevant_count = self.db.query(Feedback).filter(
            Feedback.product_id == product_id,
            Feedback.is_relevant == 1
        ).count()
        
        not_relevant_count = self.db.query(Feedback).filter(
            Feedback.product_id == product_id,
            Feedback.is_relevant == 0
        ).count()
        
        return {
            "product_id": product_id,
            "click_count": product.click_count,
            "relevance_score": product.relevance_score,
            "relevant_feedback": relevant_count,
            "not_relevant_feedback": not_relevant_count,
            "total_feedback": relevant_count + not_relevant_count
        }

