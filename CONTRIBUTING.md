# Contributing to Laya Orchestrator

Thank you for your interest in contributing to **Laya Orchestrator**!

## Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-username/laya-orchestrator.git
   cd laya-orchestrator
   ```

2. Set up a virtual environment using `uv`:
   ```bash
   uv venv .venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

3. Run tests:
   ```bash
   pytest tests/
   ```

## Guidelines

- **Keep System 1 Fast**: Any routing or decision-making logic inside `core/decision_engine.py` should remain non-autoregressive and fast (~33ms).
- **Format Code**: Follow PEP 8 and use standard typing hints.
- **Calibrated Data**: When adding new synthetic datasets for fine-tuning, make sure probabilities and scores follow strictly proper scoring rules.
