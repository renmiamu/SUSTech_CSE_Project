module cpuclk_tb();  // a reference testbench for 'cpuclk' 
    reg clkin;
    wire clkout;

    cpuclk clk1( .clk_in1(clkin), .clk_out1(clkout) );

    initial clkin = 1'b0;
    always #5 clkin = ~clkin;  // 10ns 时钟周期

    // 控制仿真持续时间
    initial begin
        #3000;  // 仿真持续 10000ns
        $finish; // 结束仿真
    end
endmodule
