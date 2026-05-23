# Annotated Disassembly — ISR CRC32

## Stage: ISR Body

### `isr_handler`

Address: `0x00000038`–`0x0000003c` | 4 bytes | 1 instructions | 1–4 cycles

```asm
;       Addr  Bytes            Mn  Mx  Instruction
; ----------  --------------  --- ---  ----------------------------------------
  0x00000038  f7ff bff0         1   4 B b.w	1c <crc32>
```
