from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import yaml
import json
from pathlib import Path


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"
    COMPLETED = "completed"


class Step(BaseModel):
    id: str
    title: str
    description: str
    files_to_modify: List[str] = Field(default_factory=list)
    verification_command: Optional[str] = None  # e.g. "pytest tests/test_auth.py"
    acceptance_criteria: List[str] = Field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    error_traceback: Optional[str] = None
    output_log: Optional[str] = None
    verification_probability: Optional[float] = None


class Plan(BaseModel):
    title: str
    description: str
    target_directory: str = "."
    steps: List[Step]
    current_step_index: int = 0
    is_completed: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def current_step(self) -> Optional[Step]:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance(self) -> bool:
        """Advance to next step if possible. Returns True if advanced, False if finished."""
        if self.current_step:
            self.current_step.status = StepStatus.COMPLETED
        self.current_step_index += 1
        if self.current_step_index >= len(self.steps):
            self.is_completed = True
            return False
        self.steps[self.current_step_index].status = StepStatus.IN_PROGRESS
        return True

    def format_state_for_laya(self) -> str:
        """Serializes current execution state into clean context for Laya System 1."""
        curr = self.current_step
        completed_steps = [s.title for s in self.steps if s.status == StepStatus.COMPLETED]
        remaining_steps = [s.title for s in self.steps if s.status == StepStatus.PENDING]
        
        state_parts = [
            f"PROJECT PLAN: {self.title}",
            f"GOAL: {self.description}",
            f"COMPLETED STEPS ({len(completed_steps)}/{len(self.steps)}): {', '.join(completed_steps) if completed_steps else 'None'}",
        ]
        
        if curr:
            state_parts.append(f"ACTIVE STEP: [{curr.id}] {curr.title}")
            state_parts.append(f"STEP STATUS: {curr.status.value.upper()}")
            state_parts.append(f"STEP DETAILS: {curr.description}")
            if curr.files_to_modify:
                files_status = []
                for f in curr.files_to_modify:
                    exists = (Path(self.target_directory) / f).exists()
                    files_status.append(f"{f} ({'EXISTS' if exists else 'NOT CREATED YET'})")
                state_parts.append(f"TARGET FILES: {', '.join(files_status)}")
            if curr.acceptance_criteria:
                state_parts.append(f"CRITERIA: {'; '.join(curr.acceptance_criteria)}")
            if curr.error_traceback:
                state_parts.append(f"LATEST FAILURE / ERROR LOG:\n{curr.error_traceback.strip()}")
            elif curr.output_log:
                state_parts.append(f"LATEST VERIFICATION OUTPUT:\n{curr.output_log.strip()[:1000]}")
        else:
            state_parts.append("ALL STEPS PROCESSED.")

        return "\n".join(state_parts)

    @classmethod
    def from_file(cls, filepath: str | Path) -> "Plan":
        path = Path(filepath)
        content = path.read_text(encoding="utf-8")
        if path.suffix in [".yaml", ".yml"]:
            data = yaml.safe_load(content)
        elif path.suffix == ".json":
            data = json.loads(content)
        elif path.suffix == ".md":
            data = cls._parse_markdown_plan(content)
        else:
            raise ValueError(f"Unsupported plan format: {path.suffix}")
        return cls(**data)

    @classmethod
    def _parse_markdown_plan(cls, md: str) -> Dict[str, Any]:
        """Simple parser to extract steps from markdown checklist."""
        lines = md.split("\n")
        title = "Implementation Plan"
        description = "Parsed from Markdown"
        steps = []
        step_counter = 1

        for line in lines:
            line = line.strip()
            if line.startswith("# "):
                title = line[2:].strip()
            elif line.startswith("- [ ]") or line.startswith("* [ ]") or line.startswith("- [x]") or line.startswith("* [x]"):
                is_done = "[x]" in line
                text = line[5:].strip()
                steps.append({
                    "id": f"step_{step_counter}",
                    "title": text,
                    "description": text,
                    "status": "completed" if is_done else "pending"
                })
                step_counter += 1

        if not steps:
            steps.append({
                "id": "step_1",
                "title": "Execute markdown specifications",
                "description": md[:500],
                "status": "pending"
            })

        return {
            "title": title,
            "description": description,
            "steps": steps
        }
