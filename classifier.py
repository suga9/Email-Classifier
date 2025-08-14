from transformers import pipeline
from functools import lru_cache

LABELS = ["Urgent", "Normal", "Low"]

@lru_cache(maxsize=1)
def get_zero_shot_classifier():
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def classify_priority(text: str):
    clf = get_zero_shot_classifier()
    result = clf(text, candidate_labels=LABELS, multi_label=False)
    # Normalize to dict: {label: score}
    scores = {lab: 0.0 for lab in LABELS}
    for lab, sc in zip(result['labels'], result['scores']):
        scores[lab] = float(sc)
    top = max(scores, key=scores.get)
    return top, scores
