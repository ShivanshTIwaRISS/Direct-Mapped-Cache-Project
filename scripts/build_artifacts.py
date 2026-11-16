#!/usr/bin/env python3
"""Render figures, report tables, team fields, analysis and a timed demo script."""
import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "build/matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

FIGURES = ROOT / "docs/diagrams"
REPORT = ROOT / "docs/report"
NAVY, BLUE, GREEN, RED = "#182f46", "#2667a5", "#1d8565", "#bb493f"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42})


def tex(value):
    return "".join({"&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#",
                    "{": r"\{", "}": r"\}", "\\": r"\textbackslash{}"}.get(c, c)
                   for c in str(value))


def save(fig, name):
    for ext in ("pdf", "png", "svg"):
        fig.savefig(FIGURES / f"{name}.{ext}", bbox_inches="tight", dpi=180)
    plt.close(fig)


def box(ax, x, y, w, h, text, color=BLUE):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                               facecolor="#f0f5fa", edgecolor=color, linewidth=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=NAVY)


def arrow(ax, start, end, label="", curve=0, color=NAVY):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12,
                               connectionstyle=f"arc3,rad={curve}", color=color))
    if label:
        ax.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.14,
                label, ha="center", fontsize=8, color=color,
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})


def architecture():
    fig, ax = plt.subplots(figsize=(11, 5.4))
    ax.set(xlim=(-0.1, 10.4), ylim=(-0.2, 5.3)); ax.axis("off")
    box(ax, 0, 2.25, 1.5, 1, "CPU / trace\ndriver")
    box(ax, 2.1, 3.8, 2.2, 1, "Latched address\n+ address decoder")
    box(ax, 5.0, 3.8, 2.5, 1, "Data RAM\n64 x 128 bits")
    box(ax, 5.0, 2.15, 2.5, 1, "Tag RAM: 64 x 22\nValid RAM: 64 x 1")
    box(ax, 8.1, 2.15, 1.9, 1, "Tag comparator\nvalid AND match")
    box(ax, 2.1, 0.45, 2.2, 1, "Controller FSM\n+ hit/miss counters")
    box(ax, 5.0, 0.45, 2.5, 1, "Line memory interface\n128-bit refill")
    box(ax, 8.1, 3.8, 1.9, 1, "Word selection\n+ response register")
    arrow(ax, (1.5, 3.1), (2.1, 4.0), "request")
    arrow(ax, (4.3, 4.3), (5, 4.3), "index")
    arrow(ax, (4.3, 4), (5, 2.9), "index")
    arrow(ax, (7.5, 2.65), (8.1, 2.65))
    arrow(ax, (7.5, 4.3), (8.1, 4.3), "word")
    arrow(ax, (9.05, 3.15), (9.05, 3.8), "hit")
    arrow(ax, (3.2, 3.8), (3.2, 1.45), "latched request")
    arrow(ax, (4.3, 0.95), (5, 0.95), "miss")
    arrow(ax, (6.25, 1.45), (6.25, 2.15), "refill")
    arrow(ax, (7.5, 1.25), (7.85, 3.8), curve=-0.12)
    ax.plot([9.05, 9.05, 4.55, 4.55], [2.15, 1.78, 1.78, 1.2], color=NAVY, linewidth=1)
    arrow(ax, (4.55, 1.2), (4.3, 1.2))
    ax.text(8.0, 1.87, "hit / miss to FSM", fontsize=8, ha="center", color=NAVY)
    ax.text(8.1, 4.98, "registered response -> CPU", fontsize=8, color=NAVY)
    ax.text(0.0, 0.05, "Data/tag/valid install together on memory completion; response is held until accepted.",
            fontsize=9, color=NAVY)
    save(fig, "architecture")


def fsm():
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.set(xlim=(-0.2, 9.2), ylim=(-0.4, 4.4)); ax.axis("off")
    for x, y, text in [(0.1, 2.7, "IDLE (00)"), (3.5, 2.7, "COMPARE (01)"),
                       (6.9, 2.7, "ALLOCATE (10)"), (3.5, 0.1, "RESPOND (11)")]:
        box(ax, x, y, 2.0, 0.9, text)
    arrow(ax, (2.15, 3.15), (3.45, 3.15), "accept request")
    arrow(ax, (5.55, 3.15), (6.85, 3.15), "miss")
    arrow(ax, (4.5, 2.65), (4.5, 1.05), "hit / alignment error")
    arrow(ax, (7.9, 2.65), (5.55, 0.55), "memory ready / refill", curve=-0.1)
    arrow(ax, (3.45, 0.55), (1.1, 2.65), "response accepted", curve=-0.12)
    ax.text(7.9, 3.95, "Wait here until\nmemory completes", ha="center", fontsize=9)
    ax.text(4.5, -0.3, "Hold response stable while resp_ready = 0", ha="center", fontsize=9)
    ax.text(0.1, 4.0, "Reset -> IDLE; all valid bits and counters cleared", fontsize=10, color=NAVY)
    save(fig, "fsm")


def charts(summary):
    data = [r for r in summary if r["trace"] != "demo"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    names = [r["trace"].title() for r in data]
    for ax, values, ylabel, limit in [
        (axes[0], [r["hit_ratio"] * 100 for r in data], "Hit rate (%)", 110),
        (axes[1], [r["amat_cycles"] for r in data], "AMAT (cycles)", 8),
    ]:
        bars = ax.bar(names, values, color=[BLUE, GREEN, "#8870a8", RED], width=0.65)
        ax.set(ylabel=ylabel, ylim=(0, limit)); ax.grid(axis="y", alpha=0.15)
        ax.bar_label(bars, labels=[f"{v:.2f}" for v in values], padding=4, fontsize=9)
    fig.suptitle("Measured RTL results: cold cache, 1,024 accesses per workload", color=NAVY)
    fig.tight_layout(); save(fig, "results")


def waveform():
    # Parse the actual simulator VCD and plot rising-edge samples for the final demo.
    scopes, codes, changes = [], {}, {}
    time = 0
    for line in (ROOT / "build/cache_demo.vcd").read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "$scope": scopes.append(parts[2])
        elif parts[0] == "$upscope": scopes.pop()
        elif parts[0] == "$var" and scopes == ["cache_controller_tb"]:
            codes[parts[3]] = parts[4]; changes.setdefault(parts[4], [])
        elif line.startswith("#"): time = int(line[1:])
        elif line[0] in "01xz":
            code, value = line[1:], line[0]
            if code in codes: changes[codes[code]].append((time, value))
        elif line[0] == "b" and len(parts) == 2 and parts[1] in codes:
            changes[codes[parts[1]]].append((time, parts[0][1:]))
    # Last reset release starts the trace; include first miss and following hit.
    start = max(t for t, v in changes["reset"] if v == "0")
    stop = start + 250_000  # VCD timescale is 1 ps; view 250 ns.
    signals = ["req_valid", "req_ready", "mem_read", "mem_ready", "resp_valid", "resp_hit"]
    fig, axes = plt.subplots(len(signals), 1, figsize=(10, 4.4), sharex=True)
    for ax, name in zip(axes, signals):
        points = [(t, v) for t, v in changes[name] if t <= stop]
        previous = [v for t, v in points if t <= start]
        selected = [(start, previous[-1] if previous else "0")]
        selected += [(t, v) for t, v in points if t > start]
        selected += [(stop, selected[-1][1])]
        xs = [(t - start) / 1000 for t, _ in selected]
        ys = [int(v) if v in ("0", "1") else float("nan") for _, v in selected]
        ax.step(xs, ys, where="post", color=BLUE, linewidth=1.5)
        ax.set(ylim=(-0.2, 1.3), yticks=[0, 1]); ax.set_ylabel(name, rotation=0, ha="right", va="center")
        ax.grid(axis="x", alpha=0.15)
    axes[-1].set_xlabel("Time since trace reset release (ns); actual Icarus VCD")
    fig.tight_layout(); save(fig, "waveform")


def main():
    FIGURES.mkdir(parents=True, exist_ok=True); REPORT.mkdir(parents=True, exist_ok=True)
    summary = json.loads((ROOT / "results/summary.json").read_text())
    synthesis = json.loads((ROOT / "results/synthesis_cells.json").read_text())
    team = json.loads((ROOT / "team.json").read_text())
    assert len(team["members"]) == 5
    types = synthesis["design"]["num_cells_by_type"]
    leaf_cells = sum(n for kind, n in types.items() if kind.startswith("$_"))
    flip_flops = sum(n for kind, n in types.items() if kind.startswith("$_DFF"))
    (REPORT / "generated_results.tex").write_text(
        "% Generated from actual RTL and Yosys outputs.\n" +
        f"\\newcommand{{\\GenericCells}}{{{leaf_cells:,}}}\n" +
        f"\\newcommand{{\\GenericFFs}}{{{flip_flops:,}}}\n" +
        "\\newcommand{\\ResultRows}{%\n" + "".join(
            f"{r['trace'].title()} & {r['accesses']} & {r['hits']} & {r['misses']} & "
            f"{100 * r['hit_ratio']:.2f} & {r['amat_cycles']:.4f} \\\\\n"
            for r in summary) + "}\n"
    )
    names = r"\\ ".join(tex(m["name"]) + " (Enrollment No. " + tex(m["enrollment_number"]) + ")"
                         for m in team["members"])
    institution = tex(team["department"]) + r"\\" + tex(team["college"])
    (REPORT / "generated_team.tex").write_text(
        "\\newcommand{\\TeamNames}{" + names + "}\n" +
        "\\newcommand{\\TeamInstitution}{" + institution + "}\n"
    )
    (REPORT / "generated_contributions.tex").write_text("\n\n".join(
        r"\noindent\textbf{" + tex(m["name"]) + " (Enrollment No. " + tex(m["enrollment_number"]) + r").} " +
        tex(m["verified_contribution"]) + " Proposed responsibility: " + tex(m["proposed_role"]) + "."
        for m in team["members"]) + "\n")
    architecture(); fsm(); charts(summary); waveform()
    table = "| Trace | Accesses | Hits | Misses | Hit rate | AMAT (cycles) |\n| --- | ---: | ---: | ---: | ---: | ---: |\n"
    table += "".join(f"| {r['trace']} | {r['accesses']} | {r['hits']} | {r['misses']} | "
                     f"{r['hit_ratio']:.2%} | {r['amat_cycles']:.6f} |\n" for r in summary)
    analysis = """# Measured hit/miss and AMAT report

Generated from actual RTL output in `results/*.csv`, checked against a separate
Python oracle. Each workload starts with an invalid cache. Four main workloads
each contain 1,024 aligned reads; the short demo contains 12.

""" + table + """
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

""" + f"Yosys generic synthesis completed with {leaf_cells:,} leaf cells, including {flip_flops:,} flip-flop cells.\n" + """
The count excludes six hierarchical module instances in the aggregate statistic.
The pre-mapping design contains two `$mem_v2` cells for data/tag storage; valid
bits are registers. The generic mapping expands arrays into registers and muxes.
`check -assert` passed before and after synthesis. See `results/synthesis.log`,
`synthesis_memory.json` and `synthesis_cells.json` for actual tool evidence.

These counts are generic logic results, not FPGA LUT counts or physical area.
No device, clock constraint, placement/routing, BRAM claim, power number or Fmax
is reported. The memory model and testbench are excluded from synthesis.
"""
    (ROOT / "docs/results_analysis.md").write_text(analysis)
    members = team["members"]
    script = """# Five-speaker prototype video script (target 4:30, limit 5:00)

The confirmed names and enrollment numbers below come from `team.json`. The
rubric requires clearly naming all five members; it does not require five narrators.
This optional template assigns a speaking section to each member. Rehearse once.
Show actual simulator execution as well as diagrams and results. The optional
generated MP4 is a captioned rehearsal walkthrough, not a team recording.

"""
    script += f"**Department:** {team['department']}\n\n**College / university:** {team['college']}\n\n"
    script += "| Team member | Enrollment number |\n| --- | --- |\n"
    script += "".join(f"| {m['name']} | {m['enrollment_number']} |\n" for m in members)
    script += "\nOpening introductions (keep enrollment numbers visible on the title card):\n\n"
    script += "\n".join(f"- {m['name']} ({m['enrollment_number']}): Say, \"I am {m['name']}.\"" for m in members)
    script += "\n\n"
    segments = [
        ("00:00–00:40", "Idea and team", "We are presenting Project 6, a Direct-Mapped Cache Controller. "
         "Our goal is to demonstrate how a small cache exploits temporal and spatial locality, "
         "and to measure hits, misses and average memory access time. "
         "Our Phase I prototype implements aligned reads using a 1 KiB cache, 16-byte blocks "
         "and 32-bit addresses. All five members now briefly introduce themselves.",
         "Title slide with all five confirmed names and enrollment numbers; use the introductions above."),
        ("00:40–01:25", "Addressing and storage", "The cache has 64 lines. Address bits 3 to 0 form "
         "the block offset, 9 to 4 select the index, and 31 to 10 are the tag. The upper two "
         "offset bits select one of four words. A hit requires both a valid entry and matching "
         "tag. Reset clears valid bits so uninitialized storage cannot create a false hit.",
         "Show docs/diagrams/architecture.png and addr_decoder.v."),
        ("01:25–02:10", "Controller and refill", "Our FSM uses IDLE, COMPARE, ALLOCATE and RESPOND. "
         "The request address is latched on acceptance. A miss holds a memory request at the "
         "aligned block base until all 16 bytes arrive. Data, tag and valid are installed together. "
         "The response stays stable until accepted. A refill is not counted as a second access.",
         "Show docs/diagrams/fsm.png, cache_fsm.v and the actual VCD waveform."),
        ("02:10–03:30", "Run the prototype", "We now run make sim. The simulator compares every "
         "response with an independent reference model. The short demo begins with a cold miss "
         "at zero, then hits at four, eight and twelve because they share a line. Address "
         "0x400 replaces index zero, so returning to zero misses. The regression also checks "
         "reset, all indices, response backpressure and exact counters. Fifteen runs cover five "
         "workloads at three memory latencies.",
         "Run make sim; show PASS lines, results/demo.csv and results/simulation.log. "
         "Show results/waveform evidence without claiming an FPGA demonstration."),
        ("03:30–04:30", "Results, AMAT and progress", "Sequential accesses hit 75 percent; the "
         "repeated working set hits 98.44 percent; seeded random accesses hit 22.75 percent; "
         "deliberate conflicts hit zero percent. At default latency, hits take one cycle and "
         "misses take seven, so the extra miss penalty is six. Sequential AMAT is one plus "
         "0.25 times six, or 2.5 cycles. Generic synthesis passes. Phase I delivers read lookup, "
         "refill and measured analysis; write policies and a board-specific implementation "
         "remain future extensions.",
         "Show docs/diagrams/results.png, results/summary.csv and synthesis evidence. "
         "Finish with the GitHub URL and final video link."),
    ]
    for member, (timing, title, words, screen) in zip(members, segments):
        script += (f"## {timing} — {member['name']} ({member['enrollment_number']}): {title}\n\n"
                   f"{words}\n\nOn screen: {screen}\n\n")
    script += """## Recording and submission

1. Activate the environment with `source .tools/venv/bin/activate` if rebuilding figures.
2. Prepare a terminal at the repository root; enlarge text so PASS lines are readable.
3. Record the screen and all five speakers using your preferred recorder.
4. Keep the export at or below 300 seconds; aim for 270 seconds.
5. Upload the recording, verify viewer access, and replace the pending URL in
   `docs/demo/video_link.md`. Commit this change with the real contributor's identity.
6. Rebuild the report after updating the course title or contribution evidence.
7. Submit the existing GitHub repository URL through the instructor's form.
"""
    (ROOT / "docs/demo/script.md").write_text(script)
    print("Generated report tables, team fields, four figures, analysis and video script.")


if __name__ == "__main__":
    main()
