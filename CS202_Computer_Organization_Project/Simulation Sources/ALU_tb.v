`timescale 1ns / 1ps

module ALU_tb;
    reg [3:0] ALUop;
    reg ALUSrc;
    reg sftmd;
    reg Branch, nBranch, Branch_lt, Branch_ge, Branch_ltu, Branch_geu;
    reg [31:0] read_data_1;
    reg [31:0] read_data_2;
    reg [31:0] imm32;

    wire [31:0] Alu_result;
    wire zero;
    wire branch_result;

    ALU uut (
        .ALUop(ALUop),
        .ALUSrc(ALUSrc),
        .sftmd(sftmd),
        .Branch(Branch),
        .nBranch(nBranch),
        .Branch_lt(Branch_lt),
        .Branch_ge(Branch_ge),
        .Branch_ltu(Branch_ltu),
        .Branch_geu(Branch_geu),
        .read_data_1(read_data_1),
        .read_data_2(read_data_2),
        .imm32(imm32),
        .Alu_result(Alu_result),
        .zero(zero),
        .branch_result(branch_result)
    );

    task reset_control;
    begin
        ALUop = 4'b0000;
        ALUSrc = 0;
        sftmd = 0;
        Branch = 0;
        nBranch = 0;
        Branch_lt = 0;
        Branch_ge = 0;
        Branch_ltu = 0;
        Branch_geu = 0;
    end
    endtask

    initial begin
        $display("==== ALU Testbench Start ====");

        // add
        reset_control(); ALUop = 4'b0000;
        read_data_1 = 32'd1; read_data_2 = 32'd2; #10;
        if (Alu_result !== 32'd3) $fatal("[add] failed");

        // sub
        reset_control(); ALUop = 4'b0001;
        read_data_1 = 32'd5; read_data_2 = 32'd3; #10;
        if (Alu_result !== 32'd2) $fatal("[sub] failed");

        // xor
        reset_control(); ALUop = 4'b0010;
        read_data_1 = 32'hAAAA_AAAA; read_data_2 = 32'h5555_5555; #10;
        if (Alu_result !== 32'hFFFF_FFFF) $fatal("[xor] failed");

        // or
        reset_control(); ALUop = 4'b0011;
        read_data_1 = 32'h0000_FF00; read_data_2 = 32'h00FF_0000; #10;
        if (Alu_result !== 32'h00FF_FF00) $fatal("[or] failed");

        // and
        reset_control(); ALUop = 4'b0100;
        read_data_1 = 32'hFFFF_FFFF; read_data_2 = 32'h0F0F_0F0F; #10;
        if (Alu_result !== 32'h0F0F_0F0F) $fatal("[and] failed");

        // sll
        reset_control(); ALUop = 4'b0101; sftmd = 1;
        read_data_1 = 32'd1; read_data_2 = 32'd3; #10;
        if (Alu_result !== 32'd8) $fatal("[sll] failed");

        // srl
        reset_control(); ALUop = 4'b0110; sftmd = 1;
        read_data_1 = 32'd16; read_data_2 = 32'd2; #10;
        if (Alu_result !== 32'd4) $fatal("[srl] failed");

        // sra
        reset_control(); ALUop = 4'b0111; sftmd = 1;
        read_data_1 = -32'sd16; read_data_2 = 32'd2; #10;
        if (Alu_result !== -32'sd4) $fatal("[sra] failed");

        // addi
        reset_control(); ALUop = 4'b0000; ALUSrc = 1;
        read_data_1 = 32'd10; imm32 = 32'd5; #10;
        if (Alu_result !== 32'd15) $fatal("[addi] failed");

        // xori
        reset_control(); ALUop = 4'b0001; ALUSrc = 1;
        read_data_1 = 32'hFFFF_0000; imm32 = 32'h0000_FFFF; #10;
        if (Alu_result !== 32'hFFFF_FFFF) $fatal("[xori] failed");

        // ori
        reset_control(); ALUop = 4'b0010; ALUSrc = 1;
        read_data_1 = 32'h1234_0000; imm32 = 32'h0000_00FF; #10;
        if (Alu_result !== 32'h1234_00FF) $fatal("[ori] failed");

        // andi
        reset_control(); ALUop = 4'b0011; ALUSrc = 1;
        read_data_1 = 32'hFFFF_00FF; imm32 = 32'h0000_00F0; #10;
        if (Alu_result !== 32'h0000_00F0) $fatal("[andi] failed");

        // slli
        reset_control(); ALUop = 4'b0100; ALUSrc = 1; sftmd = 1;
        read_data_1 = 32'd1; imm32 = 32'd5; #10;
        if (Alu_result !== 32'd32) $fatal("[slli] failed");

        // srai
        reset_control(); ALUop = 4'b0101; ALUSrc = 1; sftmd = 1;
        read_data_1 = -32'sd16; imm32 = 32'd2; #10;
        if (Alu_result !== -32'sd4) $fatal("[srai] failed");

        // srli
        reset_control(); ALUop = 4'b0110; ALUSrc = 1; sftmd = 1;
        read_data_1 = 32'd16; imm32 = 32'd2; #10;
        if (Alu_result !== 32'd4) $fatal("[srli] failed");

        // beq
        reset_control(); Branch = 1;
        read_data_1 = 32'd5; read_data_2 = 32'd5; #10;
        if (branch_result !== 1'b1) $fatal("[beq] failed");

        // bne
        reset_control(); nBranch = 1;
        read_data_1 = 32'd5; read_data_2 = 32'd3; #10;
        if (branch_result !== 1'b1) $fatal("[bne] failed");

        // blt
        reset_control(); Branch_lt = 1;
        read_data_1 = -32'sd1; read_data_2 = 32'd1; #10;
        if (branch_result !== 1'b1) $fatal("[blt] failed");

        // bge
        reset_control(); Branch_ge = 1;
        read_data_1 = 32'd5; read_data_2 = 32'd3; #10;
        if (branch_result !== 1'b1) $fatal("[bge] failed");

        // bltu
        reset_control(); Branch_ltu = 1;
        read_data_1 = 32'd2; read_data_2 = 32'd3; #10;
        if (branch_result !== 1'b1) $fatal("[bltu] failed");

        // bgeu
        reset_control(); Branch_geu = 1;
        read_data_1 = 32'd5; read_data_2 = 32'd5; #10;
        if (branch_result !== 1'b1) $fatal("[bgeu] failed");

        $display("==== All ALU Tests Passed ====");
        $finish;
    end

endmodule
