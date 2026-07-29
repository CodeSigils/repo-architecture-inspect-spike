# Repo Architecture Inspect Spike

This is a bounded compatibility spike for a thin Inspect adapter around
`repo-architecture-skill`. It is not a replacement runner, framework package,
or source of project behavior.

## Baseline Finding

The current `repo-architecture-skill/main` contains 11 declarative cases in
`evals/cases/architecture-audit.json`, a shared
`evals/cases/architecture-duplicate-mirror.json` contract, deterministic
manifest validation, named-runtime compatibility reports, and a native Codex
runner with a semantic grader.

This spike therefore tests:

1. whether source-owned cases, including the shared equivalence case, can be
   consumed without copying them;
2. whether repository-owned semantic comparison remains independent of Inspect;
3. whether a thin Inspect `Sample` and scorer translation imports successfully;
4. whether Inspect SWE can provide optional Codex execution and evidence.

It cannot yet establish native-versus-Inspect execution equivalence because the
two runners do not share the same case set. It also cannot establish
final-filesystem equivalence.

## Ownership Boundary

| Concern | Owner |
|---|---|
| Cases and expected behavior | Source repository |
| Case selection and semantic comparison | Framework-neutral `contract.py` |
| Samples, scorer wrapper, sandbox, Codex execution, and logs | Inspect adapter |
| Adoption decision | Human review after recorded results |

The adapter reads the source manifest and shared equivalence case at runtime. It
has no copied case file and no independent result schema.

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

Live runs are non-CI and bounded per sample. The validated runs used:
`--token-limit 32000 --turn-limit 2 --max-retries 1 --time-limit 120`.
The initial 12,000 token limit was sufficient for `markdown-only-discovery-skill`
(10,272 tokens) but too tight for `routed-python-review-pack` (11,785 tokens).
The 20,000-token estimated budget was validated as safe for both cases after the
first case's prompt iteration.

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

Anthropic comparator:

```bash
export ANTHROPIC_API_KEY=...
REPO_ARCHITECTURE_SOURCE=../repo-architecture-skill \
  uv run --locked inspect eval \
  src/repo_architecture_inspect_spike/task.py@repo_architecture_audit \
  --model anthropic/claude-sonnet-4-0
```

The Anthropic path is intentionally a separate-provider comparator; it does
not establish that the models are equivalent. For a controlled first check,
run the same sample and limits against each model:

```bash
--sample-id markdown-only-discovery-skill --token-limit 12000 --turn-limit 2
```

Record model, provider, sample ID, limits, retries, tokens, score, and raw
answer before comparing results. Model availability and pricing are provider
configuration, not properties of this adapter.

The bounded Anthropic probe reached the provider successfully after installing
the required SDK version, but completed zero samples because the configured
Anthropic account reported insufficient credit. This is provider-account
evidence, not an adapter or scoring result.

### Validated Runs (2026-07-28)

| Case | Model | Score | Time | Tokens | Retries |
|------|-------|-------|------|--------|---------|
| `markdown-only-discovery-skill` | Big Pickle | 1.000 | 23.8s | 10,272 | 0 |
| `routed-python-review-pack` | Big Pickle | 1.000 | 36.0s | 11,785 | 0 |

Both cases pass the strict architecture contract scorer (archetype, boundary
values, required canonical phrases, string-typed recommendations). The first
case required three prompt iterations (phrase clarity, schema clarity, then
pass) before converging — the grader remained unchanged throughout.

### Provider Status

| Provider | Authentication | Result |
|----------|---------------|--------|
| Big Pickle (OpenCode Zen) | ✅ Verified | 2/2 cases at 1.000 |
| GPT-5 (OpenAI) | ❌ `OPENAI_API_KEY=not-needed` | HTTP 401, never authenticated |
| Anthropic Claude | ✅ Key valid | Zero samples — account credit insufficient |

### Adapter Defects Found and Fixed

Live execution during the initial setup exposed three adapter defects, all
corrected:

1. **OpenAI SDK dependency** — `openai` package was required separately from
   `inspect-ai`; not listed in project dependencies.
2. **Relative source path** — Inspect's task loader changes the working
   directory; `REPO_ARCHITECTURE_SOURCE` must be resolved from the project root.
3. **Dockerfile path** — Same loader-cwd issue; Dockerfile path also required
   root-relative resolution.

### Prompt Iteration

The strict grader stayed unchanged throughout. Three prompt clarity fixes were
required before the first case passed:

| Iteration | Model | Score | Reason |
|-----------|-------|-------|--------|
| Initial prompt | Big Pickle | 0.000 | Correct archetype/boundaries but paraphrased required phrase |
| Added exact required phrases | Big Pickle | 0.000 | Used correct phrase but returned object instead of string list |
| Clarified "string recommendations, no objects" | Big Pickle | 1.000 | Full contract satisfied |

Token budget: the `routed-python-review-pack` case required 11,785 tokens
vs 10,272 for `markdown-only-discovery-skill`, despite nearly identical input
payload sizes (489 vs 450 bytes). The model's iterative reasoning depth
varies by archetype complexity, not input size.

## Decision Record

| Requirement | Status | Evidence |
|---|---|---|
| Source cases remain authoritative | ✅ Supported | Read from source manifest at runtime |
| Adapter contains no copied cases | ✅ Confirmed | No case files in this repository |
| Semantic comparison runs without Inspect | ✅ Confirmed | Unit tests pass without Inspect |
| Inspect sample/scorer mapping | ✅ Confirmed | API import, task discovery, 3-sample construction |
| Rootless Docker/Compose compatibility | ✅ Confirmed | Docker 27.5.1, Compose 5.3.1 |
| Big Pickle Codex transport | ✅ Validated | 2/2 cases at 1.000, zero retries |
| Configuration isolation | ✅ Confirmed | Loader-cwd independent source and Dockerfile paths |
| Raw diagnostic fidelity | ✅ Confirmed | Retries, usage, timing, answer, scorer explanation in logs |
| Environment-limitation mapping | ✅ Confirmed | Credential/credit blockers documented |
| Model-free scorer tests | ✅ Confirmed | 5 pytest tests pass |
| Less orchestration than native | ✅ Confirmed | No case-manifest copy, no runner dependency |
| GPT-5 authenticated execution | ❌ Blocked | OPENAI_API_KEY placeholder |
| Anthropic authenticated execution | ❌ Blocked | Account credit insufficient |
| Execution equivalence with native | ❌ Not established | Different case sets |
| Final filesystem-state scoring | ❌ Not testable | Declarative cases only |

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
