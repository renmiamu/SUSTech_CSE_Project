.data
newline: .asciiz "\n"

.text
.globl _start
_start:
    li t0, 0xB
    slli t1, t0, 4
    mv t2, t1

    li t3, 0x13
    li t4, 7

crc_loop:
    blt t4, 4, crc_done
    slli t5, 1, t4
    and t6, t2, t5
    beqz t6, skip_xor
    slli t7, t3, t4 - 4
    xor t2, t2, t7
skip_xor:
    addi t4, t4, -1
    j crc_loop

crc_done:
    andi t2, t2, 0xF
    slli t0, t0, 4
    or t1, t0, t2

    mv a0, t1
    li a7, 1
    ecall

    li a7, 4
    la a0, newline
    ecall

    li a7, 10
    ecall
