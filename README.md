Email Priority Assistant
LLM-powered assistant that:

🧭 Classifies incoming emails by urgency (Urgent / Normal / Low)

✍️ Drafts a bespoke reply per email (no rigid template)

🧩 Works with both a Streamlit UI and a Gmail Workspace Add-on

🌐 Exposes a FastAPI backend that other clients can call

Features
LLM-only reply generation (OpenAI / Anthropic / Gemini; pick one provider)

Lightweight urgency classifier (HF pipeline) + small intent summary for LLM context

Personalized greeting from the sender’s name/email, plus auto ticket ID and next-update time

Streamlit UI for demos and bulk testing with CSV

Gmail add-on that reads the selected email and calls the same backend

Easy deployment to Cloud Run or Railway
