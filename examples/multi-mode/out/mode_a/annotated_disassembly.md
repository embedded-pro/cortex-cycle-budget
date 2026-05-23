# Annotated Disassembly — Mode A — Sensored

## Stage: Sensor Filter

### `sensor_filter`

Address: `0x00000000`–`0x00000008` | 8 bytes | 3 instructions | 3–6 cycles

```asm
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
  0x00000000  ebc0 00c0         1   1   rsb	r0, r0, r0, lsl #3
  0x00000004  10c0              1   1   asrs	r0, r0, #3
  0x00000006  4770              1   4 B bx	lr
```

## Stage: PID Loop

### `pid_loop`

Address: `0x00000008`–`0x00000024` | 28 bytes | 12 instructions | 15–18 cycles

```asm
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
  0x00000008  4a05              2   2 M ldr	r2, [pc, #20]	@ (20 <pid_loop+0x18>)
  0x0000000a  6813              2   2 M ldr	r3, [r2, #0]
  0x0000000c  4403              1   1   add	r3, r0
  0x0000000e  6013              2   2 M str	r3, [r2, #0]
  0x00000010  2b00              1   1   cmp	r3, #0
  0x00000012  bfb8              1   1   it	lt
  0x00000014  330f              1   1   addlt	r3, #15
  0x00000016  0080              1   1   lsls	r0, r0, #2
  0x00000018  eb00 1023         1   1   add.w	r0, r0, r3, asr #4
  0x0000001c  4770              1   4 B bx	lr
  0x0000001e  bf00              1   1   nop	
  0x00000020  00001064          1   1   .word	0x00001064
```

## Stage: Mode A Wrap

### `mode_a_step`

Address: `0x0000002e`–`0x0000003e` | 16 bytes | 5 instructions | 5–13 cycles

```asm
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
  0x0000002e  b508              1   2 M push	{r3, lr}
  0x00000030  f7ff ffe6         1   4 B bl	0 <sensor_filter>
  0x00000034  e8bd 4008         1   2 M ldmia.w	sp!, {r3, lr}
  0x00000038  1a08              1   1   subs	r0, r1, r0
  0x0000003a  f7ff bfe5         1   4 B b.w	8 <pid_loop>
```

**Calls:**
  - `sensor_filter`
