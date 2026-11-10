## 🏎️ Cycle Estimation

**Target**: `demo-h7` | **Build**: `Release` | **Clock**: 480 MHz
**Path**: FOC Kernel (FPU-heavy)

### Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min — max) | **44** — **62** |
| Instructions on Worst Path | 23 |
| Code Size | 90 bytes |
| Path Stages | 4 |

### CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 20 kHz | 24000 | 44 (0.2%) | 62 (0.3%) | 🟢 OK |
| 40 kHz | 12000 | 44 (0.4%) | 62 (0.5%) | 🟢 OK |
| 100 kHz | 4800 | 44 (0.9%) | 62 (1.3%) | 🟢 OK |

### Path Breakdown

| Stage | Cycles | % |
|-------|--------|---|
| Park / Clarke | 10–13 | 21% |
| Magnitude (vsqrt.f32) | 12–15 | 24% |
| Normalize (vdiv.f32) | 8–11 | 18% |
| FOC Kernel Wrapper | 14–23 | 37% |
| **Total** | **44–62** | |

> 📦 Full report, annotated disassembly and JSON metrics available in workflow artifacts.