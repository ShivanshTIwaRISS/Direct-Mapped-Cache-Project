`timescale 1ns/1ps
module cache_controller_tb;
    parameter integer MEMORY_LATENCY = 5;
    reg clk = 0;
    always #5 clk = ~clk;
    reg reset = 1, req_valid = 0, resp_ready = 0;
    reg [31:0] req_addr = 0;
    wire req_ready, resp_valid, resp_hit, resp_error, mem_read, mem_ready, stall;
    wire [31:0] resp_data, mem_addr, access_count, hit_count, miss_count, transactions;
    wire [127:0] mem_rdata;
    wire [1:0] state_debug;
    cache_controller dut(.*);
    main_memory_model #(.LATENCY(MEMORY_LATENCY)) memory (
        .clk(clk), .reset(reset), .mem_read(mem_read), .mem_addr(mem_addr),
        .mem_ready(mem_ready), .mem_rdata(mem_rdata), .transaction_count(transactions)
    );
    integer cycle = 0, checks = 0, latency, trace_count = 0;
    integer fd, out_fd, scanned, expected_hit, i;
    reg [31:0] address, expected_data;
    string trace_path, out_path, vcd_path;
    always @(posedge clk) cycle <= cycle + 1;

    task reset_system;
        begin
            @(negedge clk);
            reset = 1; req_valid = 0; resp_ready = 0;
            repeat (2) @(negedge clk);
            reset = 0;
            #1;
            if (!req_ready || resp_valid || mem_read || access_count !== 0)
                $fatal(1, "Reset did not clear control and counters");
        end
    endtask

    task read_check;
        input [31:0] addr;
        input want_hit, want_error;
        input [31:0] want_data;
        input integer hold_cycles;
        integer started, before_hits, before_misses, before_transactions, watchdog;
        begin
            @(negedge clk);
            if (!req_ready) $fatal(1, "Not ready before request");
            before_hits = hit_count; before_misses = miss_count;
            before_transactions = transactions;
            req_valid = 1; req_addr = addr; resp_ready = 0;
            @(posedge clk); #1; started = cycle;
            @(negedge clk);
            // Present another request while busy. It must not replace the saved address.
            req_addr = ~addr; req_valid = 1;
            watchdog = 0;
            while (!resp_valid) begin
                if (req_ready || !stall) $fatal(1, "Busy request was accepted");
                @(posedge clk); #1;
                watchdog = watchdog + 1;
                if (watchdog > 100) $fatal(1, "Response timeout at %h", addr);
            end
            latency = cycle - started;
            if (resp_hit !== want_hit || resp_error !== want_error || resp_data !== want_data)
                $fatal(1, "addr=%h hit=%b/%b error=%b/%b data=%h/%h",
                    addr, resp_hit, want_hit, resp_error, want_error, resp_data, want_data);
            if (latency != ((want_hit || want_error) ? 1 : MEMORY_LATENCY + 2))
                $fatal(1, "Unexpected response latency %0d", latency);
            if (hit_count !== before_hits + (want_hit && !want_error) ||
                miss_count !== before_misses + (!want_hit && !want_error) ||
                transactions !== before_transactions + (!want_hit && !want_error) ||
                access_count !== hit_count + miss_count)
                $fatal(1, "Counters or memory transaction count incorrect");
            repeat (hold_cycles) begin
                @(posedge clk); #1;
                if (!resp_valid || req_ready || mem_read || resp_data !== want_data ||
                    resp_hit !== want_hit || resp_error !== want_error ||
                    hit_count !== before_hits + (want_hit && !want_error) ||
                    miss_count !== before_misses + (!want_hit && !want_error) ||
                    transactions !== before_transactions + (!want_hit && !want_error))
                    $fatal(1, "Response changed or counted twice under backpressure");
            end
            @(negedge clk); req_valid = 0; resp_ready = 1;
            @(posedge clk); #1;
            if (!req_ready || resp_valid) $fatal(1, "Response did not retire");
            @(negedge clk); resp_ready = 0;
            checks = checks + 1;
        end
    endtask

    initial begin
        if ($value$plusargs("VCD=%s", vcd_path)) begin
            $dumpfile(vcd_path); $dumpvars(0, cache_controller_tb);
        end
        reset_system();
        // All four word offsets, cold tag zero, and index boundary.
        read_check(0, 0, 0, 32'ha5a50000, 3);
        read_check(4, 1, 0, 32'ha5a50004, 0);
        read_check(8, 1, 0, 32'ha5a50008, 0);
        read_check(12, 1, 0, 32'ha5a5000c, 0);
        read_check(16, 0, 0, 32'ha5a50010, 0);
        // Same index, different tag; replacement and subsequent hit.
        read_check(32'h400, 0, 0, 32'ha5a50400, 0);
        read_check(0, 0, 0, 32'ha5a50000, 0);
        read_check(0, 1, 0, 32'ha5a50000, 2);
        read_check(32'hfffffffc, 0, 0, 32'h5a5afffc, 0);
        read_check(32'hfffffff0, 1, 0, 32'h5a5afff0, 0);
        // Misalignment is rejected without an allocation or statistics update.
        read_check(1, 0, 1, 0, 2);
        read_check(2, 0, 1, 0, 0);
        read_check(3, 0, 1, 0, 0);
        // Fill every index, reset, and prove every previously valid line is invalid.
        reset_system();
        for (i = 0; i < 64; i = i + 1)
            read_check(i * 16, 0, 0, (i * 16) ^ 32'ha5a50000, 0);
        reset_system();
        for (i = 0; i < 64; i = i + 1)
            read_check(i * 16, 0, 0, (i * 16) ^ 32'ha5a50000, 0);
        // Abort an outstanding miss. Reset must also reset the memory endpoint.
        reset_system();
        @(negedge clk); req_valid = 1; req_addr = 32'h2000;
        @(posedge clk); #1;
        @(negedge clk); req_valid = 0;
        wait(mem_read); @(posedge clk); #1;
        reset_system();
        read_check(32'h2000, 0, 0, 32'ha5a52000, 0);
        // Reset while a response is pending.
        @(negedge clk); req_valid = 1; req_addr = 32'h2000;
        @(posedge clk); #1;
        @(negedge clk); req_valid = 0;
        wait(resp_valid); reset_system();
        if (resp_valid) $fatal(1, "Stale response survived reset");

        if (!$value$plusargs("TRACE=%s", trace_path)) trace_path = "traces/demo.trace";
        if (!$value$plusargs("OUT=%s", out_path)) out_path = "build/demo.csv";
        fd = $fopen(trace_path, "r"); out_fd = $fopen(out_path, "w");
        if (!fd || !out_fd) $fatal(1, "Could not open trace/output");
        $fwrite(out_fd, "access,address,hit,data,latency_cycles\n");
        while (!$feof(fd)) begin
            scanned = $fscanf(fd, "%h %d %h\n", address, expected_hit, expected_data);
            if (scanned == 3) begin
                if (expected_hit != 0 && expected_hit != 1) $fatal(1, "Invalid expected hit");
                read_check(address, expected_hit != 0, 0, expected_data,
                           (trace_count % 17 == 0) ? 2 : 0);
                trace_count = trace_count + 1;
                $fwrite(out_fd, "%0d,%08h,%0d,%08h,%0d\n",
                        trace_count, address, resp_hit, resp_data, latency);
            end else if (!$feof(fd)) $fatal(1, "Malformed trace");
        end
        if (!trace_count) $fatal(1, "Empty trace");
        if (access_count !== trace_count || transactions !== miss_count)
            $fatal(1, "Trace totals incorrect");
        $fclose(fd); $fclose(out_fd);
        $display("PASS trace=%s accesses=%0d hits=%0d misses=%0d checks=%0d memory_latency=%0d",
                 trace_path, access_count, hit_count, miss_count, checks, MEMORY_LATENCY);
        $finish;
    end
    initial begin
        #10000000; $fatal(1, "Global simulation watchdog");
    end
endmodule
