# Measured hit/miss and AMAT report

Generated from actual RTL output in `results/*.csv`, checked against a separate
Python oracle. Each workload starts with an invalid cache. Four main workloads
each contain 1,024 aligned reads; the short demo contains 12.

| Trace | Accesses | Hits | Misses | Hit rate | AMAT (cycles) |
| --- | ---: | ---: | ---: | ---: | ---: |
| demo | 12 | 7 | 5 | 58.33% | 3.500000 |
| sequential | 1024 | 768 | 256 | 75.00% | 2.500000 |
| repeated | 1024 | 1008 | 16 | 98.44% | 1.093750 |
| random | 1024 | 233 | 791 | 22.75% | 5.634766 |
| conflict | 1024 | 0 | 1024 | 0.00% | 7.000000 |

The sequential trace reads 4 KiB in word order: every group of four words has
one compulsory miss and three hits. The repeated trace reads a 256-byte working
set sixteen times: 16 compulsory misses are followed by hits. The random trace
uses Python's `Random(6)` over 4 KiB; its measured result is trace-specific,
not a universal random-access hit rate. The conflict trace alternates 0x00000000
and 0x00000400, which continually evict each other from index zero. Its first
two misses are compulsory; later misses illustrate mapping conflicts. These
synthetic traces expose different locality patterns; they do not establish
application or processor speedups.

Default memory-model latency L=5 gives hit latency 1 cycle and miss latency
7 cycles. The additional miss penalty is 6 cycles, including the controller and
memory interface overhead. Thus AMAT = 1 + miss_ratio * 6. The sequential example
is 1 + (256/1024)*6 = 2.5 cycles. The repeated example is
1 + (16/1024)*6 = 1.09375 cycles. Every result equals the mean measured response
latency; response backpressure and idle request gaps are excluded. See
`architecture.md` for the precise acceptance-to-response timing convention.

All five traces pass at memory latencies 1, 5 and 9 (15 runs, 12,324 workload
reads). Every run also executes 142 directed read checks plus reset-abort
scenarios. Checks cover all 64 invalid bits after reset, all four word offsets,
high address tags, eviction, busy input changes, misalignment, stable held
responses, exact counters and one memory completion per miss. The simulator
has per-request and global timeouts. This is simulation coverage, not a claim
of exhaustive formal verification.

An additional seed-2026 stress test covers 4,096 accesses spanning high 32-bit
addresses, word offsets, line reuse and conflicts. Both the source RTL and
Yosys's exported synthesized netlist pass the testbench and match the oracle;
their output CSV files are identical. See `results/deep_check.json` and its log.
This establishes behavior for the tested sequences, not formal equivalence.

## Synthesis

Yosys generic synthesis completed with 21,192 leaf cells, including 9,796 flip-flop cells.

The count excludes six hierarchical module instances in the aggregate statistic.
The pre-mapping design contains two `$mem_v2` cells for data/tag storage; valid
bits are registers. The generic mapping expands arrays into registers and muxes.
`check -assert` passed before and after synthesis. See `results/synthesis.log`,
`synthesis_memory.json` and `synthesis_cells.json` for actual tool evidence.

These counts are generic logic results, not FPGA LUT counts or physical area.
No device, clock constraint, placement/routing, BRAM claim, power number or Fmax
is reported. The memory model and testbench are excluded from synthesis.
