"""
Generator Agent - Creates test cases from test units.

Improvements:
- Deduplication of generated tests (LLM and fallback)
- Cap tests per requirement
- Smarter fallback templates based on simple keyword heuristics
- Skip "empty" placeholder requirements like id="REQ" (to avoid duplicates)
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional, Tuple

from app.core.models import TestCase
from app.core.llm_client import LLMClient


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


def _guess_area(text: str) -> str:
    t = _norm(text)
    if any(k in t for k in ["логин", "вход", "авторизац", "signin", "login"]):
        return "auth"
    if any(k in t for k in ["регистрац", "signup", "register"]):
        return "register"
    if any(k in t for k in ["профиль", "profile", "аккаунт", "account"]):
        return "profile"
    if any(k in t for k in ["поиск", "search"]):
        return "search"
    if any(k in t for k in ["заказ", "order", "покуп", "checkout", "корзин", "cart"]):
        return "orders"
    return "generic"


class TestCaseGenerator:
    """Generate test cases"""

    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or LLMClient()

    def generate(self, test_units: List[Dict[str, Any]]) -> List[TestCase]:
        # 1) Filter out "empty" placeholder units to avoid duplicates like REQ + REQ-1
        filtered_units: List[Dict[str, Any]] = []
        for unit in test_units:
            rid = str(unit.get("id", "")).strip()
            title = str(unit.get("title", "")).strip()
            desc = str(unit.get("description", "")).strip()

            # If it's the default placeholder and has no real content, skip it
            if rid in ("", "REQ") and not title and not desc:
                continue

            filtered_units.append(unit)

        # 2) generate
        if self.llm.is_enabled():
            try:
                tests = self._generate_with_llm(filtered_units)
            except Exception:
                tests = self._generate_rule_based(filtered_units)
        else:
            tests = self._generate_rule_based(filtered_units)

        # 3) dedupe + cap
        tests = self._dedupe(tests)
        tests = self._cap_per_requirement(tests, limit_per_req=6)

        # 4) ensure each requirement has at least 1 pos/neg/bound (but never for placeholder REQ)
        tests = self._ensure_min_types_per_req(tests, filtered_units)

        return tests

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

    def _cap_per_requirement(self, tests: List[TestCase], limit_per_req: int = 6) -> List[TestCase]:
        counts: Dict[str, int] = {}
        out: List[TestCase] = []
        for tc in tests:
            rid = str(getattr(tc, "requirement_id", "REQ")).strip()
            if rid in ("", "REQ"):
                # don't let placeholder explode
                continue
            counts.setdefault(rid, 0)
            if counts[rid] >= limit_per_req:
                continue
            counts[rid] += 1
            out.append(tc)
        return out

    def _ensure_min_types_per_req(self, tests: List[TestCase], test_units: List[Dict[str, Any]]) -> List[TestCase]:
        by_req: Dict[str, Dict[str, int]] = {}
        for tc in tests:
            rid = str(tc.requirement_id).strip()
            if rid in ("", "REQ"):
                continue
            by_req.setdefault(rid, {})
            by_req[rid][tc.type] = by_req[rid].get(tc.type, 0) + 1

        out = list(tests)

        for unit in test_units:
            rid = str(unit.get("id", "")).strip()
            if rid in ("", "REQ"):
                continue  # never generate “minimum set” for placeholder

            title = str(unit.get("title", "Feature"))
            desc = str(unit.get("description", ""))
            area = _guess_area(f"{title}\n{desc}")

            present = by_req.get(rid, {})
            needed = [t for t in ["positive", "negative", "boundary"] if present.get(t, 0) == 0]
            if not needed:
                continue

            for t in needed:
                out.append(self._fallback_single(rid, title, desc, area, t))

        return self._dedupe(out)

    def _generate_with_llm(self, test_units: List[Dict[str, Any]]) -> List[TestCase]:
        test_cases: List[TestCase] = []

        for unit in test_units:
            requirement_id = str(unit.get("id", "REQ")).strip()
            title = unit.get("title", "Requirement")
            description = unit.get("description", "")
            acceptance = unit.get("acceptance_criteria", []) or unit.get("acceptance", []) or []

            # Skip placeholder
            if requirement_id in ("", "REQ") and not (str(title).strip() or str(description).strip()):
                continue

            system = (
                "Ты опытный QA инженер. "
                "Сгенерируй тест-кейсы для API/бэкенда по требованию. "
                "Сделай: positive, negative, boundary. "
                "Верни только JSON без markdown."
            )

            user = f"""Сгенерируй тест-кейсы для требования.

Requirement ID: {requirement_id}
Title: {title}
Description: {description}
Acceptance criteria:
{acceptance}

Верни STRICT JSON по схеме:
{{
  "tests": [
    {{
      "title": "string",
      "type": "positive|negative|boundary",
      "steps": ["шаг 1", "шаг 2"],
      "expected_result": "string",
      "preconditions": ["optional"],
      "data": {{}}
    }}
  ]
}}

Правила:
- Минимум 1 positive, 1 negative, 1 boundary.
- Не повторяй одинаковые тесты.
- Шаги короткие и конкретные.
- Только JSON.
"""

            raw = self.llm.chat(
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                max_tokens=1400,
            )

            parsed = self.llm.extract_json(raw) or {}
            tests = parsed.get("tests", []) if isinstance(parsed, dict) else []
            if not isinstance(tests, list):
                tests = []

            for i, t in enumerate(tests, start=1):
                if not isinstance(t, dict):
                    continue
                test_cases.append(
                    TestCase(
                        id=f"{requirement_id}-LLM-{i}",
                        requirement_id=str(requirement_id),
                        title=str(t.get("title") or f"{title} ({t.get('type', 'test')})"),
                        type=str(t.get("type") or "positive"),
                        steps=list(t.get("steps") or []),
                        expected_result=str(t.get("expected_result") or ""),
                        preconditions=list(t.get("preconditions") or []),
                        data=dict(t.get("data") or {}),
                    )
                )

            if not tests:
                test_cases.extend(self._fallback_for_unit(unit))

        return test_cases

    def _generate_rule_based(self, test_units: List[Dict[str, Any]]) -> List[TestCase]:
        test_cases: List[TestCase] = []
        for unit in test_units:
            test_cases.extend(self._fallback_for_unit(unit))
        return test_cases

    def _fallback_for_unit(self, unit: Dict[str, Any]) -> List[TestCase]:
        req_id = str(unit.get("id", "REQ-1")).strip()
        title = str(unit.get("title", "Feature"))
        desc = str(unit.get("description", ""))

        # If placeholder unit slipped through, skip
        if req_id in ("", "REQ") and not (title.strip() or desc.strip()):
            return []

        area = _guess_area(f"{title}\n{desc}")

        return [
            self._fallback_single(req_id, title, desc, area, "positive"),
            self._fallback_single(req_id, title, desc, area, "negative"),
            self._fallback_single(req_id, title, desc, area, "boundary"),
        ]

    def _fallback_single(self, req_id: str, title: str, desc: str, area: str, ttype: str) -> TestCase:
        if area == "auth":
            pos_steps = ["Отправить запрос логина с корректными данными", "Проверить успешный ответ и наличие токена"]
            neg_steps = ["Отправить запрос логина с неверным паролем", "Проверить код ошибки (401/400)"]
            bnd_steps = ["Отправить логин с пустым/очень длинным паролем", "Проверить, что система не падает (нет 500)"]
        elif area == "register":
            pos_steps = ["Отправить регистрацию с валидными данными", "Проверить успешный ответ и созданного пользователя"]
            neg_steps = ["Отправить регистрацию без обязательного поля", "Проверить 4xx и сообщение об ошибке"]
            bnd_steps = ["Отправить регистрацию с паролем на границе (7/8 символов)", "Проверить корректную обработку"]
        elif area == "profile":
            pos_steps = ["Отправить запрос профиля с валидным токеном", "Проверить структуру профиля в ответе"]
            neg_steps = ["Отправить запрос профиля без/с неверным токеном", "Проверить 401/403"]
            bnd_steps = ["Запросить профиль с редкими/неполными данными", "Проверить отсутствие 500 и корректную схему"]
        else:
            pos_steps = [f"Выполнить действие для '{title}' с валидными данными", "Проверить успешный ответ"]
            neg_steps = [f"Выполнить действие для '{title}' с невалидными данными", "Проверить 4xx ответ"]
            bnd_steps = [f"Выполнить действие для '{title}' с граничными значениями", "Проверить отсутствие 500"]

        if ttype == "positive":
            return TestCase(
                id=f"{req_id}-P",
                requirement_id=req_id,
                title=f"Positive: {title}",
                type="positive",
                steps=pos_steps,
                expected_result="HTTP 200/201 (успех)",
            )
        if ttype == "negative":
            return TestCase(
                id=f"{req_id}-N",
                requirement_id=req_id,
                title=f"Negative: {title}",
                type="negative",
                steps=neg_steps,
                expected_result="HTTP 4xx (ошибка валидации/доступа)",
            )
        return TestCase(
            id=f"{req_id}-B",
            requirement_id=req_id,
            title=f"Boundary: {title}",
            type="boundary",
            steps=bnd_steps,
            expected_result="Система корректно обрабатывает крайние значения (нет 500)",
        )