.text
.globl _start

_start:
    li t1, 1
    addi t1, t1, 1
    auipc t0, 0x12345     # t0 = PC + (0x12345 << 12) = PC + 0x12345000

    li t2, 0xfffffff0     # 数码管显示地址
    sw t0, 0(t2)          # 输出 t0 到数码管

loop:
    j loop                # 保持循环
