//==============================================================================
// Module      : tag_comparator
// Project     : Direct-Mapped Cache Controller (Phase I Prototype)
// Description :
//   Combinational tag-match detector. Asserts hit only when the indexed cache
//   line is valid AND its stored 22-bit tag matches the requested tag.
//==============================================================================

module tag_comparator (
    input  wire        valid,         // Valid bit for the indexed cache line
    input  wire [21:0] stored_tag,    // 22-bit tag currently held in tag_ram
    input  wire [21:0] requested_tag, // 22-bit tag decoded from CPU address
    output wire        hit            // Asserted on valid tag match
);

    // Hit requires both validity and exact 22-bit tag equality
    assign hit = valid && (stored_tag == requested_tag);

endmodule
