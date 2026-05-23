# Usage

## Command-line reference

### `cortex-cycle-budget` (single-mode)

Analyze a single critical path through one ELF.

```text
cortex-cycle-budget <config.json> --elf <path> [options]
```

| Flag                        | Required | Default                  | Description                                          |
| --------------------------- | :------: | ------------------------ | ---------------------------------------------------- |
| `config`                    |    ✅    | —                        | Positional. Path to the JSON config.                 |
| `--elf PATH`                |    ✅    | —                        | ELF binary to analyze.                               |
| `--target STR`              |    ✅    | —                        | Free-form target label (e.g. `nucleo-h743zi`).       |
| `--build-config STR`        |    ✅    | —                        | Build label (`Release`, `Debug`, …).                 |
| `--clock-mhz INT`           |    ✅    | —                        | Positive integer; CPU clock in MHz.                  |
| `--cortex {m0,m4,m7,m33}`   |    ⬜    | `m4`                     | Cortex-M variant for the timing model.               |
| `--output-dir PATH`         |    ⬜    | `.`                      | Directory for generated reports.                     |
| `--objdump PATH`            |    ⬜    | `arm-none-eabi-objdump`  | Override objdump binary.                             |
| `--size-tool PATH`          |    ⬜    | `arm-none-eabi-size`     | Override size binary.                                |
| `--disasm-file PATH`        |    ⬜    | —                        | Use a pre-generated disassembly instead of objdump.  |
| `--no-strict`               |    ⬜    | strict                   | Do not fail when a stage matches no functions.       |
| `--fail-over-max-cycles N`  |    ⬜    | —                        | Exit code 2 when `estimated_max_cycles > N`.         |

Exit codes:

| Code | Meaning                                                |
| :--: | ------------------------------------------------------ |
| `0`  | Success                                                |
| `1`  | Configuration error, missing file, parse failure       |
| `2`  | `--fail-over-max-cycles` threshold exceeded            |

### `cortex-cycle-budget-multi` (multi-mode)

Analyze multiple critical paths against potentially the same or different ELFs.

```text
cortex-cycle-budget-multi <analyses.json> --target ... --build-config ... --clock-mhz ... [options]
```

`analyses.json` is a JSON array; each entry must contain:

```json
{
  "label": "Mode A",
  "elf_path": "path/to/a.elf",
  "config_path": "path/to/a-cycle-analysis.json",
  "output_dir": "out/mode_a"
}
```

Output files in `--output-dir`:

| File                          | Purpose                                          |
| ----------------------------- | ------------------------------------------------ |
| `combined_pr_comment.md`      | One PR comment containing every mode             |
| `combined_step_summary.md`    | GitHub Actions step summary                      |
| `combined_metrics.json`       | Roll-up metrics (`overall_max_cycles`, etc.)     |

---

## GitHub Action reference

### Composite action (`./action.yml`)

```yaml
- uses: your-org/cortex-cycle-budget@v0
  with:
    config-path: cycle-analysis.json   # required
    elf-path: build/firmware.elf       # required
    target: nucleo-h743zi              # required
    build-config: Release              # required
    clock-mhz: 480                     # required
    cortex: m7                         # default: m4
    output-dir: cycle-analysis         # default
    objdump: arm-none-eabi-objdump     # default
    size-tool: arm-none-eabi-size      # default
    strict: 'true'                     # default
    fail-over-max-cycles: ''           # default: disabled
    python-version: '3.11'             # default
    package-version: ''                # default: latest from PyPI
    post-comment: 'true'               # default
    upload-artifacts: 'true'           # default
    artifact-name: cycle-analysis      # default
```

Outputs:

| Name          | Description                                       |
| ------------- | ------------------------------------------------- |
| `output-dir`  | Absolute path to the reports directory            |
| `max-cycles`  | Estimated maximum cycles across the critical path |
| `min-cycles`  | Estimated minimum cycles across the critical path |

The composite action automatically:

1. Installs Python ≥ 3.11.
2. `pip install`s `cortex-cycle-budget` (configurable via `package-version`).
3. Runs the analysis.
4. Appends the full report to `$GITHUB_STEP_SUMMARY`.
5. Posts or updates an idempotent PR comment marked with
   `<!-- cortex-cycle-budget-comment -->`.
6. Uploads the output directory as an artifact.

> ⚠️ The composite action does **not** install `arm-none-eabi-objdump`. The
> caller must either install the ARM toolchain in a prior step or pass
> `--objdump` to a tool that ships with their build container.

### Reusable workflow (`.github/workflows/cycle-analysis.yml`)

For consumers that want a one-line job:

```yaml
jobs:
  cycle-analysis:
    uses: your-org/cortex-cycle-budget/.github/workflows/cycle-analysis.yml@v0
    with:
      config-path: cycle-analysis.json
      elf-artifact-name: firmware-release
      elf-path: firmware.elf
      target: nucleo-h743zi
      build-config: Release
      clock-mhz: 480
      cortex: m7
```

The reusable workflow downloads the ELF from a previously uploaded artifact
and then invokes the composite action.

---

## Calling from Python

`cortex-cycle-budget` exposes a stable public API for programmatic use:

```python
from cortex_cycle_budget import (
    parse_disassembly,
    analyze_stages,
    generate_pr_comment,
    resolve_timing_table,
    validate_config,
)

config = {
    "path_stages": [{"label": "ISR", "patterns": ["^isr_handler$"]}],
    "cortex": "m7",
    "clock_mhz": 480,
    "target": "nucleo-h743zi",
    "build_config": "Release",
}
validate_config(config)

timing = resolve_timing_table("m7")
fns = parse_disassembly(open("firmware.disasm").read(), timing=timing)
lookup = {fn.demangled: fn for fn in fns}

stages = analyze_stages(config, fns, lookup)
print(generate_pr_comment(config, stages))
```
