# Cycle Estimation Report

**Target**: `demo-h7` | **Build**: `Release` | **Clock**: 480 MHz
**Path**: FOC Kernel (FPU-heavy)

## Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min) | **44** |
| Estimated Cycles (max) | **62** |
| Instructions on Worst Path | 23 |
| Code Size of Functions on Path | 90 bytes |
| FPU Operations on Worst Path | 14 |
| Path Stages | 4 |

## CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 20 kHz | 24000 | 44 (0.2%) | 62 (0.3%) | 🟢 OK |
| 40 kHz | 12000 | 44 (0.4%) | 62 (0.5%) | 🟢 OK |
| 100 kHz | 4800 | 44 (0.9%) | 62 (1.3%) | 🟢 OK |

## Path Breakdown

```
  Park / Clarke          ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    10–13   cycles ( 21.0%)
                         │
  Magnitude (vsqrt.f32)  █████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    12–15   cycles ( 24.2%)
                         │
  Normalize (vdiv.f32)   ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     8–11   cycles ( 17.7%)
                         │
  FOC Kernel Wrapper     ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░    14–23   cycles ( 37.1%)
```

| Stage | Min Cycles | Max Cycles | Instructions | Code Size | FPU Ops | Functions |
|-------|-----------|-----------|-------------|-----------|---------|-----------|
| Park / Clarke | 10 | 13 | 7 | 32 B | 5 | 1 |
| Magnitude (vsqrt.f32) | 12 | 15 | 4 | 14 B | 3 | 1 |
| Normalize (vdiv.f32) | 8 | 11 | 2 | 6 B | 1 | 1 |
| FOC Kernel Wrapper | 14 | 23 | 10 | 38 B | 5 | 1 |
| **TOTAL** | **44** | **62** | **23** | **90 B** | **14** | |

## Per-Function Detail — Park / Clarke

| Function | Calls | Max Cycles | Instructions on Path | FPU |
|----------|-------|-----------|----------------------|-----|
| `park_transform` | 1x | 13 | 7 | 5 |

## Per-Function Detail — Magnitude (vsqrt.f32)

| Function | Calls | Max Cycles | Instructions on Path | FPU |
|----------|-------|-----------|----------------------|-----|
| `compute_magnitude` | 1x | 15 | 4 | 3 |

## Per-Function Detail — Normalize (vdiv.f32)

| Function | Calls | Max Cycles | Instructions on Path | FPU |
|----------|-------|-----------|----------------------|-----|
| `normalize` | 1x | 11 | 2 | 1 |

## Per-Function Detail — FOC Kernel Wrapper

| Function | Calls | Max Cycles | Instructions on Path | FPU |
|----------|-------|-----------|----------------------|-----|
| `foc_kernel` | 1x | 23 | 10 | 5 |

## Instruction Mix

```
  FPU          █████████████████████████████░░░░░░░░░░░░░░░░░░░░░   14 ( 58.3%)
  Load/Store   ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    3 ( 12.5%)
  Branch       ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    6 ( 25.0%)
  ALU          ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    1 (  4.2%)
  Mul/Div      ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
```

## Optimization Quality Indicators

- ✅ **High FPU utilization** (58%) — good use of hardware FPU
- ✅ **Low load/store ratio** (12%) — efficient register usage
- ✅ **FMA instructions detected** — fused multiply-add in use
- ℹ️ **vsqrt/vdiv detected** — 7 cycles each on Cortex-M7
