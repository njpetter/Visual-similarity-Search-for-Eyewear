import os
import shutil
import subprocess
import sys
def reset_and_ingest():
    print("🧹 Cleaning up old database files...")
    files_to_delete = [
        "data/db.sqlite",
        "data/embeddings/faiss.index",
        "data/embeddings/faiss_ids.pkl"
    ]
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"   ✓ Deleted: {file_path}")
            except Exception as e:
                print(f"   ✗ Error deleting {file_path}: {e}")
    print("\n🏗️  Starting Ingestion Process...")
    try:
        subprocess.run(["python", "-m", "app.ingest_images"], check=True)
        print("\n✅ Database rebuilt successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during ingestion: {e}")
if __name__ == "__main__":
    reset_and_ingest()