module light (
    input clk,
    input reset,
    input power_state,
    input light_key,
    output reg light_state
);

reg light_key_prev;

always @(posedge clk,negedge reset) begin
    if (!reset) begin
        light_key_prev <= 0;
        light_state <= 0;
    end else begin
        if (power_state) begin
            if (light_key && !light_key_prev) begin
                light_state <= 1;
            end else if (light_key_prev && !light_key) begin
                light_state <= 0;
            end
        end else begin
            light_state <= 0;
        end
        light_key_prev <= light_key;
    end
end
    
endmodule