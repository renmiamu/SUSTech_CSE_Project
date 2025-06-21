.text
.globl _start
_start:
    li s3, 0x00001000         # Stack pointer
    li t6, 0                  # Zero for comparison
    li t5, -1                 # -1 for tests               
    li s11, 0xffffffe8       # 数码�?
    li s10, 0xffffffc2       # led
    sw t6, 8(s11)             # Turn off LED

init:
    jal switchjudge

    sw zero, 8(s11)            
    sw zero 0(s10)	      # Clear LED again
    li t1, 0xfffffff7         # Get test case index from switch (low 3 bits)
    lw a1, 0(t1)

    beq a1, t6, case0
    addi a1, a1, -1
    beq a1, t6, case1
    addi a1, a1, -1
    beq a1, t6, case2
    addi a1, a1, -1
    beq a1, t6, case3
    addi a1, a1, -1
    beq a1, t6, case4
    addi a1, a1, -1
    beq a1, t6, case5
    addi a1, a1, -1
    beq a1, t6, case6
    addi a1, a1, -1
    beq a1, t6, case7
    jal init

# case0: 输入 a �? b�?
case0:
    # Input a
    jal switchjudge
    li s1, 0xfffffff9
    li s2, 0xfffffff5
    lw t2, 0(s1)
    sw t2, 0(s10)        # Show a

    # Input b
    jal switchjudge
    lw t3, 0(s2)
    sw t3, 0(s10)        # Overwrite LED with b

    jal init

# case1: 输入 a 并压�?
case1:
    jal switchjudge
    li t1, 0xfffffff5
    lb t2, 0(t1)
    sw t2, 8(s11)
    sw t2, 0(s3)
    jal init

# case2: 输入 b 并压�?
case2:
    jal switchjudge
    li t1, 0xfffffff9
    lbu t3, 0(t1)
    sw t3, 8(s11)
    sw t3, 4(s3)
    jal init

# case3: beq 判断 a == b
case3:
    lw a5, 0(s3)
    lw a6, 4(s3)
    beq a5, a6, LEDcase3
    sw zero, 0(s10)
    jal init
LEDcase3:
    addi a7, zero,0xff
    sw a7, 0(s10)
    jal init

# case4: blt a < b (signed)
case4:
    lw a5, 0(s3)
    lw a6, 4(s3)
    blt a5, a6, LEDcase4
    sw zero, 0(s10)
    jal init
LEDcase4:
     addi a7, zero,0xff
    sw a7, 0(s10)
    jal init

# case5: bltu a < b (unsigned)
case5:
    lw a5, 0(s3)
    lw a6, 4(s3)
    bltu a5, a6, LEDcase5
    sw zero, 0(s10)
    jal init
LEDcase5:
    addi a7, zero,0xff
    sw a7, 0(s10)
    jal init

# case6: slt a < b (signed)
case6:
    lw a5, 0(s3)
    lw a6, 4(s3)
    slt t0, a5, a6
    bne t0, x0, LEDcase6
    sw zero, 0(s10)
    jal init
LEDcase6:
    addi a7, zero,0xff
    sw a7, 0(s10)
    jal init

# case7: sltu a < b (unsigned)
case7:
    lw a5, 0(s3)
    lw a6, 4(s3)
    sltu t0, a5, a6
    bne t0, x0, LEDcase7
    sw zero, 0(s10)
    jal init
LEDcase7:
    addi a7, zero,0xff
    sw a7, 0(s10)
    jal init

# switchjudge: 等待按钮按下+释放
switchjudge:
    li t1, 0xffffff00         # 按钮地址
    lw t2, 0(t1)
    beq t2, x0, switchjudge
wait_release:
    lw t2, 0(t1)
    bne t2, x0, wait_release
    jr ra
