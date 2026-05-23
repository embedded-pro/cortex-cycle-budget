# Minimal example — Cortex-M4 control loop

A bare-bones control loop with three stages: sensor read → computation → actuator output.

## Build the ELF

```bash
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -Os -nostdlib -ffreestanding \
    -Wl,-Ttext=0x0 -Wl,--entry=_start \
    control_loop.c -o control_loop.elf
```

A prebuilt `control_loop.elf` is committed in this directory for convenience.

## Run cycle analysis

```bash
cortex-cycle-budget cycle-analysis.json \
    --elf control_loop.elf \
    --target demo-m4 \
    --build-config Release \
    --clock-mhz 100 \
    --cortex m4 \
    --output-dir out
```

Outputs in `out/`:

| File                          | Purpose                                        |
| ----------------------------- | ---------------------------------------------- |
| `cycle_estimation_report.md`  | Full markdown report                           |
| `cpu_budget.md`               | CPU utilization table for `loop_rates_khz`     |
| `pr_comment.md`               | GitHub PR comment (with marker for `gh` bot)   |
| `annotated_disassembly.md`    | Disassembly annotated with cycle counts        |
| `cycle_metrics.json`          | Machine-readable summary                       |
| `full_disassembly.txt`        | Raw `objdump -d` output                        |
| `size_report.txt`             | `arm-none-eabi-size` output                    |

## Try the M7 / M33 variants

```bash
# Re-compile and re-analyze for Cortex-M7
arm-none-eabi-gcc -mcpu=cortex-m7 -mthumb -Os -nostdlib -ffreestanding \
    -Wl,-Ttext=0x0 -Wl,--entry=_start control_loop.c -o control_loop_m7.elf
cortex-cycle-budget cycle-analysis.json --elf control_loop_m7.elf \
    --target demo-m7 --build-config Release --clock-mhz 480 --cortex m7 \
    --output-dir out_m7
```
