"""
Requirements parser from text files
"""

import re
from typing import List
from app.core.models import Requirement

class RequirementsParser:
    """Parse requirements documents"""
    
    def parse(self, file_path: str) -> List[Requirement]:
        """Parse file"""
        try:
            if file_path.endswith('.txt'):
                return self._parse_txt(file_path)
            else:
                # Return sample data for demo
                return self._get_sample_requirements()
        except Exception as e:
            print(f"Error parsing file: {e}")
            return self._get_sample_requirements()
    
    def _parse_txt(self, file_path: str) -> List[Requirement]:
        """Parse text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return self._extract_requirements(text)
        except Exception as e:
            print(f"Error reading file: {e}")
            return self._get_sample_requirements()
    
    def _extract_requirements(self, text: str) -> List[Requirement]:
        """Extract requirements from text"""
        requirements = []
        lines = text.split('\n')
        current_req = None
        current_desc = []
        current_ac = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for new requirement
            if (line.startswith('Requirement') or 
                line.startswith('REQ') or 
                line.startswith('Требование')):
                
                if current_req:
                    req = Requirement(
                        id=current_req,
                        title=current_desc[0] if current_desc else "No title",
                        description='\n'.join(current_desc),
                        acceptance_criteria=current_ac
                    )
                    requirements.append(req)
                
                parts = line.split(':', 1)
                current_req = parts[0].strip()
                current_desc = [parts[1].strip()] if len(parts) > 1 else []
                current_ac = []
            
            # Check for acceptance criteria
            elif line.startswith('-') or line.startswith('•') or 'AC' in line:
                clean_line = line.lstrip('-• ').strip()
                if clean_line:
                    current_ac.append(clean_line)
            else:
                if current_req:
                    current_desc.append(line)
        
        # Add last requirement
        if current_req:
            req = Requirement(
                id=current_req,
                title=current_desc[0] if current_desc else "No title",
                description='\n'.join(current_desc),
                acceptance_criteria=current_ac
            )
            requirements.append(req)
        
        # If no requirements found, return sample
        if not requirements:
            return self._get_sample_requirements()
        
        return requirements
    
    def _get_sample_requirements(self) -> List[Requirement]:
        """Sample requirements for demo"""
        return [
            Requirement(
                id="REQ-001",
                title="User Authentication",
                description="System should allow users to authenticate with username and password.",
                acceptance_criteria=[
                    "AC1: Successful authentication with valid credentials returns token",
                    "AC2: Authentication with invalid password returns 401 error",
                    "AC3: Authentication with non-existent user returns 404 error"
                ]
            ),
            Requirement(
                id="REQ-002",
                title="Item Management",
                description="Users can view list of items.",
                acceptance_criteria=[
                    "AC4: GET /api/items returns list of items",
                    "AC5: GET /api/items/<id> returns item by ID"
                ]
            )
        ]