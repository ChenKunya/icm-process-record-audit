# 01 Benchmark Process-Record Audit

Data and scripts for the process-record audit of 74 public LLM-agent benchmarks reported in Section 7.1–7.2 and Appendix C of the manuscript *Language-Mediated Information Fusion in LLM-Based Agents: An Operation-Level Framework and Process-Record Audit*.

Each benchmark is coded on 10 process-record fields, giving 740 coding units. Every unit receives one of four final codes.

| Code | Meaning |
| --- | --- |
| D | Directly available in the public default record |
| R | No independent field exists, but the information can be recovered uniquely from the public default record, either through a deterministic mapping or after adopting an additional convention not documented in the benchmark materials. The latter cases are flagged in the recovery-stability column of the "Coding" sheet and are recoded as U in the stable-inference sensitivity. |
| U | The process object exists, but the required information is neither available nor uniquely recoverable |
| NA | The process object is not instantiated in the standard task process of the benchmark |

## Coders

| ID | Role | Units |
| --- | --- | --- |
| A01 | Primary coder (one of the authors). Codes all 740 units. These codes are the data analysed in the manuscript. | 740 |
| A02 | Annotator for the reliability check (undergraduate student), not involved in the study design or the primary coding | 80 |
| A03 | Annotator for the reliability check (undergraduate student), not involved in the study design or the primary coding | 80 |

In Appendix C.1.3, annotator 1 is A02 and annotator 2 is A03.

## Files

| File | Content |
| --- | --- |
| `data/audit_coding_table_74x10_A01.xlsx` | Full coding table of A01. The "Coding" sheet gives, for every unit, applicability, boundary strength (for NA), record status, recovery stability (for R), evidence location, rationale and confidence. The "Benchmark register" sheet lists the 74 benchmarks with IDs, titles, venues and verification levels. The "Instructions" sheet gives the field definitions and value rules. |
| `data/reliability_sample.csv` | The 8 benchmarks drawn for the reliability check |
| `data/reliability_annotation_form_blank.xlsx` | The question-based annotation form given to the annotators, with instructions, a field guide and a worked example (MINT, outside the sample) |
| `data/reliability_annotation_A02.xlsx`, `data/reliability_annotation_A03.xlsx` | Completed annotation forms of A02 and A03 |
| `scripts/audit_statistics.py` | Field-level availability, Class I/C/M proxies under four coding criteria, Wilson and bootstrap intervals, alternative proxy definitions and task-family results |
| `scripts/reliability_sampling.py` | Draws the reliability subsample |
| `scripts/reliability_statistics.py` | Krippendorff's alpha, pairwise agreement and Cohen's kappa for A01, A02 and A03 |
| `results/audit_statistics.json`, `results/reliability_statistics.json` | Output of the two statistics scripts |

## Reproducing the results

Python 3.9 or later with `numpy` and `openpyxl`. Run from this folder:

```
python scripts/audit_statistics.py
python scripts/reliability_sampling.py
python scripts/reliability_statistics.py
```

Both statistics scripts read the coded answers directly and do not use the formula columns of the workbooks. Each bootstrap uses 10,000 benchmark-level resamples with replacement. The seed is 20261019 for the audit and 20261020 for the reliability check, and 20261020 is also the sampling seed.

## Coding criteria

| Criterion | Rule |
| --- | --- |
| Protocol A (`main`) | Final codes as coded, including R cases requiring an additional convention |
| Applicability sensitivity (`app`) | NA with a weak boundary is recoded as U |
| Stable-inference sensitivity (`inf`) | R cases requiring an additional convention not documented in the benchmark materials are recoded as U |
| Joint stress test (`joint`) | Both changes |

## Proxies

| Proxy | Condition | Denominator |
| --- | --- | --- |
| Class I | Source identifier and temporal position both D or R | All 74 benchmarks. NA counts as not met. |
| Class C | Dependence relations and parameter provenance both D or R | Benchmarks where both fields are applicable |
| Class M | Validity-change event D or R | Benchmarks where the field is applicable |

The Class M proxy indicates that entry-value updates can be recovered. No benchmark records the validity state itself (0/20), as reported in Section 7.2.3.

## Reliability check

After A01 had completed all 740 units, one benchmark was drawn at random from each of the seven task families and one more from the remaining 67 benchmarks. A02 and A03 then coded the 80 units of these 8 benchmarks independently with the annotation form. For each unit the form asks whether the process object exists, whether it is directly visible in the public records, and whether it can be uniquely recovered. The answers determine D, R, U or NA. The form does not record boundary strength or recovery stability. The "Annotator information" sheet of each completed form records the annotator's answers about independence.

## Task families

Task families are defined by benchmark ID: 1–6 planning and feedback, 7–20 tool and interface, 21–37 web and graphical interface, 38–42 memory, 43–54 general and multi-agent tasks, 55–57 safety and privacy, 58–74 software, science and data tasks.
