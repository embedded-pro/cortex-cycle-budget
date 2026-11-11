# Cycle Estimation Report

**Target**: `demo-m33` | **Build**: `Release` | **Clock**: 110 MHz
**Path**: ISR CRC32

## Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min) | **42** |
| Estimated Cycles (max) | **113** |
| Instructions on Worst Path | 22 |
| Code Size of Functions on Path | 60 bytes |
| FPU Operations on Worst Path | 0 |
| Path Stages | 3 |

## CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 1 kHz | 110000 | 42 (0.0%) | 113 (0.1%) | 🟢 OK |
| 10 kHz | 11000 | 42 (0.4%) | 113 (1.0%) | 🟢 OK |

## Path Breakdown

```
  ISR Entry  ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    12–29   cycles ( 25.7%)
             │
  ISR Body   ███████████████████░░░░░░░░░░░░░░░░░░░░░    18–55   cycles ( 48.7%)
             │
  ISR Exit   ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    12–29   cycles ( 25.7%)
```

| Stage | Min Cycles | Max Cycles | Instructions | Code Size | FPU Ops | Functions |
|-------|-----------|-----------|-------------|-----------|---------|-----------|
| ISR Entry *(hw overhead)* | 12 | 29 | 0 | 0 B | 0 | 0 |
| ISR Body | 18 | 55 | 22 | 60 B | 0 | 3 |
| ISR Exit *(hw overhead)* | 12 | 29 | 0 | 0 B | 0 | 0 |
| **TOTAL** | **42** | **113** | **22** | **60 B** | **0** | |

## Per-Function Detail — ISR Body

| Function | Calls | Max Cycles | Instructions on Path | FPU |
|----------|-------|-----------|----------------------|-----|
| `crc32` | 1x | 34 | 11 | 0 |
| `crc32_byte` | 1x | 17 | 10 | 0 |
| `isr_handler` | 1x | 4 | 1 | 0 |

## Loops — ISR Body

| Function | Loop | Address | Depth | Instructions | Iterations |
|----------|------|---------|-------|--------------|------------|
| `crc32` | 1 | 0x00000026 | 1 | 5 | 1 |
| `crc32_byte` | 1 | 0x00000006 | 1 | 6 | 1 |

## Analysis Notes

- **ISR Body**: loops are charged for one iteration, set `loop_bounds` to charge more: `crc32` (1), `crc32_byte` (1)

## Instruction Mix

```
  FPU          ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
  Load/Store   █████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    4 ( 18.2%)
  Branch       █████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    6 ( 27.3%)
  ALU          ███████████████████████████░░░░░░░░░░░░░░░░░░░░░░░   12 ( 54.5%)
  Mul/Div      ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
```

## Optimization Quality Indicators

- ❌ **Low FPU utilization** (0%) — excessive overhead
- ✅ **Low load/store ratio** (18%) — efficient register usage
- ⚠️ **No FMA instructions** — consider `-ffast-math` or VFMA intrinsics
