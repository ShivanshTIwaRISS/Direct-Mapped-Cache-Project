//==============================================================================
// Module      : cache_controller
// Project     : Direct-Mapped Cache Controller (Phase I Prototype)
// Description :
//   Top-level blocking, read-only 1 KiB direct-mapped cache controller.
//   Accepts 32-bit byte addresses and returns aligned 32-bit data words.
//
// Interface Contracts:
//   - CPU Request  : Accepted on rising clk edge when (req_valid && req_ready).
//                    The requested address is latched into saved_addr.
//   - CPU Response : Retired on rising clk edge when (resp_valid && resp_ready).
//                    Data, hit, and error outputs stay stable until retirement.
//   - Main Memory  : Completes an aligned 16-byte (128-bit) line transfer on
//                    rising clk edge when (mem_read && mem_ready).
//
// Submodule Integration:
//   - addr_decoder   : Splits saved_addr into tag [31:10], index [9:4], offset [3:0].
//   - tag_ram        : 64-entry x 22-bit tag storage array.
//   - valid_bit_ram  : 64-bit resettable line-validity register array.
//   - cache_data_ram : 64-entry x 128-bit (1 KiB) data line storage array.
//   - tag_comparator : Combinational valid + tag equality hit detector.
//   - cache_fsm      : 4-state controller (IDLE, COMPARE, ALLOCATE, RESPOND).
//==============================================================================

module cache_controller (
    // Clock and Asynchronous Active-High Reset
    input  wire         clk,
    input  wire         reset,

    // CPU Request Channel
    input  wire         req_valid,
    output wire         req_ready,
    input  wire [31:0]  req_addr,

    // CPU Response Channel
    output wire         resp_valid,
    input  wire         resp_ready,
    output reg  [31:0]  resp_data,
    output reg          resp_hit,
    output reg          resp_error,

    // Main Memory Line-Refill Channel
    output wire         mem_read,
    output wire [31:0]  mem_addr,
    input  wire         mem_ready,
    input  wire [127:0] mem_rdata,

    // Performance Counters and Debug Status
    output wire [31:0]  access_count,
    output reg  [31:0]  hit_count,
    output reg  [31:0]  miss_count,
    output wire         stall,
    output wire [1:0]   state_debug
);

    // Latched request address and decoded address fields
    reg  [31:0] saved_addr;
    wire [21:0] tag;
    wire [5:0]  index;
    wire [3:0]  offset;

    // Internal control and datapath signals
    wire        valid;
    wire        hit;
    wire        compare_en;
    wire        refill_en;
    wire [21:0] stored_tag;
    wire [31:0] cached_word;

    // Alignment check: 32-bit word accesses require offset[1:0] == 2'b00
    wire        misaligned = |offset[1:0];

    // Address decomposition into Tag, Index, and Block Offset
    addr_decoder decoder (
        saved_addr,
        tag,
        index,
        offset
    );

    // Tag, Valid, and Data Storage Arrays
    tag_ram tags (
        clk,
        refill_en,
        index,
        tag,
        stored_tag
    );

    valid_bit_ram valids (
        clk,
        reset,
        refill_en,
        index,
        valid
    );

    cache_data_ram data (
        clk,
        refill_en,
        index,
        mem_rdata,
        offset[3:2],
        cached_word
    );

    // Combinational Hit/Miss Detection
    tag_comparator comparator (
        valid,
        stored_tag,
        tag,
        hit
    );

    // 4-State Cache Control FSM
    cache_fsm control (
        .clk        (clk),
        .reset      (reset),
        .mem_req    (req_valid),
        .cache_hit  (hit || misaligned),
        .mem_ready  (mem_ready),
        .resp_ready (resp_ready),
        .stall      (stall),
        .mem_read   (mem_read),
        .req_ready  (req_ready),
        .compare_en (compare_en),
        .refill_en  (refill_en),
        .resp_valid (resp_valid),
        .state_debug(state_debug)
    );

    // 16-byte aligned base address sent to main memory on refill
    assign mem_addr     = {saved_addr[31:4], 4'b0000};
    assign access_count = hit_count + miss_count;

    // Sequential Request Latch, Response Registers, and Performance Counters
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            saved_addr <= 0;
            resp_data  <= 0;
            resp_hit   <= 0;
            resp_error <= 0;
            hit_count  <= 0;
            miss_count <= 0;
        end else begin
            // Latch incoming CPU address upon handshake acceptance
            if (req_valid && req_ready) begin
                saved_addr <= req_addr;
            end

            // Evaluate lookup result and update counters once per transaction
            if (compare_en) begin
                resp_hit   <= hit && !misaligned;
                resp_error <= misaligned;
                if (misaligned) begin
                    resp_data <= 0;
                end else if (hit) begin
                    hit_count <= hit_count + 1'b1;
                    resp_data <= cached_word;
                end else begin
                    miss_count <= miss_count + 1'b1;
                end
            end

            // Forward requested word directly from refilled 128-bit memory line
            if (refill_en) begin
                resp_data <= mem_rdata[offset[3:2] * 32 +: 32];
            end
        end
    end

endmodule
