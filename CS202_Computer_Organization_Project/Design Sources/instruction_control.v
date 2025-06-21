module instruction_control (
    input [31:0] instruction,
    input [31:0] Alu_result,
    input a7,
    output reg nBranch,
    output reg Branch,
    output reg branch_lt,
    output reg branch_ge,
    output reg branch_ltu,
    output reg branch_geu,
    output reg jal,
    output reg jalr,
    output reg MemRead,
    output reg MemorIOToReg,
    output reg [3:0] ALUop,
    output reg MemWrite,
    output reg ALUSrc,
    output reg RegWrite,
    output reg sftmd,
    output reg IORead,
    output reg IOWrite
);
wire [2:0]func3;
wire [6:0]func7;
wire [6:0]opcode;
assign func3 = instruction[14:12];
assign func7 = instruction[31:25];
assign opcode = instruction[6:0];

wire is_IO_address = (Alu_result > 32'hFFFFFC00); // 0xFFFFFC00
wire is_RAM_address = (Alu_result < 32'h00010000); // 0x00000000-0x00010000

always @(*) begin
    nBranch=1'b0;
    Branch=1'b0;
    branch_ge=1'b0;
    branch_geu=1'b0;
    branch_lt=1'b0;
    branch_ltu=1'b0;
    MemRead=1'b0;
    MemorIOToReg=1'b0;
    ALUop=4'b0000;
    MemWrite=1'b0;
    ALUSrc=1'b0;
    RegWrite=1'b0;
    sftmd=1'b0;
    IORead=1'b0;
    IOWrite=1'b0;
    jal=1'b0;
    jalr=1'b0;
    ecall=1'b0;
    case(opcode)
        //R-type
        7'b0110011:begin
            RegWrite=1'b1;
            case({func3,func7})
                10'b000_0000000:begin
                    ALUop=4'b0000;        //add
                end
                10'b000_0100000:begin
                    ALUop=4'b0001;        //sub
                end
                10'b100_0000000:begin
                    ALUop=4'b0010;        //xor
                end
                10'b110_0000000:begin
                    ALUop=4'b0011;        //or
                end
                10'b111_0000000:begin
                    ALUop=4'b0100;        //and
                end
                10'b001_0000000:begin
                    ALUop=4'b0101;        //sll
                    sftmd=1'b1;
                end
                10'b101_0000000:begin
                    ALUop=4'b0110;        //srl
                    sftmd=1'b1;
                end
                10'b101_0100000:begin
                    ALUop=4'b0111;        //sra
                    sftmd=1'b1;
                end
                10'b010_0000000:begin     //slt
                    ALUop=4'b1000;
                end
                10'b011_0000000:begin     //sltu
                    ALUop=4'b1001;
                end
                10'b000_0000001:begin     //mul
                    ALUop=4'b1010;
                end
                10'b100_0000001:begin     //div
                    ALUop=4'b1011;
                end
                10'b110_0000001:begin     //rem
                    ALUop=4'b1100;
                end
            endcase
        end
        //I-type-1
        7'b0010011:begin
            RegWrite=1'b1;
            ALUSrc=1'b1;
            case(func3)
                3'b000:begin
                    ALUop=4'b0000;     //addi
                end
                3'b100:begin
                    ALUop=4'b0001;     //xori
                end
                3'b110:begin
                    ALUop=4'b0010;     //ori
                end
                3'b111:begin
                    ALUop=4'b0011;     //andi
                end
                3'b001:begin
                    ALUop=4'b0100;     //slli
                    sftmd=1'b1;
                end
                3'b101:begin
                    if (instruction[31:25]==7'b010_0000)begin
                        ALUop=4'b0101;     //srai
                        sftmd=1'b1;
                    end else begin
                        ALUop=4'b0110;     //srli
                        sftmd=1'b1;   
                    end
                end
            endcase
        end
        //I-type-2-load
        7'b0000011:begin
            ALUSrc=1'b1;
            MemorIOToReg=1'b1;
            RegWrite=1'b1;
            ALUop=4'b0000;
            if (is_IO_address) begin
                IORead=1'b1;
            end else begin
                MemRead=1'b1;
            end
        end
        //store
        7'b0100011:begin
            ALUSrc=1'b1;
            ALUop=4'b0000;
            if (is_IO_address) begin
                IOWrite=1'b1;
            end else begin
                MemWrite=1'b1;
            end
        end
        //branch
        7'b1100011:begin
            case(func3)
                3'b000:begin
                    Branch=1'b1;
                end
                3'b001:begin
                    nBranch=1'b1;
                end
                3'b100:begin
                    branch_lt=1'b1;
                end
                3'b101:begin
                    branch_ge=1'b1;
                end
                3'b110:begin
                    branch_ltu=1'b1;
                end
                3'b111:begin
                    branch_geu=1'b1;
                end
            endcase
        end
        //jal
        7'b1101111:begin
            jal=1'b1;
            RegWrite = 1'b1;
        end
        //jalr
        7'b1100111:begin
            jalr=1'b1;
            RegWrite=1'b1;
            ALUSrc=1'b1;
        end
        // lui
        7'b0110111: begin
            RegWrite = 1'b1;
            ALUSrc=1'b1;
            ALUop = 4'b1000; //直接加载高位立即数
        end

        // auipc (Add Upper Immediate to PC)
        7'b0010111: begin
            RegWrite = 1'b1;
            ALUSrc=1'b1;
            ALUop = 4'b1001; //PC + 高位立即数
        end

        //ecall
        7'b1110011: begin
            if (~a7) begin
                ALUSrc=1'b1;
                MemorIOToReg=1'b1;
                RegWrite=1'b1;
                ALUop=4'b0000;
                IORead=1'b1;
            end else begin
                ALUSrc=1'b1;
                ALUop=4'b0000;
                MemWrite=1'b1;
                end
        end
    endcase
end

    
endmodule