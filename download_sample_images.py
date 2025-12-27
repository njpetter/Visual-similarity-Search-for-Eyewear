import os
import requests
import time

# Directory to save images
SAVE_DIR = "data/images"
os.makedirs(SAVE_DIR, exist_ok=True)

# Pre-selected high-quality eyewear images from Unsplash
SAMPLE_IMAGES = [
    # Aviators / Metal Frames
    "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=600&q=80",
    "https://images.unsplash.com/photo-1577803645773-f96470509666?w=600&q=80",
    "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=600&q=80",
    
    # Wayfarer / Thick Plastic Frames
    "https://images.unsplash.com/photo-1591076482161-42ce6da69f67?w=600&q=80",
    "https://images.unsplash.com/photo-1533827432537-70133748f5c8?w=600&q=80",
    "https://images.unsplash.com/photo-1570222094114-28a9d88a2ef5?w=600&q=80",
    
    # Round / Retro Styles
    "https://images.unsplash.com/photo-1556306535-0f09a537f0a3?w=600&q=80",
    "https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?w=600&q=80",
    "https://images.unsplash.com/photo-1562590409-16a5a08e0073?w=600&q=80",
    
    # Cat Eye / Fashion
    "https://images.unsplash.com/photo-1508296695146-25d6105749bd?w=600&q=80",
    "https://images.unsplash.com/photo-1534844978-b859e5a09947?w=600&q=80",
    
    # Clear / Reading Glasses
    "https://images.unsplash.com/photo-1597248881519-db089d3744a5?w=600&q=80",
    "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600&q=80",
    "https://images.unsplash.com/photo-1509941323117-9c7881d29d97?w=600&q=80",
    
    # Sunglasses / Sport
    "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=600&q=80",
    "https://images.unsplash.com/photo-1625591348650-3a382c730414?w=600&q=80",
    
    # Rimless / Minimal
    "https://images.unsplash.com/photo-1599593079207-e85d8eb822a0?w=600&q=80"
]

def download_images():
    print(f"Starting download of {len(SAMPLE_IMAGES)} sample images...")
    
    for i, url in enumerate(SAMPLE_IMAGES):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                file_path = os.path.join(SAVE_DIR, f"glasses_{i+1}.jpg")
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"✓ Downloaded: glasses_{i+1}.jpg")
            else:
                print(f"❌ Failed: {url} (Status: {response.status_code})")
        except Exception as e:
            print(f"❌ Error downloading {url}: {e}")
        
        # Be nice to the server
        time.sleep(0.5)

    print("\n✅ Download complete! Images saved to 'data/images/'")

if __name__ == "__main__":
    download_images()