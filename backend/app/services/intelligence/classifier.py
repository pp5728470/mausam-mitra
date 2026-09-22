from app.services.intelligence.schemas import (
    SystemCategory,
    ClassificationSignal,
    ClassificationResult,
)
from app.services.intelligence.keywords import CATEGORY_KEYWORDS

CLASSIFIER_VERSION = "v1"

def classify_text(title: str, description: str | None) -> ClassificationResult:
    """
    Deterministic keyword-based classifier.
    """
    text_to_search = f"{title} {description or ''}".lower()
    
    best_category = SystemCategory.OTHER
    highest_score = 0.0
    best_signals: list[ClassificationSignal] = []
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        category_score = 0.0
        signals: list[ClassificationSignal] = []
        
        for phrase, weight in keywords:
            if phrase in text_to_search:
                # Add weight to score. Cap at 0.99 so it never reaches exactly 1.0 (100%)
                # using a simple formula: new_score = old_score + (1 - old_score) * weight
                category_score = category_score + (1 - category_score) * weight
                
                # Determine source (title or description)
                source = "title" if phrase in title.lower() else "description"
                
                signals.append(
                    ClassificationSignal(
                        phrase=phrase,
                        weight=weight,
                        source=source
                    )
                )
        
        if category_score > highest_score:
            highest_score = category_score
            best_category = category
            best_signals = signals

    # Threshold for "OTHER"
    if highest_score < 0.4:
        best_category = SystemCategory.OTHER
        highest_score = 0.0
        best_signals = []
        explanation = "No strong incident indicators detected in report text."
    else:
        # Cap confidence at 0.99
        highest_score = min(round(highest_score, 2), 0.99)
        explanation = f"Strong {best_category.value.lower().replace('_', '/')} indicators detected in report text."
        
    return ClassificationResult(
        classified_category=best_category,
        confidence=highest_score,
        signals=best_signals,
        explanation=explanation,
        classifier_version=CLASSIFIER_VERSION
    )
