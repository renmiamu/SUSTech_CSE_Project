module IFetch (
    input clk,
    input rst,
    input [31:0] imm32,
    input branch_result,
    input zero,
    input jal,
    input jalr,
    input [31:0] Alu_result,

    // UART programmer ports
    input upg_rst,
    input upg_clk,
    input upg_wen_o,
    input [14:0] upg_adr_o,    // 高位为 program/data 区分
    input [31:0] upg_dat_o,
    input upg_done_o,

    output wire [31:0] instruction,
    output reg [31:0] pc_out,
    output reg [31:0] pc_now
);

    // Program Counter
    reg [31:0] pc;
    reg [31:0] next_pc;
    wire [31:0] pc_plus_4 = pc + 4;
    wire [31:0] pc_minus_4 = pc;     

    // CPU 正常运行模式 or UART 编程模式
    wire kickOff = upg_rst | (~upg_rst & upg_done_o);

    // programrom IP 实例化
    prgrom instmem (
        .clka   (kickOff ? clk           : upg_clk),                 // 正常模式用 CPU 时钟，UART 模式用编程时钟
        .addra  (kickOff ? pc[15:2]      : upg_adr_o[13:0]),         // 取指地址或 UART 写地址
        .dina   (kickOff ? 32'h00000000  : upg_dat_o),               // 写数据（正常模式无效）
        .wea    (kickOff ? 1'b0          : (upg_wen_o & ~upg_adr_o[14])), // 仅在 UART 模式下且写的是 program 区
        .douta  (instruction)                                        // 指令输出
    );

    // 计算下一条指令地址
    always @(*) begin
        if (jalr) begin
            next_pc = Alu_result;
        end else if (jal || branch_result) begin
            next_pc = pc + imm32;
        end else begin
            next_pc = pc_plus_4;
        end
    end

    // 同步更新 PC
    always @(negedge clk or negedge rst) begin
        if (!rst) begin
            pc <= 32'b0;
        end else if (kickOff) begin
            pc <= next_pc;
        end
    end

    // PC+4 输出
    always @(negedge clk or negedge rst) begin
        if (!rst) begin
            pc_out <= 32'b0;
        end else if (kickOff) begin
            pc_out <= pc_plus_4;
        end
    end
    
    always @(negedge clk or negedge rst) begin
        if (!rst) begin
            pc_now <= 32'b0;
        end else if (kickOff) begin
            pc_now <= pc_minus_4;
        end
    end
endmodule
