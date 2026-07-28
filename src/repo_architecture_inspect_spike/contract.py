"""Repository-owned case loading and semantic comparison.

This module intentionally has no Inspect dependency. It reads the source
repository's existing contract and returns framework-neutral values.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SELECTED_CASES = (
    "markdown-only-discovery-skill",
    "routed-python-review-pack",
)


@dataclass(frozen=True)
class Case:
    """One selected source case without an independent adapter schema."""

    name: str
    observed: dict[str, Any]
    expected: dict[str, Any]


@dataclass(frozen=True)
class Comparison:
    """Deterministic comparison of an agent result with the source contract."""

    correct: bool
    errors: tuple[str, ...]


def load_cases(source_repo: Path) -> list[Case]:
    """Load selected cases directly from the source repository manifest."""
    manifest = source_repo / "evals" / "cases" / "architecture-audit.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    fixtures = data.get("fixtures")
    if not isinstance(fixtures, list):
        raise TypeError(f"{manifest}: fixtures must be a list")

    by_name = {
        item["name"]: item
        for item in fixtures
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    missing = [name for name in SELECTED_CASES if name not in by_name]
    if missing:
        raise ValueError(f"{manifest}: selected cases missing: {missing}")

    return [
        Case(
            name=name,
            observed=dict(by_name[name]["observed"]),
            expected=dict(by_name[name]["expected"]),
        )
        for name in SELECTED_CASES
    ]


def prompt_for(case: Case) -> str:
    """Create the narrow JSON-output prompt for one source case."""
    required_recommendations = case.expected["required_recommendations"]
    return (
        "Apply the repo-architecture-skill methodology to the observed repository "
        "facts below. Return one JSON object with exactly these keys: archetype, "
        "boundaries, recommendations. Choose archetype using the methodology's "
        "canonical labels: markdown-only-skill, multi-skill-pack, tool-backed-skill, "
        "operational-skill, or distribution-monorepo. The "
        "boundaries object must contain exactly "
        "these keys: authoring_source, runtime_payload, install_artifact, and "
        "maintainer_infrastructure. The recommendations array must contain only "
        "recommendations supported by the supplied facts. Apply the methodology's "
        "distinction between deterministic pull-request checks and volatile external "
        "monitoring when the evidence calls for it. Preserve canonical evidence "
        "phrases instead of paraphrasing them. If evidence identifies a directory "
        "as the runtime input, report that directory rather than only its entrypoint "
        "file. Each required recommendation must contain one of these exact "
        "canonical phrases: "
        f"{json.dumps(required_recommendations, ensure_ascii=False)}. "
        "Return raw JSON without Markdown.\n\n"
        f"case_id: {case.name}\n"
        f"observed: {json.dumps(case.observed, sort_keys=True)}"
    )


def expected_target(case: Case) -> dict[str, Any]:
    """Return the framework-neutral target derived from the source manifest."""
    return {
        "archetype": case.expected["archetype"],
        "boundaries": case.expected["boundaries"],
        "required_recommendations": case.expected["required_recommendations"],
        "prohibited_recommendations": case.expected["prohibited_recommendations"],
    }


def compare_result(result: object, target: dict[str, Any]) -> Comparison:
    """Grade the declared semantics without requiring exact prose."""
    if not isinstance(result, dict):
        return Comparison(False, ("result must be a JSON object",))

    errors: list[str] = []
    if result.get("archetype") != target["archetype"]:
        errors.append("archetype mismatch")
    if result.get("boundaries") != target["boundaries"]:
        errors.append("boundary map mismatch")

    recommendations = result.get("recommendations")
    if not isinstance(recommendations, list) or not all(
        isinstance(item, str) for item in recommendations
    ):
        errors.append("recommendations must be a string list")
        recommendations = []

    normalized = "\n".join(recommendations).casefold()
    for required in target["required_recommendations"]:
        if required.casefold() not in normalized:
            errors.append(f"missing required recommendation: {required}")
    for prohibited in target["prohibited_recommendations"]:
        if prohibited.casefold() in normalized:
            errors.append(f"prohibited recommendation present: {prohibited}")

    return Comparison(not errors, tuple(errors))


def parse_completion(completion: str) -> object:
    """Parse JSON, tolerating one conventional Markdown code fence."""
    text = completion.strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    elif text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()
    return json.loads(text)
