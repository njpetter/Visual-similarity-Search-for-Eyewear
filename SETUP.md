# Setup Instructions

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- ~2GB disk space for models and dependencies

## Step-by-Step Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: This will install:
- FastAPI and uvicorn (web framework)
- PyTorch and torchvision (deep learning)
- FAISS (vector database)
- SQLAlchemy (database ORM)
- Pillow (image processing)

Installation may take 5-10 minutes, especially for PyTorch.

### 2. Prepare Image Dataset

You need eyewear images to populate the catalog. Two options:

#### Option A: Manual Download (Recommended for Demo)

1. Download eyewear images from Lenskart or other sources
2. Save them to `data/images/` directory
3. Supported formats: JPG, JPEG, PNG
4. Recommended: 10-50 images for testing

#### Option B: Use Existing Images

If you already have eyewear images, copy them to `data/images/`

### 3. Run Image Ingestion Pipeline

This processes all images, extracts features, and populates the databases:

```bash
python -m app.ingest_images
```

**What this does:**
- Scans `data/images/` for image files
- Preprocesses each image
- Extracts 2048-dimensional embeddings using ResNet50
- Stores embeddings in FAISS vector database
- Stores metadata (brand, price, material) in SQLite
- Recognizes attributes (style, color)
- Saves index to `data/embeddings/faiss.index`

**Expected output:**
```
INFO - Found 20 images to process
INFO - Processing 1/20: image1.jpg
INFO - Processing 2/20: image2.jpg
...
INFO - Ingestion complete! Processed 20 products
```

### 4. Start the API Server

```bash
uvicorn app.main:app --reload
```

The server will start on `http://localhost:8000`

### 5. Access the Web Interface

Open your browser and go to:
```
http://localhost:8000
```

You should see the visual search interface.

### 6. Test the System

1. **Upload an image**: Click "Choose Image" and select an eyewear image
2. **Search**: Click "Search Similar Products"
3. **View results**: Browse similar products with similarity scores
4. **Provide feedback**: Click "Relevant" or "Not Relevant" on results
5. **Filter**: Try filtering by price, brand, or material

## Directory Structure After Setup

```
Lenskart-A1.1/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── feature_extractor.py
│   ├── attribute_recognizer.py
│   ├── vector_db.py
│   ├── feedback.py
│   └── ingest_images.py
├── data/
│   ├── images/              # Your catalog images
│   ├── embeddings/
│   │   ├── faiss.index      # Vector database index
│   │   └── faiss_ids.pkl    # ID mapping
│   └── db.sqlite           # Metadata database
├── uploads/                 # User uploaded images
├── requirements.txt
├── README.md
└── ARCHITECTURE.md
```

## Troubleshooting

### Issue: "No module named 'torch'"

**Solution**: Install PyTorch separately:
```bash
pip install torch torchvision
```

### Issue: "FAISS installation failed"

**Solution**: 
- On Windows: `pip install faiss-cpu`
- On Linux/Mac: `pip install faiss-cpu` or `pip install faiss-gpu` (if CUDA available)

### Issue: "No images found in data/images"

**Solution**: Make sure you've copied images to `data/images/` directory before running ingestion.

### Issue: "CUDA out of memory"

**Solution**: 
- The system uses CPU by default
- If using GPU, reduce batch size in `app/ingest_images.py`
- Or force CPU: Set `device='cpu'` in `FeatureExtractor`

### Issue: Port 8000 already in use

**Solution**: Use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

## API Testing (Optional)

You can test the API directly using curl or Python:

```bash
# Search for similar products
curl -X POST "http://localhost:8000/search" \
  -F "image=@path/to/image.jpg" \
  -F "price_min=100" \
  -F "price_max=500"

# Get product details
curl "http://localhost:8000/products/1"

# Submit feedback
curl -X POST "http://localhost:8000/feedback" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "is_relevant": true}'

# Get statistics
curl "http://localhost:8000/stats"
```

## Performance Tips

1. **First Run**: The ResNet50 model will be downloaded (~100MB) on first use
2. **Search Speed**: Should be < 500ms for 10,000 products
3. **Feature Extraction**: ~100-200ms per image (CPU), ~10-50ms (GPU)
4. **Memory**: ~2GB RAM recommended, more for larger catalogs

## Next Steps

- Add more images to improve search quality
- Train the attribute recognizer on labeled data
- Customize metadata (brands, materials) in `app/ingest_images.py`
- Deploy to production (see production considerations in ARCHITECTURE.md)

