"""
Coder Agent - Transforms test cases into executable code (Pytest).

Fixes:
- de-duplication (safety net)
- pytest parametrization
- meaningful negative/boundary expectations
- skip negative/boundary for demo endpoint /api/test (MVP honesty)
"""

from __future__ import annotations

from typing import List, Dict, Any, Tuple
import re

from app.core.models import TestCase, GeneratedCode


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _tc_key(tc: TestCase) -> Tuple[str, str, str, str]:
    return (
        _norm(getattr(tc, "requirement_id", "")),
        _norm(getattr(tc, "type", "")),
        "|".join(_norm(x) for x in (getattr(tc, "steps", None) or [])),
        _norm(getattr(tc, "expected_result", "")),
    )


def _infer_expected_codes(tc: TestCase) -> List[int]:
    t = (getattr(tc, "type", "") or "").lower()
    if t == "negative":
        return [400, 401, 403, 404, 409, 422]
    if t == "boundary":
        return [200, 201, 204, 400, 401, 403, 404, 409, 422]
    return [200, 201, 204]


def _infer_endpoint(tc: TestCase) -> Tuple[str, str, Dict[str, Any] | None]:
    text = " ".join([getattr(tc, "title", "")] + list(getattr(tc, "steps", []) or []))
    t = _norm(text)

    if any(k in t for k in ["логин", "вход", "авторизац", "signin", "login"]):
        if tc.type == "negative":
            return "POST", "/api/login", {"email": "user@test.com", "password": "wrong"}
        return "POST", "/api/login", {"email": "user@test.com", "password": "12345678"}

    if any(k in t for k in ["регистрац", "signup", "register"]):
        if tc.type == "negative":
            return "POST", "/api/register", {"email": "user@test.com"}  # missing password
        if tc.type == "boundary":
            return "POST", "/api/register", {"email": "user@test.com", "password": "1234567"}  # 7 chars
        return "POST", "/api/register", {"email": "user@test.com", "password": "12345678"}

    if any(k in t for k in ["профиль", "profile", "аккаунт", "account"]):
        return "GET", "/api/profile", None

    return "GET", "/api/test", None


class TestCoder:
    def generate_code(self, test_cases: List[TestCase]) -> GeneratedCode:
        test_cases = self._dedupe(test_cases)
        code = self._generate_pytest_code(test_cases)
        return GeneratedCode(
            code=code,
            framework="pytest",
            test_count=len(test_cases),
            coverage_estimate=min(100, len(test_cases) * 10),
        )

    def _dedupe(self, tests: List[TestCase]) -> List[TestCase]:
        seen = set()
        out: List[TestCase] = []
        for tc in tests:
            k = _tc_key(tc)
            if k in seen:
                continue
            seen.add(k)
            out.append(tc)
        return out

    def _safe(self, name: str) -> str:
        name = (name or "").lower().replace("-", "_").replace(" ", "_")
        name = re.sub(r"[^a-z0-9_]+", "_", name)
        name = re.sub(r"_+", "_", name).strip("_")
        return name or "test_case"

    def _generate_pytest_code(self, test_cases: List[TestCase]) -> str:
        params: List[Dict[str, Any]] = []
        for tc in test_cases:
            method, path, payload = _infer_endpoint(tc)
            params.append(
                {
                    "id": f"{self._safe(tc.requirement_id)}_{self._safe(tc.type)}",
                    "requirement_id": tc.requirement_id,
                    "title": tc.title,
                    "type": tc.type,
                    "steps": tc.steps or [],
                    "expected_result": tc.expected_result,
                    "method": method,
                    "path": path,
                    "payload": payload,
                    "expected_codes": _infer_expected_codes(tc),
                }
            )

        lines = [
            '"""',
            "Automatically generated tests (MVP, dedup + parametrized)",
            f"Total tests: {len(test_cases)}",
            '"""',
            "",
            "import os",
            "import pytest",
            "import requests",
            "",
            'DEFAULT_BASE_URL = "http://localhost:5000"',
            "",
            '@pytest.fixture(scope="session")',
            "def base_url():",
            '    return os.getenv("BASE_URL", DEFAULT_BASE_URL)',
            "",
            "@pytest.fixture()",
            "def session():",
            "    return requests.Session()",
            "",
            "",
            "TEST_CASES = [",
        ]
        for p in params:
            lines.append(f"    {p!r},")
        lines.extend(["]", "", ""])

        lines.extend(
            [
                '@pytest.mark.parametrize("case", TEST_CASES, ids=[c["id"] for c in TEST_CASES])',
                "def test_generated(case, session, base_url):",
                '    """Single parametrized test for all generated cases (MVP)."""',
                "    url = f\"{base_url}{case['path']}\"",
                "    method = case['method']",
                "    payload = case.get('payload')",
                "",
                "    # If still on demo endpoint, negative/boundary are not meaningful -> skip (honest MVP)",
                "    if case['path'] == '/api/test' and case['type'] in ('negative', 'boundary'):",
                "        pytest.skip(\"MVP: demo endpoint /api/test doesn't support invalid/boundary inputs yet\")",
                "",
                "    if payload is None:",
                "        resp = session.request(method, url, timeout=10)",
                "    else:",
                "        resp = session.request(method, url, json=payload, timeout=10)",
                "",
                "    if case['type'] == 'boundary':",
                "        assert resp.status_code != 500, f\"Boundary must not crash server. got={resp.status_code}\"",
                "    else:",
                "        assert resp.status_code in case['expected_codes'], (",
                "            f\"Unexpected status {resp.status_code}. expected one of {case['expected_codes']}\"",
                "        )",
                "",
                "    # Demo endpoint contract",
                "    if case['path'] == '/api/test' and resp.headers.get('content-type','').startswith('application/json'):",
                "        body = resp.json()",
                "        assert body.get('status') == 'ok'",
                "",
            ]
        )

        return "\n".join(lines)