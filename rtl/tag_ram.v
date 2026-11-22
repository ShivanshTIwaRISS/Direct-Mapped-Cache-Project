//==============================================================================
// Module      : tag_ram
// Project     : Direct-Mapped Cache Controller (Phase I Prototype)
// Description :
//   64-entry x 22-bit tag storage array (1,408 bits total).
//   Stores upper address bits [31:10] for each direct-mapped cache line.
//==============================================================================

module tag_ram (
    input  wire        clk,       // System clock
    input  wire        write_en,  // Synchronous tag write enable on refill
    input  wire [5:0]  index,     // 6-bit cache line index (0 to 63)
    input  wire [21:0] write_tag, // 22-bit tag to install on refill
    output wire [21:0] read_tag   // 22-bit stored tag at indexed line
);

    // 64 x 22-bit tag memory array
    reg [21:0] tags [0:63];

    // Synchronous tag update during block allocation
    always @(posedge clk) begin
        if (write_en) begin
            tags[index] <= write_tag;
        end
    end

    // Combinational tag read for comparison
    assign read_tag = tags[index];

endmodule
