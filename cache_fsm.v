
module cache_fsm (
    input clk,
    input reset,
    input mem_req,
    input cache_hit,    // Also true for an error that must bypass memory.
    input mem_ready,
    input resp_ready,
    output reg stall,
    output reg mem_read,
    output req_ready,
    output compare_en,
    output refill_en,
    output resp_valid,
    output [1:0] state_debug
);
    localparam IDLE = 2'b00, COMPARE = 2'b01,
               ALLOCATE = 2'b10, RESPOND = 2'b11;
    reg [1:0] state, next_state;

    assign req_ready = (state == IDLE) && !reset;
    assign compare_en = (state == COMPARE) && !reset;
    assign refill_en = (state == ALLOCATE) && mem_ready && !reset;
    assign resp_valid = (state == RESPOND) && !reset;
    assign state_debug = state;

    always @(posedge clk or posedge reset) begin
        if (reset) state <= IDLE;
        else       state <= next_state;
    end

    always @(*) begin
        stall = !req_ready; mem_read = 0; next_state = state;
        case (state)
            IDLE: if (mem_req && !reset) next_state = COMPARE;
            COMPARE: begin
                if (cache_hit) next_state = RESPOND;
                else next_state = ALLOCATE;
            end
            ALLOCATE: begin
                mem_read = !reset;
                if (mem_ready) next_state = RESPOND;
            end
            RESPOND: if (resp_ready) next_state = IDLE;
            default: next_state = IDLE;
        endcase
    end
endmodule
