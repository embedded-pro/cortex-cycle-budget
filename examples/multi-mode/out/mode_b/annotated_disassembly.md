# Annotated Disassembly — Mode B — Sensorless

## Stage: Observer

### `observer`

Address: `0x00000024`–`0x0000002e` | 10 bytes | 3 instructions | 3–6 cycles

```asm
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
  0x00000024  eb00 03a0         1   1   add.w	r3, r0, r0, asr #2
  0x00000028  eba3 1060         1   1   sub.w	r0, r3, r0, asr #5
  0x0000002c  4770              1   4 B bx	lr
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

## Stage: Mode B Wrap

### `mode_b_step`

Address: `0x0000003e`–`0x0000004e` | 16 bytes | 5 instructions | 5–13 cycles

```asm
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
  0x0000003e  b508              1   2 M push	{r3, lr}
  0x00000040  f7ff fff0         1   4 B bl	24 <observer>
  0x00000044  e8bd 4008         1   2 M ldmia.w	sp!, {r3, lr}
  0x00000048  1a08              1   1   subs	r0, r1, r0
  0x0000004a  f7ff bfdd         1   4 B b.w	8 <pid_loop>
```

**Calls:**
  - `observer`
