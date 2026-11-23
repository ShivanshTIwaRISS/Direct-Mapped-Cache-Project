//==============================================================================
// Module      : main_memory_model
// Project     : Direct-Mapped Cache Controller (Phase I Prototype)
// Description :
//   Simulation-only deterministic backing store spanning the 32-bit address
//   space. Each 32-bit word is computed as (address XOR 32'hA5A50000), allowing
//   full-address-space verification without allocating 4 GiB of simulation RAM.
//   This is a behavioral testbench model, not a synthesized DRAM controller.
//==============================================================================

`timescale 1ns/1ps

module main_memory_model #(
    parameter integer LATENCY = 5  // Configurable memory access latency (cycles >= 1)
) (
    input  wire         clk,               // System clock
    input  wire         reset,             // Asynchronous active-high reset
    input  wire         mem_read,          // Read request held active during ALLOCATE
    input  wire [31:0]  mem_addr,          // 16-byte aligned base address
    output wire         mem_ready,         // Asserted when 128-bit line data is ready
    output wire [127:0] mem_rdata,         // 16-byte block (4 x 32-bit words)
    output reg  [31:0]  transaction_count  // Total completed refill transactions
);

    // Internal request tracking registers
    reg        active;
    reg [31:0] saved_base;
    integer    remaining;

    // Deterministic data pattern across the full 32-bit address space
    function [31:0] memory_word;
        input [31:0] address;
        begin
            memory_word = address ^ 32'ha5a50000;
        end
    endfunction

    // Handshake ready when countdown reaches zero
    assign mem_ready = active && (remaining == 0) && !reset;

    // Pack 4 consecutive 32-bit words into the 128-bit cache line response
    assign mem_rdata = {
        memory_word(saved_base + 32'd12),
        memory_word(saved_base + 32'd8),
        memory_word(saved_base + 32'd4),
        memory_word(saved_base)
    };

    // Guard against invalid latency parameter configuration
    initial begin
        if (LATENCY < 1) begin
            $fatal(1, "LATENCY must be >= 1");
        end
    end

    // Sequential latency countdown and transaction counter
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            active            <= 0;
            remaining         <= 0;
            saved_base        <= 0;
            transaction_count <= 0;
        end else if (!active && mem_read) begin
            active     <= 1;
            saved_base <= mem_addr;
            remaining  <= LATENCY - 1;
        end else if (active) begin
            if (mem_ready && mem_read) begin
                active            <= 0;
                transaction_count <= transaction_count + 32'd1;
            end else if (remaining > 0) begin
                remaining <= remaining - 1;
            end
        end
    end

endmodule
