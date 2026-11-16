`timescale 1ns/1ps
// Simulation-only deterministic backing store spanning the 32-bit address space.
// Each word is address XOR A5A50000. This is not a synthesized DRAM controller.
module main_memory_model #(
    parameter integer LATENCY = 5
) (
    input clk,
    input reset,
    input mem_read,
    input [31:0] mem_addr,
    output mem_ready,
    output [127:0] mem_rdata,
    output reg [31:0] transaction_count
);
    reg active;
    reg [31:0] saved_base;
    integer remaining;
    function [31:0] memory_word;
        input [31:0] address;
        begin memory_word = address ^ 32'ha5a50000; end
    endfunction
    assign mem_ready = active && (remaining == 0) && !reset;
    assign mem_rdata = {
        memory_word(saved_base + 32'd12), memory_word(saved_base + 32'd8),
        memory_word(saved_base + 32'd4), memory_word(saved_base)
    };
    initial if (LATENCY < 1) $fatal(1, "LATENCY must be >= 1");
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            active <= 0;
            remaining <= 0;
            saved_base <= 0;
            transaction_count <= 0;
        end else if (!active && mem_read) begin
            active <= 1;
            saved_base <= mem_addr;
            remaining <= LATENCY - 1;
        end else if (active) begin
            if (mem_ready && mem_read) begin
                active <= 0;
                transaction_count <= transaction_count + 1'b1;
            end else if (remaining > 0) remaining <= remaining - 1;
        end
    end
endmodule
