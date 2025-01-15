module gesture_power_control (
    input clk,
    input reset,
    input left_key,
    input right_key,
    input [1:0] time_select,
    output reg power_state,
    output [7:0] tub_segments_gesture_time,
    output tub_select_gesture_time
);

parameter IDLE = 2'b00;
parameter LEFT_WAIT = 2'b01;
parameter RIGHT_WAIT = 2'b10;

reg [1:0] current_state, next_state;
reg [31:0] countdown, countdown_next;
wire [31:0] COUNTDOWN_TIME;

gesture_power_control_timer time_control (
    .clk(clk),
    .reset(reset),
    .time_select(time_select),
    .countdown_time(COUNTDOWN_TIME),
    .tub_segments_gesture_time(tub_segments_gesture_time),
    .tub_select_gesture_time(tub_select_gesture_time)
);

// Sequential logic: Update state, countdown, and power state
always @(posedge clk or negedge reset) begin
    if (!reset) begin
        current_state <= IDLE;         // Initial state
        power_state <= 0;              // Initial power off
        countdown <= 0;                // Initial countdown
    end else begin
        current_state <= next_state;   // Update state
        countdown <= countdown_next;    // Update countdown
        // Power state update in sequential logic
        case (next_state)
            LEFT_WAIT: begin
                if (countdown > 0 && right_key) begin
                    power_state <= 1;  // Power on if in LEFT_WAIT and right key is pressed
                end
            end
            RIGHT_WAIT: begin
                if (countdown > 0 && left_key) begin
                    power_state <= 0;  // Power off if in RIGHT_WAIT and left key is pressed
                end
            end
            default: begin
                power_state <= power_state; // Maintain previous state if not in LEFT_WAIT or RIGHT_WAIT
            end
        endcase
    end
end

// Combinatorial logic: Calculate the next state and countdown value
always @(*) begin
    next_state = current_state;      // Default to hold the current state
    countdown_next = countdown;       // Default to hold the current countdown value

    case (current_state)
        IDLE: begin
            if (left_key && power_state == 0) begin
                next_state = LEFT_WAIT;          // Enter waiting state for right key
                countdown_next = COUNTDOWN_TIME; // Initialize countdown  
            end else if (right_key && power_state == 1) begin
                next_state = RIGHT_WAIT;         // Enter waiting state for left key
                countdown_next = COUNTDOWN_TIME; // Initialize countdown
            end
        end

        LEFT_WAIT: begin
            if (countdown > 0) begin
                countdown_next = countdown - 1; // Countdown decrement
            end else begin
                next_state = IDLE;               // Countdown ends, go to IDLE
                countdown_next = 0;              // Reset countdown
            end
            if(power_state == 1)begin
                next_state = IDLE;               // Countdown ends, go to IDLE
                countdown_next = 0;
            end
        end

        RIGHT_WAIT: begin
            if (countdown > 0) begin
                countdown_next = countdown - 1; // Countdown decrement
            end else begin
                next_state = IDLE;               // Countdown ends, go to IDLE
                countdown_next = 0;              // Reset countdown
            end
            if(power_state == 0)begin
                next_state = IDLE;               // Countdown ends, go to IDLE
                countdown_next = 0;
            end
        end

        default: begin
            next_state = IDLE;                  // Default to IDLE
            countdown_next = 0;                  // Reset countdown
        end
    endcase
end

endmodule