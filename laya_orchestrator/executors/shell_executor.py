import subprocess
import os
from pathlib import Path
from typing import Dict, Any
from laya_orchestrator.executors.base import BaseExecutor, ExecutionResult


class ShellExecutor(BaseExecutor):
    """Executes shell verification commands (pytest, python, bash, npm test, etc.)."""

    def __init__(self, working_directory: str = "."):
        self.working_directory = Path(working_directory).resolve()

    def execute(self, action: str, context: Dict[str, Any]) -> ExecutionResult:
        command = context.get("command")
        if not command:
            return ExecutionResult(
                success=False,
                action_taken=action,
                output="",
                error="No verification command specified in context."
            )

        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=str(self.working_directory),
                capture_output=True,
                text=True,
                timeout=60,
            )
            success = (res.returncode == 0)
            combined_output = (res.stdout + "\n" + res.stderr).strip()

            return ExecutionResult(
                success=success,
                action_taken=action,
                output=res.stdout,
                error=res.stderr if not success else None,
                metadata={"returncode": res.returncode, "combined": combined_output}
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                action_taken=action,
                output="",
                error="Command execution timed out after 60 seconds."
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                action_taken=action,
                output="",
                error=f"Subprocess error: {str(e)}"
            )
