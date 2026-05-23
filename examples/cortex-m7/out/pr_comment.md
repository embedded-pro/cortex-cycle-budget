## 🏎️ Cycle Estimation

**Target**: `demo-h7` | **Build**: `Release` | **Clock**: 480 MHz | **Cortex**: `m7`
**Path**: FOC Kernel (FPU-heavy)

### Executive Summary

| Metric | Value |
|--------|-------|
| Estimated Cycles (min — max) | **38** — **58** |
| Total Instructions | 25 |
| Code Size | 90 bytes |
| Path Stages | 4 |

### CPU Utilization Budget

| Loop Rate | Available Cycles | Min Usage | Max Usage | Status |
|-----------|-----------------|-----------|-----------|--------|
| 20 kHz | 24000 | 38 (0.2%) | 58 (0.2%) | 🟢 OK |
| 40 kHz | 12000 | 38 (0.3%) | 58 (0.5%) | 🟢 OK |
| 100 kHz | 4800 | 38 (0.8%) | 58 (1.2%) | 🟢 OK |

### Path Breakdown

| Stage | Cycles | % |
|-------|--------|---|
| Park / Clarke | 10–13 | 22% |
| Magnitude (vsqrt.f32) | 10–13 | 22% |
| Normalize (vdiv.f32) | 8–11 | 19% |
| FOC Kernel Wrapper | 10–21 | 36% |
| **Total** | **38–58** | |

> 📦 Full report, annotated disassembly and JSON metrics available in workflow artifacts.