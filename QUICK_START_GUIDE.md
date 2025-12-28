# 🚀 Quick Start Guide - Visual Similarity Search for Eyewear

A complete step-by-step guide to get the project up and running.

---

## 📋 Prerequisites

Before you begin, make sure you have:

- **Python 3.8 or higher** installed
- **pip** (Python package manager) - usually comes with Python
- **Git** (if cloning from repository)
- **~2GB free disk space** (for models and dependencies)

### Check Python Installation

Open your terminal/command prompt and run:

```bash
python --version
# or
python3 --version
```

You should see Python 3.8 or higher. If not, download from [python.org](https://www.python.org/downloads/).

---

## 🎯 Step-by-Step Setup

### Step 1: Clone or Download the Repository

**Option A: If you have the repository on GitHub:**
```bash
git clone https://github.com/njpetter/Visual-similarity-Search-for-Eyewear.git
cd Visual-similarity-Search-for-Eyewear
```

**Option B: If you already have the project folder:**
```bash
cd path/to/Lenskart-A1.1
```

---

### Step 2: Create a Virtual Environment (Recommended)

This keeps your project dependencies isolated:

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

---

### Step 3: Install Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

**⏱️ This may take 5-10 minutes** as it downloads:
- PyTorch (deep learning framework)
- FAISS (vector database)
- FastAPI (web framework)
- Other dependencies

**Common Issues:**

If you encounter errors:
- **Windows**: Make sure you have Visual C++ Build Tools
- **Mac**: May need Xcode Command Line Tools: `xcode-select --install`
- **Linux**: May need: `sudo apt-get install build-essential`

---

### Step 4: Prepare Image Dataset

You need eyewear images in the `data/images/` directory.

**Option A: Use existing images** (if any are already in `data/images/`)

**Option B: Download sample images:**
```bash
python download_sample_images.py
```

**Option C: Add your own images:**
1. Download eyewear images from Lenskart or other sources
2. Save them as JPG or PNG files
3. Place them in the `data/images/` folder

**Recommended**: At least 10-20 images for a good demo.

---

### Step 5: Run Image Ingestion Pipeline

This processes all images, extracts features, and builds the search database:

```bash
python -m app.ingest_images
```

**What this does:**
- Scans `data/images/` for image files
- Preprocesses each image (resize, normalize)
- Extracts 2048-dimensional feature vectors using ResNet50
- Stores embeddings in FAISS vector database
- Stores metadata (brand, price, material) in SQLite database
- Recognizes attributes (style, color)

**Expected Output:**
```
INFO - Found 20 images to process
INFO - Processing 1/20: glasses_1.jpg
INFO - Processing 2/20: glasses_2.jpg
...
INFO - Ingestion complete! Processed 20 products
INFO - Vector index saved to data/embeddings/faiss.index
```

**Note**: The first run will download the ResNet50 model (~100MB), which may take a minute.

---

### Step 6: Start the Web Server

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

The `--reload` flag enables auto-reload on code changes (useful for development).

---

### Step 7: Open the Web Interface

Open your web browser and go to:

```
http://localhost:8000
```

or

```
http://127.0.0.1:8000
```

You should see the **Visual Similarity Search for Eyewear** interface! 🎉

---

## 🧪 Testing the System

### Test 1: Basic Visual Search

1. Click **"Choose Image or Drag & Drop"**
2. Select an eyewear image (from your catalog or any similar image)
3. Click **"Search Similar Products"**
4. View the ranked results with similarity scores

### Test 2: Filters

Try filtering results by:
- **Price Range**: Set min/max price
- **Brand**: Enter a brand name
- **Material**: Select from dropdown

### Test 3: Bonus Features

**Smart Cropping:**
- Upload a photo of a person wearing glasses
- The system automatically detects and crops to the eyewear region

**Multi-Modal Search:**
- Upload an image
- In the **"Text Modifier"** field, type: `but in tortoise shell color`
- Search results will prioritize tortoise shell frames

### Test 4: Feedback System

- Click **"✓ Relevant"** or **"✗ Not Relevant"** on search results
- The system learns from your feedback
- Future searches will rank relevant products higher

---

## 🔧 Common Issues & Solutions

### Issue: "No module named 'torch'"

**Solution:**
```bash
pip install torch torchvision
```

### Issue: "FAISS installation failed"

**Windows:**
```bash
pip install faiss-cpu
```

**Mac/Linux:**
```bash
pip install faiss-cpu
# or for GPU support:
pip install faiss-gpu
```

### Issue: "No images found in data/images"

**Solution:**
1. Make sure images are in `data/images/` directory
2. Images should be JPG, JPEG, or PNG format
3. Run `python download_sample_images.py` to get sample images

### Issue: "Port 8000 already in use"

**Solution:** Use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```
Then access at `http://localhost:8001`

### Issue: "CUDA out of memory" (GPU users)

**Solution:** The system uses CPU by default, but if you have GPU and see this error:
- The system will automatically fall back to CPU
- Or reduce batch size in `app/ingest_images.py`

### Issue: Import errors

**Solution:**
1. Make sure you're in the project root directory
2. Ensure virtual environment is activated
3. Reinstall dependencies: `pip install -r requirements.txt`

---

## 📁 Project Structure After Setup

```
Lenskart-A1.1/
├── app/                          # Application code
│   ├── main.py                   # FastAPI app + Web UI
│   ├── feature_extractor.py      # ResNet50 embeddings
│   ├── vector_db.py              # FAISS operations
│   ├── attribute_recognizer.py   # Style classification
│   ├── feedback.py               # Feedback system
│   ├── smart_crop.py             # Smart cropping (bonus)
│   ├── multimodal_search.py      # Multi-modal search (bonus)
│   ├── ingest_images.py          # Ingestion pipeline
│   └── models.py                 # Database models
├── data/
│   ├── images/                   # Your catalog images (✅ should have images here)
│   ├── embeddings/
│   │   ├── faiss.index          # Vector database (created after ingestion)
│   │   └── faiss_ids.pkl        # ID mapping (created after ingestion)
│   └── db.sqlite                # Metadata database (created after ingestion)
├── uploads/                      # User uploaded images (auto-created)
├── venv/                         # Virtual environment (if created)
├── requirements.txt              # Dependencies
└── README.md                     # Documentation
```

---

## 🔄 Running Again Later

Once set up, to run the project again:

1. **Activate virtual environment** (if using one):
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   ```

2. **Start the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Open browser**: `http://localhost:8000`

**Note**: You only need to run `python -m app.ingest_images` again if you add new images to the catalog.

---

## 📊 API Endpoints (Advanced)

You can also test the API directly:

### Search for Similar Products
```bash
curl -X POST "http://localhost:8000/search" \
  -F "image=@path/to/image.jpg" \
  -F "price_min=100" \
  -F "price_max=500"
```

### Get Product Details
```bash
curl "http://localhost:8000/products/1"
```

### Submit Feedback
```bash
curl -X POST "http://localhost:8000/feedback" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "is_relevant": true}'
```

### Get Statistics
```bash
curl "http://localhost:8000/stats"
```

### API Documentation

FastAPI provides automatic API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🎓 Understanding the Workflow

1. **Ingestion** (one-time setup):
   - Images → Preprocessing → ResNet50 → Embeddings → FAISS + SQLite

2. **Search** (every query):
   - User uploads image → Preprocessing → Smart cropping (if needed) → ResNet50 → Embedding → FAISS search → Filters → Multi-modal (if text provided) → Feedback boost → Results

3. **Learning** (continuous):
   - User clicks → Feedback recorded → Relevance scores updated → Future searches improved

---

## 💡 Tips for Best Results

1. **Image Quality**: Use clear, well-lit images of eyewear
2. **Catalog Size**: More images = better search results (10-50 recommended)
3. **Consistent Images**: Use product photos (not person wearing them) for catalog
4. **Feedback**: Click feedback buttons to improve results over time

---

## 🆘 Getting Help

If you encounter issues:

1. Check the error message carefully
2. Review the "Common Issues" section above
3. Check that all prerequisites are installed
4. Verify Python version (3.8+)
5. Ensure all dependencies are installed: `pip list`

---

## ✅ Quick Checklist

Before running, make sure:

- [ ] Python 3.8+ installed
- [ ] Virtual environment created (recommended)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Images in `data/images/` directory
- [ ] Ingestion pipeline run (`python -m app.ingest_images`)
- [ ] Server started (`uvicorn app.main:app --reload`)
- [ ] Browser opened to `http://localhost:8000`

---

**🎉 You're all set! Enjoy using the Visual Similarity Search system!**

For detailed architecture and technical details, see `ARCHITECTURE.md` and `README.md`.

