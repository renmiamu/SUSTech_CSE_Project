module power_control (
    input clk,
    input reset,
    input short_press,
    input long_press,
    output reg power_state
);

always @(posedge clk, negedge reset) begin
    if (!reset) begin
        power_state <= 0;       //系统复位后默认关机
    end else begin
        case (power_state)
            0:begin
                if (short_press) power_state <= 1;
            end
            1:begin
                if (long_press) power_state <= 0;
            end 
            default: power_state <= 0;
        endcase
    end
end
    
endmodule