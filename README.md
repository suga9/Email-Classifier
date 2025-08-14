# Email Priority Classifier + Reply Generator (Option #2)

A lightweight, cloud-hostable web app that:
- Classifies incoming emails into **Urgent / Normal / Low**
- Generates an **intent summary** of the email
- **Drafts a reply** based on urgency + content (template-based by default; optional hook for an external LLM)
- Lets you **edit** the draft and **copy/download** it
- Supports **batch CSV processing** and export

## Tech Stack
- **Frontend/UI:** Streamlit (simple, fast to ship, works great on Hugging Face Spaces)
- **ML/NLP:** Hugging Face Transformers
  - Zero-shot classification: `facebook/bart-large-mnli` (default)
  - Summarization: `sshleifer/distilbart-cnn-12-6` (default, small & fast)
- **Optional:** Plug in an external LLM via API for reply generation (see `llm_provider.py`).

## Run Locally
```bash
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
streamlit run app.py
```

## CSV Format
Upload a CSV with columns:
- `subject` (string)
- `body` (string)
- (optional) `from`, `to`, `timestamp`

See `sample_data/sample_emails.csv`.

## Deploy to Hugging Face Spaces (recommended)
1. Push this repo to GitHub.
2. Create a new Space (Streamlit) on Hugging Face.
3. Connect to your GitHub repo and deploy. Done.

## Project Mapping to Course Rubric
- **USER INTERFACE (Web app):** Streamlit UI with email preview, urgency badge, reply panel, copy/download controls.
- **BUSINESS APP POWERED BY AI:** Zero-shot classifier, abstractive summarizer, and automated reply drafts.
- **EMBEDDED AI FEATURES:** Classifier + Summarizer + Generator integrated in the UI workflow.
- **CLOUD HOSTED:** Ready for Hugging Face Spaces or Render. Add the deployed link to the submission.
- **ALL CODE IN GITHUB:** Push this folder as-is.

## Notes
- Zero-shot gets you a strong **MVP** without labeling a dataset. For better accuracy, fine-tune on a small labeled set later.
- Focus evaluation on the **Urgent** class (precision/recall/F1).
