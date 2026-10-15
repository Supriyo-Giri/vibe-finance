"""
LLM client – OpenAI-compatible API from .env, falls back to None if unavailable.
"""
from __future__ import annotations
import json
import re
from typing import Any, Optional
from app.config import settings

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


def llm_available() -> bool:
    return bool(
        not settings.use_mock_llm
        and settings.openai_api_key
        and HAS_HTTPX
    )


def chat(
    system: str,
    user: str,
    temperature: float = 0.3,
    max_tokens: int = 800,
) -> Optional[str]:
    """
    Call OpenAI-compatible chat completions.
    Returns assistant text or None on failure / mock mode.
    """
    if not llm_available():
        return None

    url = (settings.openai_base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.llm_model or "gpt-4o-mini",
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[llm_client] API call failed: {e}")
        return None


def chat_json(
    system: str,
    user: str,
    temperature: float = 0.2,
) -> Optional[dict]:
    """Ask for JSON only; parse and return dict or None."""
    text = chat(
        system + "\nRespond with valid JSON only. No markdown fences.",
        user,
        temperature=temperature,
        max_tokens=1000,
    )
    if not text:
        return None
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
        return None