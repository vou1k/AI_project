"""
Validator Agent - Checks test correctness
"""

from typing import List
import ast
from app.core.models import TestCase, GeneratedCode

class ValidationResult:
    def __init__(self):
        self.is_valid = True
        self.issues = []
        self.suggestions = []

    def to_dict(self):
        return {"is_valid": self.is_valid, "issues": self.issues, "suggestions": self.suggestions}

class TestValidator:
    def validate(self, code: GeneratedCode, test_cases: List[TestCase]) -> ValidationResult:
        result = ValidationResult()
        try:
            ast.parse(code.code)
        except SyntaxError as e:
            result.is_valid = False
            result.issues.append(f"Syntax error: {e}")

        test_count_in_code = code.code.count('def test_')
        if test_count_in_code != len(test_cases):
            result.issues.append(f"Test count mismatch: in code {test_count_in_code}, expected {len(test_cases)}")

        for imp in ['pytest', 'requests']:
            if f'import {imp}' not in code.code:
                result.issues.append(f"Missing import {imp}")

        result.is_valid = len(result.issues) == 0
        result.suggestions = self._generate_suggestions(result.issues)
        return result

    def _generate_suggestions(self, issues: List[str]) -> List[str]:
        suggestions = []
        for issue in issues:
            if "syntax" in issue.lower():
                suggestions.append("Check brackets, quotes, indentation and parentheses.")
            elif "import" in issue.lower():
                suggestions.append("Add missing imports at the top of the file.")
            elif "count mismatch" in issue.lower():
                suggestions.append("Ensure each generated test case becomes a `def test_...` function.")
        return suggestions
