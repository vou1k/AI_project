"""
Generator Agent - Creates test cases from test units
"""

from typing import List, Dict, Any
from app.core.models import TestCase

class TestCaseGenerator:
    """Generate test cases"""
    
    def generate(self, test_units: List[Dict[str, Any]]) -> List[TestCase]:
        """Generate test cases from test units"""
        test_cases = []
        
        for unit in test_units:
            # Generate positive tests
            positive = self._generate_positive_tests(unit)
            test_cases.extend(positive)
            
            # Generate negative tests
            negative = self._generate_negative_tests(unit)
            test_cases.extend(negative)
            
            # Generate boundary tests
            boundary = self._generate_boundary_tests(unit)
            test_cases.extend(boundary)
        
        return test_cases
    
    def _generate_positive_tests(self, unit: Dict[str, Any]) -> List[TestCase]:
        """Generate positive test cases"""
        tests = []
        
        for i, ac in enumerate(unit.get('acceptance_criteria', [])):
            test = TestCase(
                id=f"{unit['unit_id']}_POS_{i+1}",
                requirement_id=unit['requirement_id'],
                title=f"Positive test: {ac[:50]}...",
                type="positive",
                steps=[
                    "1. Prepare valid test data",
                    f"2. Execute action: {ac}",
                    "3. Verify expected result"
                ],
                expected_result=ac,
                preconditions=["System is available", "User is authenticated"],
                data={"valid": True}
            )
            tests.append(test)
        
        return tests
    
    def _generate_negative_tests(self, unit: Dict[str, Any]) -> List[TestCase]:
        """Generate negative test cases"""
        tests = []
        
        negative_scenarios = [
            "invalid data",
            "missing required fields",
            "incorrect format",
            "exceeding limits",
            "insufficient permissions"
        ]
        
        for i, scenario in enumerate(negative_scenarios[:2]):  # Take first 2 for MVP
            test = TestCase(
                id=f"{unit['unit_id']}_NEG_{i+1}",
                requirement_id=unit['requirement_id'],
                title=f"Negative test: {scenario}",
                type="negative",
                steps=[
                    f"1. Prepare {scenario}",
                    "2. Execute action",
                    "3. Verify error response"
                ],
                expected_result="System returns error message",
                preconditions=["System is available"],
                data={"valid": False, "scenario": scenario}
            )
            tests.append(test)
        
        return tests
    
    def _generate_boundary_tests(self, unit: Dict[str, Any]) -> List[TestCase]:
        """Generate boundary test cases"""
        tests = []
        
        boundary_values = ["minimum value", "maximum value", "empty value"]
        
        for i, value in enumerate(boundary_values):
            test = TestCase(
                id=f"{unit['unit_id']}_BND_{i+1}",
                requirement_id=unit['requirement_id'],
                title=f"Boundary test: {value}",
                type="boundary",
                steps=[
                    f"1. Set {value}",
                    "2. Execute action",
                    "3. Verify boundary handling"
                ],
                expected_result="System correctly handles boundary value",
                preconditions=["System is available"],
                data={"boundary": value}
            )
            tests.append(test)
        
        return tests