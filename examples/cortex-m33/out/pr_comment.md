## 🏎️ Cycle Estimation

**Target**: `demo-m33` | **Build**: `Release` | **Clock**: 110 MHz | **Cortex**: `m33`
**Path**: ISR CRC32

### Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min — max) | **25** — **62** |
| Total Instructions | 1 |
| Code Size | 4 bytes |
| Path Stages | 3 |

### CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 1 kHz | 110000 | 25 (0.0%) | 62 (0.1%) | 🟢 OK |
| 10 kHz | 11000 | 25 (0.2%) | 62 (0.6%) | 🟢 OK |

### Path Breakdown

| Stage | Cycles | % |
|-------|--------|---|
| ISR Entry | 12–29 | 47% |
| ISR Body | 1–4 | 6% |
| ISR Exit | 12–29 | 47% |
| **Total** | **25–62** | |

> 📦 Full report, annotated disassembly and JSON metrics available in workflow artifacts.