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
