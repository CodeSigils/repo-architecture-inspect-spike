# Repository Instructions

This is an experimental compatibility spike, not project authority for
`repo-architecture-skill` or a reusable evaluation framework.

- Treat the source repository's case manifest and runtime payload as read-only
  authority.
- Keep case selection and semantic comparison in `contract.py`.
- Keep Inspect-specific translation in `task.py`.
- Do not copy or independently evolve source cases.
- Keep live model execution optional; normal validation must remain model-free.
- Record unsupported requirements rather than hiding them in adapter logic.

Run the checks in `README.md` before claiming compatibility.
