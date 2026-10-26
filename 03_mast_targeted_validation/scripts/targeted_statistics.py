"""Results of the targeted test on MAST-AG2 failure trajectories (Table 19, Table D.9 and Section 7.3.5).

Usage:
    python scripts/targeted_statistics.py [output.json]

Reads data/targeted_coding_86_A01.csv and data/targeted_sample_86.csv and writes
results/targeted_statistics.json. Python 3.9+, standard library only.

M_grant, correct_solution_discarded, L6 and L7 are re-derived from the answers to Q1 to Q6 with the
rules of Appendix D.9.2 and checked against the recorded values:
    M-class grant         Q1 adopted_submitted_solution
    correct solution discarded  Q2 yes and Q1 not no_grant (a screening flag for validity decisions
                                that discarded a correct solution; it does not locate the decisive operation)
    L6                    Q3 yes and Q5 agreement_of_both_sides (undeterminable when Q3 is cannot_tell, 0 when no grant)
    L7                    not_applicable unless Q1 adopted; 0 if Q3 no or Q4 yes; undeterminable if Q3, Q4 or Q6
                          cannot be told or Q5 no_reason; 1 if Q6 is A to D; otherwise source_coupled_structure
                          when L6 holds and 0 when it does not
The L6 denominator is the trajectories where L6 is determinable, the L7 denominator the trajectories
with an M-class grant. Results are reported for all 86 trajectories and by model.
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DST = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'results' / 'targeted_statistics.json'


def derive(r):
    adopted = r['Q1_grant'] == 'adopted_submitted_solution'
    granted = r['Q1_grant'] != 'no_grant'
    m = int(adopted)
    discarded = int(r['Q2_correct_solution_rejected'] == 'yes' and granted)
    if not granted:
        l6 = '0'
    elif r['Q3_same_source'] == 'cannot_tell':
        l6 = 'undeterminable'
    else:
        l6 = '1' if r['Q3_same_source'] == 'yes' and r['Q5_grant_reason'] == 'agreement_of_both_sides' else '0'
    if not adopted:
        l7 = 'not_applicable'
    elif r['Q3_same_source'] == 'no' or r['Q4_independent_check'] == 'yes':
        l7 = '0'
    elif 'cannot_tell' in (r['Q3_same_source'], r['Q4_independent_check'], r['Q6_overreach_assertion']) \
            or r['Q5_grant_reason'] == 'no_reason':
        l7 = 'undeterminable'
    elif r['Q6_overreach_assertion'] in ('A', 'B', 'C', 'D'):
        l7 = '1'
    else:
        l7 = 'source_coupled_structure' if l6 == '1' else '0'
    return dict(M_grant=str(m), correct_solution_discarded=str(discarded), L6=l6, L7=l7)


def summary(rows):
    n = len(rows)
    q1 = Counter(r['Q1_grant'] for r in rows)
    adopted = [r for r in rows if r['Q1_grant'] == 'adopted_submitted_solution']
    l6_det = [r for r in rows if r['L6'] != 'undeterminable']
    l7 = Counter(r['L7'] for r in adopted)
    trio = lambda k: '/'.join(str(sum(r[k] == v for r in rows)) for v in ('yes', 'no', 'cannot_tell'))
    return {
        'n': n,
        'M_grant_adopted_submitted_solution': q1['adopted_submitted_solution'],
        'new_answer_by_verifier': q1['new_answer_by_verifier'],
        'no_grant': q1['no_grant'],
        'independent_check_before_grant_yes_no_cannot_tell': trio('Q4_independent_check'),
        'same_source_yes_no_cannot_tell': trio('Q3_same_source'),
        'grant_reason_agreement_of_both_sides': sum(r['Q5_grant_reason'] == 'agreement_of_both_sides' for r in rows),
        'overreach_assertion_before_grant': sum(r['Q6_overreach_assertion'] in ('A', 'B', 'C', 'D') for r in rows),
        'L6': f"{sum(r['L6'] == '1' for r in l6_det)}/{len(l6_det)}",
        'L7': f"{l7['1']}/{len(adopted)}",
        'source_coupled_structure': l7['source_coupled_structure'],
        'L7_not_met': l7['0'],
        'L7_undeterminable': l7['undeterminable'],
        'L7_among_determinable': f"{l7['1']}/{len(adopted) - l7['undeterminable']}",
        'correct_solution_discarded': sum(r['correct_solution_discarded'] == '1' for r in rows),
    }


def main():
    rows = list(csv.DictReader(open(ROOT / 'data' / 'targeted_coding_86_A01.csv', encoding='utf-8')))
    sample = {r['case_id']: r for r in csv.DictReader(open(ROOT / 'data' / 'targeted_sample_86.csv', encoding='utf-8'))}
    assert len(rows) == 86 and set(sample) == {r['case_id'] for r in rows}
    mismatch = [(r['case_id'], k) for r in rows for k, v in derive(r).items() if r[k] != v]
    out = {'derivation_mismatches': mismatch}
    groups = {
        'all_86': rows,
        'gpt-4': [r for r in rows if sample[r['case_id']]['model'] == 'gpt-4'],
        'gpt-4o': [r for r in rows if sample[r['case_id']]['model'] == 'gpt-4o'],
    }
    out['table_D9'] = {k: summary(v) for k, v in groups.items()}
    adopted = [r for r in rows if r['Q1_grant'] == 'adopted_submitted_solution']
    out['adopted_by_grant_reason'] = dict(Counter(r['Q5_grant_reason'] for r in adopted))
    out['L7_by_grant_reason'] = dict(Counter(r['Q5_grant_reason'] for r in adopted if r['L7'] == '1'))
    out['L7_by_assertion_type'] = dict(sorted(Counter(r['Q6_overreach_assertion'] for r in adopted if r['L7'] == '1').items()))
    with_assertion = [r for r in adopted if r['Q6_overreach_assertion'] in ('A', 'B', 'C', 'D')]
    out['adopted_with_overreach_assertion'] = dict(n=len(with_assertion), L7=dict(Counter(r['L7'] for r in with_assertion)))
    out['L7_if_source_coupled_structure_counted'] = (
        f"{sum(r['L7'] in ('1', 'source_coupled_structure') for r in adopted)}/{len(adopted)}")
    out['verifier_wrote_SOLUTION_FOUND'] = sum(r['Q1_grant'] != 'no_grant' for r in rows)
    out['correct_solution_discarded_cases'] = [r['case_id'] for r in rows if r['correct_solution_discarded'] == '1']
    out['perturbation_types'] = dict(Counter(sample[r['case_id']]['perturbation_type'] for r in rows).most_common())
    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(json.dumps(out, indent=1), encoding='utf-8')
    d = out['table_D9']['all_86']
    print(f"derivation mismatches {len(mismatch)}; M-class grants {d['M_grant_adopted_submitted_solution']}/86, "
          f"L6 {d['L6']}, L7 {d['L7']}")
    print(f'Written to {DST}')


if __name__ == '__main__':
    main()
