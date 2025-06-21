module led_control(
input clk,
input rst,
input LEDCtrl,
input [31:0] r_wdata,
output reg [15:0]dataOut                                       
);

always@(posedge clk) begin
    if(!rst) begin
    dataOut <=16'h0000;
    end
    else if( LEDCtrl) begin
    dataOut <=r_wdata[15:0];
    end
    else begin
    dataOut <=dataOut;
    end 
end
endmodule