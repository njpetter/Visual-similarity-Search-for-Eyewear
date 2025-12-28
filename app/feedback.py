import logging
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models import Product, Feedback
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class FeedbackSystem:
    def __init__(self, db: Session):
        self.db = db
    def record_feedback(self, query_image_path: str, product_id: int, is_relevant: bool):
        try:
            feedback = Feedback(
                query_image_path=query_image_path,
                product_id=product_id,
                is_relevant=1 if is_relevant else 0
            )
            self.db.add(feedback)
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if product:
                if is_relevant:
                    product.click_count += 1
                    product.relevance_score = (
                        product.relevance_score * 0.9 + 1.0 * 0.1
                    )
                else:
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
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if product:
                product.relevance_score *= boost_factor
                product.relevance_score = min(product.relevance_score, 1.0)
                self.db.commit()
                logger.info(f"Boosted product {product_id} to {product.relevance_score}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error boosting product: {str(e)}")
    def apply_relevance_boost(self, results: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        ranking_scores = []
        for product_id, similarity_score in results:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if product:
                ranking_score = similarity_score + (product.relevance_score * 0.1)
                ranking_scores.append((product_id, similarity_score, ranking_score))
            else:
                ranking_scores.append((product_id, similarity_score, similarity_score))
        ranking_scores.sort(key=lambda x: x[2], reverse=True)
        return [(pid, sim_score) for pid, sim_score, _ in ranking_scores]
    def get_product_stats(self, product_id: int) -> dict:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {}
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