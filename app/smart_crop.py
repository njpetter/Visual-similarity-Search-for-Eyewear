import cv2
import numpy as np
from PIL import Image
import logging
from typing import Tuple, Optional
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class SmartCropper:
    def __init__(self):
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                logger.warning("Could not load face cascade, smart cropping will use fallback method")
                self.face_cascade = None
        except Exception as e:
            logger.warning(f"Could not initialize face detection: {e}. Using fallback method.")
            self.face_cascade = None
    def detect_eyewear_region(self, image: Image.Image) -> Optional[Tuple[int, int, int, int]]:
        try:
            img_array = np.array(image.convert('RGB'))
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            if self.face_cascade is not None:
                faces = self.face_cascade.detectMultiScale(
                    img_gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(50, 50)
                )
                if len(faces) > 0:
                    face = max(faces, key=lambda f: f[2] * f[3])
                    x, y, w, h = face
                    eye_y = int(y + h * 0.2)
                    eye_h = int(h * 0.4)
                    eye_x = int(x - w * 0.1)
                    eye_w = int(w * 1.2)
                    eye_x = max(0, eye_x)
                    eye_y = max(0, eye_y)
                    eye_w = min(eye_w, img_array.shape[1] - eye_x)
                    eye_h = min(eye_h, img_array.shape[0] - eye_y)
                    if eye_w > 50 and eye_h > 50:
                        logger.info(f"Detected face region: ({eye_x}, {eye_y}, {eye_w}, {eye_h})")
                        return (eye_x, eye_y, eye_w, eye_h)
            logger.info("Face detection failed, using center crop")
            return self._center_crop_region(img_array)
        except Exception as e:
            logger.error(f"Error in eyewear detection: {e}")
            return self._center_crop_region(np.array(image.convert('RGB')))
    def _center_crop_region(self, img_array: np.ndarray) -> Tuple[int, int, int, int]:
        h, w = img_array.shape[:2]
        crop_w = int(w * 0.6)
        crop_h = int(h * 0.6)
        x = (w - crop_w) // 2
        y = (h - crop_h) // 2
        return (x, y, crop_w, crop_h)
    def crop_image(self, image: Image.Image) -> Image.Image:
        region = self.detect_eyewear_region(image)
        if region is None:
            logger.warning("Could not detect eyewear region, returning original image")
            return image
        x, y, w, h = region
        cropped = image.crop((x, y, x + w, y + h))
        logger.info(f"Cropped image from {image.size} to {cropped.size}")
        return cropped
    def should_crop(self, image: Image.Image) -> bool:
        width, height = image.size
        return width > 400 or height > 400