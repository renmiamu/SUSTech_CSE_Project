.text
.globl _start

_start:
    li t0, 12
    li t1, 3
    li t5, 0xfffffff0
    div t2, t0, t1    # t2 = 12 * 3 = 36
    sw t2, 0(t5)      # 写出结果