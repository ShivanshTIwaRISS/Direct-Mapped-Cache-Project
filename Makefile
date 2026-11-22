.PHONY: all traces sim synth report demo deepcheck check submission-check stress-dv
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

stress-dv:
	@mkdir -p build
	iverilog -g2012 -Wall -Wno-timescale -s protocol_stress_tb -o build/protocol_stress_tb \
		addr_decoder.v cache_fsm.v rtl/cache_controller.v rtl/cache_data_ram.v \
		rtl/tag_ram.v rtl/valid_bit_ram.v rtl/tag_comparator.v tb/protocol_stress_tb.sv
	vvp build/protocol_stress_tb
