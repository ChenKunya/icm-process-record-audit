# 04 Controlled Analytical Analysis

Script for the controlled analytical analysis of empirical error correlation and validity gating reported in Section 7.4 and Appendix E of the manuscript *Language-Mediated Information Fusion in LLM-Based Agents: An Operation-Level Framework and Process-Record Audit*.

The analysis uses explicit probability constructions. All results are obtained by exact enumeration. No language model is called, no agent is executed and no random numbers are drawn.

## Files

| File | Content |
| --- | --- |
| `scripts/controlled_analysis.py` | Exact enumeration of both constructions and of the parameter grids |
| `results/controlled_analysis.json` | Output of the script |

## Constructions

| Construction | Tables | Definition |
| --- | --- | --- |
| Source grouping and empirical error correlation | E.1, E.2 | Five evidence paths with marginal accuracy p. Paths 1 to 3 share a source through E_i = B·H + (1 − B)·U_i with B ~ Bernoulli(ρ). Paths 4 and 5 are independent. Naive aggregation takes the majority of the five paths. Source-grouped aggregation takes the majority within paths 1 to 3 and then the majority of that group and paths 4 and 5. Main setting p = 0.75, ρ = 0.80. |
| Validity gating | E.3, E.4 | Generator error G, verifier error V = B·G + (1 − B)·U and independent verification error W, each with marginal error rate 0.25. Verifier-only gating activates a candidate when the verifier accepts it. Independent evidence gating also requires support from the independent verification source. Main setting ρ = 0.80. |

## Output keys

| Key | Content |
| --- | --- |
| `table_E1` | Aggregation accuracy under independence and under a shared source, the change from source grouping, and the decomposition of disagreements |
| `table_E2_change_pp` | Change in accuracy from source grouping, in percentage points, over p and ρ |
| `table_E3` | Activation rates of wrong and correct candidates, grant coverage and the share of errors among active entries under the four conditions |
| `table_E4` | Activation rate of wrong candidates and share of errors among active entries over ρ |

## Reproducing the results

Python 3.9 or later, standard library only. Run from this folder:

```
python scripts/controlled_analysis.py
```

Probabilities are computed as exact fractions and reported as percentages rounded half up to two decimals.
