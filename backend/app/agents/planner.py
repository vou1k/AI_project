"""
Planner Agent - Analyzes requirements and breaks them into testable units
"""

from typing import List, Dict, Any
from app.core.models import Requirement

class RequirementsPlanner:
    """Plan testing based on requirements"""
    
    def plan(self, requirements: List[Requirement]) -> List[Dict[str, Any]]:
        """Break requirements into testable units"""
        test_units = []
        
        for req in requirements:
            # Create test unit for each acceptance criterion
            for i, ac in enumerate(req.acceptance_criteria):
                unit = {
                    "requirement_id": req.id,
                    "unit_id": f"{req.id}_UNIT_{i+1}",
                    "description": ac,
                    "priority": req.priority,
                    "acceptance_criteria": [ac]
                }
                test_units.append(unit)
            
            # If no acceptance criteria, create unit from description
            if not req.acceptance_criteria:
                unit = {
                    "requirement_id": req.id,
                    "unit_id": f"{req.id}_UNIT_1",
                    "description": req.description[:100],
                    "priority": req.priority,
                    "acceptance_criteria": [req.description]
                }
                test_units.append(unit)
        
        return test_units