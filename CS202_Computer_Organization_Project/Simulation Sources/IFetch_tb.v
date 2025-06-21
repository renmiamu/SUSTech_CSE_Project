`timescale 1ns / 1ps

module IFetch_tb;

reg clk;
reg rst;
reg [31:0] imm32;
reg branch_result;
reg zero;
reg jal;
reg jalr;
reg [31:0] Alu_result;
wire [31:0] instruction;
wire [31:0] pc_out;

IFetch uut (
    .clk(clk),
    .rst(rst),
    .imm32(imm32),
    .branch_result(branch_result),
    .zero(zero),
    .jal(jal),
    .jalr(jalr),
    .Alu_result(Alu_result),
    .instruction(instruction),
    .pc_out(pc_out)
);

initial begin
    clk = 0;
    forever #5 clk = ~clk;  // 10ns 一个周期
end

task reset_control;
begin
    imm32 = 0;
    branch_result = 0;
    jal = 0;
    jalr = 0;
    Alu_result = 0;
    zero = 0;
end
endtask

initial begin
    $display("==== IFetch Simulation Start ====");
    $monitor("Time: %0t | pc_out: %h | instruction: %h", $time, pc_out, instruction);

    reset_control();
    rst = 0; #12;
    rst = 1; #10;

    // 模拟正常 pc + 4 增长
    #10;
    #10;
    #10;

    // 模拟 jal 跳转 (pc + imm32)
    reset_control();
    jal = 1; imm32 = 32'd8; #10;
    jal = 0; #10;

    // 模拟分支跳转
    reset_control();
    branch_result = 1; imm32 = 32'd12; #10;
    branch_result = 0; #10;

    // 模拟 jalr 跳转
    reset_control();
    jalr = 1; Alu_result = 32'd40; #10;
    jalr = 0; #10;

    // 正常连续运行几拍
    #40;

    $display("==== IFetch Simulation End ====");
    $finish;
end

endmodule
