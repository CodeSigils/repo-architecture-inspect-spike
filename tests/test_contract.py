from __future__ import annotations

import json
from pathlib import Path

import pytest

from repo_architecture_inspect_spike.contract import (
    SELECTED_CASES,
    compare_result,
    expected_target,
    load_cases,
    parse_completion,
)


@pytest.fixture
def source_repo(tmp_path: Path) -> Path:
    fixtures = []
    for index, name in enumerate(SELECTED_CASES):
        fixtures.append(
            {
                "name": name,
                "observed": {"independent_skills": index + 1},
                "expected": {
                    "archetype": f"type-{index}",
                    "boundaries": {
                        "authoring_source": "source",
                        "runtime_payload": "payload",
                        "install_artifact": "artifact",
                        "maintainer_infrastructure": "maintenance",
                    },
                    "required_recommendations": [f"required-{index}"],
                    "prohibited_recommendations": [f"prohibited-{index}"],
                },
            }
        )
    source_repo_path = tmp_path / "evals" / "cases"
    source_repo_path.mkdir(parents=True)
    (source_repo_path / "architecture-audit.json").write_text(
        json.dumps({"fixtures": fixtures}),
        encoding="utf-8",
    )
    return tmp_path


def test_loads_only_selected_source_cases(source_repo: Path) -> None:
    cases = load_cases(source_repo)
    assert [case.name for case in cases] == list(SELECTED_CASES)


def test_positive_and_negative_semantic_paths(source_repo: Path) -> None:
    case = load_cases(source_repo)[0]
    target = expected_target(case)
    passing = {
        "archetype": target["archetype"],
        "boundaries": target["boundaries"],
        "recommendations": [target["required_recommendations"][0]],
    }
    assert compare_result(passing, target).correct

    failing = dict(passing)
    failing["recommendations"] = [target["prohibited_recommendations"][0]]
    comparison = compare_result(failing, target)
    assert not comparison.correct
    assert any("missing required" in error for error in comparison.errors)
    assert any("prohibited" in error for error in comparison.errors)


def test_plain_json_only() -> None:
    assert parse_completion('{"ok": true}') == {"ok": True}
    with pytest.raises(json.JSONDecodeError):
        parse_completion('```json\n{"ok": true}\n```')
