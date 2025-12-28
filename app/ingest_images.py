import os
import sys
from pathlib import Path
import logging
from sqlalchemy.orm import Session
from app.models import init_db, get_db, Product
from app.feature_extractor import FeatureExtractor
from app.attribute_recognizer import AttributeRecognizer
from app.vector_db import VectorDB
import random
import numpy as np
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
def generate_sample_metadata(image_name: str) -> dict:
    brands = ["Ray-Ban", "Oakley", "Tom Ford", "Gucci", "Prada", "Warby Parker", "Persol", "Maui Jim"]
    materials = ["Acetate", "Metal", "Plastic", "Titanium"]
    brand = random.choice(brands)
    price = random.uniform(50, 500)
    material = random.choice(materials)
    return {
        "brand": brand,
        "price": round(price, 2),
        "material": material
    }
def ingest_images(image_dir: str = "data/images", db: Session = None):
    init_db()
    if db is None:
        db_gen = get_db()
        db = next(db_gen)
    feature_extractor = FeatureExtractor()
    attribute_recognizer = AttributeRecognizer()
    vector_db = VectorDB()
    image_dir_path = Path(image_dir)
    if not image_dir_path.exists():
        logger.warning(f"Image directory {image_dir} does not exist. Creating it.")
        image_dir_path.mkdir(parents=True, exist_ok=True)
        logger.info("Please add eyewear images to data/images/ directory")
        return
    image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
    image_files = [f for f in image_dir_path.iterdir() 
                   if f.suffix in image_extensions and f.is_file()]
    if not image_files:
        logger.warning(f"No images found in {image_dir}")
        logger.info("Please add eyewear images to data/images/ directory")
        return
    logger.info(f"Found {len(image_files)} images to process")
    batch_size = 32
    all_features = []
    all_product_ids = []
    for i, image_path in enumerate(image_files):
        try:
            logger.info(f"Processing {i+1}/{len(image_files)}: {image_path.name}")
            existing_product = db.query(Product).filter(Product.image_path == image_path.name).first()
            if existing_product:
                logger.info(f"  ⚠️  Image {image_path.name} already exists in database, skipping...")
                continue
            features = feature_extractor.extract_features(str(image_path))
            metadata = generate_sample_metadata(image_path.name)
            attributes = attribute_recognizer.extract_attributes(features)
            tags = attribute_recognizer.get_tags(attributes)
            style_tags = ",".join(tags)
            product = Product(
                image_path=image_path.name,
                brand=metadata["brand"],
                price=metadata["price"],
                material=metadata["material"],
                style_tags=style_tags
            )
            db.add(product)
            db.flush()
            all_features.append(features)
            all_product_ids.append(product.id)
            if len(all_features) >= batch_size:
                features_array = np.array(all_features)
                vector_db.add_vectors(features_array, all_product_ids)
                all_features = []
                all_product_ids = []
                db.commit()
                logger.info(f"Processed batch, total products: {vector_db.index.ntotal}")
        except Exception as e:
            logger.error(f"Error processing {image_path.name}: {str(e)}", exc_info=True)
            db.rollback()
            continue
    if all_features:
        features_array = np.array(all_features)
        vector_db.add_vectors(features_array, all_product_ids)
        db.commit()
    vector_db.save_index()
    db.commit()
    logger.info(f"Ingestion complete! Processed {vector_db.index.ntotal} products")
    logger.info(f"Vector index saved to {vector_db.index_path}")
if __name__ == "__main__":
    image_dir = sys.argv[1] if len(sys.argv) > 1 else "data/images"
    ingest_images(image_dir)