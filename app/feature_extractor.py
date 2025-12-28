import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import numpy as np
from typing import List, Optional
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class FeatureExtractor:
    def __init__(self, device: Optional[str] = None):
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
        self.model = models.resnet50(weights='DEFAULT')
        self.model = nn.Sequential(*list(self.model.children())[:-1])
        self.model.eval()
        self.model.to(self.device)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        self.feature_dim = 2048
    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        tensor = self.transform(image)
        return tensor.unsqueeze(0)
    def extract_features(self, image_path: str) -> np.ndarray:
        try:
            image = Image.open(image_path)
            tensor = self.preprocess_image(image)
            tensor = tensor.to(self.device)
            with torch.no_grad():
                features = self.model(tensor)
                features = features.squeeze().cpu().numpy()
            features = features / (np.linalg.norm(features) + 1e-8)
            return features.astype('float32')
        except Exception as e:
            logger.error(f"Error extracting features from {image_path}: {str(e)}")
            raise
    def extract_features_from_image(self, image: Image.Image) -> np.ndarray:
        try:
            tensor = self.preprocess_image(image)
            tensor = tensor.to(self.device)
            with torch.no_grad():
                features = self.model(tensor)
                features = features.squeeze().cpu().numpy()
            features = features / (np.linalg.norm(features) + 1e-8)
            return features.astype('float32')
        except Exception as e:
            logger.error(f"Error extracting features from image: {str(e)}")
            raise
    def batch_extract(self, image_paths: List[str]) -> np.ndarray:
        features_list = []
        for path in image_paths:
            try:
                features = self.extract_features(path)
                features_list.append(features)
            except Exception as e:
                logger.warning(f"Skipping {path}: {str(e)}")
                continue
        if not features_list:
            raise ValueError("No valid features extracted")
        return np.array(features_list)