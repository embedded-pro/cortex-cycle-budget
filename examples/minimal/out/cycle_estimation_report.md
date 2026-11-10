# Cycle Estimation Report

**Target**: `demo-m4` | **Build**: `Release` | **Clock**: 100 MHz
**Path**: Control Loop

## Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min) | **16** |
| Estimated Cycles (max) | **28** |
| Instructions on Worst Path | 12 |
| Code Size of Functions on Path | 34 bytes |
| FPU Operations on Worst Path | 0 |
| Path Stages | 3 |

## CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 10 kHz | 10000 | 16 (0.2%) | 28 (0.3%) | 🟢 OK |
| 20 kHz | 5000 | 16 (0.3%) | 28 (0.6%) | 🟢 OK |
| 50 kHz | 2000 | 16 (0.8%) | 28 (1.4%) | 🟢 OK |

## Path Breakdown

```
  Sensor Read          ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     4–7    cycles ( 25.0%)
                       │
  Control Computation  ██████████████████████░░░░░░░░░░░░░░░░░░    10–16   cycles ( 57.1%)
                       │
  Actuator Output      ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     2–5    cycles ( 17.9%)
```

| Stage | Min Cycles | Max Cycles | Instructions | Code Size | FPU Ops | Functions |
|-------|-----------|-----------|-------------|-----------|---------|-----------|
| Sensor Read | 4 | 7 | 4 | 10 B | 0 | 1 |
| Control Computation | 10 | 16 | 6 | 18 B | 0 | 1 |
| Actuator Output | 2 | 5 | 2 | 6 B | 0 | 1 |
| **TOTAL** | **16** | **28** | **12** | **34 B** | **0** | |

## Per-Function Detail — Sensor Read

| Function | Calls | Max Cycles | Instructions on Path | FPU |
|----------|-------|-----------|----------------------|-----|
| `sensor_read` | 1x | 7 | 4 | 0 |

## Per-Function Detail — Control Computation

| Function | Calls | Max Cycles | Instructions on Path | FPU |
|----------|-------|-----------|----------------------|-----|
| `control_loop` | 1x | 16 | 6 | 0 |

## Per-Function Detail — Actuator Output

| Function | Calls | Max Cycles | Instructions on Path | FPU |
|----------|-------|-----------|----------------------|-----|
| `actuator_output` | 1x | 5 | 2 | 0 |

## Instruction Mix

```
  FPU          ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
  Load/Store   ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    2 ( 16.7%)
  Branch       ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    4 ( 33.3%)
  ALU          ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    5 ( 41.7%)
  Mul/Div      ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    1 (  8.3%)
```

## Optimization Quality Indicators

- ❌ **Low FPU utilization** (0%) — excessive overhead
- ✅ **Low load/store ratio** (17%) — efficient register usage
- ⚠️ **No FMA instructions** — consider `-ffast-math` or VFMA intrinsics
