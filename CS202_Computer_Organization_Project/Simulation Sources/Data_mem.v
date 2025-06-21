`timescale 1ns / 1ps

module Data_mem_tb;

    // Testbench signals
    reg clk;
    reg m_read;
    reg m_write;
    reg [31:0] addr;
    reg [31:0] d_in;
    wire [31:0] d_out;

    // Instantiate your Data_mem module
    Data_mem uut (
        .clk(clk),
        .m_read(m_read),
        .m_write(m_write),
        .addr(addr),
        .d_in(d_in),
        .d_out(d_out)
    );

    // Clock generation: 10ns clock period
    always #5 clk = ~clk;

    initial begin
        // Initialize signals
        clk = 0;
        m_read = 0;
        m_write = 0;
        addr = 0;
        d_in = 0;


        #10;
        addr = 32'h00000010;
        d_in = 32'hDEADBEEF;
        m_write = 1;
        #10;                 
        m_write = 0;

        #10;
        addr = 32'h00000010;
        m_read = 1;
        #10;
        m_read = 0;

        #10;
        addr = 32'h00000020;
        d_in = 32'hCAFEBABE;
        m_write = 1;
        #10;
        m_write = 0;

        #10;
        addr = 32'h00000020;
        m_read = 1;
        #10;
        m_read = 0;

    end

endmodule
