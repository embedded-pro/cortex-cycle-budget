/* Cortex-M7 FPU example.
 *
 * Demonstrates how the M7 timing model differs from M4 for floating-point
 * sqrt and divide operations (single-cycle effective throughput on M7
 * vs. 14 cycles latency on M4 for `vsqrt.f32`).
 */

#include <stdint.h>

__attribute__((noinline)) float park_transform(float ia, float ib, float ic,
                                                float sin_theta, float cos_theta) {
    /* Clarke (3 → 2) */
    float alpha = ia;
    float beta  = (ib - ic) * 0.5773502692f;
    /* Park (2 → dq) */
    float d = alpha * cos_theta + beta * sin_theta;
    return d;
}

__attribute__((noinline)) float compute_magnitude(float d, float q) {
    /* Hot path for M7: vsqrt.f32 dominates. */
    float sum = d * d + q * q;
    float out;
    __asm__ volatile ("vsqrt.f32 %0, %1" : "=t"(out) : "t"(sum));
    return out;
}

__attribute__((noinline)) float normalize(float x, float magnitude) {
    /* Hot path for M7: vdiv.f32 dominates. */
    return x / magnitude;
}

__attribute__((noinline)) float foc_kernel(float ia, float ib, float ic,
                                            float sin_t, float cos_t) {
    float d = park_transform(ia, ib, ic, sin_t, cos_t);
    float m = compute_magnitude(d, d * 0.5f);
    return normalize(d, m);
}

int _start(void) {
    volatile float r = foc_kernel(1.0f, -0.5f, -0.5f, 0.5f, 0.866f);
    (void)r;
    return 0;
}
