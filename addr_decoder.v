//==============================================================================
// Module      : addr_decoder
// Project     : Direct-Mapped Cache Controller (Phase I Prototype)
// Author      : Samarth Khera (2401010407)
// Institution : Rishihood University - Department of Computer Science and AI
//
// Description:
//   Address Decoder module for a 1 KiB Direct-Mapped Cache.
//   Decomposes a 32-bit byte address into cache Tag, Index, and Block Offset.
//
// Cache Architecture Geometry:
//   - Total Cache Capacity : 1024 Bytes (1 KiB)
//   - Block (Line) Size    : 16 Bytes (128 bits = 4 words of 32 bits each)
//   - Number of Lines      : 1024 Bytes / 16 Bytes = 64 Cache Lines
//   - Mapping Scheme       : Direct-Mapped (1 line per set, 64 sets)
//
// Bit-Field Allocation (32-bit Byte Address):
//   +----------------------------+---------------------+-------------------+
//   |         Tag [31:10]        |     Index [9:4]     |   Offset [3:0]    |
//   |           22 bits          |        6 bits       |      4 bits       |
//   +----------------------------+---------------------+-------------------+
//   - Offset [3:0] (4 bits) : Selects byte within the 16-byte cache line.
//       * Offset [3:2] (2 bits): Selects 1 of 4 words (Word 0 to 3).
//       * Offset [1:0] (2 bits): Byte offset within 32-bit word (must be 0 for aligned access).
//   - Index  [9:4] (6 bits) : Selects 1 of 64 cache lines (2^6 = 64 lines).
//   - Tag    [31:10](22 bits): Stored in tag RAM and compared against lookup address.
//==============================================================================

`timescale 1ns / 1ps

module addr_decoder (
    input  wire [31:0] address, // 32-bit memory address from CPU/requester
    output wire [21:0] tag,     // 22-bit Tag for cache line identification
    output wire [5:0]  index,   // 6-bit Cache Line Index (0 to 63)
    output wire [3:0]  offset   // 4-bit Block Offset (byte within 16-byte block)
);

    // Continuous assignments for purely combinational address decoding
    assign offset = address[3:0];   // 4 bits for 16-byte block offset
    assign index  = address[9:4];   // 6 bits for 64 cache lines
    assign tag    = address[31:10]; // Remaining 22 bits for Tag

endmodule
