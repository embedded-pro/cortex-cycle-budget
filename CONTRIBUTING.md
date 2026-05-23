# Contributing

Thanks for your interest in improving `cortex-cycle-budget`! This document
describes the development workflow.

## Prerequisites

- Python ≥ 3.11
- `arm-none-eabi-gcc`/`objdump`/`size` (for integration tests)

## One-time setup

```bash
git clone https://github.com/your-org/cortex-cycle-budget.git
cd cortex-cycle-budget
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Day-to-day workflow

```bash
# Lint
python -m ruff check src tests

# Type-check (strict)
python -m mypy src/cortex_cycle_budget

# Unit tests (fast, no toolchain)
python -m pytest tests/unit -v

# Integration tests (requires arm-none-eabi-gcc)
python -m pytest tests/integration -v

# Coverage
python -m pytest --cov --cov-report=term-missing
```

All four must be green before opening a PR.

## Adding a new instruction to the timing model

1. Add the entry to **`BASE_TIMING`** (or a `VARIANT_OVERRIDES` entry if it
   differs from the M4 baseline) in
   [`src/cortex_cycle_budget/timing_model.py`](../src/cortex_cycle_budget/timing_model.py).
2. Cite the ARM TRM section in a comment next to the entry.
3. Add a parametrized test in
   [`tests/unit/test_timing_model.py`](../tests/unit/test_timing_model.py).
4. If the instruction needs special classification, update
   `classify_instruction()` and add a corresponding test.

## Adding a new Cortex variant

1. Add the variant slug to `SUPPORTED_VARIANTS`.
2. Add per-variant deltas to `VARIANT_OVERRIDES`.
3. Add `EXCEPTION_OVERHEAD[variant]` with TRM-cited values.
4. Update `--cortex` choices in `action.yml` (validation step).
5. Update [`docs/cortex-variants.md`](cortex-variants.md) and
   [`docs/timing-model.md`](timing-model.md).
6. Add an example under `examples/cortex-<variant>/` with a small ELF.

## Coding style

- **Ruff** rules selected in `pyproject.toml` are enforced in CI.
- **Mypy strict** mode — fully typed public API.
- Public modules: pure functions, no global mutable state, all variant
  selection flows through explicit parameters.
- Tests use **pytest** (no unittest classes), Arrange-Act-Assert layout.

## Release process

1. Update `CHANGELOG.md` under a new version heading.
2. Bump `version` in `pyproject.toml` and `__version__` in
   `src/cortex_cycle_budget/__init__.py`.
3. Commit: `chore: release v0.X.Y`.
4. Tag: `git tag -a vX.Y.Z -m "vX.Y.Z"` and push.
5. The `release.yml` workflow builds, publishes to PyPI via OIDC trusted
   publishing, and creates the GitHub Release.

## Code of Conduct

Be kind. Be specific. Cite ARM TRM sections in cycle-model PRs.
