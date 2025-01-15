module timer_mode (
    input clk,
    input reset,
    input power_state,
    input set_mode,
    input set_select,          // 外部输入控制调整分钟或小时
    input increase_key,
    output reg [7:0] tub_segments_1,  // 输出当前段码
    output reg [7:0] tub_segments_2,  // 输出当前段码
    output reg [5:0] tub_select       // 位选信号，共6位数码管
);

    reg [4:0] hours;           // 小时，0~23
    reg [5:0] minutes;         // 分钟，0~59
    reg [5:0] seconds;         // 秒，0~59
    reg inc_prev;              // 按键前一状态
    reg [31:0] counter;        // 1Hz分频计数器
    reg [15:0] scan_counter;   // 动态扫描分频计数器
    reg [2:0] scan_index;      // 动态扫描索引
    reg lock_key;              // 按键锁存信号

    // 按键持续计时
    reg [31:0] key_hold_counter; // 用于记录 increase_key 按键按住的时钟周期数
    reg key_held_two_seconds;    // 标志是否按住了两秒

    parameter ONE_SECOND = 32'd100000000; // 假设输入时钟为100MHz
    parameter SCAN_DELAY = 16'd20000;     // 降低动态扫描频率（增加延迟）
    parameter HOLD_TIME = 32'd200000000;  // 两秒的持续时间

    // 数码管段码查找表
    reg [7:0] segment_lut [0:9];
    initial begin
        segment_lut[0] = 8'b1111_1100; // 数字 0
        segment_lut[1] = 8'b0110_0000; // 数字 1
        segment_lut[2] = 8'b1101_1010; // 数字 2
        segment_lut[3] = 8'b1111_0010; // 数字 3
        segment_lut[4] = 8'b0110_0110; // 数字 4
        segment_lut[5] = 8'b1011_0110; // 数字 5
        segment_lut[6] = 8'b1011_1110; // 数字 6
        segment_lut[7] = 8'b1110_0000; // 数字 7
        segment_lut[8] = 8'b1111_1110; // 数字 8
        segment_lut[9] = 8'b1110_0110; // 数字 9
    end

    // 初始化信号
    initial begin
        hours <= 0;
        minutes <= 0;
        seconds <= 0;
        counter <= 0;
        scan_index <= 0;
        tub_segments_1 <= 8'b00000000;
        tub_segments_2 <= 8'b00000000;
        tub_select <= 6'b000000;
        inc_prev <= 0;
        lock_key <= 0;
        key_hold_counter <= 0;
        key_held_two_seconds <= 0;
    end

    // 按键去抖逻辑
    reg [15:0] debounce_counter;
    reg stable_key;

    always @(posedge clk or negedge reset) begin
        if (!reset) begin
            debounce_counter <= 0;
            stable_key <= 0;
        end else if (increase_key) begin
            if (debounce_counter < 16'd10000) begin // 调整去抖计数
                debounce_counter <= debounce_counter + 1;
            end else begin
                stable_key <= 1; // 按键稳定后置位
            end
        end else begin
            debounce_counter <= 0;
            stable_key <= 0;
        end
    end

    // 按键持续按住计时逻辑
    always @(posedge clk or negedge reset) begin
        if (!reset) begin
            key_hold_counter <= 0;
            key_held_two_seconds <= 0;
        end else if (stable_key) begin
            if (key_hold_counter < HOLD_TIME) begin
                key_hold_counter <= key_hold_counter + 1;
            end else begin
                key_held_two_seconds <= 1; // 按键已持续两秒
            end
        end else begin
            key_hold_counter <= 0; // 按键松开时清零计数
            key_held_two_seconds <= 0; // 重置两秒标志
        end
    end

    // 时间计时和设置逻辑
    always @(posedge clk or negedge reset or negedge power_state) begin
        if (!reset || !power_state) begin
            // 当复位或关机时，清空状态
            hours <= 0;
            minutes <= 0;
            seconds <= 0;
            counter <= 0;
            inc_prev <= 0;
            lock_key <= 0; // 按键解锁
        end else if (power_state) begin
            if (set_mode) begin
                // 设置模式
                if (key_held_two_seconds && !lock_key) begin // 必须按住两秒
                    case (set_select)
                        0: minutes <= (minutes + 1) % 60; // 调整分钟
                        1: hours <= (hours + 1) % 24;    // 调整小时
                    endcase
                    lock_key <= 1; // 按键按下后锁定
                end
                if (!stable_key) begin
                    lock_key <= 0; // 按键释放后解锁
                end
                inc_prev <= stable_key; // 更新按键状态
            end else begin
                // 正常计时模式
                counter <= counter + 1;
                if (counter >= ONE_SECOND) begin
                    counter <= 0;
                    seconds <= seconds + 1;
                    if (seconds == 59) begin
                        seconds <= 0;
                        minutes <= minutes + 1;
                        if (minutes == 59) begin
                            minutes <= 0;
                            hours <= hours + 1;
                            if (hours == 23) begin
                                hours <= 0;
                            end
                        end
                    end
                end
                lock_key <= 0; // 清除锁存状态
            end
        end
    end

    // 动态扫描逻辑
    always @(posedge clk or negedge reset) begin
        if (!reset) begin
            scan_counter <= 0;
            scan_index <= 0;
            tub_segments_1 <= 8'b00000000;
            tub_segments_2 <= 8'b00000000;
            tub_select <= 6'b000000;
        end else begin
            scan_counter <= scan_counter + 1;
            if (scan_counter >= SCAN_DELAY) begin
                scan_counter <= 0;

                // 清除上一段信号，防止残影
                tub_segments_1 <= 8'b00000000;
                tub_segments_2 <= 8'b00000000;
                tub_select <= 6'b000000;
                
                scan_index <= (scan_index + 1) % 6;
                if (power_state) begin
                case (scan_index)
                    0: begin
                        tub_segments_1 <= segment_lut[hours / 10];  // 小时十位
                        tub_select <= 6'b100000;
                    end
                    1: begin
                        tub_segments_1 <= segment_lut[hours % 10];  // 小时个位
                        tub_select <= 6'b010000;
                    end
                    2: begin
                        tub_segments_1 <= segment_lut[minutes / 10]; // 分钟十位
                        tub_select <= 6'b001000;
                    end
                    3: begin
                        tub_segments_1 <= segment_lut[minutes % 10]; // 分钟个位
                        tub_select <= 6'b000100;
                    end
                    4: begin
                        tub_segments_2 <= segment_lut[seconds / 10]; // 秒十位
                        tub_select <= 6'b000010;
                    end
                    5: begin
                        tub_segments_2 <= segment_lut[seconds % 10]; // 秒个位
                        tub_select <= 6'b000001;
                    end
                endcase
                end
            end
        end
    end

endmodule