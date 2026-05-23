# Multi-mode example — one ELF, multiple critical paths

When the same firmware can run in several "modes" (e.g., sensored vs. sensorless,
PID vs. dq-control), use the multi-mode CLI to produce a single combined PR
comment / step summary that reports cycle budgets for every mode side by side.

## Build

```bash
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -Os -nostdlib -ffreestanding \
    -Wl,-Ttext=0x0 -Wl,--entry=_start \
    motor_modes.c -o motor_modes.elf
```

## Analyze both modes

```bash
cortex-cycle-budget-multi analyses.json \
    --target demo-m4 \
    --build-config Release \
    --clock-mhz 100 \
    --cortex m4 \
    --output-dir out
```

Outputs in `out/`:

| File                            | Purpose                                 |
| ------------------------------- | --------------------------------------- |
| `mode_a/cycle_metrics.json`     | Per-mode metrics for Mode A             |
| `mode_b/cycle_metrics.json`     | Per-mode metrics for Mode B             |
| `combined_metrics.json`         | Roll-up with `overall_max_cycles`       |
| `combined_pr_comment.md`        | One PR comment containing both modes    |
| `combined_step_summary.md`      | One GitHub Actions step summary         |

## Fail the CI build on regression

```bash
cortex-cycle-budget-multi analyses.json \
    --target demo-m4 --build-config Release \
    --clock-mhz 100 --cortex m4 \
    --output-dir out \
    --fail-over-max-cycles 800     # exit 2 if any mode exceeds 800 cycles
```
