import json
from pathlib import Path
from typing import List, Dict, Any


class DevDecisionDatasetGenerator:
    """Generates and exports calibrated decision datasets for fine-tuning Laya on software workflows."""

    @staticmethod
    def create_synthetic_dev_dataset() -> List[Dict[str, Any]]:
        """Creates a rich initial dataset of software development states and calibrated target actions."""
        samples = [
            # Sample 1: Fresh step needs implementation
            {
                "state": "PLAN: Add login endpoint\nACTIVE STEP: Write POST /api/login in auth.py\nSTATUS: pending\nFILES: auth.py",
                "question_type": "choice",
                "instructions": "Determine the immediate next action required for this software implementation plan.",
                "options": ["implement_code", "run_verification", "fix_bug", "advance_step", "complete_plan", "ask_user"],
                "target": "implement_code",
            },
            # Sample 2: Implementation ready, needs test run
            {
                "state": "PLAN: Add login endpoint\nACTIVE STEP: Write POST /api/login in auth.py\nSTATUS: in_progress\nCode written in auth.py, verification tests present in tests/test_login.py but not yet run.",
                "question_type": "choice",
                "instructions": "Determine the immediate next action required for this software implementation plan.",
                "options": ["implement_code", "run_verification", "fix_bug", "advance_step", "complete_plan", "ask_user"],
                "target": "run_verification",
            },
            # Sample 3: Test failure, needs bug fix
            {
                "state": "PLAN: Add login endpoint\nACTIVE STEP: Run verification\nLATEST FAILURE: FAILED tests/test_login.py - AssertionError: 401 != 200 invalid credentials password hashing mismatch.",
                "question_type": "choice",
                "instructions": "Determine the immediate next action required for this software implementation plan.",
                "options": ["implement_code", "run_verification", "fix_bug", "advance_step", "complete_plan", "ask_user"],
                "target": "fix_bug",
            },
            # Sample 4: All tests pass, step verified
            {
                "state": "PLAN: Add login endpoint\nACTIVE STEP: Run verification\nLATEST VERIFICATION OUTPUT: 5 passed in 0.42s. 100% test coverage achieved.",
                "question_type": "choice",
                "instructions": "Determine the immediate next action required for this software implementation plan.",
                "options": ["implement_code", "run_verification", "fix_bug", "advance_step", "complete_plan", "ask_user"],
                "target": "advance_step",
            },
            # Sample 5: Noul question on test failure
            {
                "state": "LATEST FAILURE: FAILED tests/test_login.py - AssertionError: 401 != 200",
                "question_type": "noul",
                "instructions": "Has the active step passed all acceptance criteria and tests successfully?",
                "target": 0.0,
            },
            # Sample 6: Noul question on test success
            {
                "state": "LATEST VERIFICATION OUTPUT: 12 passed in 1.1s. All acceptance criteria met.",
                "question_type": "noul",
                "instructions": "Has the active step passed all acceptance criteria and tests successfully?",
                "target": 1.0,
            },
            # Sample 7: Missing credentials or critical architectural block
            {
                "state": "PLAN: Deploy to AWS\nACTIVE STEP: Provision S3 bucket\nLATEST FAILURE: Missing AWS_ACCESS_KEY_ID in environment. User credentials required.",
                "question_type": "choice",
                "instructions": "Determine the immediate next action required for this software implementation plan.",
                "options": ["implement_code", "run_verification", "fix_bug", "advance_step", "complete_plan", "ask_user"],
                "target": "ask_user",
            },
            # Sample 8: Severity of missing credentials
            {
                "state": "LATEST FAILURE: Missing AWS_ACCESS_KEY_ID in environment. User credentials required.",
                "question_type": "score",
                "instructions": "Rate the severity of any ongoing error or risk in the execution state.",
                "target": 2.0,  # Blocker
            },
        ]
        return samples

    @classmethod
    def export_dataset(cls, output_path: str | Path, extra_traces: List[Dict[str, Any]] = None):
        data = cls.create_synthetic_dev_dataset()
        if extra_traces:
            for t in extra_traces:
                # Map recorded trace to sample
                data.append({
                    "state": t.get("state_text", ""),
                    "question_type": "choice",
                    "instructions": "Determine the immediate next action required for this software implementation plan.",
                    "target": t.get("decision", {}).get("action", "implement_code")
                })
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
        return len(data)
