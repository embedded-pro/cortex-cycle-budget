# Annotated Disassembly — FOC Kernel (FPU-heavy)

## Stage: Park / Clarke

### `park_transform`

Address: `0x00000000`–`0x00000020` | 32 bytes | 9 instructions | 10–13 cycles

```asm
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
  0x00000000  ee70 0ac1         1   1 F vsub.f32	s1, s1, s2
  0x00000004  eddf 7a05         2   2 M vldr	s15, [pc, #20]	@ 1c <park_transform+0x1c>
  0x00000008  ee60 0aa7         1   1 F vmul.f32	s1, s1, s15
  0x0000000c  ee60 0aa1         1   1 F vmul.f32	s1, s1, s3
  0x00000010  eee0 0a02         1   1 F vfma.f32	s1, s0, s4
  0x00000014  eeb0 0a60         1   1 F vmov.f32	s0, s1
  0x00000018  4770              1   4 B bx	lr
  0x0000001a  bf00              1   1   nop	
  0x0000001c  3f13cd3a          1   1   .word	0x3f13cd3a
```

## Stage: Magnitude (vsqrt.f32)

### `compute_magnitude`

Address: `0x00000020`–`0x0000002e` | 14 bytes | 4 instructions | 10–13 cycles

```asm
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
  0x00000020  ee60 0aa0         1   1 F vmul.f32	s1, s1, s1
  0x00000024  eee0 0a00         1   1 F vfma.f32	s1, s0, s0
  0x00000028  eeb1 0ae0         7   7 F vsqrt.f32	s0, s1
  0x0000002c  4770              1   4 B bx	lr
```

## Stage: Normalize (vdiv.f32)

### `normalize`

Address: `0x0000002e`–`0x00000034` | 6 bytes | 2 instructions | 8–11 cycles

```asm
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
  0x0000002e  ee80 0a20         7   7 F vdiv.f32	s0, s0, s1
  0x00000032  4770              1   4 B bx	lr
```

## Stage: FOC Kernel Wrapper

### `foc_kernel`

Address: `0x00000034`–`0x0000005a` | 38 bytes | 10 instructions | 10–21 cycles

```asm
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
  0x00000034  b508              1   2 M push	{r3, lr}
  0x00000036  f7ff ffe3         1   4 B bl	0 <park_transform>
  0x0000003a  eef6 0a00         1   1 F vmov.f32	s1, #96	@ 0x3f000000  0.5
  0x0000003e  eef0 7a40         1   1 F vmov.f32	s15, s0
  0x00000042  ee60 0a20         1   1 F vmul.f32	s1, s0, s1
  0x00000046  f7ff ffeb         1   4 B bl	20 <compute_magnitude>
  0x0000004a  eef0 0a40         1   1 F vmov.f32	s1, s0
  0x0000004e  eeb0 0a67         1   1 F vmov.f32	s0, s15
  0x00000052  e8bd 4008         1   2 M ldmia.w	sp!, {r3, lr}
  0x00000056  f7ff bfea         1   4 B b.w	2e <normalize>
```

**Calls:**
  - `park_transform`
  - `compute_magnitude`
