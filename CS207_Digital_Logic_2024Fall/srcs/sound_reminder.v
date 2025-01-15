module sound_reminder(
    input wire cleaning_reminder,  // 用作使能信号，启用时播放音频
    input wire clk,                // FPGA时钟信号，100 MHz
    input wire[2:0] suction,       // 挡位输入
    output wire speaker            // PWM信号输出到低通滤波器（音频输出）
);

    reg [31:0] counter;
    reg pwm;
    
    parameter note = 440000;  // 频率 (440Hz)
    parameter first = 550776;  // suction = 001 时的频率
    parameter second = 451699; // suction = 010 时的频率
    parameter third = 364545;   // suction = 100 时的频率

    parameter volume = 8'd175;  // 音量占空比控制 (0-255)

    initial begin
        pwm = 0;
        counter = 0;
    end

    always @(posedge clk) begin
        if (cleaning_reminder) begin
            if (counter < note) begin
                counter <= counter + 1'b1;  // 计数器递增
            end else begin
                pwm = ~pwm;  // 切换PWM状态
                counter <= 0;  // 重置计数器
            end
        end
        else begin
            if (suction == 3'b001)begin
                if (counter < first) begin
                    counter <= counter + 1'b1;  // 计数器递增
                end else begin
                    pwm = ~pwm;  // 切换PWM状态
                    counter <= 0;  // 重置计数器
                end
            end
            else if (suction == 3'b010)begin
                if (counter < second) begin
                    counter <= counter + 1'b1;  // 计数器递增
                end else begin
                    pwm = ~pwm;  // 切换PWM状态
                    counter <= 0;  // 重置计数器
                end
            end
            else if (suction == 3'b100)begin
                if (counter < third) begin
                    counter <= counter + 1'b1;  // 计数器递增
                end else begin
                    pwm = ~pwm;  // 切换PWM状态
                    counter <= 0;  // 重置计数器
                end
            end
        end
    end
    
    // 调整占空比来控制音量
    assign speaker = (counter < (note * volume) >> 8) ? 1'b1 : 1'b0;  // 占空比控制音量

endmodule
