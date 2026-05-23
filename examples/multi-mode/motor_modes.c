/* Multi-mode example — same ELF, two distinct "modes" of operation.
 *
 * Imagine a motor controller that runs different code paths depending on
 * the operating mode (e.g., sensorless vs. sensored, or current-only vs.
 * dq-control). One binary, multiple critical paths.
 */

#include <stdint.h>

__attribute__((noinline)) int32_t sensor_filter(int32_t s) {
  return (s * 7) >> 3;
}
__attribute__((noinline)) int32_t pid_loop(int32_t err) {
  static int32_t integ = 0;
  integ += err;
  return err * 4 + integ / 16;
}
__attribute__((noinline)) int32_t observer(int32_t s) {
  return s + (s >> 2) - (s >> 5);
}

/* Mode A: sensored — uses sensor_filter then pid_loop. */
__attribute__((noinline)) int32_t mode_a_step(int32_t raw, int32_t setpoint) {
  int32_t m = sensor_filter(raw);
  return pid_loop(setpoint - m);
}

/* Mode B: sensorless — uses observer then pid_loop. */
__attribute__((noinline)) int32_t mode_b_step(int32_t raw, int32_t setpoint) {
  int32_t m = observer(raw);
  return pid_loop(setpoint - m);
}

int _start(void) { return mode_a_step(10, 50) + mode_b_step(10, 50); }
