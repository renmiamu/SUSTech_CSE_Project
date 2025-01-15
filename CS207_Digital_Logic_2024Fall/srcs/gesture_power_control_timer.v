module gesture_power_control_timer (
    input clk,
    input reset,
    input [1:0] time_select,  // 2-bit input to select time
    output reg [31:0] countdown_time,  // Output for countdown time
    output reg [7:0] tub_segments_gesture_time,
    output reg tub_select_gesture_time
);

    // Time settings for different gestures
    parameter TIME_2S = 32'd200000000;  // 2 seconds (adjust based on clock frequency)
    parameter TIME_5S = 32'd500000000;  // 5 seconds
    parameter TIME_7S = 32'd700000000;  // 7 seconds
    parameter TIME_9S = 32'd900000000;  // 9 seconds
    
    // 数码管段码查找表
    reg [7:0] segment_lut [0:3];
    initial begin
        segment_lut[0] = 8'b1101_1010; // 数字 2
        segment_lut[1] = 8'b1011_0110; // 数字 5
        segment_lut[2] = 8'b1110_0000; // 数字 7
        segment_lut[3] = 8'b1110_0110; // 数字 9
    end

    always @(posedge clk or negedge reset) begin
        if (!reset) begin
            countdown_time <= TIME_5S;  // Default time to 5 seconds
            tub_segments_gesture_time<=segment_lut[1];
            tub_select_gesture_time<=1'b0;
        end else begin
            case (time_select)
                2'b00: begin
                    countdown_time <= TIME_5S;  // Set time to 2s
                    tub_segments_gesture_time<=segment_lut[1];
                    tub_select_gesture_time<=1'b1;
                end
                2'b01: begin
                    countdown_time <= TIME_2S;  // Set time to 5s
                    tub_segments_gesture_time<=segment_lut[0];
                    tub_select_gesture_time<=1'b1;
                end
                2'b10: begin
                    countdown_time <= TIME_7S;  // Set time to 7s
                    tub_segments_gesture_time<=segment_lut[2];
                    tub_select_gesture_time<=1'b1;
                end
                2'b11: begin
                    countdown_time <= TIME_9S; // Default to 5s
                    tub_segments_gesture_time<=segment_lut[3];
                    tub_select_gesture_time<=1'b1;
                end
            endcase
        end
    end
endmodule
