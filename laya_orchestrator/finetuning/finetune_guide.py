"""
Fine-tuning module for Laya on Software Engineering and Plan Orchestration.

Laya utilizes RLCD (Reinforcement Learning from Calibrated Decisions) with strictly proper
scoring rules (Brier loss / log-loss).
"""

from pathlib import Path
import json


def get_finetune_script_template() -> str:
    return '''# Fine-tuning Laya for Software Implementation Plans
# Can be run locally or on a free Kaggle / Colab T4 GPU.

import torch
from transformers import AutoTokenizer, AutoModel
import laya

print("Ready to fine-tune Laya on software development traces!")
# 1. Load base checkpoint: 'convaiinnovations/laya'
# 2. Train classification & scoring heads on dev_decisions.jsonl
# 3. Fit temperature calibration per question type
# 4. Save checkpoint to ./finetuned_laya_dev
'''


def generate_finetune_notebook(output_path: str = "finetune_laya_dev.ipynb"):
    """Creates a ready-to-run Jupyter notebook for Kaggle/Colab or local GPU."""
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Fine-tuning Laya on Software Implementation & Dev Decisions\n",
                    "This notebook fine-tunes `convaiinnovations/laya` so it becomes an expert controller for software plans and bug triage."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "!pip install -q laya torch transformers accelerate"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import laya\n",
                    "from laya import Router\n",
                    "router = Router()\n",
                    "print('Loaded base Laya model:', router)"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Load the exported dataset\n",
                    "import json\n",
                    "dataset = []\n",
                    "with open('dev_decisions.jsonl') as f:\n",
                    "    for line in f:\n",
                    "        dataset.append(json.loads(line))\n",
                    "print(f'Loaded {len(dataset)} decision training samples')"
                ]
            }
        ],
        "metadata": {
            "language_info": {"name": "python"}
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    Path(output_path).write_text(json.dumps(nb, indent=2), encoding="utf-8")
    return output_path
