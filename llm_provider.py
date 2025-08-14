# llm_provider.py
import os
from typing import Optional

def _enabled_flag() -> bool:
    v = str(os.getenv("LLM_PROVIDER", "")).strip().lower()
    # Accept simple toggles or provider names
    return v in {"1", "true", "yes", "openai", "anthropic"}

def llm_enabled() -> bool:
    """Return True if LLM use is enabled via env var LLM_PROVIDER."""
    return _enabled_flag()

def generate_with_llm(
    prompt: str,
    system: Optional[str] = "You are a helpful assistant that writes concise, clear replies.",
    max_tokens: int = 300,
) -> Optional[str]:
    """
    Generate text from the configured LLM. Returns None if disabled or on any error.
    Supports: OpenAI (LLM_PROVIDER=openai) and a no-op fallback.
    """
    if not _enabled_flag() or not prompt:
        return None

    provider = str(os.getenv("LLM_PROVIDER", "")).strip().lower()

    # ---- OpenAI path ----
    if provider in {"1", "true", "yes", "openai"}:
        api_key = os.getenv("OPENAI_API_KEY", "")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not api_key:
            return None
        try:
            from openai import OpenAI  # pip install openai>=1.52.0
            client = OpenAI(api_key=api_key)

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception:
            return None

    # (Optional) Anthropic stub—enable by setting LLM_PROVIDER=anthropic and adding the SDK.
    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        if not api_key:
            return None
        try:
            import anthropic  # pip install anthropic
            client = anthropic.Anthropic(api_key=api_key)
            content = []
            if system:
                content.append({"type": "text", "text": system})
            content.append({"type": "text", "text": prompt})
            resp = client.messages.create(model=model, max_tokens=max_tokens,
                                          messages=[{"role": "user", "content": content}])
            parts = [c.text for c in resp.content if getattr(c, "type", "") == "text"]
            return "\n".join(parts).strip() if parts else None
        except Exception:
            return None

    return None
