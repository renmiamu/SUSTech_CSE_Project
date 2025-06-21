module switch (
    input clk,
    input rst,
    input switchCtrl,
    input [15:0] switchInput,
    input [31:0] address,
    input confirmation,
    output reg [15:0] dataIOInput
);
always @(posedge clk) begin
    if (!rst) begin
        dataIOInput <= {16{1'b0}};
    end else if (switchCtrl) begin
        case (address)
            32'hffff_ff00: dataIOInput <= {{15{1'b0}}, confirmation};                         
            32'hffff_fff1: dataIOInput <= switchInput;                                   
            32'hffff_fff3: dataIOInput <= {{8{1'b0}}, switchInput[15:8]};   
            32'hffff_fff5: dataIOInput <= {{8{switchInput[7]}}, switchInput[7:0]};                     
            32'hffff_fff7: dataIOInput <= {{8{1'b0}}, switchInput[2:0]};                     
            32'hffff_fff9: dataIOInput <= {{8{1'b0}}, switchInput[7:0]};                     
            default: dataIOInput <= {16{1'b0}};
        endcase
    end else begin
        dataIOInput <= {16{1'b0}};
    end
end

    
endmodule