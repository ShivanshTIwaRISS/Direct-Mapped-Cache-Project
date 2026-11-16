//==============================================================================
// Module      : cache_fsm
// Project     : Direct-Mapped Cache Controller (Phase I Prototype)
// Author      : Samarth Khera (2401010407)
// Institution : Rishihood University - Department of Computer Science and AI
//
// Description:
//   Finite State Machine (FSM) Controller for a 1 KiB Direct-Mapped Read Cache.
//   Orchestrates request acceptance, cache lookup comparison, memory refill
//   burst allocation, and stable response handshaking.
//
// State Encoding:
//   - IDLE     (2'b00): Awaiting CPU memory request. req_ready asserted.
//   - COMPARE  (2'b01): Evaluating hit/miss via tag match and valid bit.
//   - ALLOCATE (2'b10): Refilling 16-byte block from main memory upon miss.
//   - RESPOND  (2'b11): Holding data & status stable until accepted by CPU.
//
// Handshaking Protocol:
//   - CPU Request  : Accepted when (req_valid && req_ready).
//   - CPU Response : Retired when (resp_valid && resp_ready).
//   - Memory Refill: Line captured when (mem_read && mem_ready).
//
// Latency Characteristics (Default Memory Latency L = 5):
//   - Cache Hit  : 1 clock cycle (IDLE -> COMPARE -> RESPOND -> IDLE)
//   - Cache Miss : 7 clock cycles (1 lookup + 1 req + 4 wait + 1 refill)
//==============================================================================

`timescale 1ns / 1ps

module cache_fsm (
    // Clock and Reset
    input  wire       clk,         // System clock
    input  wire       reset,       // Asynchronous active-high reset

    // CPU / Master Interface
    input  wire       mem_req,     // CPU memory request strobe
    input  wire       cache_hit,   // Tag comparator hit (or bypass error condition)
    input  wire       resp_ready,  // CPU ready to accept returned data

    // Main Memory Interface
    input  wire       mem_ready,   // Main memory line transfer completion strobe

    // Cache Control Outputs
    output reg        stall,       // Pipeline stall indicator
    output reg        mem_read,    // Read request to main memory endpoint
    output wire       req_ready,   // Ready to accept a new CPU request
    output wire       compare_en,  // Enable signal for tag and data comparison
    output wire       refill_en,   // Enable atomic installation of refilled block
    output wire       resp_valid,  // Response valid flag to CPU
    output wire [1:0] state_debug  // State debug output
);

    // FSM State Encoding
    localparam IDLE     = 2'b00,
               COMPARE  = 2'b01,
               ALLOCATE = 2'b10,
               RESPOND  = 2'b11;

    // State Registers
    reg [1:0] state;
    reg [1:0] next_state;

    // Combinational Output Control Signals
    assign req_ready   = (state == IDLE) && !reset;
    assign compare_en  = (state == COMPARE) && !reset;
    assign refill_en   = (state == ALLOCATE) && mem_ready && !reset;
    assign resp_valid  = (state == RESPOND) && !reset;
    assign state_debug = state;

    // State Register Sequential Logic (Asynchronous Active-High Reset)
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= IDLE;
        end else begin
            state <= next_state;
        end
    end

    // Next-State Combinational Logic & Output Assignments
    always @(*) begin
        // Default output values
        stall      = !req_ready;
        mem_read   = 0;
        next_state = state;

        case (state)
            //------------------------------------------------------------------
            // IDLE: Wait for CPU memory request
            //------------------------------------------------------------------
            IDLE: begin
                if (mem_req && !reset) begin
                    next_state = COMPARE;
                end
            end

            //------------------------------------------------------------------
            // COMPARE: Evaluate tag comparison and valid bit status
            //------------------------------------------------------------------
            COMPARE: begin
                if (cache_hit) begin
                    // Cache Hit: data is ready, transition to RESPOND
                    next_state = RESPOND;
                end else begin
                    // Cache Miss: stall pipeline and initiate memory refill
                    next_state = ALLOCATE;
                end
            end

            //------------------------------------------------------------------
            // ALLOCATE: Hold memory read request until line refill completes
            //------------------------------------------------------------------
            ALLOCATE: begin
                mem_read = !reset;
                if (mem_ready) begin
                    // Block transfer complete: data installed atomically
                    next_state = RESPOND;
                end
            end

            //------------------------------------------------------------------
            // RESPOND: Hold valid data stable until CPU acknowledges
            //------------------------------------------------------------------
            RESPOND: begin
                if (resp_ready) begin
                    // Transaction retired: return to IDLE for next request
                    next_state = IDLE;
                end
            end

            //------------------------------------------------------------------
            // Default Safe Fallback
            //------------------------------------------------------------------
            default: begin
                next_state = IDLE;
            end
        endcase
    end

endmodule
