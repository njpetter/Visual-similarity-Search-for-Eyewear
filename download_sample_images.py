import os
import requests
import time
SAVE_DIR = "data/images"
os.makedirs(SAVE_DIR, exist_ok=True)
WORKING_URLS = [
    "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=600&q=80",
    "https://images.unsplash.com/photo-1577803645773-f96470509666?w=600&q=80",
    "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=600&q=80",
    "https://images.unsplash.com/photo-1591076482161-42ce6da69f67?w=600&q=80",
    "https://images.unsplash.com/photo-1533827432537-70133748f5c8?w=600&q=80",
    "https://images.unsplash.com/photo-1556306535-0f09a537f0a3?w=600&q=80",
    "https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?w=600&q=80",
    "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600&q=80",
    "https://images.unsplash.com/photo-1509941323117-9c7881d29d97?w=600&q=80",
    "https://images.unsplash.com/photo-1625591348650-3a382c730414?w=600&q=80"
]
def download_images():
    print(f"--- Phase 1: Downloading {len(WORKING_URLS)} curated images ---")
    for i, url in enumerate(WORKING_URLS):
        filename = f"glasses_{i+1}.jpg"
        save_image(url, filename)
    print(f"\n--- Phase 2: Fetching more via LoremFlickr ---")
    current_count = len(WORKING_URLS)
    target_count = 50
    for i in range(current_count, target_count):
        url = f"https://loremflickr.com/600/600/glasses,sunglasses/all?lock={i}"
        filename = f"glasses_{i+1}.jpg"
        save_image(url, filename)
        time.sleep(0.5)
    print("\n[SUCCESS] Download complete! Images saved to 'data/images/'")
def save_image(url, filename):
    file_path = os.path.join(SAVE_DIR, filename)
    if os.path.exists(file_path):
        print(f"[SKIP] {filename} already exists")
        return
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"[OK] Saved: {filename}")
        else:
            print(f"[FAIL] {filename} (Status: {response.status_code})")
    except Exception as e:
        print(f"[ERROR] {filename}: {e}")
if __name__ == "__main__":
    download_images()