"""Reproduce the targeted sample of 86 MAST-AG2 failure trajectories and the 24-case review sample.

Usage:
    python scripts/select_samples.py <MAST>/traces/AG2/experiments

The MAST snapshot is commit a70542e541b2104ef8fcd785778179e173fb8d70. Python 3.9+, standard
library only.

Inclusion: runs whose folder name contains impr_topology (GPT-4 and GPT-4o, seeds 42 to 47),
trajectories with other_data.correct false. One trajectory is kept per problem (instance_id):
the GPT-4o trajectory with the smallest seed, or, when the problem has no GPT-4o failure, the
GPT-4 trajectory with the smallest seed. Cases are numbered G01 to G86 in the order of model,
seed and file name. The review sample is random.Random(20261021).sample of the 86 case IDs,
24 cases, sorted by case number.

The script checks the result against data/targeted_sample_86.csv and data/review_sample_24.csv.
"""
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEW_SEED, REVIEW_N = 20261021, 24


def main():
    exp = Path(sys.argv[1])
    failures = []
    for run in sorted(p for p in exp.iterdir() if p.is_dir() and 'impr_topology' in p.name):
        model = 'gpt-4o' if 'gpt-4o' in run.name else 'gpt-4'
        seed = int(run.name.rsplit('_', 1)[1])
        for f in sorted(run.glob('*.json')):
            rec = json.loads(f.read_text(encoding='utf-8'))
            if str(rec['other_data']['correct']).lower() == 'false':
                failures.append(dict(model=model, seed=seed, instance_id=rec['instance_id'],
                                     trajectory_file=f'{run.name}/{f.name}',
                                     perturbation_type=rec['other_data']['perturbation_type']))
    by_problem = defaultdict(list)
    for f in failures:
        by_problem[f['instance_id']].append(f)
    picked = []
    for runs in by_problem.values():
        o = [f for f in runs if f['model'] == 'gpt-4o']
        picked.append(min(o if o else runs, key=lambda f: f['seed']))
    picked.sort(key=lambda f: (f['model'], f['seed'], f['trajectory_file']))
    for i, f in enumerate(picked, 1):
        f['case_id'] = f'G{i:02d}'
    print(f'failure trajectories {len(failures)}, problems {len(by_problem)}, '
          f"GPT-4 {sum(f['model'] == 'gpt-4' for f in picked)}, GPT-4o {sum(f['model'] == 'gpt-4o' for f in picked)}")

    ref = list(csv.DictReader(open(ROOT / 'data' / 'targeted_sample_86.csv', encoding='utf-8')))
    keys = ['case_id', 'model', 'seed', 'instance_id', 'trajectory_file', 'perturbation_type']
    same = [{k: str(f[k]) for k in keys} for f in picked] == [{k: r[k] for k in keys} for r in ref]
    print('matches data/targeted_sample_86.csv:', same)

    ids = sorted(f['case_id'] for f in picked)
    review = sorted(random.Random(REVIEW_SEED).sample(ids, REVIEW_N), key=lambda x: int(x[1:]))
    ref24 = [r['case_id'] for r in csv.DictReader(open(ROOT / 'data' / 'review_sample_24.csv', encoding='utf-8'))]
    print('matches data/review_sample_24.csv:', review == ref24)


if __name__ == '__main__':
    main()
