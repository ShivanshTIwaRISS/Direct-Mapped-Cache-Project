module valid_bit_ram (
    input clk,
    input reset,
    input write_en,
    input [5:0] index,
    output valid
);
    reg [63:0] valid_bits;
    always @(posedge clk or posedge reset)
        if (reset) valid_bits <= 64'b0;
        else if (write_en) valid_bits[index] <= 1'b1;
    assign valid = valid_bits[index];
endmodule
