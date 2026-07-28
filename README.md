# Repo Architecture Inspect Spike

This is a bounded compatibility spike for a thin Inspect adapter around
`repo-architecture-skill`. It is not a replacement runner, framework package,
or source of project behavior.

## Baseline Finding

The current `repo-architecture-skill/main` contains 11 declarative cases in
`evals/cases/architecture-audit.json`, deterministic manifest validation, and
named-runtime compatibility reports. It does not contain the native live runner
and final-state semantic grader assumed by the original comparison proposal.

This spike therefore tests:

1. whether two existing cases can be consumed without copying them;
2. whether repository-owned semantic comparison remains independent of Inspect;
3. whether a thin Inspect `Sample` and scorer translation imports successfully;
4. whether Inspect SWE can provide optional Codex execution and evidence.

It cannot yet establish native-versus-Inspect execution equivalence or
final-filesystem equivalence.

## Ownership Boundary

| Concern | Owner |
|---|---|
| Cases and expected behavior | Source repository |
| Case selection and semantic comparison | Framework-neutral `contract.py` |
| Samples, scorer wrapper, sandbox, Codex execution, and logs | Inspect adapter |
| Adoption decision | Human review after recorded results |

The adapter reads the source manifest at runtime. It has no copied case file and
no independent result schema.

## Setup

The project pins the versions researched on 2026-07-28:

- `inspect-ai==0.3.248`
- `inspect-swe==0.2.65`

```bash
uv sync --locked
```

## Model-Free Validation

```bash
uv run --locked pytest
uv run --locked ruff check .
REPO_ARCHITECTURE_SOURCE=../repo-architecture-skill \
  uv run --locked python -c \
  "from repo_architecture_inspect_spike.task import dataset; print(len(dataset()))"
```

These checks validate translation and positive/negative scorer semantics
without making a model call.

## Podman Sandbox Compatibility

This host provides rootless Podman rather than Docker. Inspect AI 0.3.248's
built-in sandbox provider invokes the literal command `docker compose`; it
does not expose a container-engine setting. Podman 5.7.0 and
`podman-compose` 1.2.0 are installed, so this spike includes a project-local
`bin/docker` compatibility shim that delegates that Docker-compatible CLI
surface to Podman.

The shim is intentionally not installed globally. Scope it to an Inspect run
by prepending this project's `bin` directory to `PATH`:

```bash
REPO_ARCHITECTURE_SOURCE=../repo-architecture-skill \
  PATH="$PWD/bin:$PATH" \
  uv run --locked inspect eval \
  src/repo_architecture_inspect_spike/task.py@repo_architecture_audit \
  --model openai/gpt-5
```

The live run remains deliberate and non-CI. It requires an authenticated
Inspect model provider and may download the Codex CLI into the sandbox when no
cached version is available. Successful image/Compose validation establishes
container compatibility only; it does not establish evaluation equivalence.

## Decision Record

| Requirement | Initial status |
|---|---|
| Source cases remain authoritative | Supported by direct manifest loading |
| Adapter contains no copied cases | Supported |
| Semantic comparison runs without Inspect | Supported by unit tests |
| Inspect sample/scorer mapping | Supported: real API import, task discovery, and two-sample construction pass |
| Rootless Podman image/Compose compatibility | Supported: Compose config resolution and image build pass |
| Authenticated Codex execution equivalence | Pending live run |
| Configuration isolation | Pending live run |
| Raw Codex diagnostic fidelity | Pending log inspection |
| Environment-limitation mapping | Pending log inspection |
| Final filesystem-state scoring | Not testable with current declarative cases |
| Less orchestration than a native runner | Not comparable; native runner absent |

The local shim addresses only Inspect's hard-coded executable name. The spike
does not fall back to an unisolated live run because that would change the
contract being evaluated.

## Evidence

- [Inspect AI tasks](https://inspect.aisi.org.uk/tasks.html)
- [Inspect AI datasets](https://inspect.aisi.org.uk/datasets.html)
- [Inspect AI scoring](https://inspect.aisi.org.uk/multiple-scorers.html)
- [Inspect AI sandboxing](https://inspect.aisi.org.uk/sandboxing.html)
- [Inspect AI custom sandbox extensions](https://inspect.aisi.org.uk/extensions-sandboxes.html)
- [Podman Compose](https://docs.podman.io/en/latest/markdown/podman-compose.1.html)
- [Inspect SWE Codex CLI](https://meridianlabs-ai.github.io/inspect_swe/codex_cli.html)
- Source repository: `../repo-architecture-skill`
