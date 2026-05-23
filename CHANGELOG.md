# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0](https://github.com/embedded-pro/cortex-cycle-budget/compare/v0.1.0...v0.2.0) (2026-05-23)


### Features

* initial cortex-cycle-budget v0.1.0 ([6cf43b0](https://github.com/embedded-pro/cortex-cycle-budget/commit/6cf43b0ad236d76b5f0f3afd65b5205a8d53b53b))

## [Unreleased]

## [0.1.0] — Initial release

### Added
- Static cycle-count estimation for ARM Cortex-M binaries.
- Per-variant timing tables for **Cortex-M0, M4, M7, M33** sourced from ARM TRMs.
  - Layered design: `BASE_TIMING` + `VARIANT_OVERRIDES[variant]` →
    `resolve_timing_table(variant)`.
- Per-variant `EXCEPTION_OVERHEAD` for `exception_entry` / `exception_exit`
  stage types.
- `cortex-cycle-budget` CLI (single-mode) and `cortex-cycle-budget-multi`
  CLI (multi-config side-by-side analysis).
- Public Python API: `parse_disassembly`, `analyze_stages`, `walk_call_graph`,
  `generate_report`, `generate_pr_comment`, `generate_cpu_budget_table`,
  `generate_annotated_disasm`, `generate_json_metrics`, `validate_config`,
  `resolve_timing_table`.
- `--fail-over-max-cycles` CI gate (exit code 2 when budget is exceeded).
- Composite GitHub Action (`./action.yml`) with idempotent PR comment,
  step summary, and artifact upload.
- Reusable GitHub Actions workflow at
  `.github/workflows/cycle-analysis.yml`.
- 122 unit + integration tests covering parser, analysis, reports, config
  validation, CLI behavior, and end-to-end compilation for M4/M7/M33.
- Documentation set: usage, config schema (+ JSON schema), timing model,
  Cortex variants, architecture, troubleshooting.
- Four runnable examples: minimal M4, M7 FPU-heavy, M33 ISR with
  architectural overhead, and multi-mode (one ELF, two paths).

### Known limitations
- Cortex-M7 limited dual-issue is **not** modeled (`DUAL_ISSUE_MIN_SCALE`
  constant defined for future use).
- I-cache / D-cache, branch prediction, bus contention, and TrustZone
  transitions are **not** modeled.

[Unreleased]: https://github.com/your-org/cortex-cycle-budget/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/cortex-cycle-budget/releases/tag/v0.1.0
