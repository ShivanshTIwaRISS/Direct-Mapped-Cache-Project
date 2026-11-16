.PHONY: all traces sim synth report demo deepcheck check submission-check
PYTHON ?= $(if $(wildcard .tools/venv/bin/python),.tools/venv/bin/python,python3)
all: sim synth report

traces:
	$(PYTHON) scripts/generate_traces.py

sim:
	$(PYTHON) scripts/run_sim.py

synth:
	@mkdir -p build results
	yosys -q -Q -T -l results/synthesis.log scripts/synthesize.ys

report:
	$(PYTHON) scripts/build_artifacts.py
	tectonic -o docs/report docs/report/phase1_report.tex

demo:
	$(PYTHON) scripts/build_demo.py

deepcheck:
	$(PYTHON) scripts/deep_check.py

check: sim synth deepcheck report demo
	$(PYTHON) scripts/check_submission.py

submission-check:
	$(PYTHON) scripts/check_submission.py --strict
