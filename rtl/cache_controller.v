// Blocking, read-only direct-mapped cache. Byte addresses; 32-bit aligned reads.
// CPU accepts on req_valid && req_ready; retires on resp_valid && resp_ready.
// Memory completes one entire line on mem_read && mem_ready.
module cache_controller (
    input clk,
    input reset,
    input req_valid,
    output req_ready,
    input [31:0] req_addr,
    output resp_valid,
    input resp_ready,
    output reg [31:0] resp_data,
    output reg resp_hit,
    output reg resp_error,
    output mem_read,
    output [31:0] mem_addr,
    input mem_ready,
    input [127:0] mem_rdata,
    output [31:0] access_count,
    output reg [31:0] hit_count,
    output reg [31:0] miss_count,
    output stall,
    output [1:0] state_debug
);
    reg [31:0] saved_addr;
    wire [21:0] tag, stored_tag;
    wire [5:0] index;
    wire [3:0] offset;
    wire valid, hit, compare_en, refill_en;
    wire [31:0] cached_word;
    wire misaligned = |offset[1:0];

    addr_decoder decoder(saved_addr, tag, index, offset);
    tag_ram tags(clk, refill_en, index, tag, stored_tag);
    valid_bit_ram valids(clk, reset, refill_en, index, valid);
    cache_data_ram data(clk, refill_en, index, mem_rdata, offset[3:2], cached_word);
    tag_comparator comparator(valid, stored_tag, tag, hit);
    cache_fsm control (
        .clk(clk), .reset(reset), .mem_req(req_valid),
        .cache_hit(hit || misaligned), .mem_ready(mem_ready),
        .resp_ready(resp_ready), .stall(stall), .mem_read(mem_read),
        .req_ready(req_ready), .compare_en(compare_en), .refill_en(refill_en),
        .resp_valid(resp_valid), .state_debug(state_debug)
    );

    assign mem_addr = {saved_addr[31:4], 4'b0000};
    assign access_count = hit_count + miss_count;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            saved_addr <= 0;
            resp_data <= 0;
            resp_hit <= 0;
            resp_error <= 0;
            hit_count <= 0;
            miss_count <= 0;
        end else begin
            if (req_valid && req_ready) saved_addr <= req_addr;
            if (compare_en) begin
                resp_hit <= hit && !misaligned;
                resp_error <= misaligned;
                if (misaligned) resp_data <= 0;
                else if (hit) begin
                    hit_count <= hit_count + 1'b1;
                    resp_data <= cached_word;
                end else miss_count <= miss_count + 1'b1;
            end
            if (refill_en)
                resp_data <= mem_rdata[offset[3:2] * 32 +: 32];
        end
    end
endmodule
