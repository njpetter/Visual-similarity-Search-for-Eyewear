from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from PIL import Image
import io
import os
import logging
from typing import Optional, List
from app.models import init_db, get_db, Product, Feedback
from app.feature_extractor import FeatureExtractor
from app.attribute_recognizer import AttributeRecognizer
from app.vector_db import VectorDB
from app.feedback import FeedbackSystem
from app.smart_crop import SmartCropper
from app.multimodal_search import MultiModalSearch
from pydantic import BaseModel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(
    title="Visual Similarity Search for Eyewear",
    description="AI-powered visual search platform for eyewear products",
    version="1.0.0"
)
feature_extractor = FeatureExtractor()
attribute_recognizer = AttributeRecognizer()
vector_db = VectorDB(dimension=2048)
smart_cropper = SmartCropper()
multimodal_search = MultiModalSearch()
os.makedirs("uploads", exist_ok=True)
os.makedirs("data/images", exist_ok=True)
init_db()
app.mount("/static", StaticFiles(directory="data/images"), name="static")
class SearchFilters(BaseModel):
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    brand: Optional[str] = None
    material: Optional[str] = None
    color: Optional[str] = None
    frame_style: Optional[str] = None
class FeedbackRequest(BaseModel):
    product_id: int
    is_relevant: bool
class ProductResponse(BaseModel):
    id: int
    image_path: str
    brand: str
    price: float
    material: str
    style_tags: Optional[str]
    similarity_score: float
@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = 
    return html_content
@app.post("/search")
async def search_similar(
    image: UploadFile = File(...),
    price_min: Optional[float] = Form(None),
    price_max: Optional[float] = Form(None),
    brand: Optional[str] = Form(None),
    material: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    frame_style: Optional[str] = Form(None),
    text_modifier: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        content = await image.read()
        logger.info(f"Processing search query: {image.filename}")
        pil_image = Image.open(io.BytesIO(content))
        query_features = feature_extractor.extract_features_from_image(pil_image)
        attributes = attribute_recognizer.extract_attributes(query_features)
        filters = {}
        if price_min is not None:
            filters['price_min'] = price_min
        if price_max is not None:
            filters['price_max'] = price_max
        if brand:
            filters['brand'] = brand
        if material:
            filters['material'] = material
        if color:
            filters['color'] = color
        if frame_style:
            filters['frame_style'] = frame_style
        search_results = vector_db.search(query_features, k=50, filters=filters, product_db=db)
        search_results = [(pid, score) for pid, score in search_results if score >= 0.3]
        logger.info(f"Found {len(search_results)} results above similarity threshold (0.3)")
        if text_modifier:
            logger.info(f"Applying text modifier: {text_modifier}")
            modifiers = multimodal_search.parse_modifier(text_modifier)
            search_results = multimodal_search.apply_modifier_filter(search_results, modifiers, db)
        feedback_system = FeedbackSystem(db)
        boosted_results = feedback_system.apply_relevance_boost(search_results)
        if boosted_results:
            logger.info(f"Top similarity scores: {[f'{s:.3f}' for _, s in boosted_results[:5]]}")
        products = []
        for product_id, similarity_score in boosted_results[:10]:
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                products.append({
                    "id": product.id,
                    "image_path": product.image_path,
                    "brand": product.brand,
                    "price": product.price,
                    "material": product.material,
                    "style_tags": product.style_tags,
                    "similarity_score": similarity_score
                })
        return {
            "query_image": image.filename,
            "attributes": attributes,
            "results": products,
            "total_results": len(boosted_results)
        }
    except Exception as e:
        logger.error(f"Error in search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/products/{product_id}")
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "id": product.id,
        "image_path": product.image_path,
        "brand": product.brand,
        "price": product.price,
        "material": product.material,
        "style_tags": product.style_tags,
        "click_count": product.click_count,
        "relevance_score": product.relevance_score
    }
@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest, db: Session = Depends(get_db)):
    try:
        feedback_system = FeedbackSystem(db)
        feedback_system.record_feedback("", feedback.product_id, feedback.is_relevant)
        return {"status": "success", "message": "Feedback recorded"}
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    total_products = db.query(Product).count()
    total_feedback = db.query(Feedback).count()
    vector_stats = vector_db.get_stats()
    return {
        "total_products": total_products,
        "total_feedback": total_feedback,
        "vector_db": vector_stats
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)