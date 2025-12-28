from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from PIL import Image
import io
import os
import logging
from typing import Optional

from app.models import init_db, get_db, Product, Feedback
from app.feature_extractor import FeatureExtractor
from app.attribute_recognizer import AttributeRecognizer
from app.vector_db import VectorDB
from app.feedback import FeedbackSystem
from app.multimodal_search import MultiModalSearch
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Visual Similarity Search for Eyewear",
    description="AI-powered visual search platform for eyewear products",
    version="1.0.0"
)

# Initialize components
feature_extractor = FeatureExtractor()
attribute_recognizer = AttributeRecognizer()
vector_db = VectorDB(dimension=2048)
multimodal_search = MultiModalSearch()

# Create necessary directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("data/images", exist_ok=True)

# Initialize database
init_db()

# Mount static files for product images
app.mount("/static", StaticFiles(directory="data/images"), name="static")


# Pydantic models for API
class FeedbackRequest(BaseModel):
    product_id: int
    is_relevant: bool


# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Visual Similarity Search for Eyewear</title>
        <!-- SEARCH EMOJI FAVICON -->
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔍</text></svg>">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
                text-align: center;
            }
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 40px;
            }
            .upload-area {
                border: 3px dashed #667eea;
                border-radius: 15px;
                padding: 40px;
                text-align: center;
                margin-bottom: 30px;
                background: #f8f9ff;
                transition: all 0.3s;
            }
            .upload-area:hover {
                background: #f0f2ff;
                border-color: #764ba2;
            }
            input[type="file"] {
                display: none;
            }
            .upload-btn {
                background: #667eea;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                transition: all 0.3s;
            }
            .upload-btn:hover {
                background: #764ba2;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            .filters {
                display: flex;
                gap: 15px;
                margin-bottom: 30px;
                flex-wrap: wrap;
            }
            .filter-group {
                flex: 1;
                min-width: 200px;
            }
            .filter-group label {
                display: block;
                margin-bottom: 5px;
                color: #555;
                font-weight: 600;
            }
            .filter-group input, .filter-group select {
                width: 100%;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
            }
            .search-btn {
                background: #764ba2;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                width: 100%;
                margin-top: 10px;
            }
            .search-btn:hover {
                background: #667eea;
            }
            .search-btn:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            .preview {
                margin: 20px 0;
                text-align: center;
            }
            .preview img {
                max-width: 300px;
                max-height: 300px;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .results {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            .result-card {
                background: white;
                border: 2px solid #e0e0e0;
                border-radius: 15px;
                padding: 15px;
                transition: all 0.3s;
                cursor: pointer;
            }
            .result-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
                border-color: #667eea;
            }
            .result-card img {
                width: 100%;
                height: 200px;
                object-fit: cover;
                border-radius: 10px;
                margin-bottom: 10px;
            }
            .result-info {
                color: #333;
            }
            .result-info h3 {
                font-size: 18px;
                margin-bottom: 5px;
                color: #667eea;
            }
            .result-info p {
                margin: 5px 0;
                color: #666;
            }
            .similarity-score {
                background: #667eea;
                color: white;
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                display: inline-block;
                margin-top: 10px;
            }
            .loading {
                text-align: center;
                padding: 40px;
                color: #667eea;
                font-size: 18px;
            }
            .attributes {
                background: #f8f9ff;
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .attributes h3 {
                color: #667eea;
                margin-bottom: 10px;
            }
            .attribute-tag {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 5px 12px;
                border-radius: 15px;
                margin: 5px;
                font-size: 12px;
            }
            .feedback-btns {
                display: flex;
                gap: 10px;
                margin-top: 10px;
            }
            .feedback-btn {
                flex: 1;
                padding: 8px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 12px;
            }
            .feedback-btn.relevant {
                background: #4caf50;
                color: white;
            }
            .feedback-btn.not-relevant {
                background: #f44336;
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Visual Similarity Search for Eyewear</h1>
            <p class="subtitle">Upload an image to find similar eyewear products</p>
            
            <div class="upload-area">
                <input type="file" id="imageInput" accept="image/*">
                <button class="upload-btn" onclick="document.getElementById('imageInput').click()">
                    Choose Image or Drag & Drop
                </button>
                <div class="preview" id="preview"></div>
            </div>
            
            <div class="filters">
                <div class="filter-group">
                    <label>Min Price</label>
                    <input type="number" id="priceMin" placeholder="0">
                </div>
                <div class="filter-group">
                    <label>Max Price</label>
                    <input type="number" id="priceMax" placeholder="10000">
                </div>
                <div class="filter-group">
                    <label>Brand</label>
                    <input type="text" id="brand" placeholder="e.g., Ray-Ban">
                </div>
                
                <!-- FRAME STYLE DROPDOWN -->
                <div class="filter-group">
                    <label>Frame Style</label>
                    <select id="frameStyle">
                        <option value="">All Styles</option>
                        <option value="Aviator">Aviator</option>
                        <option value="Wayfarer">Wayfarer</option>
                        <option value="Round">Round</option>
                        <option value="Square">Square</option>
                        <option value="Cat Eye">Cat Eye</option>
                        <option value="Rimless">Rimless</option>
                        <option value="Rectangular">Rectangular</option>
                        <option value="Oversized">Oversized</option>
                    </select>
                </div>

                <!-- COLOR DROPDOWN -->
                <div class="filter-group">
                    <label>Color</label>
                    <select id="color">
                        <option value="">All Colors</option>
                        <option value="Black">Black</option>
                        <option value="Gold">Gold</option>
                        <option value="Silver">Silver</option>
                        <option value="Tortoise">Tortoise</option>
                        <option value="Brown">Brown</option>
                        <option value="Clear">Clear</option>
                        <option value="Blue">Blue</option>
                        <option value="Red">Red</option>
                    </select>
                </div>

                <div class="filter-group">
                    <label>Material</label>
                    <select id="material">
                        <option value="">All Materials</option>
                        <option value="Acetate">Acetate</option>
                        <option value="Metal">Metal</option>
                        <option value="Plastic">Plastic</option>
                        <option value="Titanium">Titanium</option>
                    </select>
                </div>
                
                <div class="filter-group" style="flex: 100%;">
                    <label>Text Modifier (🎁 Bonus Feature)</label>
                    <input type="text" id="textModifier" placeholder="e.g., 'but in tortoise shell color'">
                    <small style="color: #666; font-size: 12px; display: block; margin-top: 5px;">Try: 'tortoise shell', 'metal', 'transparent', 'aviator style'</small>
                </div>
            </div>
            
            <button class="search-btn" id="searchBtn" onclick="search()" disabled>Search Similar Products</button>
            
            <div id="attributes"></div>
            <div id="results" class="results"></div>
        </div>
        
        <script>
            let currentImageFile = null;
            
            document.getElementById('imageInput').addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    currentImageFile = file;
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        document.getElementById('preview').innerHTML = '<img src="' + e.target.result + '" alt="Preview">';
                        document.getElementById('searchBtn').disabled = false;
                    };
                    reader.readAsDataURL(file);
                }
            });
            
            async function search() {
                if (!currentImageFile) return;
                
                const formData = new FormData();
                formData.append('image', currentImageFile);
                
                const priceMin = document.getElementById('priceMin').value;
                const priceMax = document.getElementById('priceMax').value;
                const brand = document.getElementById('brand').value;
                const material = document.getElementById('material').value;
                const color = document.getElementById('color').value;
                const frameStyle = document.getElementById('frameStyle').value;
                const textModifier = document.getElementById('textModifier').value;
                
                if (priceMin) formData.append('price_min', priceMin);
                if (priceMax) formData.append('price_max', priceMax);
                if (brand) formData.append('brand', brand);
                if (material) formData.append('material', material);
                if (color) formData.append('color', color);
                if (frameStyle) formData.append('frame_style', frameStyle);
                if (textModifier) formData.append('text_modifier', textModifier);
                
                document.getElementById('results').innerHTML = '<div class="loading">🔍 Searching for similar products...</div>';
                document.getElementById('attributes').innerHTML = '';
                
                try {
                    const response = await fetch('/search', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.attributes) {
                        let attrsHtml = '<div class="attributes"><h3>Detected Attributes:</h3>';
                        attrsHtml += '<span class="attribute-tag">' + data.attributes.style + '</span>';
                        if (data.attributes.color) {
                            attrsHtml += '<span class="attribute-tag">' + data.attributes.color + '</span>';
                        }
                        attrsHtml += '</div>';
                        document.getElementById('attributes').innerHTML = attrsHtml;
                    }
                    
                    if (data.results && data.results.length > 0) {
                        let resultsHtml = '';
                        data.results.forEach(product => {
                            resultsHtml += `
                                <div class="result-card">
                                    <img src="/static/${product.image_path}" alt="${product.brand}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'200\\' height=\\'200\\'%3E%3Crect fill=\\'%23ddd\\' width=\\'200\\' height=\\'200\\'/%3E%3Ctext fill=\\'%23999\\' font-family=\\'sans-serif\\' font-size=\\'14\\' x=\\'50%25\\' y=\\'50%25\\' text-anchor=\\'middle\\' dy=\\'0.3em\\'%3ENo Image%3C/text%3E%3C/svg%3E'">
                                    <div class="result-info">
                                        <h3>${product.brand}</h3>
                                        <p>$${product.price.toFixed(2)}</p>
                                        <p>${product.material}</p>
                                        <span class="similarity-score">${(product.similarity_score * 100).toFixed(1)}% Similar</span>
                                        <div class="feedback-btns">
                                            <button class="feedback-btn relevant" onclick="submitFeedback(${product.id}, true)">✓ Relevant</button>
                                            <button class="feedback-btn not-relevant" onclick="submitFeedback(${product.id}, false)">✗ Not Relevant</button>
                                        </div>
                                    </div>
                                </div>
                            `;
                        });
                        document.getElementById('results').innerHTML = resultsHtml;
                    } else {
                        document.getElementById('results').innerHTML = '<div class="loading">No similar products found. Try a different image or adjust filters.</div>';
                    }
                } catch (error) {
                    document.getElementById('results').innerHTML = '<div class="loading" style="color: red;">Error: ' + error.message + '</div>';
                }
            }
            
            async function submitFeedback(productId, isRelevant) {
                try {
                    await fetch('/feedback', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            product_id: productId,
                            is_relevant: isRelevant
                        })
                    });
                    alert('Feedback recorded! Thank you.');
                } catch (error) {
                    console.error('Error submitting feedback:', error);
                }
            }
        </script>
    </body>
    </html>
    """
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
        if price_min is not None: filters['price_min'] = price_min
        if price_max is not None: filters['price_max'] = price_max
        if brand: filters['brand'] = brand
        if material: filters['material'] = material
        if color: filters['color'] = color
        if frame_style: filters['frame_style'] = frame_style
        
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
    
    # Print a clickable link for convenience
    print("\n" + "="*50)
    print("🚀 Server is starting! Open this link in your browser:")
    print("👉 http://127.0.0.1:8000")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)