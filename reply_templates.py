# reply_templates.py
from datetime import datetime, timedelta
import random

TONE_HEADERS = {
    "formal": "Hello,",
    "neutral": "Hi,",
    "friendly": "Hey there,"
}

TONE_CLOSINGS = {
    "formal": "Regards,\nSupport Team",
    "neutral": "Thanks,\nSupport Team",
    "friendly": "Cheers,\nSupport Team"
}

def _gen_incident_id(prefix: str = "INC") -> str:
    now = datetime.now()
    rand = "".join(random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(4))
    return f"{prefix}-{now.strftime('%Y%m%d-%H%M')}-{rand}"

def _next_update_str(minutes: int = 120) -> str:
    when = datetime.now() + timedelta(minutes=int(minutes or 120))
    return when.strftime("%b %d, %Y %I:%M %p")

def draft_reply(
    urgency: str,
    intent_summary: str,
    tone: str = "neutral",
    incident_id: str | None = None,
    next_update_minutes: int = 120,
    what_were_doing: list[str] | None = None,
):
    header = TONE_HEADERS.get(tone, TONE_HEADERS["neutral"])
    closing = TONE_CLOSINGS.get(tone, TONE_CLOSINGS["neutral"])

    inc_id = incident_id or _gen_incident_id()
    next_update = _next_update_str(next_update_minutes)

    # Default action bullets
    if not what_were_doing:
        steps = [
            "Investigating recent changes and related services",
            "Monitoring error rates and affected users",
            "Coordinating with the on-call team and vendor (if applicable)",
        ]
        if urgency == "Urgent":
            steps.insert(0, "Mitigating immediate customer impact and preparing a workaround")
    else:
        steps = list(what_were_doing)

    if urgency == "Urgent":
        opening = (
            "Thanks for flagging this—treating as priority. "
            f"We’ve opened incident {inc_id}."
        )
    elif urgency == "Low":
        opening = (
            "Thanks for your message. We’ve logged this and are tracking it. "
            f"Reference: {inc_id}."
        )
    else:
        opening = (
            "Thanks for contacting us. We’re on it. "
            f"Tracking under {inc_id}."
        )

    body = [
        opening,
        "",
        f"What we’re seeing:",
        f"- {intent_summary.strip()}",
        "",
        "What we’re doing now:",
        *[f"- {s}" for s in steps],
        "",
        f"Next update: by {next_update}",
    ]

    return f"""{header}

{'\n'.join(body)}

{closing}"""