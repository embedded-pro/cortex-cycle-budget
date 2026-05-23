# Annotated Disassembly — Control Loop

## Stage: Sensor Read

### `sensor_read`

Address: `0x00000000`–`0x0000000a` | 10 bytes | 4 instructions | 4–7 cycles

```asm
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
  0x00000000  f240 5339         1   1   movw	r3, #1337	@ 0x539
  0x00000004  4358              1   1 X muls	r0, r3
  0x00000006  1200              1   1   asrs	r0, r0, #8
  0x00000008  4770              1   4 B bx	lr
```

## Stage: Control Computation

### `control_loop`

Address: `0x00000010`–`0x00000022` | 18 bytes | 6 instructions | 6–14 cycles

```asm
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
  0x00000010  b508              1   2 M push	{r3, lr}
  0x00000012  f7ff fff5         1   4 B bl	0 <sensor_read>
  0x00000016  1a08              1   1   subs	r0, r1, r0
  0x00000018  e8bd 4008         1   2 M ldmia.w	sp!, {r3, lr}
  0x0000001c  0080              1   1   lsls	r0, r0, #2
  0x0000001e  f7ff bff4         1   4 B b.w	a <actuator_output>
```

**Calls:**
  - `sensor_read`

## Stage: Actuator Output

### `actuator_output`

Address: `0x0000000a`–`0x00000010` | 6 bytes | 2 instructions | 2–5 cycles

```asm
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
  0x0000000a  f300 000f         1   1   ssat	r0, #16, r0
  0x0000000e  4770              1   4 B bx	lr
```
