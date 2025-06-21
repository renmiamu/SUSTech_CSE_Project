.text
.globl _start

_start:
    li t0, 13
    li t1, 3
    li t5, 0xfffffff0
    rem t2, t0, t1    # t2 = 12 * 3 = 36
    sw t2, 0(t5)      # 写出结果
