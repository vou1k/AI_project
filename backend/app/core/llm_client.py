"""
LLM client for GigaChat (Sber).

This project uses the official Python SDK `gigachat` (ai-forever/gigachat) to work in РФ.

Enable by setting ONE of the following:
  - GIGACHAT_CREDENTIALS: authorization key (recommended)
  - GIGACHAT_ACCESS_TOKEN: access token (valid ~30 minutes)
  - (advanced) mTLS / user+password options supported by the SDK via env vars

Useful env vars (see official docs):
  - GIGACHAT_MODEL (default: GigaChat)
  - GIGACHAT_SCOPE (default: GIGACHAT_API_PERS)
  - GIGACHAT_BASE_URL (default: https://gigachat.devices.sberbank.ru/api/v1)
  - GIGACHAT_VERIFY_SSL_CERTS (default: true)
  - GIGACHAT_CA_BUNDLE_FILE (optional, if your environment requires it)

If credentials are not configured, the platform falls back to rule-based generation/debugging.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

try:
    from gigachat import GigaChat
except Exception:  # pragma: no cover
    GigaChat = None


class LLMDisabled(RuntimeError):
    pass


class LLMClient:
    """Thin wrapper around GigaChat SDK."""

    def __init__(self) -> None:
        self.enabled = GigaChat is not None
        self._client = None
        if self.enabled:
            # SDK can read all config from environment variables with prefix GIGACHAT_
            # so we can initialize without explicit params.
            self._client = GigaChat()

    def is_enabled(self) -> bool:
        if not self.enabled or self._client is None:
            return False
        # If no auth configured, the first request will fail. We'll treat this as "enabled"
        # only if the user provided at least one auth env var.
        import os
        return bool(os.getenv("GIGACHAT_CREDENTIALS") or os.getenv("GIGACHAT_ACCESS_TOKEN") or os.getenv("GIGACHAT_AUTHORIZATION_CVAR"))

    def chat(self, messages: List[Dict[str, str]], *, max_tokens: int = 1200) -> str:
        """Send chat request and return assistant text."""
        if not self.is_enabled() or self._client is None:
            raise LLMDisabled("GigaChat is not configured. Set GIGACHAT_CREDENTIALS (recommended) or GIGACHAT_ACCESS_TOKEN.")

        # GigaChat SDK supports .chat(messages) with OpenAI-like messages format.
        # We keep the interface aligned with the rest of the project.
        resp = self._client.chat(messages, max_tokens=max_tokens)
        # SDK response is an object; try to extract content safely
        try:
            return resp.choices[0].message.content or ""
        except Exception:
            # Fallback: stringify
            return str(resp)

    @staticmethod
    def extract_json(text: str) -> Optional[Any]:
        """Best-effort extraction of JSON object/array from an LLM response."""
        if not text:
            return None

        # Fast path: whole string
        try:
            return json.loads(text)
        except Exception:
            pass

        # Remove code fences
        cleaned = re.sub(r"^```(?:json)?\s*|```\s*$", "", text.strip(), flags=re.IGNORECASE | re.MULTILINE).strip()

        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # Extract first JSON object/array by bracket matching
        for start_ch, end_ch in [("[", "]"), ("{", "}")]:  # prefer arrays
            start = cleaned.find(start_ch)
            if start == -1:
                continue
            depth = 0
            for i in range(start, len(cleaned)):
                ch = cleaned[i]
                if ch == start_ch:
                    depth += 1
                elif ch == end_ch:
                    depth -= 1
                    if depth == 0:
                        candidate = cleaned[start:i+1]
                        try:
                            return json.loads(candidate)
                        except Exception:
                            break
        return None
