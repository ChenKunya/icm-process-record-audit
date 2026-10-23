"""Exact enumeration of the controlled analytical analysis (Appendix E of the manuscript).

Usage:
    python scripts/controlled_analysis.py [output.json]

Default output: results/controlled_analysis.json. Python 3.9+, standard library only.
No random numbers are used. Every probability is computed exactly with fractions and
reported as a percentage rounded half up to two decimals.

Construction 1 (Tables E.1 and E.2). Five evidence paths, each with marginal accuracy p
and error rate q = 1 - p. B ~ Bernoulli(rho), H and U1..U5 ~ Bernoulli(q), all independent.
Paths 1-3 share a source: E_i = B*H + (1 - B)*U_i. Paths 4 and 5 are independent: E_4 = U_4,
E_5 = U_5. Naive aggregation is a majority vote over the five paths. Source-grouped
aggregation first takes the majority within paths 1-3 and then a majority over that group
and paths 4 and 5.

Construction 2 (Tables E.3 and E.4). Generator error G, verifier error V = B*G + (1 - B)*U
and independent verification error W, each with marginal error rate q = 0.25. Under
verifier-only gating an entry becomes active when the verifier accepts it. Under
independent evidence gating the independent verification source must also support it.
"""
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as Fr
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DST = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'results' / 'controlled_analysis.json'


def pct(x):
    """Percentage of an exact fraction, rounded half up to two decimals."""
    d = Decimal(x.numerator) * 100 / Decimal(x.denominator)
    return float(d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def construction_1(p, rho):
    q = 1 - p
    out = dict(naive=Fr(0), grouped=Fr(0), first_three_wrong=Fr(0),
               naive_wrong_grouped_right=Fr(0), naive_right_grouped_wrong=Fr(0))
    for b in (0, 1):
        pb = rho if b else 1 - rho
        if pb == 0:
            continue
        for h in (0, 1):
            ph = q if h else p
            for u in product((0, 1), repeat=5):
                pu = Fr(1)
                for x in u:
                    pu *= q if x else p
                pr = pb * ph * pu
                e = [b * h + (1 - b) * u[i] for i in range(3)] + [u[3], u[4]]
                naive_ok = sum(1 - x for x in e) >= 3
                group_ok = sum(1 - x for x in e[:3]) >= 2
                grouped_ok = (group_ok + (1 - e[3]) + (1 - e[4])) >= 2
                out['naive'] += pr * naive_ok
                out['grouped'] += pr * grouped_ok
                out['first_three_wrong'] += pr * (e[0] and e[1] and e[2])
                out['naive_wrong_grouped_right'] += pr * ((not naive_ok) and grouped_ok)
                out['naive_right_grouped_wrong'] += pr * (naive_ok and not grouped_ok)
    return out


def construction_2(rho, q=Fr(1, 4), independent_gate=False):
    p = 1 - q
    wrong_active = rho + (1 - rho) * q
    right_active = 1 - (1 - rho) * q
    if independent_gate:
        wrong_active *= q
        right_active *= p
    coverage = p * right_active + q * wrong_active
    return dict(wrong_candidate_activation=wrong_active, correct_candidate_activation=right_active,
                grant_coverage=coverage, error_share_among_active=q * wrong_active / coverage)


def main():
    out = {}
    p, rho = Fr(3, 4), Fr(4, 5)
    ind, dep = construction_1(p, Fr(0)), construction_1(p, rho)
    out['table_E1'] = {
        'naive_accuracy_independent': pct(ind['naive']),
        'naive_accuracy_shared_source': pct(dep['naive']),
        'grouped_accuracy_shared_source': pct(dep['grouped']),
        'absolute_change_pp': pct(dep['grouped'] - dep['naive']),
        'relative_error_reduction': pct((dep['grouped'] - dep['naive']) / (1 - dep['naive'])),
        'first_three_wrong_independent': pct(ind['first_three_wrong']),
        'first_three_wrong_shared_source': pct(dep['first_three_wrong']),
        'naive_wrong_grouped_right': pct(dep['naive_wrong_grouped_right']),
        'naive_right_grouped_wrong': pct(dep['naive_right_grouped_wrong']),
        'amplification_of_first_three_wrong': round(float(dep['first_three_wrong'] / ind['first_three_wrong']), 1),
    }
    grid = {}
    for acc in ('0.65', '0.70', '0.75', '0.80', '0.85'):
        row = {}
        for r in ('0.00', '0.25', '0.50', '0.75', '0.90'):
            x = construction_1(Fr(acc), Fr(r))
            row[f'rho={r}'] = pct(x['grouped'] - x['naive'])
        grid[f'p={acc}'] = row
    out['table_E2_change_pp'] = grid
    out['table_E3'] = {}
    for label, r in (('independent_errors', Fr(0)), ('dependent_errors_rho_0.80', Fr(4, 5))):
        for gate in (False, True):
            name = f"{label}|{'independent_evidence_gating' if gate else 'verifier_only_gating'}"
            out['table_E3'][name] = {k: pct(v) for k, v in construction_2(r, independent_gate=gate).items()}
    out['table_E4'] = {}
    for r in ('0.00', '0.25', '0.50', '0.75', '0.80', '0.90'):
        a, b = construction_2(Fr(r)), construction_2(Fr(r), independent_gate=True)
        out['table_E4'][f'rho={r}'] = {
            'wrong_activation_verifier_only': pct(a['wrong_candidate_activation']),
            'wrong_activation_independent_gate': pct(b['wrong_candidate_activation']),
            'error_share_verifier_only': pct(a['error_share_among_active']),
            'error_share_independent_gate': pct(b['error_share_among_active']),
        }
    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(json.dumps(out, indent=1), encoding='utf-8')
    print(json.dumps(out['table_E1'], indent=1))
    print(f'Written to {DST}')


if __name__ == '__main__':
    main()
