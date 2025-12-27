"""
Vector database operations using FAISS
"""
import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorDB:
    """
    FAISS-based vector database for similarity search
    Uses IndexFlatIP (Inner Product) for cosine similarity
    """
    
    def __init__(self, dimension: int = 2048, index_path: Optional[str] = None):
        """
        Initialize vector database
        
        Args:
            dimension: Dimension of feature vectors
            index_path: Path to save/load index
        """
        self.dimension = dimension
        self.index_path = index_path or "data/embeddings/faiss.index"
        self.ids_path = index_path.replace(".index", "_ids.pkl") if index_path else "data/embeddings/faiss_ids.pkl"
        
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        # Initialize FAISS index (Inner Product for normalized vectors = Cosine Similarity)
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product
        
        # Store mapping between FAISS index and product IDs
        self.id_mapping: List[int] = []
        
        # Load existing index if available
        self.load_index()
    
    def add_vectors(self, vectors: np.ndarray, product_ids: List[int]):
        """
        Add vectors to the index
        
        Args:
            vectors: Numpy array of vectors (N x dimension)
            product_ids: List of product IDs corresponding to vectors
        """
        if vectors.shape[0] != len(product_ids):
            raise ValueError("Number of vectors must match number of product IDs")
        
        # Ensure vectors are float32 and normalized
        vectors = vectors.astype('float32')
        faiss.normalize_L2(vectors)  # Normalize for cosine similarity
        
        # Add to index
        self.index.add(vectors)
        
        # Store ID mapping
        self.id_mapping.extend(product_ids)
        
        logger.info(f"Added {len(product_ids)} vectors to index. Total: {self.index.ntotal}")
    
    def search(self, query_vector: np.ndarray, k: int = 10, 
               filters: Optional[dict] = None, product_db=None) -> List[Tuple[int, float]]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query vector (dimension,)
            k: Number of results to return
            filters: Optional filters (price_min, price_max, brand, material)
            product_db: Database session for applying filters
            
        Returns:
            List of tuples (product_id, similarity_score)
        """
        if self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []
        
        # Ensure query vector is float32 and normalized
        query_vector = query_vector.astype('float32').reshape(1, -1)
        faiss.normalize_L2(query_vector)
        
        # Search in FAISS
        distances, indices = self.index.search(query_vector, min(k * 3, self.index.ntotal))
        
        # Convert FAISS indices to product IDs and get similarities
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.id_mapping):
                product_id = self.id_mapping[idx]
                similarity = float(dist)  # Cosine similarity (0-1)
                
                # Apply filters if provided
                if filters and product_db:
                    if not self._apply_filters(product_id, filters, product_db):
                        continue
                
                results.append((product_id, similarity))
        
        # Return top k after filtering
        return results[:k]
    
    def _apply_filters(self, product_id: int, filters: dict, product_db) -> bool:
        """
        Check if product matches filters
        
        Args:
            product_id: Product ID
            filters: Filter dictionary
            product_db: Database session
            
        Returns:
            True if product matches filters
        """
        from app.models import Product
        
        product = product_db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False
        
        # Price filter
        if 'price_min' in filters and product.price < filters['price_min']:
            return False
        if 'price_max' in filters and product.price > filters['price_max']:
            return False
        
        # Brand filter
        if 'brand' in filters and product.brand.lower() != filters['brand'].lower():
            return False
        
        # Material filter
        if 'material' in filters and product.material.lower() != filters['material'].lower():
            return False
        
        return True
    
    def update_vector(self, product_id: int, new_vector: np.ndarray):
        """
        Update vector for a product (for feedback-based boosting)
        
        Note: FAISS doesn't support direct updates, so this requires rebuilding
        For simplicity, we'll track boosts in the metadata instead
        """
        logger.warning("Direct vector updates not supported. Use feedback boosting in metadata.")
    
    def save_index(self):
        """Save index to disk"""
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.ids_path, 'wb') as f:
                pickle.dump(self.id_mapping, f)
            logger.info(f"Saved index with {self.index.ntotal} vectors to {self.index_path}")
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
    
    def load_index(self):
        """Load index from disk"""
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.ids_path):
                self.index = faiss.read_index(self.index_path)
                with open(self.ids_path, 'rb') as f:
                    self.id_mapping = pickle.load(f)
                logger.info(f"Loaded index with {self.index.ntotal} vectors from {self.index_path}")
        except Exception as e:
            logger.warning(f"Could not load index: {str(e)}. Starting with empty index.")
    
    def get_stats(self) -> dict:
        """Get database statistics"""
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": "IndexFlatIP (Cosine Similarity)"
        }

