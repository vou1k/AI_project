"""
Debugger Agent - анализирует результаты тестов, различает баги приложения и ошибки тестов.
Добавлена статистика покрытия и метрики.
"""

from typing import Dict, Any, List
from app.core.models import TestSuiteResult, GeneratedCode, TestCase, DebugInfo

class TestDebugger:
    def analyze(self, results: TestSuiteResult, code: GeneratedCode,
                test_cases: List[TestCase]) -> DebugInfo:
        debug_info = DebugInfo()
        debug_info.failed_tests = []
        debug_info.root_causes = {}
        debug_info.suggestions = {}
        debug_info.is_app_bug = {}
        debug_info.fixed_code = None

        # Статистика по ошибкам тестов
        app_bug_count = 0
        test_bug_count = 0

        for res in results.results:
            if res.status != 'passed':
                failed = {
                    'test_id': res.test_id,
                    'error': res.error_message or "Unknown error",
                    'traceback': res.traceback or ""
                }
                debug_info.failed_tests.append(failed)

                cause = self._find_root_cause(res)
                debug_info.root_causes[res.test_id] = cause

                is_bug = self._is_application_bug(res)
                debug_info.is_app_bug[res.test_id] = is_bug
                if is_bug:
                    app_bug_count += 1
                else:
                    test_bug_count += 1

                debug_info.suggestions[res.test_id] = self._generate_fix_suggestions(
                    res, cause, is_bug
                )

        # Добавляем метрики покрытия и качества
        debug_info.quality_metrics = {
            "total_tests": results.total,
            "passed": results.passed,
            "failed": len(debug_info.failed_tests),
            "app_bugs": app_bug_count,
            "test_errors": test_bug_count,
            "coverage_estimate": code.coverage_estimate  # из coder.py
        }

        return debug_info

    # (остальные методы _find_root_cause, _is_application_bug, _generate_fix_suggestions)
    # они остаются без изменений – можно скопировать из предыдущей версии