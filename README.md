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

## Sandbox and bounded live runs

Inspect AI 0.3.248 requires Docker Engine 24.0.6+ and Docker Compose 2.21.0+
semantics. This spike has been verified with rootless Docker Engine 27.5.1 and
the Compose plugin 5.3.1. Podman 5.7.0 can build the image directly, but
`podman-compose` 1.2.0 does not satisfy Inspect's Docker Compose v2 contract.

Live runs are non-CI and bounded per sample to 120 seconds, 20,000 tokens, two
model retries, and a 60-second model request timeout.

OpenAI example:

```bash
REPO_ARCHITECTURE_SOURCE=../repo-architecture-skill \
  uv run --locked inspect eval \
  src/repo_architecture_inspect_spike/task.py@repo_architecture_audit \
  --model openai/gpt-5
```

OpenCode Zen Big Pickle example:

```bash
export OPENCODE_ZEN_API_KEY=...
export OPENCODE_ZEN_BASE_URL=https://opencode.ai/zen/v1
REPO_ARCHITECTURE_SOURCE=../repo-architecture-skill \
  uv run --locked inspect eval \
  src/repo_architecture_inspect_spike/task.py@repo_architecture_audit \
  --model openai-api/opencode-zen/big-pickle
```

### Live-run finding (2026-07-28)

Live execution exposed and corrected three adapter defects:

- the OpenAI provider requires the separately installed `openai` SDK;
- relative `REPO_ARCHITECTURE_SOURCE` paths must be resolved independently of
  the task loader's changed working directory.
- the sandbox Dockerfile must also be resolved independently of that directory.

The initial two-sample OpenAI run was interrupted after 5 minutes 17 seconds:
zero samples completed and the log recorded 42 connection retries. Resource
limits were added before further execution.

A one-sample Big Pickle run then completed in 25 seconds with zero retries and
9,933 tokens, but scored zero. That score is not valid comparative evidence:
the prompt provides only observed summary facts, while the grader requires an
exact boundary map and a specific monitoring recommendation that are not
derivable from those facts. The second sample was not run. The next experiment
must repair fixture sufficiency without embedding the expected answer. The
adapter now preflights concrete fixture entrypoints and refuses a model run
when the source checkout does not contain them.

## Decision Record

| Requirement | Initial status |
|---|---|
| Source cases remain authoritative | Supported by direct manifest loading |
| Adapter contains no copied cases | Supported |
| Semantic comparison runs without Inspect | Supported by unit tests |
| Inspect sample/scorer mapping | API import passes; task construction is correctly blocked by incomplete source evidence |
| Rootless Docker/Compose compatibility | Supported by image build and isolated live sample execution |
| OpenCode Zen Big Pickle transport | Supported by one bounded sample with zero retries |
| Authenticated execution equivalence | Not established; current prompt/grader contract is underdetermined |
| Fixture evidence completeness | Preflight supported; current source checkout reports missing selected entrypoints |
| Configuration isolation | Source and Dockerfile paths are loader-cwd independent |
| Raw diagnostic fidelity | Supported: retries, usage, timing, answer, and scorer explanation were preserved |
| Environment-limitation mapping | Supported for Podman incompatibility and provider connection failures |
| Final filesystem-state scoring | Not testable with current declarative cases |
| Less orchestration than a native runner | Not comparable; native runner absent |

The spike does not spoof Docker responses, rewrite unsupported Compose commands,
or fall back to an unisolated run.

## Evidence

- [Inspect AI tasks](https://inspect.aisi.org.uk/tasks.html)
- [Inspect AI datasets](https://inspect.aisi.org.uk/datasets.html)
- [Inspect AI scoring](https://inspect.aisi.org.uk/multiple-scorers.html)
- [Inspect AI sandboxing](https://inspect.aisi.org.uk/sandboxing.html)
- [Inspect AI custom sandbox extensions](https://inspect.aisi.org.uk/extensions-sandboxes.html)
- [Inspect AI model providers](https://inspect.aisi.org.uk/providers.html)
- [Podman Compose](https://docs.podman.io/en/latest/markdown/podman-compose.1.html)
- [OpenCode Zen](https://opencode.ai/docs/zen/)
- [Inspect SWE Codex CLI](https://meridianlabs-ai.github.io/inspect_swe/codex_cli.html)
- Source repository: `../repo-architecture-skill`
