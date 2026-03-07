"""Lightweight on-disk learning store (JSONL).

Goal:
  - Persist user-approved corrected tests / fixes.
  - Reuse them as few-shot examples for the fixer/chat.

This is intentionally simple (demo-friendly). It's not a real ML pipeline,
but it gives the product behavior the user asked for: "learn on corrected tests".
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class LearningExample:
    created_at: str
    session_id: str
    pytest_output: str
    original_test_code: str
    corrected_test_code: str
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "created_at": self.created_at,
            "session_id": self.session_id,
            "pytest_output": self.pytest_output,
            "original_test_code": self.original_test_code,
            "corrected_test_code": self.corrected_test_code,
            "notes": self.notes,
        }


class LearningStore:
    def __init__(self, path: str = "app/data/learned_fixes.jsonl") -> None:
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def add(
        self,
        *,
        session_id: str,
        pytest_output: str,
        original_test_code: str,
        corrected_test_code: str,
        notes: str = "",
    ) -> LearningExample:
        ex = LearningExample(
            created_at=datetime.now().isoformat(),
            session_id=session_id,
            pytest_output=(pytest_output or "")[:20000],
            original_test_code=(original_test_code or "")[:20000],
            corrected_test_code=(corrected_test_code or "")[:20000],
            notes=(notes or "")[:2000],
        )
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(ex.to_dict(), ensure_ascii=False) + "\n")
        return ex

    def load_last(self, limit: int = 5) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        out: List[Dict[str, Any]] = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            return []

        # Return most recent first
        return out[-limit:]
