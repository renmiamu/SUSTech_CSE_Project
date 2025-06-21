.text
.globl _start


_start:
    li s3, 0x00001000                  # memory
    li sp, 0x00002000
    li s11, 0xfffffff0
    li s10, 0xffffffc2
    li s9,  0xffffffc4
    li s8,  0xffffffc6
    sw zero, 0(s11)
init:
    jal switchjudge

    sw zero, 0(s11)
    sw zero, 0(s10)	      # Clear LED again
    li t1, 0xfffffff7             # SWITCH_CASE_ADDR
    lw a1, 0(t1)                  # 读取测试编号

    beq a1, zero, case0
    addi a1, a1, -1
    beq a1, zero, case1
    addi a1, a1, -1
    beq a1, zero, case2
    addi a1, a1, -1
    beq a1, zero, case3
    addi a1, a1, -1
    beq a1, zero, case4
    addi a1, a1, -1
    beq a1, zero, case5
    addi a1, a1, -1
    beq a1, zero, case6
    addi a1, a1, -1
    beq a1, zero, case7
    jal init

case0: #反转
    jal switchjudge
    li t1, 0xfffffff9
    lw t2, 0(t1)
    jal bit_reverse
    sw t2, 0(s10)        # ??修改为LED_ADDR
    jal init


case1: # 回文????
    jal switchjudge
    li t1, 0xfffffff9
    lw t2, 0(t1)
    mv s0, t2
    jal bit_reverse
    bne t2, s0, not_palindrome
    li t4, 1
    sw t4, 0(s10)   #??修改为led地址
    jal init
not_palindrome:
    sw zero, 0(s10)  #??修改为led地址
    j init

case2:
    # 第一个浮点数输入
    jal switchjudge          # 等待确认
    li t2, 0xfffffff9        # SWITCH_DATA_ADDR
    lw t3, 0(t2)             # t2 = 输入的高8??
    sw t3, 0(s3)        # 存储浮点数到 memory[a]

    jal decode_float12

    srli a0, a0, 4
    beqz t0, print_pos_a
    sw a0, 0(s8)

           # 同步显示到数码管a
input_b:
    # 第二个浮点数输入
    jal switchjudge
    li t2, 0xfffffff9
    lw t3, 0(t2)
    sw t3, 4(s3)        # 存储浮点数到 memory[b]

    jal decode_float12

    srli a0, a0, 4
    beqz t0, print_pos_b
    sw a0, 0(s8)
    neg a0, a0
    #beq t0,s5, print_neg_b
                 # 同步显示?? LED 或数码管b
    jal init
decode_float12:
    andi t3, t3, 0xFF         # ????????8λ
    srli t0, t3, 7            # ????λ S
    andi t1, t3, 0x70
    srli t1, t1, 4            # t1 = e_raw
    li t4, 3
    sub t1, t1, t4            # E = e_raw - 3

    andi t2, t3, 0x0F         # t2 = M??4λβ????
    li t5, 16
    add a0, t2, t5            # a0 = 16 + M ?? ??? 1 + M/16

    bgez t1, shift_left
    neg t6, t1
    srl a0, a0, t6            # ???? E ?Σ????????
    j done

shift_left:
    sll a0, a0, t1            # ???? E ?Σ????????

done:
    jr ra

print_neg_a:
    sw a0, 0(s8)
    neg a0, a0
    j input_b

print_pos_a:
    sw a0, 0(s9)
    j input_b

print_neg_b:
    sw a0, 0(s8)
    neg a0, a0
    j init

print_pos_b:
    sw a0, 0(s9)
    j init

case3:
    #jal switchjudge
    lw t3, 0(s3)
    jal decode_float12
    srli a0, a0, 4
    beqz t0, pos_a
    neg a0, a0
    mv s4, a0

cal_b:
    lw t3, 4(s3)
    jal decode_float12
    srli a0, a0, 4
    beqz t0, pos_b
    neg a0, a0
    add s4, s4, a0

    bltz s4, print_neg
    sw s4, 0(s9)
    j init

pos_a:
    mv s4, a0
    j cal_b

pos_b:
    add s4, s4, a0
    bltz s4, print_neg
    sw s4, 0(s9)
    j init
print_neg:
    neg s4, s4
    sw s4, 0(s8)
    j init

case4:
    jal switchjudge
    li t1, 0xfffffff9
    lw t2, 0(t1)         # 从switch读取??
    andi t2, t2, 0xF     # 提取??4位原始数??
    mv s1, t2            # 保存原始数据
    slli s1, s1, 4       # t3 = 原始数据 << 4 （准备拼接）

    jal crc4_calc        # t2 输入：原始数据，输出：CRC??

    or t4, s1, t2        # 拼接结果
    sw t4, 0(s10)        # 输出到LED
    jal init

# ===== CRC-4 多项式除法，输入: t2 = 原始数据 =====
crc4_calc:
    slli t2, t2, 4
    li   t3, 0x13
    li   t4, 4
crc_loop:
    srli t5, t2, 7
    beqz t5, skip_xor
    slli t6, t3, 3
    xor  t2, t2, t6
skip_xor:
    slli t2, t2, 1
    addi t4, t4, -1
    bnez t4, crc_loop
    srli t2, t2, 4
    andi t2, t2, 0xF
    jr   ra

case5:
    jal switchjudge
    li t1, 0xfffffff9
    lw t2, 0(t1)          # 读取输入数据??8位）

    mv t3, t2             # 备份原始数据（含CRC??
    jal crc4_check        # 校验 CRC：结果保存在 t2

    bnez t2, crc_fail     # 如果余数??0 ?? 校验失败

    li t4, 1
    sw t4, 0(s10)         # 校验通过 ?? 点亮LED
    jal init

crc_fail:
    sw zero, 0(s10)       # 校验失败 ?? 熄灭LED
    jal init

# 输入：t2 = 原始数据（含CRC??
# 输出：t2 = ??终CRC余数（若??0 ?? 校验成功??
crc4_check:
    li t3, 0x13           # 多项?? 0b10011
    li t4, 8              # 处理8??

crc_check_loop:
    srli t5, t2, 7         # 提取??高位
    beqz t5, crc_skip

    slli t6, t3, 3        # t6 = 多项式左??3位，与数据对??
    xor t2, t2, t6        # 异或操作

crc_skip:
    slli t2, t2, 1
    addi t4, t4, -1
    bnez t4, crc_check_loop

    srli t2, t2, 4        # 取最终余数（??4位）
    andi t2, t2, 0xF
    jr ra



case6:
    lui t1, 0x12345      # t0 = 0x12345000
    sw t1, 0(s11)        # 输出高位?? LED
    jal init



case7:
       # --------- JAL 测试 ---------
    li a0, 0x1
    jal ra, jal_target        # 跳转到 jal_target，ra = 当前 PC + 4
    li a0, 0xf        # 若跳转失败执行此行（错误路径，a0 = 错误值）

    j after_jal

jal_target:
               # 正确执行路径
    sw a0, 0(s11)             # 输出 a0 = 0xDEAD 到 LED 或数码管地址 0
   jal switchjudge

after_jal:

    # --------- JALR 测试 ---------
    li a1, 0x2
    la t0, jalr_target        # t0 = jalr_target 地址（若不支持 la，请手动展开）
    jalr ra, 0(t0)            # 跳转到 jalr_target

    li a1, 0xf         # 若跳转失败执行此行（错误路径）

jalr_target:
    sw a1, 0(s11)             # 输出 a1 = 0xBEEF 到 LED 或数码管地址 4
    j init





bit_reverse:
    mv t3, zero
    li t4, 8
rev_loop:
    slli t3, t3, 1
    andi t5, t2, 1
    or t3, t3, t5
    srli t2, t2, 1
    addi t4, t4, -1
    bnez t4, rev_loop
    mv t2, t3
    jr ra



switchjudge:
    li t1, 0xffffff00
    lw t2, 0(t1)
    beq t2, zero, switchjudge
wait_release:
    lw t2, 0(t1)
    bne t2, zero, wait_release
    jr ra
