"""
Smart cropping: Automatically detect and crop eyewear from busy photos
Uses face detection and simple heuristics to find eyewear region
"""
import cv2
import numpy as np
from PIL import Image
import logging
from typing import Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SmartCropper:
    """
    Detects and crops eyewear region from images
    Uses face detection to locate eye region, then crops around it
    """
    
    def __init__(self):
        """Initialize smart cropper with face detection"""
        try:
            # Try to load OpenCV's face cascade
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                logger.warning("Could not load face cascade, smart cropping will use fallback method")
                self.face_cascade = None
        except Exception as e:
            logger.warning(f"Could not initialize face detection: {e}. Using fallback method.")
            self.face_cascade = None
    
    def detect_eyewear_region(self, image: Image.Image) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect eyewear region in image
        
        Args:
            image: PIL Image
            
        Returns:
            Tuple (x, y, width, height) of eyewear region, or None if not detected
        """
        try:
            # Convert PIL to OpenCV format
            img_array = np.array(image.convert('RGB'))
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Try face detection first
            if self.face_cascade is not None:
                faces = self.face_cascade.detectMultiScale(
                    img_gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(50, 50)
                )
                
                if len(faces) > 0:
                    # Use the largest face (most likely to be the main subject)
                    face = max(faces, key=lambda f: f[2] * f[3])
                    x, y, w, h = face
                    
                    # Crop to upper half of face (where glasses typically are)
                    # Adjust to focus on eye/glasses region
                    eye_y = int(y + h * 0.2)  # Start 20% down from top of face
                    eye_h = int(h * 0.4)      # Use 40% of face height
                    eye_x = int(x - w * 0.1)  # Extend slightly left
                    eye_w = int(w * 1.2)      # Extend slightly right
                    
                    # Ensure coordinates are within image bounds
                    eye_x = max(0, eye_x)
                    eye_y = max(0, eye_y)
                    eye_w = min(eye_w, img_array.shape[1] - eye_x)
                    eye_h = min(eye_h, img_array.shape[0] - eye_y)
                    
                    if eye_w > 50 and eye_h > 50:  # Ensure minimum size
                        logger.info(f"Detected face region: ({eye_x}, {eye_y}, {eye_w}, {eye_h})")
                        return (eye_x, eye_y, eye_w, eye_h)
            
            # Fallback: Use center crop if face detection fails
            logger.info("Face detection failed, using center crop")
            return self._center_crop_region(img_array)
            
        except Exception as e:
            logger.error(f"Error in eyewear detection: {e}")
            return self._center_crop_region(np.array(image.convert('RGB')))
    
    def _center_crop_region(self, img_array: np.ndarray) -> Tuple[int, int, int, int]:
        """
        Fallback: Crop center region of image
        
        Args:
            img_array: Image as numpy array
            
        Returns:
            Tuple (x, y, width, height) of center region
        """
        h, w = img_array.shape[:2]
        # Crop center 60% of image
        crop_w = int(w * 0.6)
        crop_h = int(h * 0.6)
        x = (w - crop_w) // 2
        y = (h - crop_h) // 2
        return (x, y, crop_w, crop_h)
    
    def crop_image(self, image: Image.Image) -> Image.Image:
        """
        Crop image to eyewear region
        
        Args:
            image: PIL Image
            
        Returns:
            Cropped PIL Image
        """
        region = self.detect_eyewear_region(image)
        if region is None:
            logger.warning("Could not detect eyewear region, returning original image")
            return image
        
        x, y, w, h = region
        cropped = image.crop((x, y, x + w, y + h))
        logger.info(f"Cropped image from {image.size} to {cropped.size}")
        return cropped
    
    def should_crop(self, image: Image.Image) -> bool:
        """
        Determine if image should be cropped
        Heuristic: If image is much larger than 224x224, likely contains face
        
        Args:
            image: PIL Image
            
        Returns:
            True if cropping is recommended
        """
        width, height = image.size
        # If image is significantly larger than target size, likely needs cropping
        return width > 400 or height > 400

