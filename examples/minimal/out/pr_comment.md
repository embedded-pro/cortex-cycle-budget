## 🏎️ Cycle Estimation

**Target**: `demo-m4` | **Build**: `Release` | **Clock**: 100 MHz
**Path**: Control Loop

### Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min — max) | **16** — **28** |
| Instructions on Worst Path | 12 |
| Code Size | 34 bytes |
| Path Stages | 3 |

### CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 10 kHz | 10000 | 16 (0.2%) | 28 (0.3%) | 🟢 OK |
| 20 kHz | 5000 | 16 (0.3%) | 28 (0.6%) | 🟢 OK |
| 50 kHz | 2000 | 16 (0.8%) | 28 (1.4%) | 🟢 OK |

### Path Breakdown

| Stage | Cycles | % |
|-------|--------|---|
| Sensor Read | 4–7 | 25% |
| Control Computation | 10–16 | 57% |
| Actuator Output | 2–5 | 18% |
| **Total** | **16–28** | |

> 📦 Full report, annotated disassembly and JSON metrics available in workflow artifacts.