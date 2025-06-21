`timescale 1ns / 1ps

module instruction_control_tb;

reg [31:0] instruction;
reg [21:0] Alu_resultHigh;
wire nBranch, Branch, branch_lt, branch_ge, branch_ltu, branch_geu;
wire jal, jalr;
wire MemRead, MemorIOToReg;
wire [3:0] ALUop;
wire MemWrite, ALUSrc, RegWrite, sftmd;
wire IORead, IOWrite;

instruction_control uut (
    .instruction(instruction),
    .Alu_resultHigh(Alu_resultHigh),
    .nBranch(nBranch),
    .Branch(Branch),
    .branch_lt(branch_lt),
    .branch_ge(branch_ge),
    .branch_ltu(branch_ltu),
    .branch_geu(branch_geu),
    .jal(jal),
    .jalr(jalr),
    .MemRead(MemRead),
    .MemorIOToReg(MemorIOToReg),
    .ALUop(ALUop),
    .MemWrite(MemWrite),
    .ALUSrc(ALUSrc),
    .RegWrite(RegWrite),
    .sftmd(sftmd),
    .IORead(IORead),
    .IOWrite(IOWrite)
);

task assert_eq;
    input [1023:0] msg;
    input actual;
    input expected;
    begin
        if (actual !== expected) begin
            $display("FAILED: %s | Expected: %b, Got: %b", msg, expected, actual);
            $finish;
        end else begin
            $display(" %s passed", msg);
        end
    end
endtask

initial begin
    $display("==== instruction_control Test Start ====");

    // 测试 addi: opcode = 0010011, func3 = 000
    instruction = 32'b000000000101_00000_000_00001_0010011; // addi x1, x0, 5
    Alu_resultHigh = 22'h000001; #5;
    assert_eq("addi.RegWrite", RegWrite, 1);
    assert_eq("addi.ALUSrc", ALUSrc, 1);
    assert_eq("addi.ALUop", ALUop == 4'b0000, 1);

    // 测试 or 指令（R-type）
    instruction = 32'b0000000_00010_00001_110_00011_0110011; // or x3, x1, x2
    Alu_resultHigh = 22'h000000; #5;
    assert_eq("or.RegWrite", RegWrite, 1);
    assert_eq("or.ALUop", ALUop == 4'b0011, 1);

    // 测试 sra 指令（R-type）
    instruction = 32'b0100000_00010_00001_101_00011_0110011; // sra x3, x1, x2
    #5;
    assert_eq("sra.sftmd", sftmd, 1);
    assert_eq("sra.ALUop", ALUop == 4'b0111, 1);

    // 测试 jal 指令
    instruction = 32'b00000000000000000000000001101111; // jal x0, 0
    #5;
    assert_eq("jal.jal", jal, 1);
    assert_eq("jal.RegWrite", RegWrite, 1);

    // 测试 load 指令 (lw)，访问 RAM
    instruction = 32'b00000000010000000000000010000011; // lw x0, 4(x0)
    Alu_resultHigh = 22'h000010; #5;
    assert_eq("lw.MemRead", MemRead, 1);
    assert_eq("lw.IORead", IORead, 0);
    assert_eq("lw.MemorIOToReg", MemorIOToReg, 1);

    // 测试 load 指令，访问 IO
    Alu_resultHigh = 22'h3FFFFF; #5;
    assert_eq("lw.io.IORead", IORead, 1);
    assert_eq("lw.io.MemRead", MemRead, 0);

    // 测试 store 指令（sw），访问 RAM
    instruction = 32'b0000000_00001_00010_010_00000_0100011; // sw x1, 0(x2)
    Alu_resultHigh = 22'h000001; #5;
    assert_eq("sw.MemWrite", MemWrite, 1);

    // 测试 store 指令，访问 IO
    Alu_resultHigh = 22'h3FFFFF; #5;
    assert_eq("sw.io.IOWrite", IOWrite, 1);
    assert_eq("sw.io.MemWrite", MemWrite, 0);

    // 测试 beq
    instruction = 32'b0000000_00010_00010_000_00000_1100011; // beq x2, x2
    #5;
    assert_eq("beq.Branch", Branch, 1);

    // 测试 bne
    instruction = 32'b0000000_00010_00010_001_00000_1100011; // bne
    #5;
    assert_eq("bne.nBranch", nBranch, 1);

    // 测试 blt
    instruction = 32'b0000000_00010_00010_100_00000_1100011; // blt
    #5;
    assert_eq("blt.branch_lt", branch_lt, 1);

    // 测试 jalr
    instruction = 32'b000000000000_00001_000_00000_1100111; // jalr x0, 0(x1)
    #5;
    assert_eq("jalr.jalr", jalr, 1);
    assert_eq("jalr.RegWrite", RegWrite, 1);
    assert_eq("jalr.ALUSrc", ALUSrc, 1);

    $display("==== instruction_control Test Passed ====");
    $finish;
end

endmodule
