# 03 MAST Targeted Validation

Sample, case-level coding, review materials and scripts for the targeted test on failure trajectories with observable validity grants, reported in Sections 7.3.4–7.3.5 and Appendix D.9 of the manuscript *Language-Mediated Information Fusion in LLM-Based Agents: An Operation-Level Framework and Process-Record Audit*.

The test uses 86 failed trajectories of the AG2 multi-agent system in the MAST data, one per math problem from GSM-Plus. In each trajectory the Problem Solver and the Code Executor submit solutions, and the Verifier writes SOLUTION_FOUND with the system's final answer, which ends the conversation. The eligibility at stake is eligibility to be delivered as the final answer, which is delivered as a value, so submitted solutions are registered as pending entries by answer value. The first submission of a value creates the entry, identified by the message number and sender of that submission, and a later submission of the same value by the other side is a second source record of the same entry. Entry identity is fixed from the submissions before the grant. When the value written with SOLUTION_FOUND equals the value of an entry, this is a validity grant (Class M) to that entry and a rejection of the other entries. Each trajectory is coded on six questions, and the M-class grant, L6 and L7 are derived from the answers with the written rules of Appendix D.9.2.

## Coders

| ID | Role | Cases |
| --- | --- | --- |
| A01 | Primary coder (one of the authors), the same A01 as in `01_benchmark_record_audit` and `02_heldout_trajectory_validation`. Codes all 86 trajectories. These codes are the data analysed in the manuscript. | 86 |
| A02, A03 | Undergraduate students of computer science and technology, not involved in the study, the same two annotators as in `01_benchmark_record_audit`. First review round. | 24 |
| A04, A05 | Graduate students of computer science and technology, not involved in the study. Second review round, reported as the main review result. | 24 |

## Files

| File | Content |
| --- | --- |
| `data/targeted_sample_86.csv` | Case ID, model, seed, MAST instance ID, trajectory file, GSM-Plus perturbation type, and whether exploratory judgements on the trajectory were seen before coding |
| `data/targeted_coding_86_A01.csv` | Coding of A01 after all revisions: answers to Q1–Q6, message number of the overreach assertion, derived M-class grant, flag for validity decisions that discarded a correct solution, L6 and L7, and a note for each revised case |
| `data/type_a_recheck_A01.csv` | Re-check of the 17 trajectories first coded as Type A overreach assertions, after the wording of Type A was tightened |
| `data/corrections_after_review_round1_A01.csv` | The two cases A01 corrected after the first review round, with values before and after |
| `data/review_sample_24.csv` | The 24 cases drawn for review |
| `data/review_form_blank.xlsx` | The review form given to the coders, with instructions, decision card and annotation sheet |
| `data/review_round1_A02.xlsx`, `data/review_round1_A03.xlsx` | Completed forms of the first round |
| `data/review_round2_A04.xlsx`, `data/review_round2_A05.xlsx` | Completed forms of the second round |
| `scripts/select_samples.py` | Reproduces the 86-trajectory sample from the MAST snapshot and the 24-case review sample |
| `scripts/build_case_set.py` | Renders the trajectories as a case set with message numbers |
| `scripts/targeted_statistics.py` | Results of Table D.9 and Section 7.3.5, with the derivation of M-class grant, L6 and L7 checked against the coding table |
| `scripts/review_statistics.py` | Agreement, Cohen's kappa and Krippendorff's alpha of both review rounds (Table D.10 and Appendix D.9.4) |
| `results/targeted_statistics.json`, `results/review_statistics.json` | Output of the two statistics scripts |

## Coding table

| Column | Values |
| --- | --- |
| `Q1_grant` | `adopted_submitted_solution`, `new_answer_by_verifier`, `no_grant` |
| `Q2_correct_solution_rejected` | `yes` when one side had submitted the reference answer before the grant and it was not adopted, otherwise `no` |
| `Q3_same_source` | `yes` when the two submitted solutions share their derivation, `no`, `cannot_tell` |
| `Q4_independent_check` | `yes` when a check independent of the two derivations produced a result before the grant, `no`, `cannot_tell` |
| `Q5_grant_reason` | `agreement_of_both_sides`, `other_reason`, `no_reason` |
| `Q6_overreach_assertion` | Earliest assertion beyond its grounds before SOLUTION_FOUND. `A` unexecuted or empty code results presented as execution output, `B` information added in the user's voice, `C` unstated assumption with an unqualified conclusion, `D` other assertion beyond its grounds, `none` |
| `Q6_message` | Message number of the assertion |
| `M_grant` | `1` when Q1 is `adopted_submitted_solution` |
| `correct_solution_discarded` | `1` when Q2 is `yes` and the Verifier wrote SOLUTION_FOUND. A screening flag for validity decisions that discarded a correct solution, which does not by itself locate the decisive operation |
| `L6` | `1`, `0` or `undeterminable` |
| `L7` | `1`, `0`, `source_coupled_structure`, `undeterminable` or `not_applicable` |

Message numbers are zero-based indices into the `trajectory` list of the MAST trajectory file, which is also the numbering shown in the case set.

## Revisions of the primary coding

- After all 86 trajectories had been coded, the wording of Type A was tightened. A01 re-checked the 17 trajectories first coded as Type A. Nine were kept and eight were recoded as having no overreach assertion, so that their L7 became `source_coupled_structure` (`type_a_recheck_A01.csv`).
- After the first review round, A01 checked the items on which both annotators agreed with each other and disagreed with A01, and corrected G62 and G77 under the rules of Appendix D.9.2 (`corrections_after_review_round1_A01.csv`). The first round is compared with the coding before these corrections, the second round with the corrected coding.
- Exploratory judgements on G13, G50, G81 and G84 had been seen by A01 before coding started. The manuscript reports results with and without these four trajectories.

## Review procedure

The 24 cases were drawn from the 86 with `random.Random(20261021).sample`. Each coder received the blank form and a case set containing only these 24 cases. The form asks five of the six questions in everyday language. Form question 1 corresponds to Q1, and form questions 2 to 5 correspond to Q3 to Q6. Q2 is not part of the review. The coders worked alone, did not discuss records with others, did not use AI tools and did not consult the manuscript or the primary coding. Both rounds used the same form, decision card and case set.

## Reproducing the results

Python 3.9 or later. `review_statistics.py` also requires `openpyxl`. Run from this folder:

```
python scripts/targeted_statistics.py
python scripts/review_statistics.py
```

To reproduce the samples and case sets, obtain the MAST data and pass the folder `traces/AG2/experiments`:

```
python scripts/select_samples.py <MAST>/traces/AG2/experiments
python scripts/build_case_set.py <MAST>/traces/AG2/experiments case_set_86.html
python scripts/build_case_set.py <MAST>/traces/AG2/experiments case_set_review_24.html --review
```

## Data source

The trajectories come from the public MAST repository, snapshot commit `a70542e541b2104ef8fcd785778179e173fb8d70`, folder `traces/AG2/experiments`, the twelve runs whose names contain `impr_topology` (GPT-4 and GPT-4o, seeds 42 to 47).
