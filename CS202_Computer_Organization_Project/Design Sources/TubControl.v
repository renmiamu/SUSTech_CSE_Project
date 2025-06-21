module TubControl (
    input [4:0] data,
    output reg [7:0] lightSegment
);
always @(*) begin
    case (data)
        5'b00000:begin
            lightSegment=8'b11111100;
        end
        5'b00001:begin
            lightSegment=8'b01100000;
        end
        5'b00010:begin
            lightSegment=8'b11011010;
        end
        5'b00011:begin
            lightSegment=8'b11110010;
        end
        5'b00100:begin
            lightSegment=8'b01100110;
        end
        5'b00101:begin
            lightSegment=8'b10110110;
        end
        5'b00110:begin
            lightSegment=8'b10111110;
        end
        5'b00111:begin
            lightSegment=8'b11100000;
        end
        5'b01000:begin
            lightSegment=8'b11111110;
        end
        5'b01001:begin
            lightSegment=8'b11110110;
        end
        5'b01010:begin
            lightSegment=8'b11101110;    //A
        end
        5'b01011:begin
            lightSegment=8'b00111110;    //b
        end
        5'b01100:begin
            lightSegment=8'b10011100;    //C
        end
        5'b01101:begin
            lightSegment=8'b01111010;    //d
        end
        5'b01110:begin
            lightSegment=8'b10011110;    //E
        end
        5'b01111:begin
            lightSegment=8'b10001110;   //F
        end
        5'b10000:begin
            lightSegment=8'b00000010;   //neg
        end
        default:lightSegment=8'b11111111;         
    endcase
end
endmodule