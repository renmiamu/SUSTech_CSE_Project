`timescale 1ns / 1ps
module Tub (
    input clk,
    input [7:0] tub1, 
    input [7:0] tub2,
    input [7:0] tub3,
    input [7:0] tub4,
    input [7:0] tub5,
    input [7:0] tub6,
    input [7:0] tub7,
    input [7:0] tub8,
    output reg [7:0] tubSel,
    output reg [7:0] tubLeft,
    output reg [7:0] tubRight
);

    reg [2:0] count = 3'b000;

    always @(posedge clk) begin
        count <= count + 1'b1;

        case (count)
            3'b000: begin
                tubSel   <= 8'b0000_0001;
                tubLeft  <= tub1;

            end
            3'b001: begin
                tubSel   <= 8'b0000_0010;
                tubLeft  <= tub2;

            end
            3'b010: begin
                tubSel   <= 8'b0000_0100;
                tubLeft  <= tub3;

            end
            3'b011: begin
                tubSel   <= 8'b0000_1000;
                tubLeft  <= tub4;

            end
            3'b100: begin
                tubSel   <= 8'b0001_0000;
                tubRight <= tub5;

            end
            3'b101: begin
                tubSel   <= 8'b0010_0000;
                tubRight <= tub6;

            end
            3'b110: begin
                tubSel   <= 8'b0100_0000;
                tubRight <= tub7;

            end
            3'b111: begin
                tubSel   <= 8'b1000_0000;
                tubRight <= tub8;

            end
            default: begin
                tubSel   <= 8'b0000_0000;

            end
        endcase
    end

endmodule
