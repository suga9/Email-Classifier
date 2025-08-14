# app.py
import streamlit as st
import pandas as pd

from utils import strip_quotes_and_disclaimers, combine_subject_body
from classifier import classify_priority
from summarizer import summarize
from reply_templates import draft_reply

# Robust import: if llm_provider ever breaks, the UI still loads.
try:
    from llm_provider import llm_enabled, generate_with_llm
except Exception:
    def llm_enabled() -> bool:
        return False
    def generate_with_llm(prompt: str, *args, **kwargs):
        return None

st.set_page_config(page_title="Email Priority Classifier + Reply Generator", layout="wide")

def _reply_subject(original_subject: str) -> str:
    s = original_subject or ""
    return s if s.lower().startswith("re:") else f"Re: {s}"

def _envelope(subject: str, body_only: str, sender_name: str, recipient_name: str) -> str:
    """Wraps body with Subject, salutation, and signature (ending with Support)."""
    reply_subj = _reply_subject(subject)
    greeting = f"Dear {recipient_name.strip()}," if recipient_name.strip() else "Hello,"
    signature = f"Best regards,\n\n{sender_name}\nSupport"
    return f"Subject: {reply_subj}\n\n{greeting}\n\n{body_only.strip()}\n\n{signature}"

def classify_and_draft(subject: str, body: str, tone: str, sender_name: str, recipient_name: str):
    """
    Pipeline:
      1) Clean + classify + summarize
      2) Create fallback body via templates
      3) Try LLM for body-only; if successful, use it; else use fallback
      4) Wrap with Subject/Salutation/Signature (Support)
    Returns: label, scores, intent, reply_full, reply_source, reply_subject
    """
    raw = combine_subject_body(subject, body)
    cleaned = strip_quotes_and_disclaimers(raw)

    label, scores = classify_priority(cleaned)
    intent = summarize(cleaned)

    # --- Fallback body (no subject/salutation/signature) ---
    # We convert your existing template into a body-only by removing any greeting/sign-off if present.
    fallback_body = draft_reply(label, intent, tone=tone).strip()

    body_only = fallback_body
    reply_source = "template"

    # --- Primary: LLM (only if enabled and successful) ---
    if llm_enabled():
        prompt = f"""You are an email assistant. Based on the details below, write ONLY the BODY of a {tone} reply.
Do NOT include a subject line, greeting/salutation, or any sign-off/signature. Keep it under 180 words.
Make it clear, concise, and actionable.

Urgency: {label}
Intent summary:
{intent}

Original email:
Subject: {subject}
Body:
{cleaned}
"""
        llm_text = generate_with_llm(prompt)
        if llm_text and llm_text.strip():
            body_only = llm_text.strip()
            reply_source = "llm"

    # Wrap with subject/salutation/signature (always ends with Support)
    reply_full = _envelope(subject, body_only, sender_name=sender_name, recipient_name=recipient_name)
    return label, scores, intent, reply_full, reply_source, _reply_subject(subject)

st.title("📧 Email Priority Classifier + Reply Generator")

with st.sidebar:
    st.header("Controls")
    tone = st.radio("Reply tone", options=["formal", "neutral", "friendly"], index=1)

    st.markdown("---")
    st.subheader("Sender / Recipient")
    sender_name = st.text_input("Your name (for signature)", value="")
    recipient_name = st.text_input("Recipient name (optional)", value="")

    st.caption("Batch mode expects CSV with `subject`, `body`.")

tab1, tab2 = st.tabs(["Single Email", "Batch (CSV)"])

# ---------------------- Single Email ----------------------
with tab1:
    col1, col2 = st.columns([1, 1])
    with col1:
        subject = st.text_input("Subject", value="Payment failure on checkout for order #1824")
        body = st.text_area(
            "Body",
            height=260,
            value=(
                "Hi Support,\n\nOur client cannot process a payment on the checkout page. "
                "It fails with a 3DS timeout and shows an error. We need a workaround today.\n\nThanks"
            ),
        )
        go = st.button("Classify & Draft", type="primary")

    with col2:
        st.subheader("Results")
        if go:
            label, scores, intent, reply_full, reply_source, reply_subject = classify_and_draft(
                subject, body, tone, sender_name, recipient_name
            )
            badge_color = {"Urgent": "🔴", "Normal": "🟡", "Low": "🟢"}.get(label, "🟡")

            st.markdown(f"**Urgency:** {badge_color} **{label}**")
            st.json(scores)

            st.markdown("**Intent Summary**")
            st.write(intent)

            st.text_input("Reply Subject", value=reply_subject, disabled=True)

            st.markdown("**Reply Draft (editable)**")
            edited = st.text_area("Draft", value=reply_full, height=260)

            # Let the user know what produced the body
            st.caption("Reply body source: " + ("LLM-enhanced" if reply_source == "llm" else "Template fallback"))

            st.download_button("Download Reply (.txt)", data=edited, file_name="reply.txt")

# ---------------------- Batch Mode ----------------------
with tab2:
    st.subheader("Batch Classify")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded is not None:
        df = pd.read_csv(uploaded)

        required = {"subject", "body"}
        # Validate columns case-insensitively
        if not required.issubset(set(df.columns.str.lower())):
            st.error("CSV must contain 'subject' and 'body' columns.")
        else:
            # Normalize column names
            cols = {c: c.lower() for c in df.columns}
            df.rename(columns=cols, inplace=True)

            results = []
            with st.spinner("Processing..."):
                for _, row in df.iterrows():
                    subj = str(row.get("subject", ""))
                    bdy = str(row.get("body", ""))
                    label, scores, intent, reply_full, reply_source, reply_subject = classify_and_draft(
                        subj, bdy, tone, sender_name, recipient_name
                    )
                    results.append(
                        {
                            "subject": subj,
                            "body": bdy,
                            "urgency": label,
                            "score_urgent": scores.get("Urgent", 0.0),
                            "score_normal": scores.get("Normal", 0.0),
                            "score_low": scores.get("Low", 0.0),
                            "intent_summary": intent,
                            "reply_subject": reply_subject,
                            "reply_draft": reply_full,
                            "reply_source": reply_source,
                        }
                    )

            out = pd.DataFrame(results)
            st.dataframe(out, use_container_width=True, hide_index=True)
            st.download_button("Download Results (CSV)", data=out.to_csv(index=False), file_name="classified_emails.csv")
