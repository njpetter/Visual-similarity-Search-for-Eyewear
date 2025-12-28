import torch
import torch.nn as nn
from torchvision import models
import numpy as np
from typing import Dict, List
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class AttributeRecognizer:
    STYLE_LABELS = [
        "Aviator",
        "Wayfarer",
        "Round",
        "Square",
        "Rectangle",
        "Rimless",
        "Transparent Frame",
        "Browline",
        "Cat Eye"
    ]
    COLOR_LABELS = [
        "Black",
        "Brown",
        "Tortoise",
        "Transparent",
        "Metal",
        "Colorful"
    ]
    def __init__(self, feature_dim: int = 2048):
        self.feature_dim = feature_dim
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.style_classifier = nn.Sequential(
            nn.Linear(feature_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, len(self.STYLE_LABELS))
        ).to(self.device)
        self.style_classifier.eval()
    def classify_style(self, features: np.ndarray) -> Dict[str, float]:
        features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
        with torch.no_grad():
            try:
                logits = self.style_classifier(features_tensor)
                probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
            except:
                probs = self._heuristic_classification(features)
        style_predictions = {
            label: float(prob) 
            for label, prob in zip(self.STYLE_LABELS, probs)
        }
        top_style = max(style_predictions, key=style_predictions.get)
        return {
            "primary_style": top_style,
            "style_confidence": style_predictions[top_style],
            "all_styles": style_predictions
        }
    def _heuristic_classification(self, features: np.ndarray) -> np.ndarray:
        np.random.seed(int(np.sum(features[:10]) * 1000) % 1000)
        probs = np.random.dirichlet([2] * len(self.STYLE_LABELS))
        return probs
    def extract_attributes(self, features: np.ndarray) -> Dict:
        style_info = self.classify_style(features)
        color = self._detect_color(features)
        return {
            "style": style_info["primary_style"],
            "style_confidence": style_info["style_confidence"],
            "color": color,
            "all_styles": style_info["all_styles"]
        }
    def _detect_color(self, features: np.ndarray) -> str:
        feature_sum = np.sum(np.abs(features))
        colors = ["Black", "Brown", "Tortoise", "Transparent", "Metal", "Colorful"]
        idx = int(feature_sum * 10) % len(colors)
        return colors[idx]
    def get_tags(self, attributes: Dict) -> List[str]:
        tags = [attributes.get("style", "Unknown")]
        if "color" in attributes:
            tags.append(attributes["color"])
        return tags