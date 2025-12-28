import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple, Optional
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class VectorDB:
    def __init__(self, dimension: int = 2048, index_path: Optional[str] = None):
        self.dimension = dimension
        self.index_path = index_path or "data/embeddings/faiss.index"
        self.ids_path = index_path.replace(".index", "_ids.pkl") if index_path else "data/embeddings/faiss_ids.pkl"
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        self.index = faiss.IndexFlatIP(dimension)
        self.id_mapping: List[int] = []
        self.load_index()
    def add_vectors(self, vectors: np.ndarray, product_ids: List[int]):
        if vectors.shape[0] != len(product_ids):
            raise ValueError("Number of vectors must match number of product IDs")
        vectors = vectors.astype('float32')
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.id_mapping.extend(product_ids)
        logger.info(f"Added {len(product_ids)} vectors to index. Total: {self.index.ntotal}")
    def search(self, query_vector: np.ndarray, k: int = 10, 
               filters: Optional[dict] = None, product_db=None) -> List[Tuple[int, float]]:
        if self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []
        query_vector = query_vector.astype('float32').reshape(1, -1)
        faiss.normalize_L2(query_vector)
        distances, indices = self.index.search(query_vector, min(k * 3, self.index.ntotal))
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.id_mapping):
                product_id = self.id_mapping[idx]
                similarity = max(0.0, min(1.0, float(dist)))
                if filters and product_db:
                    if not self._apply_filters(product_id, filters, product_db):
                        continue
                results.append((product_id, similarity))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]
    def _apply_filters(self, product_id: int, filters: dict, product_db) -> bool:
        from app.models import Product
        product = product_db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False
        if 'price_min' in filters and product.price < filters['price_min']:
            return False
        if 'price_max' in filters and product.price > filters['price_max']:
            return False
        if 'brand' in filters and product.brand.lower() != filters['brand'].lower():
            return False
        if 'material' in filters and product.material.lower() != filters['material'].lower():
            return False
        return True
    def update_vector(self, product_id: int, new_vector: np.ndarray):
        logger.warning("Direct vector updates not supported. Use feedback boosting in metadata.")
    def save_index(self):
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.ids_path, 'wb') as f:
                pickle.dump(self.id_mapping, f)
            logger.info(f"Saved index with {self.index.ntotal} vectors to {self.index_path}")
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
    def load_index(self):
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.ids_path):
                self.index = faiss.read_index(self.index_path)
                with open(self.ids_path, 'rb') as f:
                    self.id_mapping = pickle.load(f)
                logger.info(f"Loaded index with {self.index.ntotal} vectors from {self.index_path}")
        except Exception as e:
            logger.warning(f"Could not load index: {str(e)}. Starting with empty index.")
    def get_stats(self) -> dict:
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": "IndexFlatIP (Cosine Similarity)"
        }