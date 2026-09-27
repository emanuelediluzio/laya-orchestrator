from pathlib import Path
from laya_orchestrator.core.plan import Plan, Step, StepStatus
from laya_orchestrator.executors.shell_executor import ShellExecutor
from laya_orchestrator.executors.code_engine import CodeEngine


def test_plan_loading_and_formatting(tmp_path: Path):
    plan_file = tmp_path / "test_plan.yaml"
    plan_file.write_text("""
title: "Test Plan"
description: "Verify plan loading"
target_directory: "."
steps:
  - id: "step-1"
    title: "Step 1 Title"
    description: "Do something"
    files_to_modify: ["hello.py"]
    acceptance_criteria: ["Criterion 1"]
""", encoding="utf-8")

    plan = Plan.from_file(plan_file)
    assert plan.title == "Test Plan"
    assert len(plan.steps) == 1
    assert plan.current_step.id == "step-1"

    state_text = plan.format_state_for_laya()
    assert "PROJECT PLAN: Test Plan" in state_text
    assert "ACTIVE STEP: [step-1] Step 1 Title" in state_text


def test_shell_executor():
    executor = ShellExecutor()
    res = executor.execute("echo", {"command": "echo 'laya_test_ok'"})
    assert res.success is True
    assert "laya_test_ok" in res.output


def test_code_engine_scaffold(tmp_path: Path):
    engine = CodeEngine(target_directory=str(tmp_path))
    step = Step(
        id="calc-step",
        title="Calculator",
        description="Implement calc",
        files_to_modify=["calculator.py"],
        acceptance_criteria=["sum function"],
    )
    res = engine.execute("implement_code", {"step": step})
    assert res.success is True
    assert (tmp_path / "calculator.py").exists()
    content = (tmp_path / "calculator.py").read_text()
    assert "execute_calc_step" in content
