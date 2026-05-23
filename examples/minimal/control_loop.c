/* Minimal critical-path example for ARM Cortex-M4.
 *
 * Models a tiny "control loop" with two stages: a sensor read and an
 * actuator output, both invoked from a top-level loop function.
 */

#include <stdint.h>

__attribute__((noinline)) int32_t sensor_read(int32_t raw) {
  /* Apply a fixed-point gain. */
  return (raw * 1337) >> 8;
}

__attribute__((noinline)) int32_t actuator_output(int32_t cmd) {
  /* Saturate to int16 range. */
  if (cmd > 32767)
    return 32767;
  if (cmd < -32768)
    return -32768;
  return cmd;
}

__attribute__((noinline)) int32_t control_loop(int32_t raw, int32_t setpoint) {
  int32_t measured = sensor_read(raw);
  int32_t error = setpoint - measured;
  int32_t cmd = error * 4;
  return actuator_output(cmd);
}

int _start(void) { return control_loop(100, 200); }
