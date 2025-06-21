module writeback_mux (
    input MemorIOToReg,
    input [31:0] Alu_result,
    input [31:0] r_wdata,
    input [31:0] pc_out,
    input jal,
    output reg [31:0] writeback_data
);

always @(*) begin
    if (MemorIOToReg)begin
        writeback_data=r_wdata;
    end else if (jal) begin
        writeback_data<=pc_out;
    end else begin
        writeback_data=Alu_result;
    end
end
    
endmodule