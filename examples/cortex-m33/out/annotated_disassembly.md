# Annotated Disassembly — ISR CRC32

## Stage: ISR Body

### `crc32`

Address: `0x0000001c`–`0x00000038` | 28 bytes | 11 instructions | worst path 11 instructions, 34 cycles

```asm
; '>' marks the instructions on the worst path
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
> 0x0000001c  b538              5   5 M push	{r3, r4, r5, lr}
> 0x0000001e  4604              1   1   mov	r4, r0
> 0x00000020  1845              1   1   adds	r5, r0, r1
> 0x00000022  f04f 30ff         1   1   mov.w	r0, #4294967295	@ 0xffffffff
> 0x00000026  42ac              1   1   cmp	r4, r5
> 0x00000028  d101              1   4 B bne.n	2e <crc32+0x12>
> 0x0000002a  43c0              1   1   mvns	r0, r0
> 0x0000002c  bd38              6   8 M pop	{r3, r4, r5, pc}
> 0x0000002e  f814 1b01         2   2 M ldrb.w	r1, [r4], #1
> 0x00000032  f7ff ffe5         1   4 B bl	0 <crc32_byte>
> 0x00000036  e7f6              1   4 B b.n	26 <crc32+0xa>
```

**Calls:**
  - `crc32_byte`

### `crc32_byte`

Address: `0x00000000`–`0x0000001c` | 28 bytes | 10 instructions | worst path 10 instructions, 17 cycles

```asm
; '>' marks the instructions on the worst path
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
> 0x00000000  2308              1   1   movs	r3, #8
> 0x00000002  4048              1   1   eors	r0, r1
> 0x00000004  4904              2   2 M ldr	r1, [pc, #16]	@ (18 <crc32_byte+0x18>)
> 0x00000006  f010 0201         1   1   ands.w	r2, r0, #1
> 0x0000000a  bf18              1   1   it	ne
> 0x0000000c  460a              1   1   movne	r2, r1
> 0x0000000e  3b01              1   1   subs	r3, #1
> 0x00000010  ea82 0050         1   1   eor.w	r0, r2, r0, lsr #1
> 0x00000014  d1f7              1   4 B bne.n	6 <crc32_byte+0x6>
> 0x00000016  4770              1   4 B bx	lr
  0x00000018  edb88320          0   0   .word	0xedb88320
```

### `isr_handler`

Address: `0x00000038`–`0x0000003c` | 4 bytes | 1 instructions | worst path 1 instructions, 4 cycles

```asm
; '>' marks the instructions on the worst path
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
> 0x00000038  f7ff bff0         1   4 B b.w	1c <crc32>
```
