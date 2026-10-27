"""Agreement statistics of the two review rounds of the targeted test (Table D.11 and Appendix D.9.4).

Usage:
    python scripts/review_statistics.py [output.json]

Reads data/targeted_coding_86_A01.csv, data/corrections_after_review_round1_A01.csv,
data/review_sample_24.csv and the four completed review forms, and writes results/review_statistics.json.
Python 3.9+ with openpyxl. Agreement is computed on the 24 drawn cases.

The five questions of the review form correspond to the coding table as follows:
    form Q1 -> Q1 grant           A adopted, B new answer by the Verifier, C no grant
    form Q2 -> Q3 same source     A not independent (same source), B independent, C cannot tell
    form Q3 -> Q4 independent check  A yes, B no, C cannot tell
    form Q4 -> Q5 grant reason    A agreement of both sides, B other reason, C no reason, D not applicable
    form Q5 -> Q6 overreach assertion  A to D, E none, F cannot tell
M-class grant, L6 and L7 are derived from the answers of every coder with the rules of Appendix D.9.2.
Q5 and L7 are compared only on cases that all coders in the comparison judged as adopting a submitted
solution. Round 2 (A04, A05) is compared with the corrected A01 coding, round 1 (A02, A03) with the A01
coding before the two corrections made after round 1, and round 2 is also compared with that earlier coding.
Agreement is reported as a percentage rounded half up to one decimal, Cohen's kappa and Krippendorff's
alpha (nominal) rounded half up to two decimals.
"""
import csv
import itertools
import json
import sys
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as Fr
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
DST = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'results' / 'review_statistics.json'
FORMS = {'A02': 'review_round1_A02.xlsx', 'A03': 'review_round1_A03.xlsx',
         'A04': 'review_round2_A04.xlsx', 'A05': 'review_round2_A05.xlsx'}
F_Q1 = {'A': 'adopted', 'B': 'new_answer', 'C': 'no_grant'}
F_TRI = {'A': 'yes', 'B': 'no', 'C': 'cannot_tell'}
F_Q4 = {'A': 'agreement', 'B': 'other_reason', 'C': 'no_reason', 'D': None}
F_Q5 = {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'none', 'F': 'cannot_tell'}
A_Q1 = {'adopted_submitted_solution': 'adopted', 'new_answer_by_verifier': 'new_answer', 'no_grant': 'no_grant'}
A_Q5 = {'agreement_of_both_sides': 'agreement', 'other_reason': 'other_reason', 'no_reason': 'no_reason'}


def r2(x):
    """Exact fraction rounded half up to two decimals."""
    return float((Decimal(x.numerator) / Decimal(x.denominator)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def pct(k, n):
    return float((Decimal(100) * k / n).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


def derive(d):
    d = dict(d)
    d['m'] = int(d['q1'] == 'adopted')
    if d['q1'] == 'no_grant':
        d['l6'] = '0'
    elif d['q3'] == 'cannot_tell':
        d['l6'] = 'undeterminable'
    else:
        d['l6'] = '1' if d['q3'] == 'yes' and d['q5'] == 'agreement' else '0'
    if d['q1'] != 'adopted':
        d['l7'] = 'not_applicable'
    elif d['q3'] == 'no' or d['q4'] == 'yes':
        d['l7'] = '0'
    elif 'cannot_tell' in (d['q3'], d['q4'], d['q6']) or d['q5'] == 'no_reason':
        d['l7'] = 'undeterminable'
    elif d['q6'] in ('A', 'B', 'C', 'D'):
        d['l7'] = '1'
    else:
        d['l7'] = 'source_coupled_structure' if d['l6'] == '1' else '0'
    d['l7_holds'] = int(d['l7'] == '1')
    d['assertion_present'] = int(d['q6'] in ('A', 'B', 'C', 'D'))
    return d


def read_primary(cases):
    rows = {r['case_id']: r for r in csv.DictReader(open(DATA / 'targeted_coding_86_A01.csv', encoding='utf-8'))}
    final = {c: derive(dict(q1=A_Q1[rows[c]['Q1_grant']], q3=rows[c]['Q3_same_source'],
                            q4=rows[c]['Q4_independent_check'], q5=A_Q5[rows[c]['Q5_grant_reason']],
                            q6=rows[c]['Q6_overreach_assertion'])) for c in cases}
    for c in cases:
        assert final[c]['l7'] == rows[c]['L7'] and final[c]['l6'] == rows[c]['L6'], c
    earlier = {c: dict(v) for c, v in final.items()}
    for r in csv.DictReader(open(DATA / 'corrections_after_review_round1_A01.csv', encoding='utf-8')):
        if r['case_id'] in earlier and r['item'] == 'Q1_grant':
            earlier[r['case_id']]['q1'] = A_Q1[r['value_before']]
        if r['case_id'] in earlier and r['item'] == 'Q6_overreach_assertion':
            earlier[r['case_id']]['q6'] = r['value_before']
    return final, {c: derive(v) for c, v in earlier.items()}


def read_form(path, cases):
    ws = openpyxl.load_workbook(path)['3 Annotation']
    res = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not r[1]:
            continue
        f = lambda v: str(v).strip()[:1]
        res[r[1]] = derive(dict(q1=F_Q1[f(r[2])], q3=F_TRI[f(r[3])], q4=F_TRI[f(r[4])], q5=F_Q4[f(r[5])],
                                q6=F_Q5[f(r[6])]))
    assert list(res) == cases
    return res


def cohen(a, b):
    n = len(a)
    agree = sum(x == y for x, y in zip(a, b))
    po = Fr(agree, n)
    ca, cb = Counter(a), Counter(b)
    pe = Fr(sum(ca[c] * cb[c] for c in set(ca) | set(cb)), n * n)
    return dict(n=n, agreement=agree, agreement_pct=pct(agree, n), kappa=None if pe == 1 else r2((po - pe) / (1 - pe)))


def kalpha(units):
    o = Counter()
    for v in units:
        m = len(v)
        for i, k in itertools.permutations(range(m), 2):
            o[(v[i], v[k])] += Fr(1, m - 1)
    cats = sorted({c for c, _ in o}, key=str)
    nc = {c: sum(o[(c, k)] for k in cats) for c in cats}
    n = sum(nc.values())
    do = sum(o[(c, k)] for c in cats for k in cats if c != k)
    de = sum(nc[c] * nc[k] for c in cats for k in cats if c != k)
    return None if de == 0 else r2(1 - (n - 1) * do / de)


ITEMS = [('q1', 'Q1 grant'), ('q3', 'Q3 same source'), ('q4', 'Q4 independent check'), ('q5', 'Q5 grant reason'),
         ('q6', 'Q6 overreach assertion'), ('assertion_present', 'Q6 assertion present or not'),
         ('m', 'M-class grant'), ('l6', 'L6'), ('l7_holds', 'L7 holds or not'), ('l7', 'L7 four outcomes')]
ADOPTED_ONLY = {'q5', 'l7', 'l7_holds'}


def compare(coders, cases):
    adopted = [c for c in cases if all(coders[k][c]['q1'] == 'adopted' for k in coders)]
    out = {}
    for it, name in ITEMS:
        sub = adopted if it in ADOPTED_ONLY else cases
        res = {f'{a}_vs_{b}': cohen([coders[a][c][it] for c in sub], [coders[b][c][it] for c in sub])
               for a, b in itertools.combinations(coders, 2)}
        res['alpha'] = kalpha([[coders[k][c][it] for k in coders] for c in sub])
        out[name] = res
    for it in ('q3', 'q4', 'assertion_present'):
        out[f'{dict(ITEMS)[it]} on cases all judged adopted'] = {
            f'{a}_vs_{b}': cohen([coders[a][c][it] for c in adopted], [coders[b][c][it] for c in adopted])
            for a, b in itertools.combinations(coders, 2)}
    out['n_cases_all_judged_adopted'] = len(adopted)
    out['L7_count'] = {k: f"{sum(coders[k][c]['l7'] == '1' for c in adopted)}/{len(adopted)}" for k in coders}
    out['disagreements'] = [dict(case_id=c, **{f'{k}_{it}': coders[k][c][it] for k in coders
                                               for it in ('q1', 'q3', 'q4', 'q5', 'q6', 'l7')})
                            for c in cases if len({tuple(coders[k][c][x] for x in ('q1', 'q3', 'q4', 'q5', 'q6'))
                                                   for k in coders}) > 1]
    return out


def rounds(final, earlier, forms, cases):
    return {'n_cases': len(cases),
            'round2_vs_corrected_A01': compare({'A01': final, 'A04': forms['A04'], 'A05': forms['A05']}, cases),
            'round1_vs_A01_before_corrections': compare({'A01': earlier, 'A02': forms['A02'], 'A03': forms['A03']}, cases),
            'round2_vs_A01_before_corrections': compare({'A01': earlier, 'A04': forms['A04'], 'A05': forms['A05']}, cases)}


def main():
    drawn = [r['case_id'] for r in csv.DictReader(open(DATA / 'review_sample_24.csv', encoding='utf-8'))]
    assert len(drawn) == 24
    final, earlier = read_primary(drawn)
    forms = {k: read_form(DATA / v, drawn) for k, v in FORMS.items()}
    out = rounds(final, earlier, forms, drawn)
    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(json.dumps(out, indent=1), encoding='utf-8')
    main_res = out['round2_vs_corrected_A01']
    print('Round 2 against the corrected A01 coding on the 24 review cases (Table D.11)')
    for _, name in ITEMS:
        r = main_res[name]
        print(f'  {name:28s}', '  '.join(f"{k} {v['agreement_pct']}% ({v['kappa']})" for k, v in r.items() if k != 'alpha'),
              ' alpha', r['alpha'])
    print(f'Written to {DST}')


if __name__ == '__main__':
    main()
