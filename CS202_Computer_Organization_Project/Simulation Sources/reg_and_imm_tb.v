`timescale 1ns / 1ps

module reg_and_imm_tb;

reg clk;
reg rst;
reg [31:0] inst;
reg [31:0] write_data;
reg RegWrite;
wire [31:0] read_data_1, read_data_2, imm32;

reg_and_imm uut (
    .clk(clk),
    .rst(rst),
    .inst(inst),
    .write_data(write_data),
    .RegWrite(RegWrite),
    .read_data_1(read_data_1),
    .read_data_2(read_data_2),
    .imm32(imm32)
);

// 生成时钟
initial begin
    clk = 0;
    forever #5 clk = ~clk; // 10ns clock
end

// 简单 assert 工具
task assert_eq;
    input [1023:0] msg;
    input [31:0] actual;
    input [31:0] expected;
    begin
        if (actual !== expected) begin
            $display("FAILED: %s | Expected: %h, Got: %h", msg, expected, actual);
            $finish;
        end else begin
            $display("%s passed", msg);
        end
    end
endtask

initial begin
    $display("==== reg_and_imm Simulation Start ====");

    // 初始化
    RegWrite = 0;
    write_data = 0;
    inst = 0;
    rst = 0; #12; // 触发复位，清零寄存器
    rst = 1;

    // 写寄存器 x5
    inst = 32'b000000000000_00000_000_00101_0010011; // addi x5, x0, 0
    RegWrite = 1;
    write_data = 32'h12345678;
    #10;

    // 读 rs1 = x5
    inst = 32'b000000000000_00101_000_00100_0010011; // addi x4, x5, 0
    RegWrite = 0;
    #1;
    assert_eq("Read x5", read_data_1, 32'h12345678);

    // 不应写 x0
    inst = 32'b000000000000_00000_000_00000_0010011; // addi x0, x0, 0
    RegWrite = 1;
    write_data = 32'hFFFFFFFF;
    #10;
    inst = 32'b000000000000_00000_000_00100_0010011; // addi x4, x0, 0
    RegWrite = 0;
    #1;
    assert_eq("x0 should remain zero", read_data_1, 32'h0);

    //  R-type 
    inst = 32'b0000000_00010_00001_000_00100_0110011;
    #1;
    assert_eq("R-type imm", imm32, 32'h0);

    //  I-type  (0010011)
    inst = 32'b111111111100_00001_000_00010_0010011; // addi x2, x1, -4
    #1;
    assert_eq("I-type imm", imm32, -4);

    //  S-type  (store)
    inst = 32'b1111111_00011_00010_010_00000_0100011; // sw x3, -32(x2)
    #1;
    assert_eq("S-type imm", imm32, -32);

    //  B-type 
    inst = 32'b1_000000_00010_00011_000_00000_1100011; // beq x2, x3, -4096

    #1;
    assert_eq("B-type imm", imm32, -4096);

    $display("==== reg_and_imm Simulation End ====");
    $finish;
end

endmodule
