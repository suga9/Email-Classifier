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

def classify_and_draft(subject: str, body: str, tone: str):
    """
    Pipeline:
      1) Clean + classify + summarize
      2) Create fallback reply via templates
      3) Try LLM as primary; if it returns text, use it. Otherwise keep fallback.
    Returns: label, scores, intent, reply, reply_source ('llm' or 'template')
    """
    raw = combine_subject_body(subject, body)
    cleaned = strip_quotes_and_disclaimers(raw)

    label, scores = classify_priority(cleaned)
    intent = summarize(cleaned)

    # --- Fallback (always available) ---
    fallback_reply = draft_reply(label, intent, tone=tone)
    reply = fallback_reply
    reply_source = "template"

    # --- Primary: LLM (only if enabled and successful) ---
    if llm_enabled():
        prompt = f"""You are an email assistant. Draft a {tone} reply.

Urgency: {label}
Original email:
Subject: {subject}
Body:
{cleaned}

Intent summary:
{intent}

Write a clear, concise, professional reply the user can send as-is.
Do not include code fences or markdown formatting. Keep it under 180 words unless escalation is essential."""
        llm_text = generate_with_llm(prompt)
        if llm_text and llm_text.strip():
            reply = llm_text.strip()
            reply_source = "llm"

    return label, scores, intent, reply, reply_source

st.title("📧 Email Priority Classifier + Reply Generator")

with st.sidebar:
    st.header("Controls")
    tone = st.radio("Reply tone", options=["formal", "neutral", "friendly"], index=1)
    st.markdown("---")
    st.caption("Batch mode expects CSV with `subject`, `body`. See sample in repo.")

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
            label, scores, intent, reply, reply_source = classify_and_draft(subject, body, tone)
            badge_color = {"Urgent": "🔴", "Normal": "🟡", "Low": "🟢"}.get(label, "🟡")

            st.markdown(f"**Urgency:** {badge_color} **{label}**")
            st.json(scores)

            st.markdown("**Intent Summary**")
            st.write(intent)

            st.markdown("**Reply Draft (editable)**")
            edited = st.text_area("Draft", value=reply, height=220)

            # Let the user know what produced the draft
            if reply_source == "llm":
                st.caption("Reply source: LLM-enhanced")
            else:
                st.caption("Reply source: Template fallback")

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
                    label, scores, intent, reply, reply_source = classify_and_draft(subj, bdy, tone)
                    results.append(
                        {
                            "subject": subj,
                            "body": bdy,
                            "urgency": label,
                            "score_urgent": scores.get("Urgent", 0.0),
                            "score_normal": scores.get("Normal", 0.0),
                            "score_low": scores.get("Low", 0.0),
                            "intent_summary": intent,
                            "reply_draft": reply,
                            "reply_source": reply_source,  # helpful for QA
                        }
                    )

            out = pd.DataFrame(results)
            st.dataframe(out, use_container_width=True, hide_index=True)
            st.download_button("Download Results (CSV)", data=out.to_csv(index=False), file_name="classified_emails.csv")
