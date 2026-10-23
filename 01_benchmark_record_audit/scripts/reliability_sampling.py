"""Draw the reliability subsample of the benchmark audit.

One benchmark is drawn at random from each of the seven task families, and one more
from the remaining benchmarks, giving 8 benchmarks x 10 fields = 80 coding units.
Benchmark IDs follow the "Benchmark register" sheet of the coding table.

Usage:
    python scripts/reliability_sampling.py
"""
import random

SEED = 20261020
FAMILIES = [('Planning and feedback', 1, 6), ('Tools and interfaces', 7, 20),
            ('Web and graphical interface', 21, 37), ('Memory', 38, 42),
            ('General and multi-agent', 43, 54), ('Safety and privacy', 55, 57),
            ('Software, science, and data', 58, 74)]

rng = random.Random(SEED)
picked = []
for name, lo, hi in FAMILIES:
    b = rng.choice(list(range(lo, hi + 1)))
    picked.append(b)
    print(f'{len(picked)}  benchmark {b:2d}  {name}')
rest = [i for i in range(1, 75) if i not in picked]
picked.append(rng.choice(rest))
print(f'{len(picked)}  benchmark {picked[-1]:2d}  additional draw from the remaining {len(rest)}')
print('sorted IDs:', sorted(picked))
