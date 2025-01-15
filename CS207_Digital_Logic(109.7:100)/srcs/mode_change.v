module mode_change(
    input clk,             // 时钟信号
    input reset,           // 复位信号
    input menu_btn,        // 菜单键输入
    input [2:0] speed_btn, // 速度按键输入 (000:无输入, 001:1档, 010:2档, 100:3档)
    input clean_btn,       // 自清洁按键输入
    input set_mode,        // 是否调整remind_time
    input display_mode,    // 是否显示累计工作时间
    input set_select,      // 外部输入控制调整分钟或小时
    input increase_key,
    input power_state,
    output reg [2:0] mode, // 模式输出 (000:待机, 001:1档, 010:2档, 100:3档, 111:自清洁)
    output reg countdown,   // 倒计时输出（1为倒计时中，0为不倒计时）
    output reg cleaning_reminder, // 自清洁提醒信号
    output reg [7:0] tub_segments_1,  // 输出当前段码
    output reg [7:0] tub_segments_2,  // 输出当前段码
    output reg [7:0] tub_select      // 位选信号，共6位数码管
);

    // 状态定义
    parameter STANDBY = 3'b000;          // 待机模式
    parameter WAIT_FOR_SPEED = 3'b001;   // 等待速度按键模式
    parameter SUCTION_1 = 3'b010;        // 抽油烟1档
    parameter SUCTION_2 = 3'b011;        // 抽油烟2档
    parameter SUCTION_3 = 3'b100;        // 抽油烟3档
    parameter CLEANING = 3'b111;         // 自清洁模式
    parameter SUCTION_3_TIMER = 3'b101;  // 抽油烟3档倒计时模式
    parameter RETURN_TO_STANDBY = 3'b110; // 返回待机的倒计时模式
    parameter SCAN_DELAY = 16'd20000;     // 降低动态扫描频率（增加延迟）


    reg [2:0] current_state, next_state;
    reg [31:0] timer; // 倒计时计时器
    reg [31:0] STANDBY_timer; // 倒计时计时器
    reg suction_3_used; // 标志风扇三级档位是否已经使用

    // 消抖逻辑信号
    reg menu_btn_sync_0, menu_btn_sync_1;
    reg [19:0] debounce_counter; // 20-bit计数器用于消抖
    reg menu_btn_stable;

    reg [15:0] scan_counter;   // 动态扫描分频计数器
    reg [2:0] scan_index;      // 动态扫描索引

    // 累计工作时长
    reg [4:0] hours;
    reg [5:0] minutes;
    reg [5:0] seconds;
    reg [31:0] counter;

    // 提醒时间
    wire [4:0] remind_hours;
    wire [5:0] remind_minutes;

    parameter ONE_SECOND = 32'd100000000; // 假设输入时钟为100MHz

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

     // 初始化计时信号
    initial begin
        hours <= 0;
        minutes <= 0;
        seconds <= 0;
        counter <= 0;
        tub_segments_1 <= 8'b00000000;
        tub_segments_2 <= 8'b00000000;
        tub_select <= 8'b00000000;
    end

    // 按键消抖逻辑
    always @(posedge clk or negedge reset) begin
        if (!reset) begin
            menu_btn_sync_0 <= 0;
            menu_btn_sync_1 <= 0;
            debounce_counter <= 0;
            menu_btn_stable <= 0;
        end else begin
            // 同步化处理，防止时钟域交叉带来的亚稳态
            menu_btn_sync_0 <= menu_btn;
            menu_btn_sync_1 <= menu_btn_sync_0;

            // 消抖计数逻辑
            if (menu_btn_sync_1 == menu_btn_stable) begin
                debounce_counter <= 0;
            end else begin
                debounce_counter <= debounce_counter + 1;
                if (debounce_counter == 20'd1000000) begin
                    menu_btn_stable <= menu_btn_sync_1;
                    debounce_counter <= 0;
                end
            end
        end
    end

    // 单次响应逻辑
    reg menu_btn_stable_last;
    wire menu_btn_pressed;

    assign menu_btn_pressed = (menu_btn_stable && !menu_btn_stable_last);

    always @(posedge clk or negedge reset) begin
        if (!reset) begin
            menu_btn_stable_last <= 0;
        end else begin
            menu_btn_stable_last <= menu_btn_stable;
        end
    end

    // 状态转换
    always @(posedge clk or negedge reset) begin
        if (!reset) begin
            current_state <= STANDBY;
            mode <= 3'b000;
        end else if (power_state) begin
                    current_state <= next_state;
            // 更新模式输出
            case (next_state)
                STANDBY: mode <= 3'b000;
                WAIT_FOR_SPEED: mode <= 3'b000; // 等待输入时保持待机状态
                SUCTION_1: mode <= 3'b001;
                SUCTION_2: mode <= 3'b010;
                SUCTION_3: mode <= 3'b100;
                SUCTION_3_TIMER: mode <= 3'b100; // 保持3档模式，但处于倒计时状态
                RETURN_TO_STANDBY: mode <= 3'b000; // 返回待机倒计时
                CLEANING: mode <= 3'b111;
                default: mode <= 3'b000;
            endcase
        end
    end

    // 标志位更新逻辑（同步逻辑）
    always @(posedge clk or negedge reset) begin
        if (!reset) begin
            suction_3_used <= 0;
        end else if (current_state == SUCTION_3 && next_state == SUCTION_3_TIMER) begin
            suction_3_used <= 1; // 当进入 SUCTION_3_TIMER 后标志位设置为 1
        end
    end

   // 状态机逻辑
    always @(*) begin  
        next_state = current_state; // 默认保持当前状态
        if (power_state) begin  // 只有当 power_state 为 1 时，才允许状态切换
            case(current_state)
                STANDBY: begin
                    if (menu_btn_pressed) begin
                        next_state = WAIT_FOR_SPEED; // 按菜单键后进入等待速度按键模式
                    end
                end
                WAIT_FOR_SPEED: begin
                    if (speed_btn != 3'b000) begin
                        case(speed_btn)
                            3'b001: next_state = SUCTION_1;   // 按1档键，进入1档模式
                            3'b010: next_state = SUCTION_2;   // 按2档键，进入2档模式
                            3'b100: begin
                                if (!suction_3_used) begin
                                    next_state = SUCTION_3;   // 按3档键，进入3档模式（仅限第一次）
                                end
                            end
                            default: next_state = WAIT_FOR_SPEED;
                        endcase
                    end else if (clean_btn) begin
                        next_state = CLEANING; // 按清洁键，进入自清洁模式
                    end
                end
                SUCTION_1: begin
                    if (menu_btn_pressed) next_state = STANDBY;  
                    // 按菜单键返回待机
                   else if(speed_btn == 3'b010) next_state = SUCTION_2;
                end
                SUCTION_2: begin
                    if (menu_btn_pressed) next_state = STANDBY;  // 按菜单键返回待机
                    else if(speed_btn == 3'b001) next_state = SUCTION_1;
                end
                SUCTION_3: begin
                    next_state = SUCTION_3_TIMER; // 开始60秒倒计时
                end
                SUCTION_3_TIMER: begin
                    if (timer == 0) next_state = SUCTION_2;  // 倒计时结束后进入二档模式
                    else if (menu_btn_pressed) next_state = RETURN_TO_STANDBY;  // 按菜单键返回待机
                end
                RETURN_TO_STANDBY: begin
                    if (timer == 0) next_state = STANDBY;  // 倒计时结束后返回待机
                end
                CLEANING: begin
                    if (timer > 0)
                        next_state = CLEANING;
                    else if (timer == 0)
                        next_state = STANDBY;  // 倒计时结束后返回待机
                end
            endcase
        end
    end


    // 计时器逻辑
     always @(posedge clk or negedge reset) begin
        if (!reset)begin
            timer <= 32'd1800000000;
            STANDBY_timer <= 32'd600000000;
            end // 初始化为自清洁倒计时（180秒）
        else if (next_state == SUCTION_3_TIMER && timer > 0)
            timer <= timer - 1; // 3档倒计时中递减
        else if (next_state == SUCTION_3_TIMER && timer == 0)
            timer <= 32'd600000000; // 启动3档倒计时（60秒） 
//        else if (next_state == RETURN_TO_STANDBY && STANDBY_timer == 0)
//            timer <= STANDBY_timer; // 启动返回待机倒计时（60秒）
        else if (next_state == RETURN_TO_STANDBY && STANDBY_timer > 0) begin
            STANDBY_timer <= STANDBY_timer - 1; // 返回待机倒计时
            timer <= STANDBY_timer; 
        end
        else if (next_state == CLEANING && countdown == 1)
            timer <= timer - 1; // 自清洁模式倒计时递减
        else if (next_state == CLEANING && timer == 0) 
            timer <= 32'd1800000000; // 启动自清洁倒计时（180秒）
        else
            timer <= 0;  // 其他模式不计时
    end

    // 倒计时指示
    always @(next_state or timer) begin
        if ((next_state == SUCTION_3_TIMER || next_state == RETURN_TO_STANDBY || next_state == CLEANING) && timer > 0)
            countdown = 1;  // 倒计时中
        else
            countdown = 0;  // 不倒计时
    end

    // 工作时长计数器
    always @(posedge clk or negedge reset) begin
        if (!reset|| clean_btn) begin
            // 复位时或开始自清洁时，清空状态
            hours <= 0;
            minutes <= 0;
            seconds <= 0;
            counter <= 0;
          end else if (power_state && (current_state == SUCTION_1 || current_state == SUCTION_2 || current_state == SUCTION_3||current_state == SUCTION_3_TIMER||current_state == RETURN_TO_STANDBY)) begin
            // 累计工作时长
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
        end else if (power_state && current_state == CLEANING) begin
            // 自清洁模式，清空工作时长
            hours <= 0;
            minutes <= 0;
            seconds <= 0;
            counter <= 0;
            cleaning_reminder <= 0; // 已开启自清洁，清空提醒信号

        end else if (power_state && current_state == STANDBY) begin
            if (hours >= remind_hours && minutes >= remind_minutes) begin
                cleaning_reminder <= 1; // 默认工作时间累计10小时，提醒自清洁
            end
        end else if(current_state != STANDBY) begin
            cleaning_reminder <= 0;
            end  
    end

    //设置提醒时间
    timer_setter remind_setter(
       .clk(clk),
       .reset(reset),
       .hours(remind_hours),
       .minutes(remind_minutes),
       .set_mode(set_mode),
       .set_select(set_select),
       .increase_key(increase_key),
       .visible(~display_mode)      // 外部输入控制数码管显示
    );

    // 时间显示逻辑
    always @(posedge clk or negedge reset) begin
        if (!reset) begin
            scan_counter <= 0;
            scan_index <= 0;
            tub_segments_1 <= 8'b00000000;
            tub_segments_2 <= 8'b00000000;
            tub_select <= 8'b000000;
        end else begin
            scan_counter <= scan_counter + 1;
            if (scan_counter >= SCAN_DELAY) begin
                scan_counter <= 0;

                // 清除上一段信号，防止残影
                tub_segments_1 <= 8'b00000000;
                tub_segments_2 <= 8'b00000000;
                tub_select <= 8'b000000;
                
                // 只有当 visible 为高时才更新显示
                if (power_state) begin
                if (display_mode) begin
                    scan_index <= (scan_index + 1) % 6;
                    case (scan_index)
                        0: begin
                            tub_segments_1 <= segment_lut[hours / 10];  // 小时十位
                            tub_select <= 8'b10000000;
                        end
                        1: begin
                            tub_segments_1 <= segment_lut[hours % 10];  // 小时个位
                            tub_select <= 8'b01000000;
                        end
                        2: begin
                            tub_segments_1 <= segment_lut[minutes / 10]; // 分钟十位
                            tub_select <= 8'b00100000;
                        end
                        3: begin
                            tub_segments_1 <= segment_lut[minutes % 10]; // 分钟个位
                            tub_select <= 8'b00010000;
                        end
                        4: begin
                            tub_segments_2 <= segment_lut[seconds / 10]; // 秒十位
                            tub_select <= 8'b00001000;
                        end
                        5: begin
                            tub_segments_2 <= segment_lut[seconds % 10]; // 秒个位
                            tub_select <= 8'b00000100;
                        end
                    endcase
                end
                else begin
                    scan_index <= (scan_index + 1) % 4;

                    case (scan_index)
                        0: begin
                            tub_segments_1 <= segment_lut[remind_hours / 10];  // 小时十位
                            tub_select <= 8'b10000000;
                        end
                        1: begin
                            tub_segments_1 <= segment_lut[remind_hours % 10];  // 小时个位
                            tub_select <= 8'b01000000;
                        end
                        2: begin
                            tub_segments_1 <= segment_lut[remind_minutes / 10]; // 分钟十位
                            tub_select <= 8'b00100000;
                        end
                        3: begin
                            tub_segments_1 <= segment_lut[remind_minutes % 10]; // 分钟个位
                            tub_select <= 8'b00010000;
                        end
                    endcase
                end
            end
                end
                
        end
    end

endmodule
