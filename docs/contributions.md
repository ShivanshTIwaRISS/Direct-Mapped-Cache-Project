# Contributions and Git history

The repository originally had one remote commit, `f6fbe40`, authored by
`samarth-khera`, with the decoder, initial three-state FSM and README. It has
been preserved. The original README listed Samarth and Tattva plus three
placeholders. No full five-member identity list or other member commits were
available during this audit.

The integration, tests, traces, analysis, report and demo preparation added in
this work are AI-assisted. They must not be represented as five completed
individual contributions. `team.json` is the source for names and proposed
review responsibilities; edit it with confirmed details before submission.

Each person should make a substantive change they understand and can explain,
run the relevant checks, and commit using their own configured Git identity.
Use these proposed tasks as a starting point:

| Member slot | Proposed work to own and verify | Useful evidence |
| --- | --- | --- |
| 1: Samarth | Explain decoder and original FSM; review the four-state extension and timing | Original commit, reviewed RTL change, personal video section |
| 2: Tattva | Review storage and reset; add a justified cache-storage improvement or test | Own meaningful commit and storage explanation |
| 3 | Review memory handshaking; extend protocol validation | Own meaningful implementation/test commit |
| 4 | Review oracle and trace analysis; add a representative workload with interpretation | Own trace/analysis commit and results |
| 5 | Verify references, institution details, PDF and demo presentation | Own substantial documentation/video contribution |

These are proposed tasks, not completed credits. After real work is done,
replace pending entries in `team.json` with accurate contribution descriptions
and commit hashes, then rebuild the report. Do not backdate commits, create
commits as other people, or split this assisted work into fabricated authors.

Suggested workflow: each member creates a branch, makes their change, runs
`make check`, and opens a PR. Preserve authorship when merging. Record each
member's name in the final video; the supplied five-speaker script is optional.
