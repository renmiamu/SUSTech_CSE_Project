module cpuclk (
    input clk_in1,           // 内部100MHz主时钟
    output reg clk_out1,     // 分频输出1：周期 = 10000，频率 ≈ 10kHz
    output reg clk_out2      // 新增输出：10MHz
);

    parameter period1 = 10000;  // clk_out1 分频系数（输出10kHz）
    parameter period2 = 10;     // clk_out2 分频系数（输出10MHz）

    reg [24:0] cnt1 = 0;
    reg [3:0] cnt2 = 0;

    always @(posedge clk_in1) begin
        // clk_out1 分频逻辑
        if (cnt1 == (period1 >> 1) - 1) begin
            cnt1 <= 0;
            clk_out1 <= ~clk_out1;
        end else begin
            cnt1 <= cnt1 + 1;
        end

        // clk_out2 分频逻辑
        if (cnt2 == (period2 >> 1) - 1) begin
            cnt2 <= 0;
            clk_out2 <= ~clk_out2;
        end else begin
            cnt2 <= cnt2 + 1;
        end
    end
endmodule

//module cpuclk (
//    input wire clk_in1,
//    output wire clk_out1
//);
    
//    reg clk_div;
//    initial clk_div = 0;
//    always #(22) clk_div = ~clk_div;
//    assign clk_out1 = clk_div;
//    endmodule