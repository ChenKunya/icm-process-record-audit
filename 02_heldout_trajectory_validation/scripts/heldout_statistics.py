"""Statistics of the Who&When held-out examination (100 failure trajectories).

Usage:
    python scripts/heldout_statistics.py [coding_matrix.csv] [output.json]

Defaults: data/whowhen_heldout_coding_matrix_A01.csv and results/heldout_statistics.json.
Requires Python 3.9+ and the standard library only.

Reported: operation-level determinability, I/C/M distribution among determinable cases,
strict first-order diagnostic coverage and the distribution of L1-L6, results by sample
group with two-sided Fisher exact tests, and the three sensitivity analyses. Intervals
are 95% Wilson score intervals.
"""
import csv
import json
import math
import sys
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'data' / 'whowhen_heldout_coding_matrix_A01.csv'
DST = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'results' / 'heldout_statistics.json'
CONSTRUCTS = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6']


def pct(k, n):
    return float((Decimal(100) * Decimal(str(k)) / n).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


def wilson(k, n, z=1.959963984540054):
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [pct(max(0.0, centre - half), 1), pct(min(1.0, centre + half), 1)]


def share(k, n):
    return dict(k=k, n=n, pct=pct(k, n), wilson95=wilson(k, n))


def fisher_two_sided(a, b, c, d):
    """Two-sided Fisher exact test for the 2 x 2 table [[a, b], [c, d]]."""
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d

    def prob(x):
        return math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)

    observed = prob(a)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    return sum(prob(x) for x in range(lo, hi + 1) if prob(x) <= observed * (1 + 1e-7))


def summarise(cases):
    det = [c for c in cases if c['icm_class'] != 'U']
    cls = Counter(c['icm_class'] for c in det)
    covered = sum(c['strict_diagnostic'] in CONSTRUCTS for c in det)
    return det, cls, covered


def main():
    with open(SRC, encoding='utf-8') as f:
        cases = list(csv.DictReader(f))
    assert len(cases) == 100
    det, cls, covered = summarise(cases)
    out = {'source': SRC.name, 'n_cases': len(cases)}
    out['determinable'] = share(len(det), len(cases))
    out['class_distribution'] = {k: share(cls[k], len(det)) for k in ('I', 'C', 'M')}
    out['strict_diagnostic_coverage'] = share(covered, len(det))
    diag = Counter(c['strict_diagnostic'] for c in det)
    out['first_order_constructs'] = {k: share(diag[k], len(det)) for k in CONSTRUCTS}
    out['reference_quality'] = dict(Counter(c['reference_quality'] for c in cases))
    out['reason_codes'] = dict(sorted(Counter(c['reason_code'] for c in cases).items()))

    groups = {}
    for g in ('Algorithm-Generated', 'Hand-Crafted'):
        sub = [c for c in cases if c['stratum'] == g]
        d, k, cov = summarise(sub)
        groups[g] = dict(n=len(sub), determinable=share(len(d), len(sub)), I=k['I'], C=k['C'], M=k['M'],
                         strict_coverage=share(cov, len(d)))
    out['by_sample_group'] = groups
    ag, hc = groups['Algorithm-Generated'], groups['Hand-Crafted']
    out['fisher_class_by_group_p'] = round(fisher_two_sided(ag['I'], ag['C'], hc['I'], hc['C']), 4)
    agk, agn = ag['strict_coverage']['k'], ag['strict_coverage']['n']
    hck, hcn = hc['strict_coverage']['k'], hc['strict_coverage']['n']
    out['fisher_coverage_by_group_p'] = round(fisher_two_sided(agk, agn - agk, hck, hcn - hck), 4)

    # sensitivity analyses
    def recode(rule):
        res = []
        for c in cases:
            c = dict(c)
            if rule in ('boundary_to_C', 'all_to_C') and c['reason_code'] == 'R7':
                c['icm_class'], c['strict_diagnostic'] = 'C', 'None'
            if rule == 'all_to_C' and c['reason_code'] == 'R8':
                c['icm_class'], c['strict_diagnostic'] = 'C', 'None'
            if rule == 'exclude_ambiguous' and c['reference_quality'] == 'ambiguous':
                continue
            res.append(c)
        return res

    sens = {}
    for name in ('exclude_ambiguous', 'boundary_to_C', 'all_to_C'):
        sub = recode(name)
        d, k, cov = summarise(sub)
        sens[name] = dict(denominator=len(sub), determinable=share(len(d), len(sub)), I=k['I'], C=k['C'], M=k['M'],
                          strict_coverage=share(cov, len(d)))
    out['sensitivity'] = sens

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(json.dumps(out, indent=1), encoding='utf-8')
    print(f"determinable {len(det)}/100, strict coverage {covered}/{len(det)}, "
          f"Fisher p = {out['fisher_class_by_group_p']} and {out['fisher_coverage_by_group_p']}")
    print(f'Written to {DST}')


if __name__ == '__main__':
    main()
