## 🏎️ Cycle Estimation

**Target**: `demo-m33` | **Build**: `Release` | **Clock**: 110 MHz
**Path**: ISR CRC32

### Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min — max) | **42** — **113** |
| Instructions on Worst Path | 22 |
| Code Size | 60 bytes |
| Path Stages | 3 |

### CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 1 kHz | 110000 | 42 (0.0%) | 113 (0.1%) | 🟢 OK |
| 10 kHz | 11000 | 42 (0.4%) | 113 (1.0%) | 🟢 OK |

### Path Breakdown

| Stage | Cycles | % |
|-------|--------|---|
| ISR Entry | 12–29 | 26% |
| ISR Body | 18–55 | 49% |
| ISR Exit | 12–29 | 26% |
| **Total** | **42–113** | |

> ⚠️ 1 analysis note(s) — calls not followed, loops counted once — are listed in the full report.
> 📦 Full report, annotated disassembly and JSON metrics available in workflow artifacts.