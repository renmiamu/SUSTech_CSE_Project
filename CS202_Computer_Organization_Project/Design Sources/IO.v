module IO (
    input clk,
    input rst,
    input switchCtrl,
    input [31:0] r_wdata,
    input LEDCtrl,
    input [15:0] switchInput,
    input [31:0] address,
    input confirmation,
    input [31:0] writeData,      // data written to display
    output [15:0] dataIOInput,
    output [7:0] tubSel,
    output [7:0] tubLeft,
    output [7:0] tubRight,
    output [15:0] dataOut,
    output [3:0] r,
    output [3:0] g,
    output [3:0] b,
    output hs,
    output vs
);

    wire [15:0] sw_data_out;

    switch sw(
        .clk(clk),
        .rst(rst),
        .switchCtrl(switchCtrl),
        .switchInput(switchInput),
        .address(address),
        .confirmation(confirmation),
        .dataIOInput(sw_data_out)
    );

    assign dataIOInput = sw_data_out;

    reg segWrite;
    reg ledWrite;
    reg segDecimalWrite;
    reg [15:0] ledReg;  // ? 添加寄存器保持 LED 状态

    assign dataOut = ledReg; // ? 始终输出保持的 LED 值

    // 数码管数据寄存器
    reg [4:0] s1, s2, s3, s4, s5, s6, s7, s8;
    wire [7:0] led1, led2, led3, led4, led5, led6, led7, led8;

    // 写入判断
    always @(*) begin
        segWrite = (address == 32'hffff_fff0);
        ledWrite = (address == 32'hffff_ffc2);
        segDecimalWrite = (address == 32'hffff_ffc4);
        segDecimalNegWrite = (address == 32'hffff_ffc6)
    end

    // ? LED 保持显示逻辑
    always @(posedge clk or negedge rst) begin
        if (!rst)begin
            ledReg <= 16'b0;
        end else if (ledWrite)begin
            ledReg <= writeData[15:0];
        end else begin
            ledReg <= ledReg;
        end    
    end

    reg [31:0] tmp;  // 临时变量用于十进制转换
    // ? 数码管保持逻辑
    always @(posedge clk or negedge rst) begin
        if (!rst) begin
            s1 <= 5'd0; s2 <= 5'd0; s3 <= 5'd0; s4 <= 5'd0;
            s5 <= 5'd0; s6 <= 5'd0; s7 <= 5'd0; s8 <= 5'd0;
        end else if (segWrite) begin
            s1 <= {1'b0,writeData[31:28]};
            s2 <= {1'b0,writeData[27:24]};
            s3 <= {1'b0,writeData[23:20]};
            s4 <= {1'b0,writeData[19:16]};
            s5 <= {1'b0,writeData[15:12]};
            s6 <= {1'b0,writeData[11:8]};
            s7 <= {1'b0,writeData[7:4]};
            s8 <= {1'b0,writeData[3:0]};
        end else if (segDecimalWrite) begin
            tmp=writeData;
            s8 <= tmp % 10; tmp = tmp / 10;
            s7 <= tmp % 10; tmp = tmp / 10;
            s6 <= tmp % 10; tmp = tmp / 10;
            s5 <= tmp % 10; tmp = tmp / 10;
            s4 <= tmp % 10; tmp = tmp / 10;
            s3 <= tmp % 10; tmp = tmp / 10;
            s2 <= tmp % 10; tmp = tmp / 10;
            s1 <= tmp % 10;
        end else if (segDecimalNegWrite)begin
            tmp=writeData;
            s8 <= tmp % 10; tmp = tmp / 10;
            s7 <= tmp % 10; tmp = tmp / 10;
            s6 <= tmp % 10; tmp = tmp / 10;
            s5 <= tmp % 10; tmp = tmp / 10;
            s4 <= tmp % 10; tmp = tmp / 10;
            s3 <= tmp % 10; tmp = tmp / 10;
            s2 <= tmp % 10; tmp = tmp / 10;
            s1 <= 5'b10000;
        end
        else begin
            s1 <= s1;
            s2 <= s2;
            s3 <= s3;
            s4 <= s4;
            s5 <= s5;
            s6 <= s6;
            s7 <= s7;
            s8 <= s8;
        end
    end

    // Tub 控制
    TubControl tub1(.data(s1), .lightSegment(led1));
    TubControl tub2(.data(s2), .lightSegment(led2));
    TubControl tub3(.data(s3), .lightSegment(led3));
    TubControl tub4(.data(s4), .lightSegment(led4));
    TubControl tub5(.data(s5), .lightSegment(led5));
    TubControl tub6(.data(s6), .lightSegment(led6));
    TubControl tub7(.data(s7), .lightSegment(led7));
    TubControl tub8(.data(s8), .lightSegment(led8));

    // Tub 显示模块
    Tub tub (
        .clk(clk),
        .tub1(led1),
        .tub2(led2),
        .tub3(led3),
        .tub4(led4),
        .tub5(led5),
        .tub6(led6),
        .tub7(led7),
        .tub8(led8),
        .tubSel(tubSel),
        .tubLeft(tubLeft),
        .tubRight(tubRight)
    );

    // VGA 显示模块
    vga display (
    .clk(clk),
    .rst(rst),
    .s1(s1), .s2(s2), .s3(s3), .s4(s4),
    .s5(s5), .s6(s6), .s7(s7), .s8(s8),
    .r(r), .g(g), .b(b),
    .hs(hs), .vs(vs)
    );
endmodule
