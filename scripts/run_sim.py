#!/usr/bin/env python3
"""Compile and run actual RTL, then independently audit every output row."""
import csv
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from generate_traces import ROOT, main as generate, oracle, workloads

SOURCES = ["addr_decoder.v", "cache_fsm.v"] + [
    str(p.relative_to(ROOT)) for p in sorted((ROOT / "rtl").glob("*.v"))
]


def run(command):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(result.returncode)
    return result.stdout + result.stderr


def main():
    for tool in ("iverilog", "vvp"):
        if not shutil.which(tool):
            raise SystemExit(f"Missing {tool}; see README installation instructions.")
    generate()
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "results").mkdir(exist_ok=True)
    summary = []
    log = []
    for memory_latency in (1, 5, 9):
        executable = f"build/cache_tb_{memory_latency}"
        log.append(run([
            "iverilog", "-g2012", "-Wall", "-Wno-timescale", "-s", "cache_controller_tb",
            f"-Pcache_controller_tb.MEMORY_LATENCY={memory_latency}", "-o", executable,
            *SOURCES, "tb/main_memory_model.v", "tb/cache_controller_tb.sv",
        ]))
        for name, addresses in workloads().items():
            output = f"results/{name}.csv" if memory_latency == 5 else f"build/{name}_{memory_latency}.csv"
            command = ["vvp", executable, f"+TRACE=traces/{name}.trace", f"+OUT={output}"]
            if name == "demo" and memory_latency == 5:
                command += ["+VCD=build/cache_demo.vcd"]
            message = run(command)
            print(message.strip())
            log.append(message)
            if "PASS trace=" not in message:
                raise SystemExit("Simulation did not report success")
            with (ROOT / output).open() as file:
                rows = list(csv.DictReader(file))
            expected = list(oracle(addresses))
            assert len(rows) == len(expected), "Output length mismatch"
            for number, (row, (address, hit, data)) in enumerate(zip(rows, expected), 1):
                assert (int(row["access"]), int(row["address"], 16), int(row["hit"]),
                        int(row["data"], 16), int(row["latency_cycles"])) == (
                            number, address, hit, data, 1 if hit else memory_latency + 2
                        ), f"RTL/oracle mismatch: {name} access {number}"
            if memory_latency == 5:
                hits = sum(int(row["hit"]) for row in rows)
                misses = len(rows) - hits
                mean = sum(int(row["latency_cycles"]) for row in rows) / len(rows)
                amat = 1 + misses / len(rows) * (memory_latency + 1)
                assert abs(mean - amat) < 1e-12
                summary.append({"trace": name, "accesses": len(rows), "hits": hits,
                                "misses": misses, "hit_ratio": hits / len(rows),
                                "miss_ratio": misses / len(rows), "hit_cycles": 1,
                                "miss_cycles": memory_latency + 2,
                                "miss_penalty_cycles": memory_latency + 1,
                                "amat_cycles": amat, "measured_mean_cycles": mean})
    (ROOT / "results/summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (ROOT / "results/summary.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(summary[0]))
        writer.writeheader(); writer.writerows(summary)
    (ROOT / "results/simulation.log").write_text("".join(log))
    versions = {"python": platform.python_version(), "platform": platform.platform(),
                "iverilog": run(["iverilog", "-V"]).splitlines()[0],
                "regression_runs": 15, "memory_latencies": [1, 5, 9]}
    (ROOT / "results/tool_versions.json").write_text(json.dumps(versions, indent=2) + "\n")
    print("PASS: 15 RTL runs; all data, classification, counters and AMAT independently checked.")


if __name__ == "__main__":
    main()
