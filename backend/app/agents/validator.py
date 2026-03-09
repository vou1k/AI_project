"""
Validator Agent - Checks test correctness
"""

from typing import List, Optional
from app.core.models import TestCase, GeneratedCode

class ValidationResult:
    """Validation result"""
    def __init__(self):
        self.is_valid = True
        self.issues = []
        self.suggestions = []
    
    def to_dict(self):
        return {
            "is_valid": self.is_valid,
            "issues": self.issues,
            "suggestions": self.suggestions
        }

class TestValidator:
    """Validate generated tests"""
    
    def validate(self, code: GeneratedCode, test_cases: List[TestCase]) -> ValidationResult:
        """Validate generated code"""
        
        result = ValidationResult()
        
        # Check Python syntax
        try:
            compile(code.code, '<string>', 'exec')
        except SyntaxError as e:
            result.is_valid = False
            result.issues.append(f"Syntax error: {e}")
        
        # Check test count
        test_count_in_code = code.code.count('def test_')
        if test_count_in_code != len(test_cases):
            result.issues.append(
                f"Test count mismatch: in code {test_count_in_code}, expected {len(test_cases)}"
            )
        
        # Check fixtures
        if 'def client' not in code.code:
            result.issues.append("Missing 'client' fixture")
        
        # Check imports
        required_imports = ['pytest', 'requests']
        for imp in required_imports:
            if f'import {imp}' not in code.code:
                result.issues.append(f"Missing import {imp}")
        
        result.is_valid = len(result.issues) == 0
        result.suggestions = self._generate_suggestions(result.issues)
        
        return result
    
    def _generate_suggestions(self, issues: List[str]) -> List[str]:
        """Generate fix suggestions"""
        suggestions = []
        
        for issue in issues:
            if "syntax" in issue.lower():
                suggestions.append("Check brackets and quotes")
            elif "fixture" in issue.lower():
                suggestions.append("Add fixture for creating client")
            elif "import" in issue.lower():
                suggestions.append("Add required imports at the beginning of file")
        
        return suggestions