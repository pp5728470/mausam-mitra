from pydantic import BaseModel
from typing import List
from enum import Enum

# System classified categories
class SystemCategory(str, Enum):
    HEAVY_RAINFALL = "HEAVY_RAINFALL"
    FLOOD_WATERLOGGING = "FLOOD_WATERLOGGING"
    STORM_STRONG_WINDS = "STORM_STRONG_WINDS"
    LIGHTNING = "LIGHTNING"
    EXTREME_HEAT = "EXTREME_HEAT"
    HAILSTORM = "HAILSTORM"
    LANDSLIDE = "LANDSLIDE"
    DENSE_FOG = "DENSE_FOG"
    OTHER = "OTHER"

class ClassificationSignal(BaseModel):
    phrase: str
    weight: float
    source: str

class ClassificationResult(BaseModel):
    classified_category: SystemCategory
    confidence: float
    signals: List[ClassificationSignal]
    explanation: str
    classifier_version: str

class ClassificationResponse(ClassificationResult):
    report_id: str
