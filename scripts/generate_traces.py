#!/usr/bin/env python3
"""Deterministic workloads and a separate, address-based direct-map oracle."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def workloads():
    rng = random.Random(6)
    return {
        "demo": [0, 4, 8, 12, 0, 0x400, 0, 0, 16, 20, 0x3FC, 0x3F0],
        "sequential": list(range(0, 4096, 4)),
        "repeated": list(range(0, 256, 4)) * 16,
        "random": [rng.randrange(0, 4096 // 4) * 4 for _ in range(1024)],
        "conflict": [0, 1024] * 512,
    }


def oracle(addresses):
    # Store full block numbers rather than splitting tag bits like the RTL does.
    resident = [None] * 64
    for address in addresses:
        block_number = address // 16
        slot = block_number % 64
        hit = resident[slot] == block_number
        resident[slot] = block_number
        yield address, int(hit), address ^ 0xA5A50000


def main():
    (ROOT / "traces").mkdir(exist_ok=True)
    manifest = {}
    for name, addresses in workloads().items():
        rows = list(oracle(addresses))
        (ROOT / "traces" / f"{name}.trace").write_text(
            "".join(f"{a:08x} {h} {d:08x}\n" for a, h, d in rows)
        )
        hits = sum(row[1] for row in rows)
        manifest[name] = {"accesses": len(rows), "hits": hits, "misses": len(rows) - hits}
    (ROOT / "traces" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
