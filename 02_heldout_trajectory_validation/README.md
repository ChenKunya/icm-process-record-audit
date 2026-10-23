# 02 Held-Out Trajectory Validation

Case-level coding and statistics for the held-out examination of public failure trajectories reported in Sections 7.3.1–7.3.3 and Appendix D.1–D.8 of the manuscript *Language-Mediated Information Fusion in LLM-Based Agents: An Operation-Level Framework and Process-Record Audit*.

The examination uses 100 failure trajectories from the Who&When benchmark (68 Algorithm-Generated, 32 Hand-Crafted). For each trajectory the decisive minimal operation is located, its direct-effect signature determines the ICM class (I, C, M or undecidable), and the first-order diagnostics L1–L6 are judged under the strict criteria. The determination rules were fixed on a separate 19-case pilot sample whose case identifiers do not overlap with the held-out sample.

## Coder

All 100 cases were coded by A01, the primary coder (one of the authors), who is also A01 in `01_benchmark_record_audit`. The held-out sample was not double-coded.

## Files

| File | Content |
| --- | --- |
| `data/whowhen_heldout_coding_matrix_A01.csv` | One row per case: case ID, sample group, path of the trajectory file in the Who&When data, ICM class, strict first-order diagnostic, reference quality, reason code, coding rationale and coder ID |
| `data/reason_codes.csv` | Definitions of the eight reason codes and their frequencies |
| `scripts/heldout_statistics.py` | Determinability, class distribution, strict diagnostic coverage, results by sample group with Fisher exact tests, and the three sensitivity analyses |
| `results/heldout_statistics.json` | Output of the script |

## Column values

| Column | Values |
| --- | --- |
| `icm_class` | `I`, `C`, `M`, or `U` for undecidable |
| `strict_diagnostic` | `L1`–`L6` when the full conditions of that diagnostic are met, `None` for determinable cases that meet none, `NA` for undecidable cases |
| `reference_quality` | `consistent` when the public annotation agrees with the visible trajectory, `ambiguous` when the two are directly or highly suspiciously inconsistent |

## Reproducing the results

Python 3.9 or later, standard library only. Run from this folder:

```
python scripts/heldout_statistics.py
```

## Data source

Obtain the Who&When trajectories from the public repository of the benchmark. The snapshot used in this study is commit `6c9b068598cddaa9e9755dc9d1a3cc4a38970289`. The pilot sample was drawn with random seed 20260916 and the held-out sample with seed 20260917, stratified by sample group, after excluding all 20 case identifiers drawn for the pilot.
