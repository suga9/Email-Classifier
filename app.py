import streamlit as st
import pandas as pd
from utils import strip_quotes_and_disclaimers, combine_subject_body
from classifier import classify_priority
from summarizer import summarize
from reply_templates import draft_reply
from llm_provider import llm_enabled, generate_with_llm

st.set_page_config(page_title="Email Priority Classifier + Reply Generator", layout="wide")

def classify_and_draft(subject: str, body: str, tone: str):
    raw = combine_subject_body(subject, body)
    cleaned = strip_quotes_and_disclaimers(raw)
    label, scores = classify_priority(cleaned)
    intent = summarize(cleaned)
    reply = draft_reply(label, intent, tone=tone)
    return label, scores, intent, reply

st.title("📧 Email Priority Classifier + Reply Generator")

with st.sidebar:
    st.header("Controls")
    tone = st.radio("Reply tone", options=["formal", "neutral", "friendly"], index=1)
    st.markdown("---")
    st.caption("Batch mode expects CSV with `subject`, `body`. See sample in repo.")

tab1, tab2 = st.tabs(["Single Email", "Batch (CSV)"])

with tab1:
    col1, col2 = st.columns([1, 1])
    with col1:
        subject = st.text_input("Subject", value="Payment failure on checkout for order #1824")
        body = st.text_area("Body", height=260, value=(
            "Hi Support,\n\nOur client cannot process a payment on the checkout page. "
            "It fails with a 3DS timeout and shows an error. We need a workaround today.\n\nThanks"
        ))
        go = st.button("Classify & Draft", type="primary")
    with col2:
        st.subheader("Results")
        if go:
            label, scores, intent, reply = classify_and_draft(subject, body, tone)
            badge_color = {"Urgent": "🔴", "Normal": "🟡", "Low": "🟢"}.get(label, "🟡")
            st.markdown(f"**Urgency:** {badge_color} **{label}**")
            st.json(scores)
            st.markdown("**Intent Summary**")
            st.write(intent)
            st.markdown("**Reply Draft (editable)**")
            edited = st.text_area("Draft", value=reply, height=220)
            st.download_button("Download Reply (.txt)", data=edited, file_name="reply.txt")

with tab2:
    st.subheader("Batch Classify")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        required = {"subject", "body"}
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
                    label, scores, intent, reply = classify_and_draft(subj, bdy, tone)
                    results.append({
                        "subject": subj,
                        "body": bdy,
                        "urgency": label,
                        "score_urgent": scores.get("Urgent", 0.0),
                        "score_normal": scores.get("Normal", 0.0),
                        "score_low": scores.get("Low", 0.0),
                        "intent_summary": intent,
                        "reply_draft": reply
                    })
            out = pd.DataFrame(results)
            st.dataframe(out, use_container_width=True, hide_index=True)
            st.download_button("Download Results (CSV)", data=out.to_csv(index=False), file_name="classified_emails.csv")
