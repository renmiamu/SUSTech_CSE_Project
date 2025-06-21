module reg_and_imm (
    input clk,
    input rst,
    input [31:0] inst,
    input [31:0] write_data,
    input RegWrite,
    output reg [31:0] read_data_1,
    output reg [31:0] read_data_2,
    output reg [31:0] imm32,
    output a7
);
reg [31:0] registers [0:31];
wire [4:0] rs1;
wire [4:0] rs2;
wire [4:0] rd;
wire [6:0] opcode;

assign rs1=inst[19:15];
assign rs2=inst[24:20];
assign rd=inst[11:7];
assign opcode=inst[6:0];
assign a7=registers[17][0];

always @(posedge clk ) begin
    if (!rst) begin
        registers[0]<={32{1'b0}};
        registers[1]<={32{1'b0}};
        registers[2]<={32{1'b0}};
        registers[3]<={32{1'b0}};
        registers[4]<={32{1'b0}};
        registers[5]<={32{1'b0}};
        registers[6]<={32{1'b0}};
        registers[7]<={32{1'b0}};
        registers[8]<={32{1'b0}};
        registers[9]<={32{1'b0}};
        registers[10]<={32{1'b0}};
        registers[11]<={32{1'b0}};
        registers[12]<={32{1'b0}};
        registers[13]<={32{1'b0}};
        registers[14]<={32{1'b0}};
        registers[15]<={32{1'b0}};
        registers[16]<={32{1'b0}};
        registers[17]<={32{1'b0}};
        registers[18]<={32{1'b0}};
        registers[19]<={32{1'b0}};
        registers[20]<={32{1'b0}};
        registers[21]<={32{1'b0}};
        registers[22]<={32{1'b0}};
        registers[23]<={32{1'b0}};
        registers[24]<={32{1'b0}};
        registers[25]<={32{1'b0}};
        registers[26]<={32{1'b0}};
        registers[27]<={32{1'b0}};
        registers[28]<={32{1'b0}};
        registers[29]<={32{1'b0}};
        registers[30]<={32{1'b0}};
        registers[31]<={32{1'b0}};
    end else if (RegWrite==1'b1)begin
        if (rd!=5'b00000) begin
            registers[rd]<=write_data;
        end
    end
end

always @(*) begin
    if (rs1==5'b00000) begin
        read_data_1={32{1'b0}};
    end else begin
        read_data_1=registers[rs1];
    end

    if (rs2==5'b00000) begin
        read_data_2={32{1'b0}};
    end else begin
        read_data_2=registers[rs2];
    end

    case (opcode)
        //r
        7'b0110011:begin
            imm32={32{1'b0}};
        end
        //i
        7'b0010011,7'b1100111:begin
            imm32={{20{inst[31]}},inst[31:20]};
        end
        //load
        7'b0000011:begin
            imm32={{20{inst[31]}},inst[31:20]};
        end
        //store
        7'b0100011:begin
            imm32={{20{inst[31]}},inst[31:25],inst[11:7]};
        end
        //b
        7'b1100011:begin
            imm32={{19{inst[31]}},inst[31],inst[7],inst[30:25],inst[11:8],1'b0};
        end
        //jal
        7'b1101111:begin
            imm32={{11{inst[31]}},inst[31],inst[19:12],inst[20],inst[30:21],1'b0};
        end
        //u
        7'b0110111,7'b0010111:begin
            imm32={inst[31:12],{12{1'b0}}};
        end
        

    endcase
end

    
endmodule