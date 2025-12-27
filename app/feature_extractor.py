"""
Feature extraction using ResNet50 for generating image embeddings
"""
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
    """Extracts features from images using ResNet50"""
    
    def __init__(self, device: Optional[str] = None):
        """
        Initialize the feature extractor
        
        Args:
            device: 'cuda' for GPU, 'cpu' for CPU (auto-detected if None)
        """
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        # Load pre-trained ResNet50
        self.model = models.resnet50(pretrained=True)
        
        # Remove the final classification layer to get feature vectors
        self.model = nn.Sequential(*list(self.model.children())[:-1])
        self.model.eval()  # Set to evaluation mode
        self.model.to(self.device)
        
        # Image preprocessing pipeline
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # Feature dimension: 2048 for ResNet50
        self.feature_dim = 2048
    
    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """
        Preprocess image for feature extraction
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed tensor
        """
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Apply transformations
        tensor = self.transform(image)
        return tensor.unsqueeze(0)  # Add batch dimension
    
    def extract_features(self, image_path: str) -> np.ndarray:
        """
        Extract feature vector from image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            Feature vector as numpy array (2048 dimensions)
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path)
            tensor = self.preprocess_image(image)
            tensor = tensor.to(self.device)
            
            # Extract features
            with torch.no_grad():
                features = self.model(tensor)
                # Flatten the features
                features = features.squeeze().cpu().numpy()
            
            # Normalize to unit vector for cosine similarity
            features = features / (np.linalg.norm(features) + 1e-8)
            
            return features.astype('float32')
            
        except Exception as e:
            logger.error(f"Error extracting features from {image_path}: {str(e)}")
            raise
    
    def extract_features_from_image(self, image: Image.Image) -> np.ndarray:
        """
        Extract feature vector from PIL Image object
        
        Args:
            image: PIL Image object
            
        Returns:
            Feature vector as numpy array
        """
        try:
            tensor = self.preprocess_image(image)
            tensor = tensor.to(self.device)
            
            with torch.no_grad():
                features = self.model(tensor)
                features = features.squeeze().cpu().numpy()
            
            # Normalize for cosine similarity
            features = features / (np.linalg.norm(features) + 1e-8)
            
            return features.astype('float32')
            
        except Exception as e:
            logger.error(f"Error extracting features from image: {str(e)}")
            raise
    
    def batch_extract(self, image_paths: List[str]) -> np.ndarray:
        """
        Extract features from multiple images efficiently
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            Matrix of feature vectors (N x 2048)
        """
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

