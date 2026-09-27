from typing import Optional, Callable, Dict, Any, List
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from laya_orchestrator.core.plan import Plan, Step, StepStatus
from laya_orchestrator.core.decision_engine import LayaDecisionEngine, LayaDecision
from laya_orchestrator.executors.shell_executor import ShellExecutor
from laya_orchestrator.executors.code_engine import CodeEngine


class OrchestrationTrace(dict):
    """Execution step log used for telemetry and Laya RLCD fine-tuning datasets."""
    pass


class LayaOrchestrator:
    """The hybrid orchestrator coupling Laya System 1 fast decisions with System 2 execution."""

    def __init__(
        self,
        plan: Plan,
        target_directory: Optional[str] = None,
        max_cycles: int = 20,
        confidence_threshold: float = 0.50,
        on_step_callback: Optional[Callable[[LayaDecision, Step], None]] = None,
    ):
        self.plan = plan
        self.target_dir = Path(target_directory or plan.target_directory).resolve()
        self.max_cycles = max_cycles
        self.confidence_threshold = confidence_threshold
        self.on_step_callback = on_step_callback

        self.console = Console()
        self.decision_engine = LayaDecisionEngine()
        self.shell_executor = ShellExecutor(working_directory=str(self.target_dir))
        self.code_engine = CodeEngine(target_directory=str(self.target_dir))
        self.traces: List[Dict[str, Any]] = []

    def run(self) -> bool:
        """Executes the autonomous loop until the plan is completed or max cycles reached."""
        self.console.print(Panel(f"[bold cyan]Starting Laya Autonomous Orchestrator[/bold cyan]\nPlan: {self.plan.title} ({len(self.plan.steps)} steps)"))

        cycle = 0
        while cycle < self.max_cycles and not self.plan.is_completed:
            cycle += 1
            curr_step = self.plan.current_step
            if not curr_step:
                self.console.print("[green]No active step remaining. Plan is complete![/green]")
                self.plan.is_completed = True
                break

            # 1. State serialization
            state_text = self.plan.format_state_for_laya()

            # 2. Laya System 1 Fast Decision (~33ms)
            decision = self.decision_engine.evaluate_state(state_text)
            curr_step.verification_probability = decision.step_verified_prob

            # Display decision info in Rich
            self._display_decision(cycle, curr_step, decision)

            # Record trace for fine-tuning dataset
            self.traces.append({
                "cycle": cycle,
                "step_id": curr_step.id,
                "state_text": state_text,
                "decision": decision.model_dump(),
            })

            if self.on_step_callback:
                self.on_step_callback(decision, curr_step)

            # 3. Action routing
            action = decision.action

            # Safeguard / Calibration check: If confidence is low and severity high, handle carefully
            if decision.action_confidence < self.confidence_threshold:
                self.console.print(f"[yellow]⚠️ Laya confidence ({decision.action_confidence:.2f}) below threshold ({self.confidence_threshold:.2f}). Proceeding with caution.[/yellow]")

            if action == "advance_step":
                self.console.print(f"[bold green]✔ Advancing to next step...[/bold green]")
                has_next = self.plan.advance()
                if not has_next:
                    self.console.print("[bold green]🎉 All steps completed successfully![/bold green]")
                    return True

            elif action == "complete_plan":
                if not all(s.status == StepStatus.COMPLETED for s in self.plan.steps):
                    self.console.print("[yellow]⚠️ Laya suggested complete_plan, but pending steps remain. Proceeding to implement active step.[/yellow]")
                    action = "implement_code"
                else:
                    self.plan.is_completed = True
                    self.console.print("[bold green]🎉 All steps verified! Plan successfully completed![/bold green]")
                    return True

            if action in ["implement_code", "fix_bug"]:
                self.console.print(f"[blue]⚡ System 2 executing: {action} on {curr_step.files_to_modify}...[/blue]")
                exec_res = self.code_engine.execute(action, {"step": curr_step, "plan": self.plan})
                curr_step.output_log = exec_res.output
                if not exec_res.success:
                    curr_step.error_traceback = exec_res.error
                else:
                    curr_step.error_traceback = None
                    self.console.print(f"[dim]{exec_res.output}[/dim]")
                    # Immediately run step verification
                    if curr_step.verification_command:
                        self.console.print(f"[magenta]🧪 Running verification command: {curr_step.verification_command}[/magenta]")
                        res = self.shell_executor.execute("verify", {"command": curr_step.verification_command})
                        curr_step.output_log = res.output
                        if res.success:
                            self.console.print(f"[green]✔ Verification PASSED![/green]")
                            curr_step.status = StepStatus.COMPLETED
                            self.plan.advance()
                        else:
                            self.console.print(f"[red]✖ Verification FAILED (exit code {res.metadata.get('returncode')})[/red]")
                            curr_step.error_traceback = res.error or res.output
                            curr_step.status = StepStatus.FAILED

            elif action == "run_verification":
                if not curr_step.verification_command:
                    self.console.print("[dim]No verification command for this step; treating as verified.[/dim]")
                    curr_step.status = StepStatus.COMPLETED
                    self.plan.advance()
                    continue

                self.console.print(f"[magenta]🧪 Running verification command: {curr_step.verification_command}[/magenta]")
                res = self.shell_executor.execute("verify", {"command": curr_step.verification_command})
                curr_step.output_log = res.output
                if res.success:
                    self.console.print(f"[green]✔ Verification PASSED![/green]")
                    curr_step.error_traceback = None
                    curr_step.status = StepStatus.COMPLETED
                    self.plan.advance()
                else:
                    self.console.print(f"[red]✖ Verification FAILED with exit code {res.metadata.get('returncode')}[/red]")
                    curr_step.error_traceback = res.error or res.output
                    curr_step.status = StepStatus.FAILED

            elif action == "ask_user":
                self.console.print("[bold yellow]❓ Laya decided to pause and ask user for clarification.[/bold yellow]")
                return False

            else:
                self.console.print(f"[red]Unknown action returned by Laya: {action}[/red]")

        return self.plan.is_completed

    def _display_decision(self, cycle: int, step: Step, decision: LayaDecision):
        table = Table(title=f"Cycle {cycle} | Active: [{step.id}] {step.title}", show_header=True, header_style="bold magenta")
        table.add_column("Laya Decision", style="cyan")
        table.add_column("Confidence", justify="right", style="green")
        table.add_column("Step Verified (noul)", justify="right", style="yellow")
        table.add_column("Severity", justify="right", style="red")

        table.add_row(
            decision.action,
            f"{decision.action_confidence:.2%}",
            f"{decision.step_verified_prob:.2%}",
            f"{decision.severity_score:.2f}",
        )
        self.console.print(table)
