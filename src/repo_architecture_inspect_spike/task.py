"""Inspect task translating the repository-owned architecture contract."""

from __future__ import annotations

import json
import os
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.scorer import Score, Target, accuracy, scorer
from inspect_ai.solver import TaskState
from inspect_swe import codex_cli

from repo_architecture_inspect_spike.contract import (
    compare_result,
    expected_target,
    load_cases,
    parse_completion,
    prompt_for,
)


def source_repository() -> Path:
    """Resolve the source repository without embedding a machine-local path."""
    configured = os.environ.get("REPO_ARCHITECTURE_SOURCE")
    source = Path(configured) if configured else Path.cwd().parent / "repo-architecture-skill"
    return source.resolve()


def dataset() -> MemoryDataset:
    """Translate selected source cases into Inspect samples."""
    samples = [
        Sample(
            id=case.name,
            input=prompt_for(case),
            target=json.dumps(expected_target(case), sort_keys=True),
            metadata={
                "source_manifest": "evals/cases/architecture-audit.json",
                "adapter_schema": "none",
            },
        )
        for case in load_cases(source_repository())
    ]
    return MemoryDataset(samples=samples, name="repo-architecture-thin-adapter")


@scorer(metrics=[accuracy()])
def architecture_contract():
    """Apply the repository-owned semantic comparison through Inspect."""

    async def score(state: TaskState, target: Target) -> Score:
        try:
            result = parse_completion(state.output.completion)
            expected = json.loads(target.text)
            comparison = compare_result(result, expected)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            return Score(value=0, answer=state.output.completion, explanation=str(exc))

        return Score(
            value=1 if comparison.correct else 0,
            answer=state.output.completion,
            explanation="; ".join(comparison.errors) or "repository contract satisfied",
        )

    return score


@task
def repo_architecture_audit() -> Task:
    """Run two existing cases through Codex CLI in an Inspect sandbox."""
    return Task(
        dataset=dataset(),
        solver=codex_cli(
            web_search="disabled",
            goals=False,
            version="auto",
        ),
        scorer=architecture_contract(),
        sandbox=("docker", "docker/Dockerfile"),
    )
