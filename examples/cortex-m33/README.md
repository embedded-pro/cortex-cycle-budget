# Cortex-M33 example — ISR with exception_entry / exception_exit overhead

Demonstrates how the analyzer accounts for **architectural ISR overhead** in
addition to user code: the `exception_entry` and `exception_exit` stage types
inject the per-variant TRM-defined cycle counts automatically.

## Why M33 ≈ M4 in this analyzer

The Cortex-M33 v8-M Mainline core has the same integer pipeline and FPU
characteristics as the M4 (Armv7-M FPv4). The differences (TrustZone, MPU,
DSP extensions) do not change instruction cycle counts. As a result the
M33 timing table is identical to M4 in this tool.

## Build

```bash
arm-none-eabi-gcc -mcpu=cortex-m33 -mthumb -mfpu=fpv5-sp-d16 -mfloat-abi=hard \
    -Os -nostdlib -ffreestanding \
    -Wl,-Ttext=0x0 -Wl,--entry=_start \
    isr.c -o isr.elf
```

## Analyze

```bash
cortex-cycle-budget cycle-analysis.json \
    --elf isr.elf \
    --target demo-m33 \
    --build-config Release \
    --clock-mhz 110 \
    --cortex m33 \
    --output-dir out
```

The resulting `cpu_budget.md` table accounts for **12–29 cycles** entry +
**12 cycles** exit overhead in addition to the CRC32 work. See
`cycle_metrics.json → stages[0]` for the entry overhead values.
