module key_press_detector (
    input clk,
    input reset,
    input key_input,
    output reg short_press,
    output reg long_press
);
reg [31:0] press_count;
reg key_prev;

parameter LONG_PRESS_TIME = 32'd300000000;

always @(posedge clk, negedge reset) begin
    if (!reset) begin
        press_count <= 0;
        short_press <= 0;
        long_press <= 0;
    end else begin
        if (key_input) begin
            press_count <= press_count + 1;
            if (press_count > LONG_PRESS_TIME) begin
                long_press <= 1;
            end
        end else if (!key_input && key_prev) begin
            if (press_count <= LONG_PRESS_TIME) begin
                short_press <= 1;
            end
            press_count <= 0;
            long_press <= 0;
        end else begin
            short_press <= 0;
            long_press <= 0;
        end
        key_prev <= key_input;
    end
end

    
endmodule