`timescale 1ns / 1ps

module vga_test (
    input clk,       // 100MHz
    input rst,       // 高电平复位
    output [3:0] r,
    output [3:0] g,
    output [3:0] b,
    output hs,
    output vs,
    output [11:0] leds
);

    reg [3:0] s1, s2, s3, s4, s5, s6, s7, s8;
    
    always @(posedge clk or negedge rst) begin
            if (!rst) begin
                s1 <= 4'd0; s2 <= 4'd0; s3 <= 4'd0; s4 <= 4'd0;
                s5 <= 4'd0; s6 <= 4'd0; s7 <= 4'd0; s8 <= 4'd0;
            end else begin
                s1 <= 4'h1;
                s2 <= 4'h2;
                s3 <= 4'h3;
                s4 <= 4'h4;
                s5 <= 4'h5;
                s6 <= 4'h6;
                s7 <= 4'h7;
                s8 <= 4'h8;
            end
        end
vga display (
    .clk(clk),
    .rst(rst),
    .s1(s1), .s2(s2), .s3(s3), .s4(s4),
    .s5(s5), .s6(s6), .s7(s7), .s8(s8),
    .r(r), .g(g), .b(b),
    .hs(hs), .vs(vs)
);

    assign leds[11:8] = r;
    assign leds[7:4] = g;
    assign leds[3:0] = b;

endmodule
