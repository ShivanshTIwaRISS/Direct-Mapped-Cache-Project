#!/usr/bin/env python3
"""Microarchitectural Miss Decomposition, Latency Sensitivity, and Throughput Telemetry.

Provides deep analytical telemetry for the 1 KiB Direct-Mapped Read Cache:
  1. Compulsory vs. Conflict (3C) miss decomposition across baseline workloads.
  2. Memory latency sensitivity sweep (L = 1..20) validating AMAT(L) = 1 + miss_ratio * (L + 1).
  3. Response backpressure throughput characterization (reads/cycle vs stall cycles).
  4. Power-of-two stride aliasing analysis (4 B, 16 B, 64 B, 256 B, 1024 B).
"""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse_trace(trace_path):
    """Parse trace file returning list of (address, want_hit, want_data)."""
    rows = []
    for line in trace_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        rows.append((int(parts[0], 16), int(parts[1]), int(parts[2], 16)))
    return rows


def analyze_3c_misses(addresses):
    """Decompose cache misses into Compulsory, Capacity, and Conflict misses.

    Compares the 64-line direct-mapped cache against an ideal fully-associative
    cache with 64 lines and LRU replacement policy.
    """
    seen_blocks = set()
    dm_resident = [None] * 64
    fa_resident = []  # LRU list: most recently used at front, max size 64

    total_accesses = len(addresses)
    hits = 0
    compulsory_misses = 0
    capacity_misses = 0
    conflict_misses = 0

    for address in addresses:
        block = address // 16
        set_idx = block % 64

        is_dm_hit = (dm_resident[set_idx] == block)
        is_fa_hit = (block in fa_resident)

        if is_dm_hit:
            hits += 1
        else:
            if block not in seen_blocks:
                compulsory_misses += 1
            else:
                # Re-reference to an evicted block
                if is_fa_hit:
                    # Would have hit in fully-associative cache of same capacity -> Conflict miss
                    conflict_misses += 1
                else:
                    # Missed even in fully-associative cache -> Capacity miss
                    capacity_misses += 1

        seen_blocks.add(block)
        dm_resident[set_idx] = block

        # Update FA LRU state
        if is_fa_hit:
            fa_resident.remove(block)
            fa_resident.insert(0, block)
        else:
            fa_resident.insert(0, block)
            if len(fa_resident) > 64:
                fa_resident.pop()

    total_misses = compulsory_misses + capacity_misses + conflict_misses
    return {
        "accesses": total_accesses,
        "hits": hits,
        "misses": total_misses,
        "hit_ratio": hits / total_accesses if total_accesses else 0.0,
        "miss_ratio": total_misses / total_accesses if total_accesses else 0.0,
        "compulsory": compulsory_misses,
        "capacity": capacity_misses,
        "conflict": conflict_misses,
        "compulsory_pct": (compulsory_misses / total_misses * 100.0) if total_misses else 0.0,
        "capacity_pct": (capacity_misses / total_misses * 100.0) if total_misses else 0.0,
        "conflict_pct": (conflict_misses / total_misses * 100.0) if total_misses else 0.0,
    }


def analyze_workload_3c():
    """Run 3C decomposition on all 4 main workloads + demo."""
    results = {}
    traces = ["demo", "sequential", "repeated", "random", "conflict"]
    for name in traces:
        tpath = ROOT / "traces" / f"{name}.trace"
        if not tpath.exists():
            continue
        parsed = parse_trace(tpath)
        addresses = [p[0] for p in parsed]
        results[name] = analyze_3c_misses(addresses)
    return results


def latency_sensitivity_sweep(miss_ratios, latencies=None):
    """Compute AMAT across memory latencies L using AMAT(L) = 1 + miss_ratio * (L + 1)."""
    if latencies is None:
        latencies = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20]
    sweep = {}
    for L in latencies:
        sweep[L] = {}
        for name, mr in miss_ratios.items():
            sweep[L][name] = 1.0 + mr * (L + 1)
    return sweep


def backpressure_throughput(amat_dict, stall_cycles_list=None):
    """Calculate effective throughput (reads/cycle) under varying backpressure stalls.

    In the 4-state FSM:
      Transaction latency = 1 (hit) or (L+2) (miss).
      Retirement cycle into IDLE adds 1 cycle.
      Stall adds S cycles during RESPOND.
      Cycle time per transaction = 1 + AMAT + S.
      Throughput = 1 / (1 + AMAT + S) reads/cycle.
    """
    if stall_cycles_list is None:
        stall_cycles_list = [0, 1, 2, 4, 8, 16]
    tput = {}
    for S in stall_cycles_list:
        tput[S] = {}
        for name, amat in amat_dict.items():
            avg_cycles = 1.0 + amat + S
            tput[S][name] = 1.0 / avg_cycles
    return tput


def stride_aliasing_study():
    """Simulate power-of-two strides over a 4 KiB array (1,024 accesses) demonstrating set aliasing."""
    strides = [4, 16, 64, 256, 1024]
    results = {}
    for stride in strides:
        addresses = [(i * stride) % 4096 for i in range(1024)]
        stats = analyze_3c_misses(addresses)
        sets_touched = len(set((a // 16) % 64 for a in addresses))
        results[stride] = {
            "stride_bytes": stride,
            "sets_touched": sets_touched,
            "hits": stats["hits"],
            "misses": stats["misses"],
            "hit_ratio": stats["hit_ratio"],
            "compulsory": stats["compulsory"],
            "conflict": stats["conflict"],
        }
    return results


def print_report():
    print("================================================================================")
    print("PROJECT 6: 1 KiB DIRECT-MAPPED READ CACHE - MICROARCHITECTURAL TELEMETRY")
    print("================================================================================")

    # 1. 3C Miss Decomposition
    decomp = analyze_workload_3c()
    print("\n1. COMPULSORY VS. CONFLICT (3C) MISS DECOMPOSITION:")
    print(f"{'Trace':<12} {'Accesses':>8} {'Hits':>6} {'Misses':>6} {'HitRate':>8} {'Compulsory':>11} {'Conflict':>9} {'Capacity':>9}")
    print("-" * 75)
    for name, d in decomp.items():
        print(f"{name:<12} {d['accesses']:>8} {d['hits']:>6} {d['misses']:>6} {d['hit_ratio']*100:>7.2f}% "
              f"{d['compulsory']:>6} ({d['compulsory_pct']:>5.1f}%) "
              f"{d['conflict']:>4} ({d['conflict_pct']:>5.1f}%) "
              f"{d['capacity']:>4} ({d['capacity_pct']:>5.1f}%)")

    # 2. Memory Latency Sensitivity
    miss_ratios = {k: v["miss_ratio"] for k, v in decomp.items()}
    lat_sweep = latency_sensitivity_sweep(miss_ratios)
    print("\n2. MEMORY LATENCY SENSITIVITY SWEEP (AMAT in cycles vs. Latency L):")
    header_l = [1, 2, 3, 5, 7, 9, 10, 15, 20]
    print(f"{'Trace':<12} " + " ".join(f"L={L:<4}" for L in header_l))
    print("-" * 65)
    for name in decomp.keys():
        row = [f"{lat_sweep[L][name]:<6.3f}" for L in header_l]
        print(f"{name:<12} " + " ".join(row))

    # 3. Power-of-Two Stride Aliasing
    stride_res = stride_aliasing_study()
    print("\n3. POWER-OF-TWO STRIDE ALIASING & SET-0 PATHOLOGICAL THRASHING:")
    print(f"{'Stride':<10} {'Sets Used':>10} {'Hits':>6} {'Misses':>7} {'HitRate':>8} {'Compulsory':>11} {'Conflict':>9}")
    print("-" * 65)
    for s, data in stride_res.items():
        print(f"{str(s)+' B':<10} {data['sets_touched']:>6}/64 {data['hits']:>6} {data['misses']:>7} "
              f"{data['hit_ratio']*100:>7.2f}% {data['compulsory']:>11} {data['conflict']:>9}")

    # 4. Backpressure Throughput
    amat_l5 = {k: 1.0 + v * 6.0 for k, v in miss_ratios.items()}
    tput = backpressure_throughput(amat_l5)
    print("\n4. EFFECTIVE THROUGHPUT (reads/cycle) UNDER RESPONSE BACKPRESSURE (L=5):")
    stalls = [0, 1, 2, 4, 8, 16]
    print(f"{'Trace':<12} " + " ".join(f"S={s:<5}" for s in stalls))
    print("-" * 55)
    for name in decomp.keys():
        row = [f"{tput[s][name]:<7.4f}" for s in stalls]
        print(f"{name:<12} " + " ".join(row))

    print("\nTelemetry characterization complete.")


def main():
    print_report()


if __name__ == "__main__":
    main()
