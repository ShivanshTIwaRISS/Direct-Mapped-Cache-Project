# Five-speaker prototype video script (target 4:30, limit 5:00)

The confirmed names and enrollment numbers below come from `team.json`. The
rubric requires clearly naming all five members; it does not require five narrators.
This optional template assigns a speaking section to each member. Rehearse once.
Show actual simulator execution as well as diagrams and results. The optional
generated MP4 is a captioned rehearsal walkthrough, not a team recording.

**Department:** Computer Science and AI

**College / university:** Rishihood University

| Team member | Enrollment number |
| --- | --- |
| Navprabhat Singh | 2401010293 |
| Samarth Khera | 2401010407 |
| Pratham Malhotra | 2401010343 |
| Shivansh Tiwari | 2401020108 |
| Tattva Rajput | 2401010478 |

Opening introductions (keep enrollment numbers visible on the title card):

- Navprabhat Singh (2401010293): Say, "I am Navprabhat Singh."
- Samarth Khera (2401010407): Say, "I am Samarth Khera."
- Pratham Malhotra (2401010343): Say, "I am Pratham Malhotra."
- Shivansh Tiwari (2401020108): Say, "I am Shivansh Tiwari."
- Tattva Rajput (2401010478): Say, "I am Tattva Rajput."

## 00:00–00:40 — Navprabhat Singh (2401010293): Idea and team

We are presenting Project 6, a Direct-Mapped Cache Controller. Our goal is to demonstrate how a small cache exploits temporal and spatial locality, and to measure hits, misses and average memory access time. Our Phase I prototype implements aligned reads using a 1 KiB cache, 16-byte blocks and 32-bit addresses. All five members now briefly introduce themselves.

On screen: Title slide with all five confirmed names and enrollment numbers; use the introductions above.

## 00:40–01:25 — Samarth Khera (2401010407): Addressing and storage

The cache has 64 lines. Address bits 3 to 0 form the block offset, 9 to 4 select the index, and 31 to 10 are the tag. The upper two offset bits select one of four words. A hit requires both a valid entry and matching tag. Reset clears valid bits so uninitialized storage cannot create a false hit.

On screen: Show docs/diagrams/architecture.png and addr_decoder.v.

## 01:25–02:10 — Pratham Malhotra (2401010343): Controller and refill

Our FSM uses IDLE, COMPARE, ALLOCATE and RESPOND. The request address is latched on acceptance. A miss holds a memory request at the aligned block base until all 16 bytes arrive. Data, tag and valid are installed together. The response stays stable until accepted. A refill is not counted as a second access.

On screen: Show docs/diagrams/fsm.png, cache_fsm.v and the actual VCD waveform.

## 02:10–03:30 — Shivansh Tiwari (2401020108): Run the prototype

We now run make sim. The simulator compares every response with an independent reference model. The short demo begins with a cold miss at zero, then hits at four, eight and twelve because they share a line. Address 0x400 replaces index zero, so returning to zero misses. The regression also checks reset, all indices, response backpressure and exact counters. Fifteen runs cover five workloads at three memory latencies.

On screen: Run make sim; show PASS lines, results/demo.csv and results/simulation.log. Show results/waveform evidence without claiming an FPGA demonstration.

## 03:30–04:30 — Tattva Rajput (2401010478): Results, AMAT and progress

Sequential accesses hit 75 percent; the repeated working set hits 98.44 percent; seeded random accesses hit 22.75 percent; deliberate conflicts hit zero percent. At default latency, hits take one cycle and misses take seven, so the extra miss penalty is six. Sequential AMAT is one plus 0.25 times six, or 2.5 cycles. Generic synthesis passes. Phase I delivers read lookup, refill and measured analysis; write policies and a board-specific implementation remain future extensions.

On screen: Show docs/diagrams/results.png, results/summary.csv and synthesis evidence. Finish with the GitHub URL and final video link.

## Recording and submission

1. Activate the environment with `source .tools/venv/bin/activate` if rebuilding figures.
2. Prepare a terminal at the repository root; enlarge text so PASS lines are readable.
3. Record the screen and all five speakers using your preferred recorder.
4. Keep the export at or below 300 seconds; aim for 270 seconds.
5. Upload the recording, verify viewer access, and replace the pending URL in
   `docs/demo/video_link.md`. Commit this change with the real contributor's identity.
6. Rebuild the report after updating the course title or contribution evidence.
7. Submit the existing GitHub repository URL through the instructor's form.
