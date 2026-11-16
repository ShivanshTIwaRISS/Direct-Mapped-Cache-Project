#!/usr/bin/env python3
"""Extra full-address-space stress plus post-synthesis behavioral regression."""
import csv
import json
import random
import subprocess

from generate_traces import ROOT, oracle
from run_sim import SOURCES, run


def main():
    rng = random.Random(2026)
    addresses = []
    for _ in range(512):
        base = rng.getrandbits(32) & 0xFFFFFFF0
        # All offsets, high tags, a conflicting replacement and immediate reuse.
        other = base ^ 0x400
        addresses.extend([base, base + 4, base + 8, base + 12,
                          other, other + 12, base, base + 8])
    expected = list(oracle(addresses))
    (ROOT / "build/stress.trace").write_text(
        "".join(f"{a:08x} {h} {d:08x}\n" for a, h, d in expected))
    log = []
    for label, sources in [("rtl", SOURCES), ("synthesized", ["build/cache_synth.v"])]:
        executable = f"build/stress_{label}"
        log.append(run(["iverilog", "-g2012", "-s", "cache_controller_tb", "-o", executable,
                        *sources, "tb/main_memory_model.v", "tb/cache_controller_tb.sv"]))
        output = f"build/stress_{label}.csv"
        message = run(["vvp", executable, "+TRACE=build/stress.trace", f"+OUT={output}"])
        print(label + ": " + message.strip()); log.append(label + ": " + message)
        assert "PASS trace=" in message
        with (ROOT / output).open() as file:
            rows = list(csv.DictReader(file))
        assert len(rows) == len(expected)
        for number, (row, (address, hit, data)) in enumerate(zip(rows, expected), 1):
            assert (int(row["access"]), int(row["address"], 16), int(row["hit"]),
                    int(row["data"], 16), int(row["latency_cycles"])) == (
                        number, address, hit, data, 1 if hit else 7), f"{label}: row {number}"
    assert (ROOT / "build/stress_rtl.csv").read_bytes() == (ROOT / "build/stress_synthesized.csv").read_bytes()
    results = {"status": "PASS", "seed": 2026, "stress_accesses_per_design": len(addresses),
               "designs_checked": ["rtl", "synthesized"], "outputs_identical": True,
               "directed_checks_per_design": 142, "scope": "trace equivalence, not a formal proof"}
    (ROOT / "results/deep_check.json").write_text(json.dumps(results, indent=2) + "\n")
    (ROOT / "results/deep_check.log").write_text("".join(log))
    print("PASS: full-address stress and synthesized-netlist outputs match the oracle and each other.")


if __name__ == "__main__":
    main()
