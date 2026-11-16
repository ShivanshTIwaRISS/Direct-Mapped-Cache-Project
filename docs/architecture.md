# Cache specification and design rationale

The Phase I baseline is a blocking, read-only cache with 1,024 data bytes,
64 direct-mapped lines and 16 bytes per line. It accepts 32-bit byte addresses
and returns one aligned 32-bit word. All seven suggested architectural blocks
are implemented: data RAM, tag RAM, valid RAM, decoder, comparator, control FSM,
and a line-refill memory interface. The memory model is simulation-only.

## Address fields and storage

`offset = address[3:0]`, `index = address[9:4]`, and `tag = address[31:10]`.
`offset[3:2]` selects one of four words. `offset[1:0]` must be zero.
The line base is `{address[31:4], 4'b0000}`. In a returned 128-bit line,
bits `[31:0]` contain the word at the base and `[127:96]` the word at base+12.

Data storage is 64 x 128 = 8,192 bits. Tags require 64 x 22 = 1,408 bits;
valid bits add 64 bits. The total architectural cache storage is 9,664 bits
(1,208 bytes), excluding counters, address/response registers and FSM state.
The data capacity is therefore 1 KiB; metadata is additional.

## Transaction contract

| Interface | Contract |
| --- | --- |
| CPU request | Accepted at a rising edge with `req_valid && req_ready`; address is latched. |
| CPU response | Retired at a rising edge with `resp_valid && resp_ready`; data/hit/error stay stable until retirement. |
| Busy | `req_ready=0` and `stall=1` outside IDLE. An upstream requester retains an unaccepted request until ready. |
| Memory | `mem_read` and the aligned `mem_addr` remain stable throughout ALLOCATE. A full line transfers at a rising edge with `mem_read && mem_ready`. |
| Reset | Active-high asynchronous reset clears valid bits, counters and pending response; both cache and memory endpoint must reset together to cancel a transfer. |
| Alignment | A misaligned read produces `resp_error=1`, `resp_hit=0`, `resp_data=0`; no memory request or hit/miss count. |
| Statistics | Each valid aligned lookup increments exactly one counter in COMPARE. Refill does not count again. Counters wrap modulo 2^32. |

There is one outstanding transaction. The memory interface has no independent
request-accept signal: the endpoint must not interpret a held `mem_read` as
multiple transfers. The supplied endpoint implements that contract. An AXI,
burst-beat, or external DRAM adapter would require additional work.

## FSM

| State (debug code) | Operation | Next state |
| --- | --- | --- |
| IDLE (00) | Accept and latch a request | COMPARE on acceptance |
| COMPARE (01) | Check valid and tag; update one statistic | RESPOND on hit/error, otherwise ALLOCATE |
| ALLOCATE (10) | Hold memory request; atomically write line, tag and valid on transfer | RESPOND on memory completion |
| RESPOND (11) | Hold response until acknowledged | IDLE on response retirement |

Atomic installation of data, tag and valid prevents partial lines from being
used. Uninitialized tags/data are safe because reset invalidates all entries.
An address separated by 0x400 bytes has the same index and a different tag,
which the conflict workload uses to demonstrate eviction.

## Timing and AMAT convention

Measure from the rising edge accepting a request to the first edge after which
`resp_valid` is asserted, excluding later response backpressure and testbench
request gaps. A hit takes 1 cycle. With memory-model parameter L >= 1, a miss
takes L+2 cycles: one comparison cycle, one memory capture cycle, L-1 waiting
cycles, and one completion cycle. Therefore the additional miss penalty is L+1.

For the default L=5: hit=1, miss=7, penalty=6 cycles and
`AMAT = 1 + miss_ratio * 6`. This equals the measured arithmetic mean of
per-request latency in every trace. It is not the average spacing between
transactions: response retirement, return to IDLE, and any testbench gaps also
affect throughput. With the test clock's 10 ns period, multiplying by 10 gives
simulation nanoseconds, not a measured FPGA clock or hardware timing guarantee.

## Scope and limitations

The cache geometry is deliberately fixed to the original decoder configuration.
The memory-model latency is parameterized and tested at 1, 5 and 9 cycles.
The model computes `word(address) = address XOR 0xA5A50000`, covering high tag
bits without allocating 4 GiB of simulation RAM. It is not a workload benchmark
of real DRAM. There are no stores, dirty bits, write policies, coherence,
prefetching, replacement choices, subword loads or a CPU core in Phase I.

Generic Yosys synthesis verifies that the RTL can be synthesized. Asynchronous
array reads map to registers and multiplexers in the generic flow. FPGA BRAM
inference, device LUT/FF counts, pin constraints, timing closure and hardware
demonstration need a selected device and vendor flow.
