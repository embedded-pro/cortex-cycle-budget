# Cycle Estimation Report

**Target**: `demo-m4` | **Build**: `Release` | **Clock**: 100 MHz | **Cortex**: `m4`
**Path**: Control Loop

## Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min) | **16** |
| Estimated Cycles (max) | **33** |
| Total Instructions | 16 |
| Total Code Size | 44 bytes |
| FPU Operations | 0 |
| Path Stages | 3 |

## CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 10 kHz | 10000 | 16 (0.2%) | 33 (0.3%) | 🟢 OK |
| 20 kHz | 5000 | 16 (0.3%) | 33 (0.7%) | 🟢 OK |
| 50 kHz | 2000 | 16 (0.8%) | 33 (1.7%) | 🟢 OK |

## Path Breakdown

```
  Sensor Read          ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     4–7    cycles ( 21.2%)
                       │
  Control Computation  █████████████████████████░░░░░░░░░░░░░░░    10–21   cycles ( 63.6%)
                       │
  Actuator Output      ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     2–5    cycles ( 15.2%)
```

| Stage | Min Cycles | Max Cycles | Instructions | Code Size | FPU Ops | Functions |
|-------|-----------|-----------|-------------|-----------|---------|-----------|
| Sensor Read | 4 | 7 | 4 | 10 B | 0 | 1 |
| Control Computation | 10 | 21 | 10 | 28 B | 0 | 2 |
| Actuator Output | 2 | 5 | 2 | 6 B | 0 | 1 |
| **TOTAL** | **16** | **33** | **16** | **44 B** | **0** | |

## Per-Function Detail — Control Computation

| Function | Calls | Min Cycles | Max Cycles | FPU | Load/Store | Branch | ALU |
|----------|-------|-----------|-----------|-----|------------|--------|-----|
| `control_loop` | 1x | 6 | 14 | 0 | 2 | 2 | 2 |
| `sensor_read` | 1x | 4 | 7 | 0 | 0 | 1 | 2 |

## Instruction Mix

```
  FPU          ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
  Load/Store   ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    2 ( 12.5%)
  Branch       ███████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    5 ( 31.2%)
  ALU          █████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    7 ( 43.8%)
  Mul/Div      ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    2 ( 12.5%)
```

## Optimization Quality Indicators

- ❌ **Low FPU utilization** (0%) — excessive overhead
- ✅ **Low load/store ratio** (12%) — efficient register usage
- ⚠️ **No FMA instructions** — consider `-ffast-math` or VFMA intrinsics
