# Cortex-M variant notes

Quick reference for the four supported variants. For full cycle tables see
[timing-model.md](timing-model.md).

## Cortex-M0 (Armv6-M)

- **No hardware divide** — `sdiv`/`udiv` are absent; division goes through
  `__aeabi_uidiv`/`__aeabi_idiv` helpers. The tool reports `(0, 0)` for the
  hardware mnemonics; charges show up under the helper function instead.
- **No FPU** — any `v*` instructions in your binary are extremely suspicious
  and probably indicate a binary built for the wrong target.
- **No DSP / SIMD** — `smla*`, `qadd`, etc. are unavailable.
- **Multiply** is 1 cycle in the `M0+` core; some early M0 implementations
  take up to 32 cycles. The table conservatively models the slower case.
- **Exception entry/exit** is fixed at 16 cycles each.

Suggested clock: typically 8–48 MHz.

## Cortex-M4 (Armv7E-M)

The **baseline** variant in this tool. All other variants are deltas on top.

- **FPv4-SP** single-precision FPU. `vsqrt.f32` and `vdiv.f32` cost
  **14 cycles** each (latency).
- Hardware integer divide: **2–12 cycles**.
- DSP extension (`smla*`, `q*`, packed ops) supported.
- Exception entry: **12 cycles** (FPU-disabled) or up to **29** (FPU lazy
  stacking, worst case).

Suggested clock: typically 120–180 MHz.

## Cortex-M7 (Armv7E-M)

- **FPv5-SP-D16** (or FPv5-D16 with double-precision) FPU. `vsqrt.f32` and
  `vdiv.f32` drop to **7 cycles** (ARM DDI 0489F §7.5).
- Hardware integer divide: **2–7 cycles** (faster than M4).
- **Dual-issue** of integer + FPU pairs in many cases. *Not yet modeled here.*
  A `DUAL_ISSUE_MIN_SCALE = {"m7": 0.85}` constant is defined for future use.
- I-cache and D-cache present — **completely unmodeled** by this static
  analyzer. Real cycle counts can deviate significantly on cache misses.

Suggested clock: typically 216–600 MHz.

> ⚠️ M7 estimates from this tool tend to be **upper bounds**. For
> cache-resident hot paths, real measurements are often lower.

## Cortex-M33 (Armv8-M Mainline)

- **FPv5-SP-D16** FPU. Cycle costs match M4 for FPU operations (no `vsqrt`
  speedup like M7).
- Hardware integer divide: **2–12 cycles**, same as M4.
- DSP extension (optional, present on most parts).
- **TrustZone**: secure ↔ non-secure transitions add overhead **not modeled**
  here (extra 3+ cycles per SG/BXNS).
- MPU and security attribution can introduce wait states **not modeled**.

Suggested clock: typically 100–160 MHz.

---

## Picking the right `--cortex` value

| Your device family            | Use `--cortex`  |
| ----------------------------- | --------------- |
| STM32F0, STM32G0, nRF51       | `m0`            |
| STM32F4, TM4C, SAM4           | `m4`            |
| STM32F7, STM32H7, MIMXRT      | `m7`            |
| STM32L5, STM32U5, nRF53/91    | `m33`           |
