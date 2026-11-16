#!/usr/bin/env python3
"""Create a captioned 3:30 draft MP4 from real simulation evidence (no voices)."""
import csv
import json
import shutil
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT / "build/demo"
BG, INK, MUTED, BLUE = "#102235", "#edf4fb", "#b6c9da", "#57b7ea"


def font(size, mono=False):
    candidates = (["/System/Library/Fonts/Monaco.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"] if mono else
                  ["/System/Library/Fonts/Supplemental/Arial.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for candidate in candidates:
        if Path(candidate).exists(): return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size=size)


def slide(title, lines=None, picture=None, footer="", highlight=None):
    canvas = Image.new("RGB", (1280, 720), BG); draw = ImageDraw.Draw(canvas)
    draw.text((48, 28), "PROJECT 6  /  PHASE I PROTOTYPE", font=font(18), fill=BLUE)
    draw.text((48, 65), title, font=font(37), fill=INK)
    if picture:
        image = Image.open(ROOT / picture).convert("RGB")
        image.thumbnail((1184, 470))
        canvas.paste(image, ((1280 - image.width) // 2, 128 + (470 - image.height) // 2))
    elif lines:
        ypos = 140
        for index, line in enumerate(lines):
            draw.text((58, ypos), line, font=font(25, mono=highlight is not None),
                      fill=BLUE if index == highlight else INK)
            ypos += 34
    for number, line in enumerate(textwrap.wrap(footer, 94)):
        draw.text((48, 620 + number * 27), line, font=font(23), fill=MUTED)
    draw.text((48, 690), "Generated rehearsal walkthrough | Team names confirmed; final recording pending",
              font=font(15), fill=MUTED)
    return canvas


def main():
    if not shutil.which("ffmpeg"): raise SystemExit("ffmpeg is required for make demo")
    FRAMES.mkdir(parents=True, exist_ok=True)
    team = json.loads((ROOT / "team.json").read_text())
    summary = json.loads((ROOT / "results/summary.json").read_text())
    segments = []

    def add(image, duration):
        name = f"frame_{len(segments):03}.png"
        image.save(FRAMES / name); segments.append((name, duration))

    add(slide("Direct-Mapped Cache Controller", [
        "Goal: implement lookup and refill; analyze locality and AMAT.", "",
        "1 KiB data capacity | 16-byte lines | 64 cache lines",
        "32-bit byte addresses | aligned 32-bit reads", "",
        "Working RTL + self-checking simulation + generic synthesis",
    ], footer="This draft presents actual prototype results. The final submission must clearly introduce all five group members by name."), 12)
    add(slide("Team members and enrollment numbers", [
        f"{i + 1}. {member['name']}  |  {member['enrollment_number']}"
        for i, member in enumerate(team["members"])
    ] + ["", "Clearly introduce all five group members in the final recording."],
        footer="All five names and enrollment numbers are confirmed. Record the final presentation with clear team introductions."), 22)
    add(slide("Addressing, storage and lookup", picture="docs/diagrams/architecture.png",
              footer="Tag = address[31:10]; index = address[9:4]; offset = address[3:0]. A hit requires valid AND matching tag."), 22)
    add(slide("Controller and atomic refill", picture="docs/diagrams/fsm.png",
              footer="Latch the request, classify once, refill the whole line on a miss, then hold the response until accepted."), 20)
    passed = [line for line in (ROOT / "results/simulation.log").read_text().splitlines()
              if line.startswith("PASS trace=") and "memory_latency=5" in line]
    lines = ["$ make sim", ""]
    for line in passed:
        words = line.split()
        lines.append(words[1].replace("trace=traces/", "").replace(".trace", "") + "  " +
                     "  ".join(words[2:5]))
    lines += ["", "PASS: 15 runs, five workloads, latencies 1 / 5 / 9.",
              "Each response and each counter checked; watchdogs enabled."]
    add(slide("Actual saved RTL regression output", lines,
              footer="Reproduce with make sim. The Python oracle and RTL agree on every address, returned word, hit/miss result and latency."), 24)
    with (ROOT / "results/demo.csv").open() as file:
        rows = list(csv.DictReader(file))
    table = [" #   Address     Result   Data        Cycles"] + [
        f"{int(r['access']):2}   {r['address']}    {'HIT ' if r['hit'] == '1' else 'MISS'}    {r['data']}     {r['latency_cycles']}"
        for r in rows]
    for i in range(12):
        add(slide("Step through the measured 12-access demo", table,
                  footer="0, 4, 8 and 12 share a line. Address 0x400 evicts index zero. Each row comes from actual RTL output.",
                  highlight=i + 1), 2)
    add(slide("The demo explains spatial reuse and conflict", [
        "12 aligned accesses: 7 hits and 5 misses", "",
        "A cold miss fetches all four words in a 16-byte line.",
        "Same index + different tag replaces the resident line.",
        "An immediate repeat then hits the newly filled line.",
    ], footer="Inspect results/demo.csv alongside traces/demo.trace."), 4)
    add(slide("Waveform from the real simulator VCD", picture="docs/diagrams/waveform.png",
              footer="The first request waits for memory; later same-line requests hit. Response data and status remain stable during backpressure."), 24)
    add(slide("Measured locality and AMAT", picture="docs/diagrams/results.png",
              footer="Default hit = 1 cycle, miss = 7 cycles; additional miss penalty = 6. Sequential AMAT = 1 + 0.25 x 6 = 2.5 cycles."), 22)
    synthesis = json.loads((ROOT / "results/synthesis_cells.json").read_text())
    kinds = synthesis["design"]["num_cells_by_type"]
    cells = sum(n for k, n in kinds.items() if k.startswith("$_"))
    ffs = sum(n for k, n in kinds.items() if k.startswith("$_DFF"))
    add(slide("Generic synthesis: actual tool evidence", [
        "$ make synth", "", "Yosys structural check: PASS before and after synthesis",
        f"Generic leaf cells: {cells:,}", f"Included flip-flop cells: {ffs:,}", "",
        "Data + tag arrays infer two memories before generic mapping.",
        "Testbench and memory model are excluded from synthesis.",
    ], footer="These are generic logic counts. Device LUTs, BRAM, Fmax, physical area and power require a selected FPGA flow."), 18)
    add(slide("Phase I progress and final team actions", [
        "Ready: RTL, verification, traces, AMAT and synthesis evidence.",
        "Ready: IEEE report, diagrams, demo script and this draft video.", "",
        "Ready: all five names and enrollment numbers confirmed.",
        "Pending: department, college and course details.",
        "Pending: each member's real contribution and Git history.",
        "Pending: team recording, accessible hosted URL, submission form.", "",
        "github.com/samarth-khera/Direct-Mapped-Cache-Project",
    ], footer="Record the five-speaker script in about 4:30; keep the final video under five minutes."), 18)
    duration = sum(duration for _, duration in segments)
    assert duration == 210 and duration <= 300
    concat = "".join(f"file '{name}'\nduration {duration}\n" for name, duration in segments)
    concat += f"file '{segments[-1][0]}'\n"
    (FRAMES / "concat.txt").write_text(concat)
    output = ROOT / "docs/demo/phase1_prototype_draft.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat",
                    "-safe", "0", "-i", str(FRAMES / "concat.txt"), "-t", str(duration),
                    "-vf", "fps=10,format=yuv420p", "-c:v", "libx264", "-crf", "24",
                    "-movflags", "+faststart", str(output)], check=True)
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_name,width,height",
        "-of", "json", str(output)], text=True))
    assert float(probe["format"]["duration"]) <= 300
    (ROOT / "results/demo_video.json").write_text(json.dumps(probe, indent=2) + "\n")
    print(f"Created {output.relative_to(ROOT)}: {duration}s, 1280x720, captioned draft.")


if __name__ == "__main__":
    main()
