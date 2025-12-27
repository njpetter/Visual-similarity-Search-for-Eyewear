# System Architecture

## Overview

The Visual Similarity Search system is built with a modular architecture that separates concerns into distinct layers:

1. **AI Inference Layer** - Feature extraction and attribute recognition
2. **Data Storage Layer** - Structured database (SQLite) and vector database (FAISS)
3. **API Layer** - FastAPI REST endpoints
4. **Presentation Layer** - Web UI for user interaction

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                    (Web Browser / HTML/JS)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP Requests
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API LAYER                              │
│                         (FastAPI)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   /search    │  │  /feedback   │  │   /stats     │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI INFERENCE LAYER                         │
│                                                                 │
│  ┌────────────────────┐      ┌─────────────────────┐          │
│  │ Feature Extractor  │      │ Attribute Recognizer│          │
│  │   (ResNet50)       │      │   (Style Classifier)│          │
│  │                    │      │                     │          │
│  │ Input: Image       │      │ Input: Embeddings   │          │
│  │ Output: 2048-dim   │      │ Output: Style Tags  │          │
│  │      embedding     │      │    (Aviator, etc.)  │          │
│  └────────────────────┘      └─────────────────────┘          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  DATA STORAGE    │  │  DATA STORAGE    │  │  DATA STORAGE    │
│     LAYER        │  │     LAYER        │  │     LAYER        │
│                  │  │                  │  │                  │
│  ┌────────────┐  │  │  ┌────────────┐ │  │  ┌────────────┐  │
│  │ SQLite DB  │  │  │  │ FAISS      │ │  │  │ Feedback   │  │
│  │            │  │  │  │ Vector DB  │ │  │  │ System     │  │
│  │ Metadata:  │  │  │  │            │ │  │  │            │  │
│  │ - Brand    │  │  │  │ Embeddings │ │  │  │ Tracks:    │  │
│  │ - Price    │  │  │  │ (2048-dim) │ │  │  │ - Clicks   │  │
│  │ - Material │  │  │  │            │ │  │  │ - Relevance│  │
│  │ - Tags     │  │  │  │ Cosine     │ │  │  │            │  │
│  └────────────┘  │  │  │ Similarity │ │  │  └────────────┘  │
└──────────────────┘  │  └────────────┘ │  └──────────────────┘
                      │                  │
                      └──────────────────┘
```

## Data Flow

### 1. Image Ingestion Pipeline

```
Catalog Images → Preprocessing → ResNet50 → Embeddings → FAISS + SQLite
                      ↓
                 Resize 224x224
                 Normalize
                 RGB conversion
```

**Steps:**
1. Load image from `data/images/`
2. Preprocess: Resize to 224x224, normalize, convert to RGB
3. Extract features using ResNet50 (2048-dimensional vector)
4. Normalize vector for cosine similarity
5. Store embedding in FAISS index
6. Store metadata (brand, price, material) in SQLite
7. Recognize attributes and store as tags

### 2. Visual Search Flow

```
User Upload → Preprocessing → ResNet50 → Embedding → FAISS Search → Filter → Boost → Results
                                      ↓
                            Attribute Recognition
                                      ↓
                            Style Classification
```

**Steps:**
1. User uploads image via web interface
2. Image is preprocessed (same as ingestion)
3. ResNet50 extracts 2048-dim embedding
4. Query FAISS index with cosine similarity
5. Apply filters (price, brand, material) if specified
6. Apply feedback-based boosting
7. Return top-K results with similarity scores

### 3. Feedback Loop

```
User Click → Feedback Record → Product Boost → Improved Rankings
     ↓
Relevant/Not Relevant
     ↓
Update relevance_score
     ↓
Affect future searches
```

**Steps:**
1. User clicks "Relevant" or "Not Relevant" on a result
2. Feedback is recorded in database
3. Product's `relevance_score` is updated
4. Future searches combine similarity (70%) + relevance (30%)
5. Products with higher relevance scores rank higher

## Components

### Feature Extractor (`app/feature_extractor.py`)

- **Model**: ResNet50 (pre-trained on ImageNet)
- **Input**: Image (JPG/PNG)
- **Output**: 2048-dimensional normalized vector
- **Method**: Remove final classification layer, use penultimate layer
- **Normalization**: L2 normalization for cosine similarity

### Vector Database (`app/vector_db.py`)

- **Technology**: FAISS (Facebook AI Similarity Search)
- **Index Type**: IndexFlatIP (Inner Product for normalized vectors = Cosine Similarity)
- **Storage**: Persistent index saved to disk
- **Operations**: Add, Search, Update (via metadata boosting)

### Structured Database (`app/models.py`)

- **Technology**: SQLite (SQLAlchemy ORM)
- **Tables**:
  - `products`: Product metadata
  - `feedback`: User feedback records
- **Indexes**: On brand, price, material for fast filtering

### Attribute Recognizer (`app/attribute_recognizer.py`)

- **Purpose**: Classify eyewear style and attributes
- **Output**: Style tags (Aviator, Wayfarer, Round, etc.)
- **Method**: Transfer learning from ResNet features
- **Note**: For production, requires training on labeled data

### Feedback System (`app/feedback.py`)

- **Purpose**: Learn from user interactions
- **Method**: Weighted combination of similarity + relevance score
- **Storage**: Tracks clicks and calculates relevance scores

## Distance Metric: Cosine Similarity

**Formula**: `cos(θ) = (A·B) / (||A|| × ||B||)`

**Why Cosine Similarity?**
- Better for high-dimensional vectors (2048 dimensions)
- Measures angle between vectors, ignores magnitude
- Works well for normalized embeddings
- Range: -1 to 1 (or 0 to 1 for normalized vectors)

**Implementation in FAISS:**
- Use `IndexFlatIP` (Inner Product) on L2-normalized vectors
- `IP(A, B) = A·B` when ||A|| = ||B|| = 1
- Equivalent to cosine similarity for normalized vectors

## Scalability Considerations

### Current Implementation
- **Vector DB**: FAISS IndexFlatIP (exact search)
- **Capacity**: Handles 10,000+ products efficiently
- **Latency**: < 500ms for search

### For Production Scale
- **FAISS IndexIVFFlat**: Approximate search for millions of vectors
- **Sharding**: Partition vectors across multiple indices
- **Caching**: Cache frequent queries
- **GPU**: Use FAISS GPU for faster search
- **Distributed**: Consider Milvus or Pinecone for cloud scale

## Security Considerations

1. **File Uploads**: Validate image types and sizes
2. **Path Traversal**: Sanitize file paths
3. **Rate Limiting**: Limit API requests per user
4. **Input Validation**: Validate filter parameters

## Monitoring & Observability

1. **Logging**: Python logging module
2. **Error Tracking**: Exception handling with detailed logs
3. **Performance Metrics**: Log search latency
4. **Usage Stats**: Track search queries and feedback

