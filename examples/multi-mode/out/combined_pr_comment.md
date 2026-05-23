<!-- cortex-cycle-budget-comment -->
## 🏎️ Cycle Analysis Results

### Mode A (Sensored) | demo-m4

**CPU Utilization Budget**

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 20 kHz | 5000 | 23 (0.5%) | 37 (0.7%) | 🟢 OK |

<details>
<summary>Click to expand full details</summary>

# Cycle Estimation Report

**Target**: `demo-m4` | **Build**: `Release` | **Clock**: 100 MHz | **Cortex**: `m4`
**Path**: Mode A — Sensored

## Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min) | **23** |
| Estimated Cycles (max) | **37** |
| Total Instructions | 20 |
| Total Code Size | 52 bytes |
| FPU Operations | 0 |
| Path Stages | 3 |

## CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 20 kHz | 5000 | 23 (0.5%) | 37 (0.7%) | 🟢 OK |

## Path Breakdown

```
  Sensor Filter  ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     3–6    cycles ( 16.2%)
                 │
  PID Loop       ███████████████████░░░░░░░░░░░░░░░░░░░░░    15–18   cycles ( 48.6%)
                 │
  Mode A Wrap    ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░     5–13   cycles ( 35.1%)
```

| Stage | Min Cycles | Max Cycles | Instructions | Code Size | FPU Ops | Functions |
|-------|-----------|-----------|-------------|-----------|---------|-----------|
| Sensor Filter | 3 | 6 | 3 | 8 B | 0 | 1 |
| PID Loop | 15 | 18 | 12 | 28 B | 0 | 1 |
| Mode A Wrap | 5 | 13 | 5 | 16 B | 0 | 1 |
| **TOTAL** | **23** | **37** | **20** | **52 B** | **0** | |

## Instruction Mix

```
  FPU          ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
  Load/Store   ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    5 ( 25.0%)
  Branch       ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    4 ( 20.0%)
  ALU          ███████████████████████████░░░░░░░░░░░░░░░░░░░░░░░   11 ( 55.0%)
  Mul/Div      ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
```

## Optimization Quality Indicators

- ❌ **Low FPU utilization** (0%) — excessive overhead
- ✅ **Low load/store ratio** (25%) — efficient register usage
- ⚠️ **No FMA instructions** — consider `-ffast-math` or VFMA intrinsics


</details>

---

### Mode B (Sensorless) | demo-m4

**CPU Utilization Budget**

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 20 kHz | 5000 | 23 (0.5%) | 37 (0.7%) | 🟢 OK |

<details>
<summary>Click to expand full details</summary>

# Cycle Estimation Report

**Target**: `demo-m4` | **Build**: `Release` | **Clock**: 100 MHz | **Cortex**: `m4`
**Path**: Mode B — Sensorless

## Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min) | **23** |
| Estimated Cycles (max) | **37** |
| Total Instructions | 20 |
| Total Code Size | 54 bytes |
| FPU Operations | 0 |
| Path Stages | 3 |

## CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 20 kHz | 5000 | 23 (0.5%) | 37 (0.7%) | 🟢 OK |

## Path Breakdown

```
  Observer     ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     3–6    cycles ( 16.2%)
               │
  PID Loop     ███████████████████░░░░░░░░░░░░░░░░░░░░░    15–18   cycles ( 48.6%)
               │
  Mode B Wrap  ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░     5–13   cycles ( 35.1%)
```

| Stage | Min Cycles | Max Cycles | Instructions | Code Size | FPU Ops | Functions |
|-------|-----------|-----------|-------------|-----------|---------|-----------|
| Observer | 3 | 6 | 3 | 10 B | 0 | 1 |
| PID Loop | 15 | 18 | 12 | 28 B | 0 | 1 |
| Mode B Wrap | 5 | 13 | 5 | 16 B | 0 | 1 |
| **TOTAL** | **23** | **37** | **20** | **54 B** | **0** | |

## Instruction Mix

```
  FPU          ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
  Load/Store   ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    5 ( 25.0%)
  Branch       ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    4 ( 20.0%)
  ALU          ███████████████████████████░░░░░░░░░░░░░░░░░░░░░░░   11 ( 55.0%)
  Mul/Div      ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
```

## Optimization Quality Indicators

- ❌ **Low FPU utilization** (0%) — excessive overhead
- ✅ **Low load/store ratio** (25%) — efficient register usage
- ⚠️ **No FMA instructions** — consider `-ffast-math` or VFMA intrinsics


</details>
