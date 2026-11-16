# Contributions and Git history

The repository originally had one remote commit, `f6fbe40`, authored by
`samarth-khera`, with the decoder, initial three-state FSM and README. It has
been preserved. At the initial audit, the README listed only the first names of
Samarth Khera and Tattva Rajput plus three placeholders. The user has since confirmed the full five-member
roster and enrollment numbers below.

The integration, tests, traces, analysis, report and demo preparation added in
this work are AI-assisted. They must not be represented as five completed
individual contributions. `team.json` is the source for names and proposed
review responsibilities. Names and enrollment numbers are confirmed; completed
contribution descriptions and further commit evidence should be updated as
each member completes their work.

Each person should make a substantive change they understand and can explain,
run the relevant checks, and commit using their own configured Git identity.
Use these proposed tasks as a starting point:

| Team member | Enrollment number | Proposed work to own and verify | Existing evidence / next evidence |
| --- | --- | --- | --- |
| Navprabhat Singh | 2401010293 | Verify references, institution details, PDF and demo presentation | Completed personal contribution and commit evidence pending |
| Samarth Khera | 2401010407 | Explain decoder and original FSM; review the four-state extension and timing | Original commit `f6fbe40`; further personal review work can be recorded |
| Pratham Malhotra | 2401010343 | Review integration and memory handshaking; extend protocol validation | AI-assisted package and metadata commits `193f6ed` and `83031a7` use Pratham Malhotra's configured Git identity |
| Shivansh Tiwari | 2401020108 | Review oracle and trace analysis; add a representative workload with interpretation | Completed personal contribution and commit evidence pending |
| Tattva Rajput | 2401010478 | Review storage and reset; add a justified storage improvement or test | Listed in the original README; personal implementation commit evidence pending |

These are proposed tasks, not completed credits. After real work is done,
replace pending entries in `team.json` with accurate contribution descriptions
and commit hashes, then rebuild the report. Do not backdate commits, create
commits as other people, or split this assisted work into fabricated authors.

Suggested workflow: each member creates a branch, makes their change, runs
`make check`, and opens a PR. Preserve authorship when merging. Record each
member's name in the final video; the supplied five-speaker script is optional.
