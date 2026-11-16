module tag_ram (
    input clk,
    input write_en,
    input [5:0] index,
    input [21:0] write_tag,
    output [21:0] read_tag
);
    reg [21:0] tags [0:63];
    always @(posedge clk)
        if (write_en) tags[index] <= write_tag;
    assign read_tag = tags[index];
endmodule
