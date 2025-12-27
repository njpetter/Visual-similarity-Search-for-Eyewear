"""
Quick start script for the Visual Similarity Search application
"""
import sys
import os

def check_setup():
    """Check if system is set up correctly"""
    print("Checking setup...")
    
    # Check if data/images exists and has images
    if not os.path.exists("data/images"):
        print("⚠️  Warning: data/images/ directory not found")
        print("   Please create it and add eyewear images")
        return False
    
    image_files = [f for f in os.listdir("data/images") 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print("⚠️  Warning: No images found in data/images/")
        print("   Please add eyewear images to data/images/")
        return False
    
    # Check if database exists
    if not os.path.exists("data/db.sqlite"):
        print("⚠️  Database not found. Run image ingestion first:")
        print("   python -m app.ingest_images")
        return False
    
    print("✅ Setup looks good!")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_setup()
    else:
        print("Visual Similarity Search for Eyewear")
        print("=" * 50)
        print("\nTo start the server, run:")
        print("  uvicorn app.main:app --reload")
        print("\nOr check setup:")
        print("  python run.py --check")
        print("\nFor first-time setup, see SETUP.md")

