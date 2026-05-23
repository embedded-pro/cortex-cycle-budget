# cortex-cycle-budget

[![CI](https://github.com/your-org/cortex-cycle-budget/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/cortex-cycle-budget/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/cortex-cycle-budget.svg)](https://pypi.org/project/cortex-cycle-budget/)
[![Python](https://img.shields.io/pypi/pyversions/cortex-cycle-budget.svg)](https://pypi.org/project/cortex-cycle-budget/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

> Static cycle-count estimation for ARM Cortex-M binaries — **CI-friendly,
> framework-agnostic, zero runtime dependencies**.

`cortex-cycle-budget` analyzes an ELF binary (via `arm-none-eabi-objdump`) and
estimates the cycle cost of a **user-defined critical path** through your
firmware. It supports **Cortex-M0**, **Cortex-M4**, **Cortex-M7**, and
**Cortex-M33** with per-variant timing tables sourced from the ARM Technical
Reference Manuals.

It is designed for **hard-real-time loops** (motor control, signal processing,
servo loops) where you must guarantee that a control iteration fits inside a
fixed cycle budget.

---

## ✨ Features

| Feature                                           | Status |
| ------------------------------------------------- | :----: |
| Cortex-M0 / M4 / M7 / M33 timing models           |   ✅   |
| FPU costs (`vsqrt.f32`, `vdiv.f32`, …)            |   ✅   |
| Exception entry/exit overhead (per-variant)       |   ✅   |
| Call-graph walking from an entry function         |   ✅   |
| Strict & non-strict pattern matching              |   ✅   |
| CPU-utilization budget table at N kHz             |   ✅   |
| Annotated disassembly (Markdown)                  |   ✅   |
| Machine-readable JSON metrics                     |   ✅   |
| Multi-mode analyzer (one ELF, many critical paths)|   ✅   |
| GitHub composite action + reusable workflow       |   ✅   |
| PR comment with stable marker (idempotent update) |   ✅   |
| `--fail-over-max-cycles` CI gate                  |   ✅   |
| Cortex-M7 dual-issue (limited modelling planned)  |   🚧   |

---

## 🚀 Quickstart

### 1. Install

```bash
pip install cortex-cycle-budget
```

Runtime dependencies: **none** (Python ≥ 3.11 stdlib only). At analysis time
you need `arm-none-eabi-objdump` (and optionally `arm-none-eabi-size`) on
`PATH`, or pass `--objdump`/`--size-tool`.

### 2. Write a config (`cycle-analysis.json`)

```json
{
  "path_name": "FOC Control Loop",
  "loop_rates_khz": [20, 40, 100],
  "path_stages": [
    {"label": "ADC Read",  "patterns": ["^adc_read$"]},
    {"label": "FOC Math",  "entry": "^foc_step$", "patterns": ["^foc_.*$"]},
    {"label": "PWM Write", "patterns": ["^pwm_write$"]}
  ]
}
```

See [docs/config-schema.md](docs/config-schema.md) for the full schema.

### 3. Run

```bash
cortex-cycle-budget cycle-analysis.json \
    --elf build/firmware.elf \
    --target nucleo-h743zi \
    --build-config Release \
    --clock-mhz 480 \
    --cortex m7 \
    --output-dir reports
```

Outputs in `reports/`:

| File                          | Purpose                                          |
| ----------------------------- | ------------------------------------------------ |
| `cycle_estimation_report.md`  | Full Markdown report                             |
| `cpu_budget.md`               | CPU utilization at every configured loop rate    |
| `pr_comment.md`               | Compact PR comment (with idempotent marker)      |
| `annotated_disassembly.md`    | Disassembly annotated with per-instr cycles      |
| `cycle_metrics.json`          | Machine-readable summary for downstream tooling  |
| `full_disassembly.txt`        | Raw `objdump -d` output                          |
| `size_report.txt`             | `arm-none-eabi-size` output                      |

### 4. Use in GitHub Actions

```yaml
- uses: your-org/cortex-cycle-budget@v0
  with:
    config-path: cycle-analysis.json
    elf-path: build/firmware.elf
    target: nucleo-h743zi
    build-config: Release
    clock-mhz: 480
    cortex: m7
    fail-over-max-cycles: 20000   # fail the PR if the budget is blown
```

The action posts an idempotent PR comment, appends a step summary, and uploads
all reports as an artifact. See [docs/usage.md](docs/usage.md) for the full
input/output reference.

---

## 📚 Documentation

| Document                                                | What it covers                                |
| ------------------------------------------------------- | --------------------------------------------- |
| [docs/usage.md](docs/usage.md)                          | CLI flags, action inputs/outputs, examples    |
| [docs/config-schema.md](docs/config-schema.md)          | Full JSON config schema + reference           |
| [docs/timing-model.md](docs/timing-model.md)            | How cycle counts are derived (TRM citations)  |
| [docs/cortex-variants.md](docs/cortex-variants.md)      | M0 / M4 / M7 / M33 differences & caveats      |
| [docs/architecture.md](docs/architecture.md)            | Internal module layout & data flow            |
| [docs/troubleshooting.md](docs/troubleshooting.md)      | Common errors & their fixes                   |
| [CONTRIBUTING.md](CONTRIBUTING.md)                      | Dev setup, testing, release process           |
| [CHANGELOG.md](CHANGELOG.md)                            | Version history                               |

---

## 🧪 Examples

Four runnable examples ship in [examples/](examples/):

| Example                                         | Highlights                                       |
| ----------------------------------------------- | ------------------------------------------------ |
| [examples/minimal](examples/minimal/)           | 3-stage Cortex-M4 control loop                   |
| [examples/cortex-m7](examples/cortex-m7/)       | FPU-heavy FOC kernel (vsqrt/vdiv)                |
| [examples/cortex-m33](examples/cortex-m33/)     | ISR with `exception_entry` / `exception_exit`    |
| [examples/multi-mode](examples/multi-mode/)     | One ELF, two distinct critical paths             |

---

## ⚠️ Scope & limitations

This tool gives **static, deterministic estimates**. It does **not** model:

- Cache hits/misses (Cortex-M7 I-cache, D-cache, AXI bus contention).
- Branch prediction accuracy on M7.
- Memory wait states from external flash / SDRAM.
- Interrupt nesting and tail-chaining beyond the documented worst case.
- Cortex-M7 dual-issue at the instruction-pair level (planned).

Estimates are intended as a **CI guardrail**, not a substitute for cycle-accurate
hardware profiling (e.g., DWT/CYCCNT or a logic analyzer).

---

## 📄 License

Apache-2.0 — see [LICENSE](LICENSE).
