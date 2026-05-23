## 🏎️ Cycle Estimation

**Target**: `demo-m4` | **Build**: `Release` | **Clock**: 100 MHz | **Cortex**: `m4`
**Path**: Control Loop

### Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min — max) | **16** — **33** |
| Total Instructions | 16 |
| Code Size | 44 bytes |
| Path Stages | 3 |

### CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 10 kHz | 10000 | 16 (0.2%) | 33 (0.3%) | 🟢 OK |
| 20 kHz | 5000 | 16 (0.3%) | 33 (0.7%) | 🟢 OK |
| 50 kHz | 2000 | 16 (0.8%) | 33 (1.7%) | 🟢 OK |

### Path Breakdown

| Stage | Cycles | % |
|-------|--------|---|
| Sensor Read | 4–7 | 21% |
| Control Computation | 10–21 | 64% |
| Actuator Output | 2–5 | 15% |
| **Total** | **16–33** | |

> 📦 Full report, annotated disassembly and JSON metrics available in workflow artifacts.