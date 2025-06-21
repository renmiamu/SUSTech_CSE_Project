`timescale 1ns / 1ps

module CPU_tb;

    // Inputs
    reg clk;
    reg reset;
    reg [15:0] switchInput;
    reg confirmation;

    // Outputs
    wire [7:0] tubSel;
    wire [7:0] tubLeft;
    wire [7:0] tubRight;
    wire [31:0] instruction;
    wire [31:0] pc_current;
    // Instantiate CPU DUT
    CPU uut (
        .clk(clk),
        .reset(reset),
        .switchInput(switchInput),
        .enter(confirmation),
        .tubSel(tubSel),
        .seg_led1234(tubLeft),
        .seg_led5678(tubRight)
    );

    // Clock generation: 100MHz => 10ns period
    initial clk = 0;
    always #5 clk = ~clk;

    initial begin
        // Initialize input values
        reset = 0;
        switchInput = 16'h0000;
        confirmation = 0;

        // Dump waveforms for GTKWave
        $dumpfile("cpu_tb.vcd");
        $dumpvars(0, CPU_tb);

        // Release reset after 2 cycles
        #20;
        reset = 1;

        // Observe more time
        #500;

        #20;
        switchInput = 16'h0001;
        
        #20;
        confirmation = 1;

        #500;
        confirmation = 0;

        #40;
        switchInput = 16'h0003;
        
        #500;
        confirmation = 1;

        #20;
        confirmation = 0;

        //$finish;
    end


endmodule
