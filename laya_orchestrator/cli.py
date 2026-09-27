import typer
from pathlib import Path
from typing import Optional
from rich.console import Console

from laya_orchestrator.core.plan import Plan
from laya_orchestrator.core.orchestrator import LayaOrchestrator

app = typer.Typer(help="Laya Autonomous Plan-to-Code Orchestrator CLI")
console = Console()


@app.command()
def run(
    plan_file: str = typer.Argument(..., help="Path to plan file (.yaml, .json, or .md)"),
    target_dir: Optional[str] = typer.Option(None, "--dir", "-d", help="Target working directory"),
    max_cycles: int = typer.Option(20, "--max-cycles", "-c", help="Maximum execution cycles"),
    threshold: float = typer.Option(0.50, "--threshold", "-t", help="Confidence threshold"),
):
    """Run autonomous execution loop for a plan file using Laya."""
    path = Path(plan_file)
    if not path.exists():
        console.print(f"[bold red]Plan file not found: {plan_file}[/bold red]")
        raise typer.Exit(code=1)

    plan = Plan.from_file(path)
    orchestrator = LayaOrchestrator(
        plan=plan,
        target_directory=target_dir,
        max_cycles=max_cycles,
        confidence_threshold=threshold,
    )
    success = orchestrator.run()
    if success:
        console.print("[bold green]Orchestration succeeded![/bold green]")
    else:
        console.print("[bold yellow]Orchestration stopped or reached max cycles.[/bold yellow]")


if __name__ == "__main__":
    app()
