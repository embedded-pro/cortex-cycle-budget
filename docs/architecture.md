# Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         cli_single.py                           │
│                         cli_multi.py                            │
└────────────┬──────────────────────────────┬─────────────────────┘
             │                              │
             ▼                              ▼
┌─────────────────────┐         ┌──────────────────────┐
│   tooling.py        │         │   config.py          │
│   • run_objdump     │         │   • validate_config  │
│   • run_size        │         └──────────────────────┘
│   • log             │
└─────────────────────┘
             │
             ▼
┌─────────────────────┐         ┌──────────────────────────┐
│    parser.py        │ ◀────── │  timing_model.py         │
│  parse_disassembly  │         │  • BASE_TIMING           │
│                     │         │  • VARIANT_OVERRIDES     │
└─────────────────────┘         │  • EXCEPTION_OVERHEAD    │
             │                  │  • resolve_timing_table  │
             ▼                  │  • normalize_mnemonic    │
┌─────────────────────┐         │  • classify_instruction  │
│     paths.py        │ ◀────── │  • instruction_timing    │
│  • analyze_paths    │         └──────────────────────────┘
│  • classify_flow    │
└─────────────────────┘
             │
             ▼
┌─────────────────────┐
│    analysis.py      │
│  • analyze_stages   │
│  • path_breakdown   │
└─────────────────────┘
             │
             ▼
┌─────────────────────┐
│    reports.py       │
│  • generate_report  │
│  • cpu_budget_table │
│  • pr_comment       │
│  • annotated_disasm │
│  • json_metrics     │
└─────────────────────┘
```

## Module responsibilities

| Module              | Responsibility                                                                |
| ------------------- | ----------------------------------------------------------------------------- |
| `models.py`         | Dataclasses (`Instruction`, `Function`, `PathStage`) and exceptions.          |
| `timing_model.py`   | Per-variant timing tables and mnemonic classification.                        |
| `tooling.py`        | Thin wrappers around `arm-none-eabi-objdump` / `size` and stderr logging.     |
| `parser.py`         | Convert raw objdump text → typed `Function` list with cycle estimates.        |
| `config.py`         | Pure JSON-config validation; raises `ConfigError` with aggregated messages.   |
| `paths.py`          | Control-flow graph per function; worst and best path, direct callees included. |
| `analysis.py`       | Pick each stage's roots and charge their paths to the stages that name them.  |
| `reports.py`        | Pure rendering: stages + config → Markdown / JSON / annotated disasm.         |
| `cli_single.py`     | Single-mode CLI orchestration.                                                |
| `cli_multi.py`      | Multi-mode CLI orchestration; combined PR comment / step summary.            |

## Data flow

1. **CLI** parses arguments, loads & validates the JSON config.
2. **tooling** invokes `objdump -d -C` (or reads `--disasm-file`).
3. **parser** turns disassembly text into `list[Function]`; each instruction
   is classified and assigned `(min, max)` cycles via `get_timing()` using
   the variant-specific table from `resolve_timing_table(cortex)`.
4. **analysis** processes each stage:
   - **pattern stages** match functions by regex; **paths** costs the worst
     path of each, and every function on it is charged to the stage that
     names it (see [path-analysis.md](path-analysis.md)).
   - **architectural stages** (`exception_entry`/`exception_exit`) charge the
     per-variant overhead from `EXCEPTION_OVERHEAD[cortex]`.
5. **reports** render the final outputs from the `PathStage` list.

## Design principles

- **Pure functions over classes.** Every module's public surface is a small
  set of free functions operating on plain dataclasses.
- **No global state.** All variant-specific behavior flows through explicit
  `timing` / `cortex` parameters.
- **Backwards compatibility.** Top-level constants (`TIMING`, `EXCEPTION_OVERHEAD`)
  default to the M4 baseline so existing scripts keep working.
- **Stdlib only at runtime.** No external runtime dependencies; `dev` extras
  add `pytest`, `ruff`, `mypy`.
- **Aggregated error reporting.** `validate_config()` collects every problem
  before raising, so users see all issues in one go.
