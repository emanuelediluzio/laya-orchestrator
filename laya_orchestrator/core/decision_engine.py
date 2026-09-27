from typing import Dict, Any, Optional
import laya
from laya import Router
from pydantic import BaseModel


class LayaDecision(BaseModel):
    action: str
    action_confidence: float
    action_probabilities: Dict[str, float]
    step_verified_prob: float
    severity_score: float
    model_used: str
    raw_response: Dict[str, Any]


class LayaDecisionEngine:
    """System 1 fast calibrated decision engine powered by convaiinnovations/laya."""

    def __init__(self, model_checkpoint: Optional[str] = None):
        self.router = Router()
        self.model_checkpoint = model_checkpoint

    def evaluate_state(self, state_text: str) -> LayaDecision:
        """Evaluates state against typed decision questions in a single forward pass (~33ms)."""
        questions = {
            "next_action": {
                "type": "choice",
                "instructions": "Determine the immediate next action required for this software implementation plan.",
                "criteria": {
                    "implement_code": "Write new source files or implement required logic for the step",
                    "run_verification": "Execute tests, linters, or verification commands to check behavior",
                    "fix_bug": "Fix an existing error, exception, or test failure",
                    "advance_step": "The active step has passed verification; move forward to the next step",
                    "complete_plan": "All steps are completed and verified; finalize execution",
                    "ask_user": "Unresolvable ambiguity or missing external credentials; escalate to user",
                },
            },
            "step_verified": {
                "type": "noul",
                "instructions": "Has the active step passed all acceptance criteria and tests successfully?",
            },
            "severity": {
                "type": "score",
                "instructions": "Rate the severity of any ongoing error or risk in the execution state.",
                "criteria": [
                    "no issue or minor cosmetic warning",
                    "recoverable bug or test failure",
                    "critical blocker or architectural incompatibility",
                ],
            },
        }

        raw = self.router.predict(state_text, questions)
        answers = raw.get("answers", {})

        action_data = answers.get("next_action", {})
        action = action_data.get("choice", "implement_code")
        action_prob = action_data.get("answer_confidence", 0.0)
        action_probs = action_data.get("probabilities", {})

        step_verified_data = answers.get("step_verified", {})
        step_verified_prob = step_verified_data.get("noul", 0.0)

        severity_data = answers.get("severity", {})
        severity_score = severity_data.get("score", 0.0)

        model_name = raw.get("routing", {}).get("model", "english")

        return LayaDecision(
            action=action,
            action_confidence=action_prob,
            action_probabilities=action_probs,
            step_verified_prob=step_verified_prob,
            severity_score=severity_score,
            model_used=model_name,
            raw_response=raw,
        )
