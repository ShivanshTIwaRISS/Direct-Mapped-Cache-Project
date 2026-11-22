//==============================================================================
// Module      : cache_data_ram
// Project     : Direct-Mapped Cache Controller (Phase I Prototype)
// Description :
//   64 lines x 128 bits = 1 KiB (1,024 bytes) data storage array.
//   Each line stores four 32-bit words; word_offset selects the target word.
//   No hardware reset: valid_bit_ram guards uninitialized entries against hits.
//==============================================================================

module cache_data_ram (
    input  wire         clk,         // System clock
    input  wire         write_en,    // Atomic 128-bit line write enable
    input  wire [5:0]   index,       // 6-bit cache line index (0 to 63)
    input  wire [127:0] write_data,  // 16-byte block returned from main memory
    input  wire [1:0]   word_offset, // Selects 1 of 4 words within the line
    output wire [31:0]  read_data    // Selected 32-bit word output
);

    // 64 x 128-bit storage array (1 KiB total data capacity)
    reg [127:0] lines [0:63];

    // Synchronous line refill write
    always @(posedge clk) begin
        if (write_en) begin
            lines[index] <= write_data;
        end
    end

    // Combinational word read slice based on word_offset (offset[3:2])
    assign read_data = lines[index][word_offset * 32 +: 32];

endmodule
