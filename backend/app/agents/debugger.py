"""
Debugger Agent - Analyzes test results and suggests fixes
"""

from typing import Dict, Any, List
from app.core.models import TestSuiteResult, GeneratedCode, TestCase, DebugInfo

class TestDebugger:
    """Analyze test results and debug"""
    
    def analyze(self, results: TestSuiteResult, code: GeneratedCode, 
                test_cases: List[TestCase]) -> DebugInfo:
        """Analyze test results"""
        
        debug_info = DebugInfo()
        
        # Initialize all fields
        debug_info.failed_tests = []
        debug_info.root_causes = {}
        debug_info.suggestions = {}
        debug_info.is_app_bug = {}
        debug_info.fixed_code = None
        
        # If no results, return empty debug info
        if not results or not results.results:
            return debug_info
        
        # If all tests passed, return success message
        all_passed = all(r.status == 'passed' for r in results.results)
        if all_passed:
            debug_info.failed_tests = []
            debug_info.root_causes = {"info": "All tests passed successfully!"}
            debug_info.suggestions = {"info": ["No issues found. Great job!"]}
            return debug_info
        
        # Process failed tests
        for result in results.results:
            if result.status != 'passed':
                # Collect failed test info
                failed_info = {
                    'test_id': result.test_id or "unknown",
                    'error': result.error_message or "Unknown error",
                    'traceback': result.traceback or ""
                }
                debug_info.failed_tests.append(failed_info)
                
                # Find root cause
                cause = self._find_root_cause(result)
                debug_info.root_causes[result.test_id or "unknown"] = cause
                
                # Determine if it's app bug or test error
                is_bug = self._is_application_bug(result)
                debug_info.is_app_bug[result.test_id or "unknown"] = is_bug
                
                # Generate suggestions
                debug_info.suggestions[result.test_id or "unknown"] = self._generate_fix_suggestions(
                    result, cause, is_bug
                )
        
        return debug_info
    
    def _find_root_cause(self, result) -> str:
        """Find root cause of failure"""
        if not result or not result.error_message:
            return "No error message available"
            
        error_msg = result.error_message.lower()
        
        if "connectionerror" in error_msg or "connection refused" in error_msg:
            return "Application is unavailable"
        elif "assertionerror" in error_msg:
            if "200" in error_msg:
                return "Expected success response but got error"
            elif "400" in error_msg or "401" in error_msg:
                return "Expected auth error but got different code"
            else:
                return "Expected and actual results don't match"
        elif "timeout" in error_msg:
            return "Request timeout"
        elif "keyerror" in error_msg or "attributeerror" in error_msg:
            return "Test error: accessing non-existent field"
        else:
            return "Unknown error"
    
    def _is_application_bug(self, result) -> bool:
        """Determine if failure is application bug"""
        if not result or not result.error_message:
            return False
            
        error_msg = result.error_message
        
        # Positive test failing - likely app bug
        if "200" in error_msg and "AssertionError" in error_msg:
            return True
        if "500" in error_msg:
            return True
        
        return False
    
    def _generate_fix_suggestions(self, result, cause: str, is_bug: bool) -> List[str]:
        """Generate fix suggestions"""
        suggestions = []
        
        if is_bug:
            suggestions.extend([
                "Check application logs for errors",
                "Verify data is correctly saved in database",
                "Check error handling in application code"
            ])
        else:
            if "AssertionError" in cause:
                suggestions.extend([
                    "Verify expected result in test case",
                    "Check if test data matches actual data",
                    "Update test to match current behavior"
                ])
            elif "Connection" in cause:
                suggestions.extend([
                    "Check if demo application is running (python demo_app/app.py)",
                    "Verify port 5000 is not in use",
                    "Check CORS settings"
                ])
            elif "Timeout" in cause:
                suggestions.extend([
                    "Increase timeout in test",
                    "Check application performance",
                    "Add retry mechanism"
                ])
            else:
                suggestions.extend([
                    "Review test case logic",
                    "Check test data validity",
                    "Verify environment configuration"
                ])
        
        return suggestions