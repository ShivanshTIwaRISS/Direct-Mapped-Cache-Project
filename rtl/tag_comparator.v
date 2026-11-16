module tag_comparator (
    input valid,
    input [21:0] stored_tag,
    input [21:0] requested_tag,
    output hit
);
    assign hit = valid && (stored_tag == requested_tag);
endmodule
