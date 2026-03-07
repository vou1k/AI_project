"""
Debugger Agent - Analyzes test results and suggests fixes.

Optional LLM enhancement (GigaChat):
  - richer root-cause analysis and suggestions
  - chat after analysis
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from app.core.models import TestSuiteResult, GeneratedCode, TestCase, DebugInfo
from app.core.llm_client import LLMClient
from app.core.learning_store import LearningStore


class TestDebugger:
    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or LLMClient()
        self.learning = LearningStore()

    def analyze(self, results: TestSuiteResult, code: GeneratedCode, test_cases: List[TestCase]) -> DebugInfo:
        debug_info = DebugInfo()
        debug_info.failed_tests = []
        debug_info.root_causes = {}
        debug_info.suggestions = {}
        debug_info.is_app_bug = {}
        debug_info.fixed_code = None

        if not results or not getattr(results, "results", None):
            return debug_info

        all_passed = all(r.status == "passed" for r in results.results)
        if all_passed:
            debug_info.root_causes = {"info": "All tests passed successfully!"}
            debug_info.suggestions = {"info": ["No issues found. Great job!"]}
            return debug_info

        # Heuristics first
        for r in results.results:
            if r.status != "passed":
                debug_info.failed_tests.append(
                    {
                        "test_id": r.test_id or "unknown",
                        "error": r.error_message or "Unknown error",
                        "traceback": r.traceback or "",
                    }
                )

                cause = self._find_root_cause(r)
                debug_info.root_causes[r.test_id or "unknown"] = cause

                is_bug = self._is_application_bug(r)
                debug_info.is_app_bug[r.test_id or "unknown"] = is_bug

                debug_info.suggestions[r.test_id or "unknown"] = self._generate_fix_suggestions(r, cause, is_bug)

        # Optional LLM refine
        if self.llm.is_enabled():
            try:
                refined = self._llm_refine(results, code, debug_info)
                if refined and isinstance(refined, dict):
                    if isinstance(refined.get("root_causes"), dict):
                        debug_info.root_causes.update(refined.get("root_causes", {}))
                    if isinstance(refined.get("suggestions"), dict):
                        debug_info.suggestions.update(refined.get("suggestions", {}))
            except Exception:
                pass

        return debug_info

    def chat(self, chat_history: List[Dict[str, str]], *, context: Dict[str, Any]) -> str:
        if not self.llm.is_enabled():
            return (
                "GigaChat не настроен. Задайте GIGACHAT_CREDENTIALS (рекомендуется) "
                "или GIGACHAT_ACCESS_TOKEN и перезапустите backend."
            )

        system = (
            "Ты AI QA assistant. Помоги разобраться с падениями тестов и предложи исправления. "
            "Можно предлагать изменения тестов и (если уместно) поведения приложения."
        )

        learned = self.learning.load_last(limit=4)
        learned_block = "\n\n".join(
            [
                "Пример исправления #{}:\npytest_output=...\noriginal=...\ncorrected=...".format(i + 1)
                + "\npytest_output:\n"
                + (str(ex.get("pytest_output", ""))[:900])
                + "\noriginal_test_code:\n"
                + (str(ex.get("original_test_code", ""))[:900])
                + "\ncorrected_test_code:\n"
                + (str(ex.get("corrected_test_code", ""))[:900])
                for i, ex in enumerate(learned)
            ]
        )

        ctx = {
            "session": context.get("session_id"),
            "tests_count": context.get("tests_count"),
            "latest_pytest_output": (context.get("pytest_output", "") or "")[:4000],
            "debug_summary": context.get("debug_summary", {}),
        }

        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    f"Контекст (JSON):\n{ctx}"
                    + ("\n\nНакопленные примеры исправлений (few-shot):\n" + learned_block if learned_block else "")
                ),
            },
        ]
        messages.extend(chat_history[-10:])

        reply = self.llm.chat(messages, max_tokens=900)
        return (reply or "").strip()

    def generate_fixed_tests(
        self,
        *,
        instruction: str,
        pytest_output: str,
        original_test_code: str,
    ) -> str:
        """Ask LLM to produce a corrected pytest file.

        Returns full file content (not a diff) to keep UX dead simple.
        """

        if not self.llm.is_enabled():
            return (
                "GigaChat не настроен. Нужен GIGACHAT_CREDENTIALS (рекомендуется) или "
                "GIGACHAT_ACCESS_TOKEN, чтобы генерировать исправления кода."
            )

        learned = self.learning.load_last(limit=4)
        few_shot = []
        for ex in learned:
            few_shot.append(
                {
                    "pytest_output": str(ex.get("pytest_output", ""))[:1200],
                    "original": str(ex.get("original_test_code", ""))[:1200],
                    "corrected": str(ex.get("corrected_test_code", ""))[:1200],
                }
            )

        system = (
            "Ты Senior SDET. Твоя задача: по выводу pytest и исходному файлу тестов "
            "сгенерировать ИСПРАВЛЕННУЮ версию pytest файла. "
            "Если поведение приложения выглядит неправильным, добавь комментарии TODO "
            "с предложением изменений в приложении, но основной результат должен быть валидным pytest файлом."
        )

        user = (
            "Входные данные:\n"
            f"INSTRUCTION (от пользователя):\n{instruction}\n\n"
            f"PYTEST_OUTPUT:\n{(pytest_output or '')[:6000]}\n\n"
            f"ORIGINAL_TEST_FILE:\n{(original_test_code or '')[:6000]}\n\n"
            "Примеры исправлений (few-shot):\n"
            f"{few_shot}\n\n"
            "Верни ТОЛЬКО полный текст исправленного pytest файла. Без markdown, без пояснений."
        )

        fixed = self.llm.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=1600,
        )
        return (fixed or "").strip()

    def _find_root_cause(self, result) -> str:
        if not result or not result.error_message:
            return "No error message available"

        msg = (result.error_message or "").lower()

        if "connectionerror" in msg or "connection refused" in msg:
            return "Application is unavailable"
        if "timeout" in msg:
            return "Request timeout"
        if "keyerror" in msg or "attributeerror" in msg:
            return "Test error: accessing non-existent field"
        if "assertionerror" in msg:
            return "Expected and actual results don't match"

        return "Unknown error"

    def _is_application_bug(self, result) -> bool:
        if not result or not result.error_message:
            return False

        msg = result.error_message
        if "500" in msg:
            return True
        if "AssertionError" in msg and "200" in msg:
            return True
        return False

    def _generate_fix_suggestions(self, result, cause: str, is_bug: bool) -> List[str]:
        if is_bug:
            return [
                "Check application logs for errors",
                "Verify data is correctly saved in database",
                "Check error handling in application code",
            ]

        if "unavailable" in (cause or "").lower():
            return [
                "Check if demo application is running (python demo_app/app.py)",
                "Verify port 5000 is not in use",
            ]

        if "timeout" in (cause or "").lower():
            return [
                "Increase timeout in test",
                "Check application performance",
            ]

        return [
            "Review test case logic",
            "Check test data validity",
            "Verify environment configuration",
        ]

    def _llm_refine(
        self, results: TestSuiteResult, code: GeneratedCode, debug_info: DebugInfo
    ) -> Optional[Dict[str, Any]]:
        failed = debug_info.failed_tests[:10]
        system = "Ты Senior QA/SDET. По выводу pytest определи причины и предложи исправления. Верни только JSON."
        prompt = f"""Вход:
failed_tests={failed}
generated_code_snippet={code.code[:2500] if code and getattr(code,'code',None) else ''}

Верни STRICT JSON:
{{
  "root_causes": {{"<test_id>": "string"}},
  "suggestions": {{"<test_id>": ["string", "string"]}}
}}
"""
        raw = self.llm.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            max_tokens=900,
        )
        parsed = self.llm.extract_json(raw)
        return parsed if isinstance(parsed, dict) else None