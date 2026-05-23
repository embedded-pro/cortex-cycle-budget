/* Cortex-M33 example — TrustZone-aware ISR pattern.
 *
 * The M33 inherits the M4 FPU timing but uses the v8-M security extension.
 * For static cycle analysis, this is identical to M4 in the timing model
 * (FPU costs, integer divide, exception entry overhead).
 */

#include <stdint.h>

__attribute__((noinline)) uint32_t crc32_byte(uint32_t crc, uint8_t byte) {
    crc ^= byte;
    for (int i = 0; i < 8; ++i) {
        crc = (crc >> 1) ^ ((crc & 1u) ? 0xEDB88320u : 0u);
    }
    return crc;
}

__attribute__((noinline)) uint32_t crc32(const uint8_t *data, uint32_t len) {
    uint32_t crc = 0xFFFFFFFFu;
    for (uint32_t i = 0; i < len; ++i) {
        crc = crc32_byte(crc, data[i]);
    }
    return ~crc;
}

__attribute__((noinline)) uint32_t isr_handler(const uint8_t *frame, uint32_t len) {
    return crc32(frame, len);
}

int _start(void) {
    static const uint8_t msg[] = "hello world";
    return (int)isr_handler(msg, sizeof(msg) - 1);
}
