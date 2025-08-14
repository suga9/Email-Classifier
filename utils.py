import re

QUOTE_PATTERNS = [
    r"""^On .*wrote:$""",          # common quoted reply marker
    r"""^From:.*$""",             # email headers
    r"""^Sent:.*$""",
    r"""^To:.*$""",
    r"""^Subject:.*$"""
]

DISCLAIMER_PATTERNS = [
    r"""This message.*confidential.*""",
    r"""DISCLAIMER:.*"""
]

def strip_quotes_and_disclaimers(text: str) -> str:
    lines = text.splitlines()
    cleaned = []
    stop = False
    for line in lines:
        if any(re.match(p, line.strip(), flags=re.IGNORECASE) for p in QUOTE_PATTERNS):
            stop = True
        if not stop:
            cleaned.append(line)
    text = "\n".join(cleaned)
    for p in DISCLAIMER_PATTERNS:
        text = re.sub(p, "", text, flags=re.IGNORECASE|re.DOTALL)
    return text.strip()

def combine_subject_body(subject: str, body: str) -> str:
    subject = subject or ""
    body = body or ""
    if subject and not subject.endswith('.'):
        subject = subject + ":"
    return f"{subject}\n\n{body}".strip()
