"""Requirements parser from text files (and raw text).

MVP:
  - .txt parsing (upload)
  - raw text parsing (textarea) via RequirementsParser.parse_text(...)
  - fallback sample requirements for demo
"""

from __future__ import annotations

from typing import List
from app.core.models import Requirement


class RequirementsParser:
    """Parse requirements documents"""

    def parse(self, file_path: str) -> List[Requirement]:
        """Parse a requirements file by path."""
        try:
            if file_path.endswith(".txt"):
                return self._parse_txt(file_path)
            # Other formats are handled elsewhere in the project (docx/pdf),
            # but for MVP we return sample data.
            return self._get_sample_requirements()
        except Exception as e:
            print(f"Error parsing file: {e}")
            return self._get_sample_requirements()

    def parse_text(self, text: str) -> List[Requirement]:
        """Parse requirements directly from a raw text string."""
        try:
            return self._extract_requirements(text or "")
        except Exception as e:
            print(f"Error parsing text: {e}")
            return self._get_sample_requirements()

    def _parse_txt(self, file_path: str) -> List[Requirement]:
        """Parse a .txt file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            return self._extract_requirements(text)
        except Exception as e:
            print(f"Error reading file: {e}")
            return self._get_sample_requirements()

    def _extract_requirements(self, text: str) -> List[Requirement]:
        """Extract requirements from a plain text document.

        Supported styles (mixed is OK):
          - 'Requirement: ...'
          - 'REQ-001: ...'
          - 'Требование: ...'
          - Enumerated list '1. ...', '2) ...'
        Acceptance criteria:
          - lines starting with '-' or '•'
          - lines containing 'AC' like 'AC1: ...'
        """
        requirements: List[Requirement] = []

        lines = (text or "").splitlines()
        current_id = None
        current_title = None
        current_desc: List[str] = []
        current_ac: List[str] = []
        counter = 1

        def flush():
            nonlocal current_id, current_title, current_desc, current_ac, counter
            if not current_id and not current_title and not current_desc and not current_ac:
                return
            rid = current_id or f"REQ-{counter:03d}"
            counter += 1
            title = current_title or (current_desc[0] if current_desc else "No title")
            desc = "\n".join(current_desc).strip() if current_desc else (title or "")
            requirements.append(
                Requirement(
                    id=rid,
                    title=title or "No title",
                    description=desc,
                    acceptance_criteria=current_ac,
                )
            )
            current_id = None
            current_title = None
            current_desc = []
            current_ac = []

        for raw in lines:
            line = (raw or "").strip()
            if not line:
                continue

            # New requirement patterns
            is_new = False
            if line.startswith(("Requirement", "REQ", "Требование")):
                is_new = True
            elif line[:2].isdigit() and (line[1] in [".", ")"]):
                is_new = True

            if is_new:
                # flush previous
                if current_id or current_title or current_desc or current_ac:
                    flush()

                # Extract id/title from "REQ-001: Title" or "Requirement: Title"
                if ":" in line:
                    left, right = line.split(":", 1)
                    left = left.strip()
                    right = right.strip()
                    if left.upper().startswith("REQ"):
                        current_id = left
                        current_title = right or None
                    else:
                        # "Requirement: X" / "Требование: X"
                        current_title = right or left
                        current_id = None
                else:
                    # "1. Title"
                    current_title = line.lstrip("0123456789. )").strip() or line
                    current_id = None
                if current_title:
                    current_desc.append(current_title)
                continue

            # Acceptance criteria lines
            if line.startswith(("-", "•")) or ("AC" in line and len(line) < 200):
                clean = line.lstrip("-• ").strip()
                if clean:
                    current_ac.append(clean)
                continue

            # Normal description
            current_desc.append(line)

        # last
        if current_id or current_title or current_desc or current_ac:
            flush()

        if not requirements:
            return self._get_sample_requirements()
        return requirements

    def _get_sample_requirements(self) -> List[Requirement]:
        """Sample requirements for demo."""
        return [
            Requirement(
                id="REQ-001",
                title="User Authentication",
                description="System should allow users to authenticate with username and password.",
                acceptance_criteria=[
                    "AC1: Successful authentication with valid credentials returns token",
                    "AC2: Authentication with invalid password returns 401 error",
                    "AC3: Authentication with non-existent user returns 404 error",
                ],
            ),
            Requirement(
                id="REQ-002",
                title="Item Management",
                description="Users can view list of items.",
                acceptance_criteria=[
                    "AC4: GET /api/items returns list of items",
                    "AC5: GET /api/items/<id> returns item by ID",
                ],
            ),
        ]
