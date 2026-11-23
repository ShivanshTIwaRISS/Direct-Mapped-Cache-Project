//==============================================================================
// Module      : protocol_stress_tb
// Project     : Direct-Mapped Cache Controller (Phase I Hardening)
// Author      : Tattva Rajput (2401010478)
// Institution : Rishihood University - Department of Computer Science and AI
//
// Description:
//   Advanced Protocol Stress, Assertion Monitor, and Corner-Case Testbench.
//   Exercises unverified protocol dimensions without modifying baseline testbench:
//     1. Continuous cycle-by-cycle SVA-style protocol assertions.
//     2. Sustained & randomized response backpressure (0-16 cycle stalls).
//     3. Exhaustive cycle-by-cycle reset-abort sweep across all FSM states.
//     4. Torture misalignment interleaving with valid accesses and high tags.
//     5. Wide memory-latency sweep (L = 1..20) and jittered dynamic delay.
//==============================================================================

`timescale 1ns/1ps

module protocol_stress_tb;

    // Clock and Reset Signals
    reg clk = 0;
    always #5 clk = ~clk;

    reg         reset      = 1;
    reg         req_valid  = 0;
    reg  [31:0] req_addr   = 0;
    wire        req_ready;

    wire        resp_valid;
    reg         resp_ready = 0;
    wire [31:0] resp_data;
    wire        resp_hit;
    wire        resp_error;

    wire        mem_read;
    wire [31:0] mem_addr;
    wire        mem_ready;
    wire [127:0] mem_rdata;

    wire [31:0] access_count;
    wire [31:0] hit_count;
    wire [31:0] miss_count;
    wire        stall;
    wire [1:0]  state_debug;
    wire [31:0] transactions;

    // Configurable Memory Latency for Stress Tests
    integer current_mem_latency = 5;

    // Instantiate Device Under Test (DUT) with explicit named ports
    cache_controller dut (
        .clk          (clk),
        .reset        (reset),
        .req_valid    (req_valid),
        .req_ready    (req_ready),
        .req_addr     (req_addr),
        .resp_valid   (resp_valid),
        .resp_ready   (resp_ready),
        .resp_data    (resp_data),
        .resp_hit     (resp_hit),
        .resp_error   (resp_error),
        .mem_read     (mem_read),
        .mem_addr     (mem_addr),
        .mem_ready    (mem_ready),
        .mem_rdata    (mem_rdata),
        .access_count (access_count),
        .hit_count    (hit_count),
        .miss_count   (miss_count),
        .stall        (stall),
        .state_debug  (state_debug)
    );

    // Dynamic Main Memory Model Supporting Variable Latency
    reg        mem_active = 0;
    reg [31:0] mem_saved_base = 0;
    integer    mem_remaining = 0;
    reg [31:0] mem_tx_count = 0;

    assign transactions = mem_tx_count;

    function [31:0] memory_word;
        input [31:0] address;
        begin
            memory_word = address ^ 32'ha5a50000;
        end
    endfunction

    assign mem_ready = mem_active && (mem_remaining == 0) && !reset;
    assign mem_rdata = {
        memory_word(mem_saved_base + 32'd12),
        memory_word(mem_saved_base + 32'd8),
        memory_word(mem_saved_base + 32'd4),
        memory_word(mem_saved_base)
    };

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            mem_active    <= 0;
            mem_remaining <= 0;
            mem_saved_base <= 0;
            mem_tx_count  <= 0;
        end else if (!mem_active && mem_read) begin
            mem_active     <= 1;
            mem_saved_base <= mem_addr;
            mem_remaining  <= current_mem_latency - 1;
        end else if (mem_active) begin
            if (mem_ready && mem_read) begin
                mem_active   <= 0;
                mem_tx_count <= mem_tx_count + 32'd1;
            end else if (mem_remaining > 0) begin
                mem_remaining <= mem_remaining - 1;
            end
        end
    end

    // Telemetry and Tracking Counters
    integer total_assertions_checked = 0;
    integer completed_reads          = 0;
    integer completed_aligned_reads  = 0;

    //==========================================================================
    // Protocol Invariant Assertion Monitors (Checked Every Clock Cycle)
    //==========================================================================
    reg        prev_resp_valid = 0;
    reg [31:0] prev_resp_data  = 0;
    reg        prev_resp_hit   = 0;
    reg        prev_resp_error = 0;

    always @(posedge clk) begin
        if (!reset) begin
            total_assertions_checked <= total_assertions_checked + 6;

            // Invariant 1: Response Stability Under Backpressure
            // If resp_valid is held high without resp_ready, data and flags MUST NOT glitch
            if (prev_resp_valid && !resp_ready) begin
                if (resp_data !== prev_resp_data ||
                    resp_hit  !== prev_resp_hit  ||
                    resp_error !== prev_resp_error) begin
                    $fatal(1, "[ASSERTION FAILED] Response changed under backpressure! data=%h/%h hit=%b/%b error=%b/%b",
                           resp_data, prev_resp_data, resp_hit, prev_resp_hit, resp_error, prev_resp_error);
                end
            end

            // Invariant 2: Mutual Exclusion of Hit and Error
            if (resp_valid && resp_hit && resp_error) begin
                $fatal(1, "[ASSERTION FAILED] resp_hit and resp_error simultaneously asserted!");
            end

            // Invariant 3: Request Acceptance Mutual Exclusion (req_ready only in IDLE)
            if (req_ready && (state_debug !== 2'b00)) begin
                $fatal(1, "[ASSERTION FAILED] req_ready asserted outside IDLE state (state=%b)!", state_debug);
            end

            // Invariant 4: Stall Indicator Coherence
            if (stall !== (state_debug !== 2'b00)) begin
                $fatal(1, "[ASSERTION FAILED] stall signal mismatch with FSM state (stall=%b, state=%b)!", stall, state_debug);
            end

            // Invariant 5: Memory Read Only in ALLOCATE
            if (mem_read && (state_debug !== 2'b10)) begin
                $fatal(1, "[ASSERTION FAILED] mem_read asserted outside ALLOCATE state (state=%b)!", state_debug);
            end

            // Invariant 6: Strict Counter Conservation
            if (access_count !== (hit_count + miss_count)) begin
                $fatal(1, "[ASSERTION FAILED] access_count (%0d) != hit_count (%0d) + miss_count (%0d)!",
                       access_count, hit_count, miss_count);
            end
        end

        prev_resp_valid <= resp_valid && !reset;
        prev_resp_data  <= resp_data;
        prev_resp_hit   <= resp_hit;
        prev_resp_error <= resp_error;
    end

    //==========================================================================
    // Helper Tasks
    //==========================================================================
    task reset_dut;
        begin
            @(negedge clk);
            reset      = 1;
            req_valid  = 0;
            req_addr   = 0;
            resp_ready = 0;
            repeat (3) @(negedge clk);
            reset = 0;
            #1;
            if (!req_ready || resp_valid || mem_read || access_count !== 0) begin
                $fatal(1, "Reset did not fully clear DUT state");
            end
        end
    endtask

    // Transaction Driver with Dynamic Hold Cycles
    task execute_read(
        input  [31:0] addr,
        input         want_hit,
        input         want_error,
        input  [31:0] want_data,
        input  integer stall_cycles,
        output integer observed_latency
    );
        integer start_cycle;
        integer timeout;
        begin
            @(negedge clk);
            while (!req_ready) @(negedge clk);

            req_valid  = 1;
            req_addr   = addr;
            resp_ready = 0;

            @(posedge clk); #1;
            start_cycle = $time / 10;

            @(negedge clk);
            // Present opposing address while busy to prove latching stability
            req_addr  = ~addr;
            req_valid = 1;

            timeout = 0;
            while (!resp_valid) begin
                @(posedge clk); #1;
                timeout = timeout + 1;
                if (timeout > 200) $fatal(1, "Timeout waiting for response at addr=%h", addr);
            end

            observed_latency = ($time / 10) - start_cycle;

            // Verify Response Correctness
            if (resp_hit !== want_hit || resp_error !== want_error || resp_data !== want_data) begin
                $fatal(1, "Read mismatch at %h: hit=%b (exp %b), error=%b (exp %b), data=%h (exp %h)",
                       addr, resp_hit, want_hit, resp_error, want_error, resp_data, want_data);
            end

            // Apply Sustained Backpressure
            repeat (stall_cycles) begin
                @(posedge clk); #1;
                if (!resp_valid) $fatal(1, "resp_valid dropped prematurely during backpressure!");
            end

            // Retire Transaction
            @(negedge clk);
            req_valid  = 0;
            resp_ready = 1;

            @(posedge clk); #1;
            if (resp_valid && resp_ready && (state_debug == 2'b11)) begin
                // In RESPOND, retiring on this edge
            end

            @(negedge clk);
            resp_ready = 0;
            completed_reads = completed_reads + 1;
            if (!want_error) begin
                completed_aligned_reads = completed_aligned_reads + 1;
            end
        end
    endtask

    //==========================================================================
    // Test Suites Execution
    //==========================================================================
    integer lat_out;
    integer i, k;

    initial begin
        $display("=================================================================");
        $display("STARTING PROTOCOL STRESS & CORNER-CASE VERIFICATION SUITE");
        $display("=================================================================");

        reset_dut();

        //----------------------------------------------------------------------
        // Suite 1: Sustained & Randomized Backpressure Stress (0 to 16 cycles)
        //----------------------------------------------------------------------
        $display("[SUITE 1] Testing Sustained and Randomized Backpressure (0-16 cycles)...");
        for (i = 0; i < 32; i = i + 1) begin
            // Alternate misses and hits with pseudo-random backpressure stalls
            integer stalls;
            stalls = (i * 7 + 3) % 17; // 0 through 16 stall cycles
            execute_read(i * 16, 0, 0, (i * 16) ^ 32'ha5a50000, stalls, lat_out);
            execute_read(i * 16 + 4, 1, 0, (i * 16 + 4) ^ 32'ha5a50000, stalls / 2, lat_out);
        end
        $display("  -> Suite 1 Passed: 64 transactions with 0-16 cycle backpressure verified.");

        //----------------------------------------------------------------------
        // Suite 2: Exhaustive Cycle-by-Cycle Reset Abort Sweep
        //----------------------------------------------------------------------
        $display("[SUITE 2] Testing Cycle-by-Cycle Reset Aborts Across All FSM States...");
        // Test aborting at every cycle of ALLOCATE (latency 5 = cycles 1, 2, 3, 4, 5, 6)
        for (k = 1; k <= 7; k = k + 1) begin
            reset_dut();
            // Start a clean miss
            @(negedge clk);
            req_valid = 1;
            req_addr  = 32'h0000_1000 + (k * 16);
            @(posedge clk); #1;
            @(negedge clk);
            req_valid = 0;

            // Wait k cycles after request acceptance, then assert asynchronous reset
            repeat (k) @(posedge clk);
            #2 reset = 1;
            @(negedge clk);
            reset = 0;
            #1;

            // Verify DUT completely recovered to IDLE with 0 valid bits
            if (!req_ready || resp_valid || mem_read || access_count !== 0) begin
                $fatal(1, "[RESET SWEEP FAILED] DUT failed to recover cleanly after abort at cycle %0d", k);
            end

            // Re-request the same address to prove no stale or corrupted line survived
            execute_read(32'h0000_1000 + (k * 16), 0, 0, (32'h0000_1000 + (k * 16)) ^ 32'ha5a50000, 1, lat_out);
        end
        $display("  -> Suite 2 Passed: Cycle-by-cycle reset-abort sweep cleanly verified.");

        //----------------------------------------------------------------------
        // Suite 3: Torture Misalignment Interleaving
        //----------------------------------------------------------------------
        $display("[SUITE 3] Testing Torture Misaligned Access Interleaving...");
        reset_dut();
        // Pre-fill cache lines at indices 5 and 6
        execute_read(32'h0000_0050, 0, 0, 32'h0000_0050 ^ 32'ha5a50000, 0, lat_out);
        execute_read(32'h0000_0060, 0, 0, 32'h0000_0060 ^ 32'ha5a50000, 0, lat_out);

        // Interleave misaligned accesses with different byte offsets (01, 10, 11) and high tags
        execute_read(32'hDEAD_0051, 0, 1, 32'h0000_0000, 3, lat_out); // offset 1
        execute_read(32'hCAFE_0052, 0, 1, 32'h0000_0000, 1, lat_out); // offset 2
        execute_read(32'hBEEF_0053, 0, 1, 32'h0000_0000, 5, lat_out); // offset 3

        // Verify previously cached valid line was NOT corrupted by misaligned writes
        execute_read(32'h0000_0050, 1, 0, 32'h0000_0050 ^ 32'ha5a50000, 0, lat_out);
        execute_read(32'h0000_0064, 1, 0, 32'h0000_0064 ^ 32'ha5a50000, 0, lat_out);

        // Verify hit/miss counters only counted the 4 aligned accesses
        if (access_count !== 4 || hit_count !== 2 || miss_count !== 2) begin
            $fatal(1, "[MISALIGNMENT FAILED] Counters corrupted by misaligned access! access=%0d, hit=%0d, miss=%0d",
                   access_count, hit_count, miss_count);
        end
        $display("  -> Suite 3 Passed: Misaligned access torture interleaving verified.");

        //----------------------------------------------------------------------
        // Suite 4: Wide Memory Latency Sweep (L = 1, 2, 3, 4, 7, 10, 16, 20)
        //----------------------------------------------------------------------
        $display("[SUITE 4] Testing Wide Memory Latency Sweep (L = 1..20)...");
        reset_dut();
        begin
            integer test_lats[0:7];
            integer l_idx, l_val;
            test_lats[0] = 1;  test_lats[1] = 2;  test_lats[2] = 3;  test_lats[3] = 4;
            test_lats[4] = 7;  test_lats[5] = 10; test_lats[6] = 16; test_lats[7] = 20;

            for (l_idx = 0; l_idx < 8; l_idx = l_idx + 1) begin
                l_val = test_lats[l_idx];
                current_mem_latency = l_val;
                // Miss latency must strictly equal L + 2 cycles
                execute_read(32'h0001_0000 + (l_idx * 16), 0, 0, (32'h0001_0000 + (l_idx * 16)) ^ 32'ha5a50000, 0, lat_out);
                if (lat_out !== (l_val + 2)) begin
                    $fatal(1, "[LATENCY SWEEP FAILED] Miss latency %0d != expected %0d for L=%0d", lat_out, l_val + 2, l_val);
                end
                // Hit latency must strictly equal 1 cycle regardless of memory latency
                execute_read(32'h0001_0000 + (l_idx * 16) + 4, 1, 0, (32'h0001_0000 + (l_idx * 16) + 4) ^ 32'ha5a50000, 0, lat_out);
                if (lat_out !== 1) begin
                    $fatal(1, "[LATENCY SWEEP FAILED] Hit latency %0d != expected 1 for L=%0d", lat_out, l_val);
                end
            end
        end
        $display("  -> Suite 4 Passed: Latency invariance across L=1..20 verified.");

        //----------------------------------------------------------------------
        // Suite 5: Dynamic Jittered Memory Delay (Variable per Request)
        //----------------------------------------------------------------------
        $display("[SUITE 5] Testing Dynamic Jittered Memory Delay...");
        reset_dut();
        for (i = 0; i < 20; i = i + 1) begin
            integer jit_l;
            jit_l = (i * 5 + 3) % 12 + 1; // Latency dynamically varies 1 to 12
            current_mem_latency = jit_l;
            execute_read(32'h0002_0000 + (i * 16), 0, 0, (32'h0002_0000 + (i * 16)) ^ 32'ha5a50000, 1, lat_out);
            if (lat_out !== (jit_l + 2)) begin
                $fatal(1, "[JITTER FAILED] Miss latency %0d != expected %0d for dynamic L=%0d", lat_out, jit_l + 2, jit_l);
            end
        end
        $display("  -> Suite 5 Passed: Dynamic jittered memory delay verified.");

        // Final Summary
        $display("=================================================================");
        $display("ALL PROTOCOL STRESS TESTS PASSED SUCCESSFULLY!");
        $display("  Completed Reads           : %0d", completed_reads);
        $display("  Completed Aligned Reads   : %0d", completed_aligned_reads);
        $display("  Protocol Assertions Evaluated : %0d", total_assertions_checked);
        $display("=================================================================");
        $finish;
    end

    // Global Simulation Watchdog (10 ms)
    initial begin
        #10000000;
        $fatal(1, "[WATCHDOG] Global simulation timeout in protocol_stress_tb");
    end

endmodule
