"""
Data models for AI Test Platform
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

class Requirement:
    """Requirement model"""
    def __init__(self, id: str, title: str, description: str, 
                 acceptance_criteria: List[str] = None, 
                 dependencies: List[str] = None,
                 priority: str = "medium"):
        self.id = id
        self.title = title
        self.description = description
        self.acceptance_criteria = acceptance_criteria or []
        self.dependencies = dependencies or []
        self.priority = priority
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "dependencies": self.dependencies,
            "priority": self.priority
        }

class TestCase:
    """Test case model"""
    def __init__(self, id: str, requirement_id: str, title: str, 
                 type: str, steps: List[str], expected_result: str,
                 preconditions: List[str] = None, data: Dict = None):
        self.id = id
        self.requirement_id = requirement_id
        self.title = title
        self.type = type  # positive, negative, boundary
        self.steps = steps
        self.expected_result = expected_result
        self.preconditions = preconditions or []
        self.data = data or {}
    
    def to_dict(self):
        return {
            "id": self.id,
            "requirement_id": self.requirement_id,
            "title": self.title,
            "type": self.type,
            "steps": self.steps,
            "expected_result": self.expected_result,
            "preconditions": self.preconditions,
            "data": self.data
        }

class GeneratedCode:
    """Generated code model"""
    def __init__(self, code: str, framework: str = "pytest", 
                 test_count: int = 0, coverage_estimate: float = 0.0):
        self.code = code
        self.framework = framework
        self.test_count = test_count
        self.coverage_estimate = coverage_estimate
    
    def to_dict(self):
        return {
            "code": self.code,
            "framework": self.framework,
            "test_count": self.test_count,
            "coverage_estimate": self.coverage_estimate
        }

class TestResult:
    """Individual test result"""
    def __init__(self, test_id: str, status: str, duration: float = 0.0,
                 error_message: str = None, traceback: str = None,
                 logs: List[str] = None):
        self.test_id = test_id
        self.status = status  # passed, failed, error
        self.duration = duration
        self.error_message = error_message
        self.traceback = traceback
        self.logs = logs or []
    
    def to_dict(self):
        return {
            "test_id": self.test_id,
            "status": self.status,
            "duration": self.duration,
            "error_message": self.error_message,
            "traceback": self.traceback,
            "logs": self.logs
        }

class TestSuiteResult:
    """Test suite results"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.duration = 0.0
        self.results = []
        # Raw runner output (stdout+stderr) to support post-mortem analysis/chat
        self.raw_output: str = ""
        # Exit code from the test runner (0=success)
        self.exit_code: int | None = None
        self.timestamp = datetime.now()
    
    def to_dict(self):
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "duration": self.duration,
            "results": [r.to_dict() for r in self.results],
            "raw_output": self.raw_output,
            "exit_code": self.exit_code,
            "timestamp": self.timestamp.isoformat()
        }

class DebugInfo:
    """Debug information"""
    def __init__(self):
        self.failed_tests = []
        self.root_causes = {}
        self.suggestions = {}
        self.is_app_bug = {}
        self.fixed_code = None
    
    def to_dict(self):
        return {
            "failed_tests": self.failed_tests,
            "root_causes": self.root_causes,
            "suggestions": self.suggestions,
            "is_app_bug": self.is_app_bug,
            "fixed_code": self.fixed_code
        }

class TestSession:
    """Test session"""
    def __init__(self, id: str):
        self.id = id
        self.requirements = []
        self.test_cases = []
        self.generated_code = None
        self.test_results = None
        self.debug_info = None
        self.chat_history = []  # list of {role, content}
        # Convenience fields for "fix -> learn" flow
        self.last_test_file_path: str | None = None
        self.last_fixed_test_code: str | None = None
        self.created_at = datetime.now()
    
    def to_dict(self):
        return {
            "id": self.id,
            "requirements_count": len(self.requirements),
            "test_cases_count": len(self.test_cases),
            "has_results": self.test_results is not None,
            "has_debug": self.debug_info is not None,
            "chat_messages": len(self.chat_history),
            "created_at": self.created_at.isoformat()
        }