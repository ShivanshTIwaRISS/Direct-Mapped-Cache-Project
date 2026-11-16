#!/usr/bin/env python3
"""Check technical evidence and report final submission requirements separately."""
import argparse
import ast
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise SystemExit("FAIL: " + message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    required = [
        "README.md", "Makefile", ".gitignore", ".gitattributes", "addr_decoder.v", "cache_fsm.v",
        "rtl/cache_controller.v", "rtl/cache_data_ram.v", "rtl/tag_ram.v",
        "rtl/valid_bit_ram.v", "rtl/tag_comparator.v", "tb/cache_controller_tb.sv",
        "tb/main_memory_model.v", "docs/architecture.md", "docs/results_analysis.md",
        "docs/contributions.md", "docs/phase1_audit.md", "docs/demo/script.md",
        "docs/demo/video_link.md", "docs/demo/phase1_prototype_draft.mp4",
        "docs/report/phase1_report.tex", "docs/report/phase1_report.pdf",
        "docs/report/generated_results.tex", "docs/report/generated_team.tex",
        "docs/report/generated_contributions.tex", "results/simulation.log",
        "results/synthesis.log", "results/synthesis_memory.json", "results/synthesis_cells.json",
        "results/summary.csv", "results/summary.json", "results/deep_check.json",
        "results/deep_check.log", "results/demo_video.json", "team.json",
        ".github/workflows/verify.yml",
    ]
    for name in required:
        require((ROOT / name).is_file() and (ROOT / name).stat().st_size > 0, "Missing or empty " + name)
    for script in (ROOT / "scripts").glob("*.py"):
        ast.parse(script.read_text(), filename=str(script))
    for document in (ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))):
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
            if target.startswith(("https://", "http://", "#")):
                continue
            require((document.parent / target.split("#", 1)[0]).exists(),
                    f"Broken local link in {document.relative_to(ROOT)}: {target}")
    pdf = (ROOT / "docs/report/phase1_report.pdf").read_bytes()
    require(pdf.startswith(b"%PDF-") and len(pdf) > 20000, "Report is not a compiled PDF")
    report = (ROOT / "docs/report/phase1_report.tex").read_text()
    for text in ("{IEEEtran}", "{abstract}", "{Literature Review}", "{Proposed Solution}",
                 "{Individual Contributions}", "{thebibliography}"):
        require(text in report, "Required IEEE report component missing: " + text)
    log = (ROOT / "results/simulation.log").read_text()
    require(len(re.findall(r"^PASS trace=", log, re.M)) == 15, "Expected 15 passing regression runs")
    require("FATAL" not in log and "ERROR" not in log, "Simulation failures found")
    synthesis_log = (ROOT / "results/synthesis.log").read_text()
    require("ERROR:" not in synthesis_log and "Found and reported 0 problems" in synthesis_log,
            "Missing successful synthesis structural check")
    summary = json.loads((ROOT / "results/summary.json").read_text())
    require({r["trace"] for r in summary} == {"demo", "sequential", "repeated", "random", "conflict"},
            "Trace summary incomplete")
    for result in summary:
        with (ROOT / f"results/{result['trace']}.csv").open() as file:
            rows = list(csv.DictReader(file))
        trace_rows = (ROOT / f"traces/{result['trace']}.trace").read_text().splitlines()
        require(len(rows) == len(trace_rows) == result["accesses"], "Trace/result lengths disagree")
        resident, hits = {}, 0
        for number, (row, source) in enumerate(zip(rows, trace_rows), 1):
            address_text, want_hit, want_data = source.split()
            address = int(address_text, 16)
            block, index = address // 16, address // 16 % 64
            hit = int(resident.get(index) == block)
            resident[index] = block; hits += hit
            require(int(row["access"]) == number and int(row["address"], 16) == address,
                    "RTL row number/address incorrect")
            require(int(row["hit"]) == int(want_hit) == hit, "Classification mismatch")
            require(int(row["data"], 16) == int(want_data, 16) == address ^ 0xA5A50000,
                    "Returned data mismatch")
            require(int(row["latency_cycles"]) == (1 if hit else 7), "Measured latency mismatch")
        require(hits == result["hits"] and len(rows) - hits == result["misses"], "Counters mismatch")
        mean = sum(int(row["latency_cycles"]) for row in rows) / len(rows)
        require(abs(mean - result["amat_cycles"]) < 1e-12 and
                abs(mean - (1 + 6 * result["misses"] / result["accesses"])) < 1e-12,
                "Measured and analytical AMAT disagree")
    stress = json.loads((ROOT / "results/deep_check.json").read_text())
    require(stress["status"] == "PASS" and stress["outputs_identical"] and
            stress["stress_accesses_per_design"] == 4096, "Missing netlist stress verification")
    for name in ("architecture", "fsm", "results", "waveform"):
        for ext in ("png", "pdf", "svg"):
            require((ROOT / f"docs/diagrams/{name}.{ext}").is_file(), "Missing diagram: " + name)
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height",
        "-of", "json", str(ROOT / "docs/demo/phase1_prototype_draft.mp4")], text=True))
    require(0 < float(probe["format"]["duration"]) <= 300, "Draft video exceeds five minutes")
    require(any(s.get("width") == 1280 and s.get("height") == 720 for s in probe["streams"]),
            "Draft video resolution incorrect")
    pending = []
    team = json.loads((ROOT / "team.json").read_text())
    require(len(team["members"]) == 5, "Exactly five member records required")
    enrollments = [member["enrollment_number"] for member in team["members"]]
    require(len(set(enrollments)) == 5 and all(re.fullmatch(r"\d{10}", value) for value in enrollments),
            "Five unique 10-digit enrollment numbers are required")
    for document in ("README.md", "docs/contributions.md", "docs/phase1_audit.md",
                     "docs/demo/script.md", "docs/report/generated_team.tex"):
        content = (ROOT / document).read_text()
        require(team["department"] in content and team["college"] in content,
                "Missing department or university in " + document)
    for document in ("README.md", "docs/contributions.md", "docs/demo/script.md",
                     "docs/report/generated_team.tex", "docs/report/generated_contributions.tex"):
        content = (ROOT / document).read_text()
        for member in team["members"]:
            require(member["name"] in content and member["enrollment_number"] in content,
                    f"Missing team member or enrollment number in {document}: {member['name']}")
    for i, member in enumerate(team["members"], 1):
        if not member.get("confirmed") or "pending" in (member["name"] + member["enrollment_number"]).lower():
            pending.append(f"{member['name']}: confirmed full name and enrollment number")
        if not member.get("contribution_commits"):
            pending.append(f"{member['name']}: completed contribution and real commit evidence")
        else:
            for commit in member["contribution_commits"]:
                require(bool(re.fullmatch(r"[0-9a-f]{7,40}", commit)), "Invalid contribution commit")
                exists = subprocess.run(["git", "cat-file", "-e", commit + "^{commit}"], cwd=ROOT,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                require(exists.returncode == 0, "Contribution commit not found: " + commit)
    for field in ("college", "department", "course"):
        if "pending" in team.get(field, "PENDING").lower(): pending.append("Confirmed " + field)
    final_link = next((line for line in (ROOT / "docs/demo/video_link.md").read_text().splitlines()
                       if line.startswith("Final recording URL:")), "")
    if not re.search(r"https://\S+", final_link) or "PENDING" in final_link:
        pending.append("Final hosted video with all five introductions")
    review = team.get("submission_review", {})
    for field, description in [
        ("contributions_verified", "Human review of five meaningful contributions and authorship"),
        ("video_access_verified", "Final video reviewed for introductions, duration and evaluator access"),
        ("form_submitted", "Submission through the instructor's form"),
    ]:
        if not review.get(field): pending.append(description)
    evidence = {"technical_package": "PASS", "regression_runs": 15, "workload_reads": 12324,
                "stress_reads_per_design": 4096, "synthesized_outputs_match": True,
                "draft_video_seconds": float(probe["format"]["duration"]),
                "team_members": [{"name": m["name"], "enrollment_number": m["enrollment_number"]}
                                 for m in team["members"]],
                "team_details_confirmed": all(m.get("confirmed") for m in team["members"]),
                "department": team["department"], "college": team["college"],
                "submission_ready": not pending, "pending": pending}
    (ROOT / "results/phase1_checks.json").write_text(json.dumps(evidence, indent=2) + "\n")
    # The hash manifest excludes itself and the check-status output.
    artifacts = sorted({*required, *[str(p.relative_to(ROOT)) for p in (ROOT / "traces").glob("*")],
                        *[str(p.relative_to(ROOT)) for p in (ROOT / "results").glob("*.csv")],
                        *[str(p.relative_to(ROOT)) for p in (ROOT / "scripts").glob("*") if p.is_file()],
                        *[str(p.relative_to(ROOT)) for p in (ROOT / "docs/diagrams").glob("*")],
                        "requirements.txt"})
    manifest = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in artifacts}
    (ROOT / "results/artifact_sha256.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"PASS: technical package ({len(manifest)} hashed artifacts); RTL/netlist checks, report and 210s draft.")
    if pending:
        print("SUBMISSION PENDING:")
        for item in pending: print("- " + item)
    else: print("Submission checklist complete; retain the actual review evidence.")
    if args.strict and pending: raise SystemExit(2)


if __name__ == "__main__":
    main()
