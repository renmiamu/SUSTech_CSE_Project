`timescale 1ns / 1ps

//²¿·Ö´úÂë²Î¿¼ÁËÍøÂçÊµÏÖ£º
//https://github.com/RoderickQiu/CS202-Project
module vga (
    input clk,
    input rst,  // active low reset
    input [3:0] s1, s2, s3, s4, s5, s6, s7, s8,
    output reg [3:0] r,
    output reg [3:0] g,
    output reg [3:0] b,
    output hs,
    output vs
);

    // VGA bounds
    parameter UP_BOUND    = 31;
    parameter DOWN_BOUND  = 510;
    parameter LEFT_BOUND  = 144;
    parameter RIGHT_BOUND = 783;

    parameter up_pos_0    = 267;
    parameter down_pos_0  = 274;
    parameter left_pos    = 400;              // ä¸ºé?‚åº”8å­—ç¬¦ç¨å¾®å·¦ç§»
    parameter right_pos   = left_pos + 8*7-1; // 8ä¸ªå­—ç¬? Ã— æ¯å­—ç¬?7åˆ? = 56åˆ?

    wire pclk;
    reg [1:0] count;
    reg [9:0] hcount, vcount;
    wire [7:0] p0[0:55];  // 8ä¸ªå­—ç¬? Ã— æ¯å­—ç¬?7åˆ? = 56åˆ?

    // Generate character columns
    vga_char_set p1 (.clk(clk), .rst(rst), .data(s1), .col0(p0[0]),  .col1(p0[1]),  .col2(p0[2]),  .col3(p0[3]),  .col4(p0[4]),  .col5(p0[5]),  .col6(p0[6]));
    vga_char_set p2 (.clk(clk), .rst(rst), .data(s2), .col0(p0[7]),  .col1(p0[8]),  .col2(p0[9]),  .col3(p0[10]), .col4(p0[11]), .col5(p0[12]), .col6(p0[13]));
    vga_char_set p3 (.clk(clk), .rst(rst), .data(s3), .col0(p0[14]), .col1(p0[15]), .col2(p0[16]), .col3(p0[17]), .col4(p0[18]), .col5(p0[19]), .col6(p0[20]));
    vga_char_set p4 (.clk(clk), .rst(rst), .data(s4), .col0(p0[21]), .col1(p0[22]), .col2(p0[23]), .col3(p0[24]), .col4(p0[25]), .col5(p0[26]), .col6(p0[27]));
    vga_char_set p5 (.clk(clk), .rst(rst), .data(s5), .col0(p0[28]), .col1(p0[29]), .col2(p0[30]), .col3(p0[31]), .col4(p0[32]), .col5(p0[33]), .col6(p0[34]));
    vga_char_set p6 (.clk(clk), .rst(rst), .data(s6), .col0(p0[35]), .col1(p0[36]), .col2(p0[37]), .col3(p0[38]), .col4(p0[39]), .col5(p0[40]), .col6(p0[41]));
    vga_char_set p7 (.clk(clk), .rst(rst), .data(s7), .col0(p0[42]), .col1(p0[43]), .col2(p0[44]), .col3(p0[45]), .col4(p0[46]), .col5(p0[47]), .col6(p0[48]));
    vga_char_set p8 (.clk(clk), .rst(rst), .data(s8), .col0(p0[49]), .col1(p0[50]), .col2(p0[51]), .col3(p0[52]), .col4(p0[53]), .col5(p0[54]), .col6(p0[55]));

    // Pixel clock
    assign pclk = count[1];
    always @(posedge clk or negedge rst)
        if (!rst) count <= 0;
        else count <= count + 1;

    // HSYNC / VSYNC counters
    assign hs = (hcount < 96) ? 0 : 1;
    always @(posedge pclk or negedge rst)
        if (!rst) hcount <= 0;
        else if (hcount == 799) hcount <= 0;
        else hcount <= hcount + 1;

    assign vs = (vcount < 2) ? 0 : 1;
    always @(posedge pclk or negedge rst)
        if (!rst) vcount <= 0;
        else if (hcount == 799) begin
            if (vcount == 520) vcount <= 0;
            else vcount <= vcount + 1;
        end

    // RGB output logic
    always @(posedge pclk or negedge rst) begin
        if (!rst) begin
            r <= 0; g <= 0; b <= 0;
        end else if (vcount >= UP_BOUND && vcount <= DOWN_BOUND &&
                     hcount >= LEFT_BOUND && hcount <= RIGHT_BOUND) begin
            if (hcount >= left_pos && hcount <= right_pos) begin
                if (vcount >= up_pos_0 && vcount <= down_pos_0) begin
                    if (p0[hcount - left_pos][vcount - up_pos_0]) begin
                        r <= 4'b1111;
                        g <= 4'b1111;
                        b <= 4'b1111;
                    end else begin
                        r <= 0; g <= 0; b <= 0;
                    end
                end else begin
                    r <= 0; g <= 0; b <= 0;
                end
            end else begin
                r <= 0; g <= 0; b <= 0;
            end
        end else begin
            r <= 0; g <= 0; b <= 0;
        end
    end

endmodule
