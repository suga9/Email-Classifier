from transformers import pipeline
from functools import lru_cache

@lru_cache(maxsize=1)
def get_summarizer():
    # smaller & faster than BART-large
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def summarize(text: str, max_tokens: int = 120):
    if not text or len(text.split()) < 12:
        return text
    sm = get_summarizer()
    out = sm(text, max_length=max_tokens, min_length=30, do_sample=False)
    return out[0]['summary_text']
