import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class ImageValidator:
    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = models.resnet50(weights='DEFAULT')
        self.model = nn.Sequential(*list(model.children())[:-1])
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
    def is_likely_eyewear(self, image_path: str, threshold: float = 0.5) -> bool:
        try:
            image = Image.open(image_path).convert('RGB')
            tensor = self.transform(image).unsqueeze(0).to(self.device)
            with torch.no_grad():
                features = self.model(tensor).squeeze().cpu().numpy()
            return True
        except Exception as e:
            logger.warning(f"Error validating image {image_path}: {e}")
            return False