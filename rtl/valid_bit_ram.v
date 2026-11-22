//==============================================================================
// Module      : valid_bit_ram
// Project     : Direct-Mapped Cache Controller (Phase I Prototype)
// Description :
//   64-bit valid flag array (1 bit per cache line).
//   Asynchronous active-high reset clears all valid bits to prevent false hits
//   from uninitialized tag/data storage after startup or reset.
//==============================================================================

module valid_bit_ram (
    input  wire       clk,      // System clock
    input  wire       reset,    // Asynchronous active-high reset
    input  wire       write_en, // Sets valid bit during atomic line refill
    input  wire [5:0] index,    // 6-bit cache line index (0 to 63)
    output wire       valid     // Current valid status for indexed line
);

    // 64-bit register storing validity for lines 0 through 63
    reg [63:0] valid_bits;

    // Clear all valid bits on reset; mark indexed line valid on refill
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            valid_bits <= 64'b0;
        end else if (write_en) begin
            valid_bits[index] <= 1'b1;
        end
    end

    // Combinational valid-bit lookup
    assign valid = valid_bits[index];

endmodule
