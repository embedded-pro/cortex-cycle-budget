<!-- cortex-cycle-budget-comment -->
## 🏎️ Cycle Analysis Results

### Mode A (Sensored) | demo-m4

**CPU Utilization Budget**

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 20 kHz | 5000 | 25 (0.5%) | 37 (0.7%) | 🟢 OK |

<details>
<summary>Click to expand full details</summary>

# Cycle Estimation Report

**Target**: `demo-m4` | **Build**: `Release` | **Clock**: 100 MHz
**Path**: Mode A — Sensored

## Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min) | **25** |
| Estimated Cycles (max) | **37** |
| Instructions on Worst Path | 18 |
| Code Size of Functions on Path | 52 bytes |
| FPU Operations on Worst Path | 0 |
| Path Stages | 3 |

## CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 20 kHz | 5000 | 25 (0.5%) | 37 (0.7%) | 🟢 OK |

## Path Breakdown

```
  Sensor Filter  ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     3–6    cycles ( 16.2%)
                 │
  PID Loop       █████████████████░░░░░░░░░░░░░░░░░░░░░░░    13–16   cycles ( 43.2%)
                 │
  Mode A Wrap    ████████████████░░░░░░░░░░░░░░░░░░░░░░░░     9–15   cycles ( 40.5%)
```

| Stage | Min Cycles | Max Cycles | Instructions | Code Size | FPU Ops | Functions |
|-------|-----------|-----------|-------------|-----------|---------|-----------|
| Sensor Filter | 3 | 6 | 3 | 8 B | 0 | 1 |
| PID Loop | 13 | 16 | 10 | 28 B | 0 | 1 |
| Mode A Wrap | 9 | 15 | 5 | 16 B | 0 | 1 |
| **TOTAL** | **25** | **37** | **18** | **52 B** | **0** | |

## Per-Function Detail — Sensor Filter

| Function | Calls | Max Cycles | Instructions on Path | FPU |
|----------|-------|-----------|----------------------|-----|
| `sensor_filter` | 1x | 6 | 3 | 0 |

## Per-Function Detail — PID Loop

| Function | Calls | Max Cycles | Instructions on Path | FPU |
|----------|-------|-----------|----------------------|-----|
| `pid_loop` | 1x | 16 | 10 | 0 |

## Per-Function Detail — Mode A Wrap

| Function | Calls | Max Cycles | Instructions on Path | FPU |
|----------|-------|-----------|----------------------|-----|
| `mode_a_step` | 1x | 15 | 5 | 0 |

## Instruction Mix

```
  FPU          ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
  Load/Store   █████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    5 ( 26.3%)
  Branch       ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    4 ( 21.1%)
  ALU          ██████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░   10 ( 52.6%)
  Mul/Div      ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
```

## Optimization Quality Indicators

- ❌ **Low FPU utilization** (0%) — excessive overhead
- ⚠️ **Moderate load/store ratio** (26%)
- ⚠️ **No FMA instructions** — consider `-ffast-math` or VFMA intrinsics


</details>

---

### Mode B (Sensorless) | demo-m4

**CPU Utilization Budget**

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 20 kHz | 5000 | 25 (0.5%) | 37 (0.7%) | 🟢 OK |

<details>
<summary>Click to expand full details</summary>

# Cycle Estimation Report

**Target**: `demo-m4` | **Build**: `Release` | **Clock**: 100 MHz
**Path**: Mode B — Sensorless

## Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min) | **25** |
| Estimated Cycles (max) | **37** |
| Instructions on Worst Path | 18 |
| Code Size of Functions on Path | 54 bytes |
| FPU Operations on Worst Path | 0 |
| Path Stages | 3 |

## CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 20 kHz | 5000 | 25 (0.5%) | 37 (0.7%) | 🟢 OK |

## Path Breakdown

```
  Observer     ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     3–6    cycles ( 16.2%)
               │
  PID Loop     █████████████████░░░░░░░░░░░░░░░░░░░░░░░    13–16   cycles ( 43.2%)
               │
  Mode B Wrap  ████████████████░░░░░░░░░░░░░░░░░░░░░░░░     9–15   cycles ( 40.5%)
```

| Stage | Min Cycles | Max Cycles | Instructions | Code Size | FPU Ops | Functions |
|-------|-----------|-----------|-------------|-----------|---------|-----------|
| Observer | 3 | 6 | 3 | 10 B | 0 | 1 |
| PID Loop | 13 | 16 | 10 | 28 B | 0 | 1 |
| Mode B Wrap | 9 | 15 | 5 | 16 B | 0 | 1 |
| **TOTAL** | **25** | **37** | **18** | **54 B** | **0** | |

## Per-Function Detail — Observer

| Function | Calls | Max Cycles | Instructions on Path | FPU |
|----------|-------|-----------|----------------------|-----|
| `observer` | 1x | 6 | 3 | 0 |

## Per-Function Detail — PID Loop

| Function | Calls | Max Cycles | Instructions on Path | FPU |
|----------|-------|-----------|----------------------|-----|
| `pid_loop` | 1x | 16 | 10 | 0 |

## Per-Function Detail — Mode B Wrap

| Function | Calls | Max Cycles | Instructions on Path | FPU |
|----------|-------|-----------|----------------------|-----|
| `mode_b_step` | 1x | 15 | 5 | 0 |

## Instruction Mix

```
  FPU          ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
  Load/Store   █████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    5 ( 26.3%)
  Branch       ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    4 ( 21.1%)
  ALU          ██████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░   10 ( 52.6%)
  Mul/Div      ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
```

## Optimization Quality Indicators

- ❌ **Low FPU utilization** (0%) — excessive overhead
- ⚠️ **Moderate load/store ratio** (26%)
- ⚠️ **No FMA instructions** — consider `-ffast-math` or VFMA intrinsics


</details>
