// 64 lines x 128 bits = 1 KiB. No reset: validity guards uninitialized data.
module cache_data_ram (
    input clk,
    input write_en,
    input [5:0] index,
    input [127:0] write_data,
    input [1:0] word_offset,
    output [31:0] read_data
);
    reg [127:0] lines [0:63];
    always @(posedge clk)
        if (write_en) lines[index] <= write_data;
    assign read_data = lines[index][word_offset * 32 +: 32];
endmodule
