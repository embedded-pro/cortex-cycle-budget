# Cycle Estimation Report

**Target**: `demo-m33` | **Build**: `Release` | **Clock**: 110 MHz | **Cortex**: `m33`
**Path**: ISR CRC32

## Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min) | **25** |
| Estimated Cycles (max) | **62** |
| Total Instructions | 1 |
| Total Code Size | 4 bytes |
| FPU Operations | 0 |
| Path Stages | 3 |

## CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 1 kHz | 110000 | 25 (0.0%) | 62 (0.1%) | 🟢 OK |
| 10 kHz | 11000 | 25 (0.2%) | 62 (0.6%) | 🟢 OK |

## Path Breakdown

```
  ISR Entry  ██████████████████░░░░░░░░░░░░░░░░░░░░░░    12–29   cycles ( 46.8%)
             │
  ISR Body   ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     1–4    cycles (  6.5%)
             │
  ISR Exit   ██████████████████░░░░░░░░░░░░░░░░░░░░░░    12–29   cycles ( 46.8%)
```

| Stage | Min Cycles | Max Cycles | Instructions | Code Size | FPU Ops | Functions |
|-------|-----------|-----------|-------------|-----------|---------|-----------|
| ISR Entry *(hw overhead)* | 12 | 29 | 0 | 0 B | 0 | 0 |
| ISR Body | 1 | 4 | 1 | 4 B | 0 | 1 |
| ISR Exit *(hw overhead)* | 12 | 29 | 0 | 0 B | 0 | 0 |
| **TOTAL** | **25** | **62** | **1** | **4 B** | **0** | |

## Per-Function Detail — ISR Body

| Function | Calls | Min Cycles | Max Cycles | FPU | Load/Store | Branch | ALU |
|----------|-------|-----------|-----------|-----|------------|--------|-----|
| `isr_handler` | 1x | 1 | 4 | 0 | 0 | 1 | 0 |

## Instruction Mix

```
  FPU          ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
  Load/Store   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
  Branch       ██████████████████████████████████████████████████    1 (100.0%)
  ALU          ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
  Mul/Div      ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    0 (  0.0%)
```

## Optimization Quality Indicators

- ❌ **Low FPU utilization** (0%) — excessive overhead
- ✅ **Low load/store ratio** (0%) — efficient register usage
- ⚠️ **No FMA instructions** — consider `-ffast-math` or VFMA intrinsics
