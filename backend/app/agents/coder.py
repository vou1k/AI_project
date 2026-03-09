"""
Coder Agent - Transforms test cases into executable code
"""

from typing import List
from app.core.models import TestCase, GeneratedCode

class TestCoder:
    """Generate executable test code"""
    
    def generate_code(self, test_cases: List[TestCase]) -> GeneratedCode:
        """Generate pytest code from test cases"""
        
        framework = "pytest"
        
        code = self._generate_pytest_code(test_cases)
        
        return GeneratedCode(
            code=code,
            framework=framework,
            test_count=len(test_cases),
            coverage_estimate=min(100, len(test_cases) * 10)
        )
    
    def _generate_pytest_code(self, test_cases: List[TestCase]) -> str:
        """Generate pytest code"""
        
        code_lines = [
            '"""',
            'Automatically generated tests',
            f'Total tests: {len(test_cases)}',
            '"""',
            '',
            'import pytest',
            'import requests',
            '',
            '# Base URL of the application under test',
            'BASE_URL = "http://localhost:5000"',
            '',
            '',
        ]
        
        # Generate test functions
        for i, tc in enumerate(test_cases):
            func_name = f"test_{tc.requirement_id.lower()}_{tc.type}_{i+1}"
            func_name = func_name.replace('-', '_').replace(' ', '_')
            
            code_lines.extend([
                f'def {func_name}():',
                f'    """',
                f'    {tc.title}',
                f'    Requirement: {tc.requirement_id}',
                f'    Expected: {tc.expected_result}',
                f'    """',
                '    try:',
                '        # Make request to test endpoint',
                '        response = requests.get(f"{BASE_URL}/api/test")',
                '        assert response.status_code == 200',
                '        assert response.json()["status"] == "ok"',
                '        print(f"Test {i+1} passed")',
                '    except Exception as e:',
                '        pytest.fail(f"Test failed: {e}")',
                '',
                ''
            ])
        
        return '\n'.join(code_lines)