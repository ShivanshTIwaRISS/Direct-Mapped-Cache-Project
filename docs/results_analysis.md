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

## Compulsory vs. Conflict (3C) Miss Decomposition

To separate the fundamental limits of spatial locality from direct-mapped mapping
hazards, the 3C model evaluates each workload against an ideal fully-associative
cache of identical capacity (64 lines, 1 KiB) with LRU replacement:

| Trace | Accesses | Hits | Misses | Hit Rate | Compulsory Misses | Conflict Misses | Capacity Misses |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| demo | 12 | 7 | 5 | 58.33% | 4 (80.0%) | 1 (20.0%) | 0 (0.0%) |
| sequential | 1024 | 768 | 256 | 75.00% | 256 (100.0%) | 0 (0.0%) | 0 (0.0%) |
| repeated | 1024 | 1008 | 16 | 98.44% | 16 (100.0%) | 0 (0.0%) | 0 (0.0%) |
| random | 1024 | 233 | 791 | 22.75% | 250 (31.6%) | 76 (9.6%) | 465 (58.8%) |
| conflict | 1024 | 0 | 1024 | 0.00% | 2 (0.2%) | 1022 (99.8%) | 0 (0.0%) |

- `sequential`: 256 unique 16-byte blocks are referenced in word order. Each block
  misses once on its first word (compulsory) and hits on the remaining three words.
  There are zero conflict or capacity misses.
- `repeated`: Working set is 256 bytes (16 blocks), which easily fits inside the
  64-line cache. The initial pass generates 16 compulsory misses; all subsequent 15
  passes achieve 100% hits.
- `conflict`: Alternates between addresses `0x00000000` (block 0, tag 0) and
  `0x00000400` (block 64, tag 1). Both addresses decode to `index = 0`. The first
  two misses are compulsory cold misses; the remaining 1,022 misses are 100% conflict
  misses. The working set is only 32 bytes (2 blocks), demonstrating that direct-mapped
  indexing can completely collapse hit rate even when capacity is vastly underutilized.
- `random`: Spans 256 blocks over a 64-line capacity, resulting in 250 compulsory,
  76 mapping conflict, and 465 capacity misses.

## Power-of-Two Stride Aliasing

Accessing memory with power-of-two strides demonstrates spatial locality collapse
and index aliasing across a 4 KiB array (1,024 accesses):

| Stride | Sets Used | Hits | Misses | Hit Rate | Compulsory | Conflict |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 B | 64 / 64 | 768 | 256 | 75.00% | 256 | 0 |
| 16 B | 64 / 64 | 0 | 1024 | 0.00% | 256 | 0 |
| 64 B | 16 / 64 | 0 | 1024 | 0.00% | 64 | 960 |
| 256 B | 4 / 64 | 0 | 1024 | 0.00% | 16 | 1008 |
| 1024 B | 1 / 64 | 0 | 1024 | 0.00% | 4 | 1020 |

At stride 4 B (sequential word reads), 4 words are consumed per line refill,
yielding the theoretical 75% hit rate. At stride 16 B (one word per line), spatial reuse
drops to zero. At stride 64 B and 256 B, address bits `[9:4]` alias into only 16
and 4 sets respectively, leaving the remainder of the cache completely idle.
At stride 1024 B (0x400), every single access maps to Set 0 (`index = 0`), creating
complete pathological set-0 thrashing (1,020 conflict evictions).

## Effective Throughput vs. AMAT Under Backpressure

AMAT defines the arithmetic mean latency from request acceptance to response
validity ($1 + \text{miss\_ratio} \times (L + 1)$). It excludes retirement handshaking
and downstream stall overhead.

In the 4-state FSM (`IDLE -> COMPARE -> ALLOCATE -> RESPOND -> IDLE`):
- Minimum hit cycle: 1 lookup + 1 retire = 2 cycles (peak throughput = 0.50 reads/cycle).
- Minimum miss cycle ($L=5$): 1 lookup + 6 refill + 1 retire = 8 cycles (peak throughput = 0.125 reads/cycle).
- With average response backpressure stall $S$ cycles:
  $$\bar{T}_{\text{trans}} = 1 + \text{AMAT} + S \implies \text{Throughput} = \frac{1}{1 + \text{AMAT} + S} \quad [\text{reads/cycle}]$$

| Workload | AMAT (L=5) | Throughput (S=0) | Throughput (S=2) | Throughput (S=8) | Throughput (S=16) |
| :--- | ---: | ---: | ---: | ---: | ---: |
| repeated | 1.094 cycles | 0.4776 | 0.2443 | 0.0991 | 0.0553 |
| sequential | 2.500 cycles | 0.2857 | 0.1818 | 0.0870 | 0.0513 |
| demo | 3.500 cycles | 0.2222 | 0.1538 | 0.0800 | 0.0488 |
| random | 5.635 cycles | 0.1507 | 0.1158 | 0.0683 | 0.0442 |
| conflict | 7.000 cycles | 0.1250 | 0.1000 | 0.0625 | 0.0417 |

## Protocol Stress and Cycle-Accurate Assertion Verification

The dedicated verification suite (`make stress-dv`, `tb/protocol_stress_tb.sv`) verifies
uncovered protocol dimensions across 8,298 concurrent cycle-by-cycle assertions:
1. **Response Stability:** During arbitrary `resp_ready` backpressure stalls (0–16 cycles),
   `resp_data`, `resp_hit`, and `resp_error` remain strictly glitch-free.
2. **Mutual Exclusion:** `resp_hit` and `resp_error` are mutually exclusive; `req_ready`
   is asserted strictly in `IDLE`.
3. **Cycle-by-Cycle Reset Abort Sweep:** Asynchronous reset asserted mid-`COMPARE`, mid-refill
   (cycles 1 through 5 of `ALLOCATE`), on the exact `mem_ready` edge, and during `RESPOND`
   guarantees zero stale line installation, immediate FSM return to `IDLE`, and clean recovery.
4. **Misalignment Isolation:** Torture sequences of misaligned reads (`offset[1:0] != 2'b00`)
   interleaved with valid hits/misses confirm zero memory transactions, zero counter corruption,
   and zero cache line pollution.
5. **Memory Delay Decoupling:** Continuous sweeps across $L \in \{1..20\}$ and dynamic jittered
   latencies confirm that miss latency is invariant at exactly $L + 2$ cycles.
