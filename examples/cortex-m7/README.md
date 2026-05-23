# Cortex-M7 example — FPU-heavy FOC kernel

Demonstrates how the **M7 timing model** differs from M4 for floating-point
divide and square-root, which dominate motor-control FOC loops.

## Why M7 is faster than M4 here

| Operation     | Cortex-M4 (cycles) | Cortex-M7 (cycles) | Source                       |
| ------------- | ------------------ | ------------------ | ---------------------------- |
| `vsqrt.f32`   | 14                 | 7                  | ARM TRM DDI0489F §7.5        |
| `vdiv.f32`    | 14                 | 7                  | ARM TRM DDI0489F §7.5        |
| `sdiv`/`udiv` | 2–12               | 2–7                | ARM TRM DDI0489F §6.5        |

The M7 also supports **limited dual-issue** of integer + FPU pairs, which is
not yet modeled in this static analyzer (a `DUAL_ISSUE_MIN_SCALE` constant
is defined for future use).

## Build

```bash
arm-none-eabi-gcc -mcpu=cortex-m7 -mthumb -mfpu=fpv5-sp-d16 -mfloat-abi=hard \
    -Os -nostdlib -ffreestanding \
    -Wl,-Ttext=0x0 -Wl,--entry=_start \
    foc_kernel.c -o foc_kernel.elf
```

## Analyze with the M7 timing model

```bash
cortex-cycle-budget cycle-analysis.json \
    --elf foc_kernel.elf \
    --target demo-h7 \
    --build-config Release \
    --clock-mhz 480 \
    --cortex m7 \
    --output-dir out
```

## Compare M4 vs. M7 estimates

Run the analysis twice (same ELF, different `--cortex`) and observe the
difference in `cycle_metrics.json → summary.estimated_max_cycles`:

```bash
cortex-cycle-budget cycle-analysis.json --elf foc_kernel.elf \
    --target compare --build-config Release --clock-mhz 100 \
    --cortex m4 --output-dir out_m4
cortex-cycle-budget cycle-analysis.json --elf foc_kernel.elf \
    --target compare --build-config Release --clock-mhz 100 \
    --cortex m7 --output-dir out_m7

jq '.summary.estimated_max_cycles' out_m4/cycle_metrics.json
jq '.summary.estimated_max_cycles' out_m7/cycle_metrics.json
```
