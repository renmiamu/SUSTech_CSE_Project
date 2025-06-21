module Data_mem (
    input clk,                  // CPU 主时钟
    input m_read,               // CPU 读使能（用于控制 CPU 端逻辑）
    input m_write,              // CPU 写使能
    input [31:0] addr,          // CPU 地址
    input [31:0] d_in,          // CPU 写数据
    output [31:0] d_out,        // RAM 输出数据

    // UART 编程接口
    input         upg_rst_i,    // UART reset
    input         upg_clk_i,    // UART 写时钟（10MHz）
    input         upg_wen_i,    // UART 写使能
    input  [13:0] upg_adr_i,    // UART 地址
    input  [31:0] upg_dat_i,    // UART 写数据
    input         upg_done_i    // UART 完成标志
);
    
    wire ram_clk = !clk;
    // 模式切换信号：为1时 CPU 正常工作，为0时 UART 编程中
    wire kickOff = upg_rst_i | (~upg_rst_i & upg_done_i);
    
    wire [13:0] ram_addr = kickOff ? addr[15:2] : upg_adr_i;
        
    wire [31:0] ram_data = kickOff ? d_in        : upg_dat_i;
    // 时钟、写使能、地址、写数据，按模式多路选择
    wire ram_we   = kickOff ? m_write     : upg_wen_i;
    
    

    // RAM 实例（建议使用 IP Catalog 生成的单端口 RAM）
    RAM udram (
        .clka   (kickOff ? ram_clk : upg_clk_i),
        .wea    (ram_we),
        .addra  (ram_addr),
        .dina   (ram_data),
        .douta  (d_out)
    );

endmodule
