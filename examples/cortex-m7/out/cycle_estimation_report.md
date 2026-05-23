# Cycle Estimation Report

**Target**: `demo-h7` | **Build**: `Release` | **Clock**: 480 MHz | **Cortex**: `m7`
**Path**: FOC Kernel (FPU-heavy)

## Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min) | **38** |
| Estimated Cycles (max) | **58** |
| Total Instructions | 25 |
| Total Code Size | 90 bytes |
| FPU Operations | 14 |
| Path Stages | 4 |

## CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 20 kHz | 24000 | 38 (0.2%) | 58 (0.2%) | 🟢 OK |
| 40 kHz | 12000 | 38 (0.3%) | 58 (0.5%) | 🟢 OK |
| 100 kHz | 4800 | 38 (0.8%) | 58 (1.2%) | 🟢 OK |

## Path Breakdown

```
  Park / Clarke          ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    10–13   cycles ( 22.4%)
                         │
  Magnitude (vsqrt.f32)  ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    10–13   cycles ( 22.4%)
                         │
  Normalize (vdiv.f32)   ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     8–11   cycles ( 19.0%)
                         │
  FOC Kernel Wrapper     ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░    10–21   cycles ( 36.2%)
```

| Stage | Min Cycles | Max Cycles | Instructions | Code Size | FPU Ops | Functions |
|-------|-----------|-----------|-------------|-----------|---------|-----------|
| Park / Clarke | 10 | 13 | 9 | 32 B | 5 | 1 |
| Magnitude (vsqrt.f32) | 10 | 13 | 4 | 14 B | 3 | 1 |
| Normalize (vdiv.f32) | 8 | 11 | 2 | 6 B | 1 | 1 |
| FOC Kernel Wrapper | 10 | 21 | 10 | 38 B | 5 | 1 |
| **TOTAL** | **38** | **58** | **25** | **90 B** | **14** | |

## Instruction Mix

```
  FPU          ████████████████████████████░░░░░░░░░░░░░░░░░░░░░░   14 ( 56.0%)
  Load/Store   ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    3 ( 12.0%)
  Branch       ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    6 ( 24.0%)
  ALU          ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    2 (  8.0%)
  Mul/Div      ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
```

## Optimization Quality Indicators

- ✅ **High FPU utilization** (56%) — good use of hardware FPU
- ✅ **Low load/store ratio** (12%) — efficient register usage
- ✅ **FMA instructions detected** — fused multiply-add in use
- ℹ️ **vsqrt/vdiv detected** — 7 cycles each on Cortex-M7
