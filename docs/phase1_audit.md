# Phase I audit against the supplied rubric

The rubric awards 10 marks for the IEEE report, 15 for a prototype video, and
5 for the repository. The evaluator decides the marks; this audit records
evidence and remaining actions without assigning a score.

## Starting state

The local branch initially had no commits or working files. GitHub had one
commit, `f6fbe40`, with `addr_decoder.v`, a preliminary `cache_fsm.v` and a short
README listing only the first names of Samarth Khera and Tattva Rajput, plus three name placeholders. That commit was
fetched and checked out without rewriting its history. No report, testbench,
cache storage, traces, measured statistics, synthesis evidence or video were
present in that commit.

## Confirmed team

| Team member | Enrollment number |
| --- | --- |
| Navprabhat Singh | 2401010293 |
| Samarth Khera | 2401010407 |
| Pratham Malhotra | 2401010343 |
| Shivansh Tiwari | 2401020108 |
| Tattva Rajput | 2401010478 |

These user-confirmed details are stored in `team.json` and included in the
report, contribution records and demo materials. Department, college and course
details have not been supplied.

## Rubric checklist

| Required item | Current state | Evidence / remaining action |
| --- | --- | --- |
| IEEE format | Implemented | IEEEtran conference class and compiled PDF in `docs/report/` |
| Abstract | Implemented | Implemented scope and actual measurements |
| Literature review | Implemented | Discussion of locality, direct mapping, Jouppi and CACTI |
| Proposed solution | Implemented | Geometry, architecture, protocol, FSM, timing and verification |
| Individual contributions | Section present; team completion pending | Original author evidence preserved; proposed roles labeled; completed personal work and commits still needed |
| References | Implemented | Five entries including original research and official tool sources |
| Video maximum five minutes | Draft implemented | 210-second captioned MP4 and a 270-second team recording script |
| Video explains idea | Implemented in draft and script | Goal, configuration, locality and AMAT |
| Team names and enrollment numbers | Complete | All five confirmed pairs appear in `team.json`, README, report and demo materials |
| Video introduces all five members | Names ready; final recording pending | Confirmed roster is on the draft video team card; record the spoken introductions |
| Video shows working/progress | Draft implemented; final recording pending | Actual simulator output, trace walkthrough, VCD, charts and synthesis evidence |
| Repository contains report | Published; team details updated | LaTeX, compiled PDF and generated tables |
| Repository contains final video link | Pending | `docs/demo/video_link.md` explicitly marks the final hosted URL pending |
| Repository contains prototype files | Published | RTL, testbench, memory endpoint, scripts, traces and Makefile |
| Relevant artifacts | Implemented | Figures, CSV/JSON/log evidence and draft video |
| Genuine version history | Preserved | Original commit retained; assisted work uses the configured author |
| Five meaningful individual contributions | Further evidence pending | Existing commits identify Samarth Khera and Pratham Malhotra; further completed work and personal commit evidence remain pending |
| Repository link submitted through form | Pending | Institution details and final form submission required |

## Verification evidence

- Fifteen RTL runs: five traces at memory-model latencies 1, 5 and 9.
- 12,324 workload reads checked against an address-based Python oracle.
- Every run includes 142 directed read checks and additional reset-abort cases.
- Full 32-bit address stress: 4,096 requests on RTL and the synthesized netlist;
  outputs match the oracle and each other.
- Tests cover reset invalidation at all 64 indices, every word offset, high
  tags, conflict eviction, misalignment, input changes while busy, held
  responses, exact statistics and one completed memory transaction per miss.
- AMAT independently recomputed from per-access measured RTL latency.
- Yosys structural checks pass before and after generic synthesis, excluding
  the testbench and external memory model.
- IEEEtran report compiles to PDF; figures include a real VCD plot.
- Draft MP4: H.264, 1280x720, 210 seconds, captioned rehearsal material without
  recorded team introductions; all five confirmed names and enrollment numbers
  appear on its team card.
- `make check` rebuilds the technical package. `make submission-check` also
  enforces final identity, contribution and video readiness. Technical success
  is reported separately from the unfinished submission requirements.

See `results/phase1_checks.json`, `results/artifact_sha256.json`,
`results/deep_check.json` and the raw simulator/synthesis outputs.

## Finish the submission

1. The five names and enrollment numbers in `team.json` are confirmed. Add the
   remaining department, college and course details.
2. Each person must do and understand a substantive contribution. Update the
   contribution descriptions and add `contribution_commits` arrays with their
   actual commit hashes. A person must review meaningful work and authorship.
3. Rebuild the report and review its author and contributions sections.
4. Record the five-speaker script with all five introductions. Keep the final
   export at or below 300 seconds, host it and verify evaluator access.
5. Put the hosted URL on the `Final recording URL:` line in
   `docs/demo/video_link.md`, then commit and push the final updates.
6. Update `team.json`'s `submission_review` flags only after completing those
   checks and submitting the instructor's form. Run `make submission-check`.

Stores, FPGA integration and timing closure are future technical extensions,
distinct from the remaining Phase I team and submission requirements above.
