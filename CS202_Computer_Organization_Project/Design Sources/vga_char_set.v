`timescale 1ns / 1ps

//部分代码参考了网络实现：
//https://github.com/RoderickQiu/CS202-Project
module vga_char_set (
    input clk,
    input rst,
    input [3:0] data,
    output reg [7:0] col0,
    output reg [7:0] col1,
    output reg [7:0] col2,
    output reg [7:0] col3,
    output reg [7:0] col4,
    output reg [7:0] col5,
    output reg [7:0] col6
);

    always @(posedge clk or negedge rst) begin
        if (!rst) begin
            col0 <= 0; col1 <= 0; col2 <= 0;
            col3 <= 0; col4 <= 0; col5 <= 0; col6 <= 0;
        end else begin
            // 榛樿娓呴浂鎵?鏈夊垪锛岄槻姝㈡畫褰?
            col0 <= 8'b0000_0000;
            col1 <= 8'b0000_0000;
            col2 <= 8'b0000_0000;
            col3 <= 8'b0000_0000;
            col4 <= 8'b0000_0000;
            col5 <= 8'b0000_0000;
            col6 <= 8'b0000_0000;

            case (data)
                4'h0: begin
                    col1 <= 8'b0011_1110;
                    col2 <= 8'b0101_0001;
                    col3 <= 8'b0100_1001;
                    col4 <= 8'b0100_0101;
                    col5 <= 8'b0011_1110;
                end
                4'h1: begin
                    col2 <= 8'b0100_0010;
                    col3 <= 8'b0111_1111;
                    col4 <= 8'b0100_0000;
                end
                4'h2: begin
                    col1 <= 8'b0100_0010;
                    col2 <= 8'b0110_0001;
                    col3 <= 8'b0101_0001;
                    col4 <= 8'b0100_1001;
                    col5 <= 8'b0100_0110;
                end
                4'h3: begin
                    col1 <= 8'b0010_0010;
                    col2 <= 8'b0100_0001;
                    col3 <= 8'b0100_1001;
                    col4 <= 8'b0100_1001;
                    col5 <= 8'b0011_0110;
                end
                4'h4: begin
                    col1 <= 8'b0001_1000;
                    col2 <= 8'b0001_0100;
                    col3 <= 8'b0001_0010;
                    col4 <= 8'b0111_1111;
                    col5 <= 8'b0001_0000;
                end
                4'h5: begin
                    col1 <= 8'b0010_0111;
                    col2 <= 8'b0100_0101;
                    col3 <= 8'b0100_0101;
                    col4 <= 8'b0100_0101;
                    col5 <= 8'b0011_1001;
                end
                4'h6: begin
                    col1 <= 8'b0011_1110;
                    col2 <= 8'b0100_1001;
                    col3 <= 8'b0100_1001;
                    col4 <= 8'b0100_1001;
                    col5 <= 8'b0011_0010;
                end
                4'h7: begin
                    col1 <= 8'b0110_0001;
                    col2 <= 8'b0001_0001;
                    col3 <= 8'b0000_1001;
                    col4 <= 8'b0000_0101;
                    col5 <= 8'b0000_0011;
                end
                4'h8: begin
                    col1 <= 8'b0011_0110;
                    col2 <= 8'b0100_1001;
                    col3 <= 8'b0100_1001;
                    col4 <= 8'b0100_1001;
                    col5 <= 8'b0011_0110;
                end
                4'h9: begin
                    col1 <= 8'b0010_0110;
                    col2 <= 8'b0100_1001;
                    col3 <= 8'b0100_1001;
                    col4 <= 8'b0100_1001;
                    col5 <= 8'b0011_1110;
                end
                4'hA: begin
                    col1 <= 8'b0111_1100;
                    col2 <= 8'b0001_0010;
                    col3 <= 8'b0001_0001;
                    col4 <= 8'b0001_0010;
                    col5 <= 8'b0111_1100;
                end
                4'hB: begin
                    col1 <= 8'b0111_1111;
                    col2 <= 8'b0100_1001;
                    col3 <= 8'b0100_1001;
                    col4 <= 8'b0100_1001;
                    col5 <= 8'b0011_0110;
                end
                4'hC: begin
                    col1 <= 8'b0011_1110;
                    col2 <= 8'b0100_0001;
                    col3 <= 8'b0100_0001;
                    col4 <= 8'b0100_0001;
                    col5 <= 8'b0010_0010;
                end
                4'hD: begin
                    col1 <= 8'b0111_1111;
                    col2 <= 8'b0100_0001;
                    col3 <= 8'b0100_0001;
                    col4 <= 8'b0100_0001;
                    col5 <= 8'b0011_1110;
                end
                4'hE: begin
                    col1 <= 8'b0111_1111;
                    col2 <= 8'b0100_1001;
                    col3 <= 8'b0100_1001;
                    col4 <= 8'b0100_1001;
                    col5 <= 8'b0100_0001;
                end
                4'hF: begin
                    col1 <= 8'b0111_1111;
                    col2 <= 8'b0000_1001;
                    col3 <= 8'b0000_1001;
                    col4 <= 8'b0000_1001;
                    col5 <= 8'b0000_0001;
                end
                default: begin
                    col1 <= 8'b0010_0010;
                    col2 <= 8'b0001_0100;
                    col3 <= 8'b0000_1000;
                    col4 <= 8'b0001_0100;
                    col5 <= 8'b0010_0010;
                end
            endcase
        end
    end

endmodule
