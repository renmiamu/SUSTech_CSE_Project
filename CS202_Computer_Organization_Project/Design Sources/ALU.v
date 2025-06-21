module ALU (
    input [3:0] ALUop,
    input ALUSrc,
    input sftmd,
    input Branch,
    input nBranch,
    input Branch_lt,
    input Branch_ge,
    input Branch_ltu,
    input Branch_geu,
    input [31:0] read_data_1,
    input [31:0] read_data_2,
    input [31:0] pc,
    input [31:0] imm32,
    output reg [31:0] Alu_result,
    output reg zero,
    output reg branch_result
);

wire is_imm;
assign is_imm = (ALUSrc == 1'b1);

wire input_2;

always @(*) begin
    zero=1'b0;
    Alu_result={32{1'b0}};
    branch_result=1'b0;
    case({ALUop,ALUSrc,sftmd,Branch,nBranch,Branch_lt,Branch_ge,Branch_ltu,Branch_geu,is_imm})
        13'b0000_0_0_0_0_0_0_0_0_0:begin        //add
            Alu_result=read_data_1+read_data_2;
        end
        13'b0001_0_0_0_0_0_0_0_0_0:begin        //sub
            Alu_result=read_data_1-read_data_2;
        end
        13'b0010_0_0_0_0_0_0_0_0_0:begin        //xor
            Alu_result=read_data_1^read_data_2;
        end
        13'b0011_0_0_0_0_0_0_0_0_0:begin        //or
            Alu_result=read_data_1|read_data_2;
        end
        13'b0100_0_0_0_0_0_0_0_0_0:begin        //and
            Alu_result=read_data_1&read_data_2;
        end
        13'b0101_0_1_0_0_0_0_0_0_0:begin        //sll
            Alu_result=read_data_1<<read_data_2;
        end
        13'b0110_0_1_0_0_0_0_0_0_0:begin        //srl
            Alu_result=read_data_1>>read_data_2;
        end
        13'b0111_0_1_0_0_0_0_0_0_0:begin        //sra
            Alu_result = $signed(read_data_1) >>> read_data_2;
        end
        13'b1000_0_0_0_0_0_0_0_0_0:begin       //slt
            Alu_result = ($signed(read_data_1) < $signed(read_data_2)) ? 32'd1 : 32'd0;
        end
        13'b1001_0_0_0_0_0_0_0_0_0:begin       //sltu
            Alu_result = (read_data_1 < read_data_2) ? 32'd1 : 32'd0;
        end
        13'b1010_0_0_0_0_0_0_0_0_0:begin       //mul
            Alu_result = read_data_1 * read_data_2[31:0];
        end
        13'b1011_0_0_0_0_0_0_0_0_0:begin       //div
            Alu_result = read_data_1 / read_data_2;
        end
        13'b1100_0_0_0_0_0_0_0_0_0:begin       //rem
            Alu_result = read_data_1 % read_data_2;
        end
        13'b0000_1_0_0_0_0_0_0_0_1:begin        //addi  load  store
            Alu_result=read_data_1+imm32;
        end
        13'b0001_1_0_0_0_0_0_0_0_1:begin        //xori
            Alu_result=read_data_1^imm32;
        end
        13'b0010_1_0_0_0_0_0_0_0_1:begin        //ori
            Alu_result=read_data_1|imm32;
        end
        13'b0011_1_0_0_0_0_0_0_0_1:begin        //andi
            Alu_result=read_data_1&imm32;
        end
        13'b0100_1_1_0_0_0_0_0_0_1:begin        //slli
            Alu_result=read_data_1<<imm32[4:0];
        end
        13'b0101_1_1_0_0_0_0_0_0_1:begin        //srai
            Alu_result=$signed(read_data_1) >>> imm32;
        end
        13'b0110_1_1_0_0_0_0_0_0_1:begin        //srli
            Alu_result=read_data_1>>imm32[4:0];
        end
        13'b0000_0_0_1_0_0_0_0_0_0:begin        //beq
            if (read_data_1==read_data_2) begin
                branch_result=1'b1;
            end
        end
        13'b0000_0_0_0_1_0_0_0_0_0:begin       //bnq
            if (read_data_1!=read_data_2) begin
                branch_result=1'b1;
            end
        end
        13'b0000_0_0_0_0_1_0_0_0_0:begin       //blt
            if ($signed(read_data_1)<$signed(read_data_2)) begin
                branch_result=1'b1;
            end            
        end
        13'b0000_0_0_0_0_0_1_0_0_0:begin       //bge
            if ($signed(read_data_1)>=$signed(read_data_2)) begin
                branch_result=1'b1;
            end               
        end
        13'b0000_0_0_0_0_0_0_1_0_0:begin       //bltu
            if (read_data_1<read_data_2) begin
                branch_result=1'b1;
            end
        end
        13'b0000_0_0_0_0_0_0_0_1_0:begin       //bgeu
            if (read_data_1>=read_data_2) begin
                branch_result=1'b1;
            end
        end
        13'b1000_1_0_0_0_0_0_0_0_1:begin       //lui
            Alu_result=imm32;
        end
        13'b1001_1_0_0_0_0_0_0_0_1:begin       //auipc
            Alu_result=pc+imm32;
        end
    endcase
    if (Alu_result=={32{1'b0}})begin
        zero=1'b1;
    end
end
    
endmodule