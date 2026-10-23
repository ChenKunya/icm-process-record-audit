"""Statistics of the benchmark process-record audit (74 benchmarks x 10 fields).

Usage:
    python scripts/audit_statistics.py [coding_table.xlsx] [output.json]

Defaults: data/audit_coding_table_74x10_A01.xlsx and results/audit_statistics.json.
Requires Python 3.9+, numpy and openpyxl.

Only the raw coded columns of the "Coding" sheet are read (applicability, boundary
strength, record status, recovery stability). Final codes are derived here and do
not depend on the formula column of the workbook.

Coding criteria
    main   Protocol A
    app    applicability sensitivity: NA with a weak boundary is recoded as U
    inf    stable-inference sensitivity: R that requires an additional convention is recoded as U
    joint  both changes

Proxies
    Class I  source identifier and temporal position both D or R; denominator 74
    Class C  dependence relations and parameter provenance both D or R; benchmarks
             where both fields are applicable
    Class M  validity-change event D or R; benchmarks where the field is applicable

Bootstrap: benchmarks are resampled with replacement, 10,000 replicates, seed
20261019. The four criteria draw from one generator in the order listed above.
"""
import collections
import json
import math
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import numpy as np
import openpyxl

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'data' / 'audit_coding_table_74x10_A01.xlsx'
DST = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'results' / 'audit_statistics.json'

FIELDS = ['Source identifier', 'Temporal position', 'State version', 'Dependence relations',
          'Parameter provenance', 'Propagable uncertainty representation', 'Conflict representation',
          'Responsibility or commitment status', 'Validity-change event', 'Version lineage and rollback']
FAMILIES = [('Planning and feedback', 1, 6), ('Tools and interfaces', 7, 20),
            ('Web and graphical interface', 21, 37), ('Memory', 38, 42),
            ('General and multi-agent', 43, 54), ('Safety and privacy', 55, 57),
            ('Software, science, and data', 58, 74)]
CRITERIA = ['main', 'app', 'inf', 'joint']
SEED, N_BOOT = 20261019, 10000
I_FIELDS, C_FIELDS, M_FIELD, LINEAGE = (0, 1), (3, 4), 8, 9


def text(x):
    return '' if x is None else str(x).strip()


def load(path):
    ws = openpyxl.load_workbook(path)['Coding']
    cells, names = {}, {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[1] is None:
            continue
        b = int(r[1])
        names[b] = text(r[2])
        cells[(b, text(r[4]))] = dict(app=text(r[5]), boundary=text(r[6]), status=text(r[7]),
                                      stability=text(r[8]))
    return cells, names


def final_code(c, rule):
    if c['app'] == 'Not applicable':
        weak = c['boundary'] == 'Weak boundary'
        return 'U' if rule in ('app', 'joint') and weak else 'NA'
    if c['status'] == 'R' and rule in ('inf', 'joint') and c['stability'] == 'Requires additional convention':
        return 'U'
    return c['status']


def pct(k, n, digits=1):
    """Percentage rounded half up, as reported in the manuscript."""
    q = Decimal(1).scaleb(-digits)
    return float((Decimal(100) * k / n).quantize(q, rounding=ROUND_HALF_UP))


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * max(0.0, centre - half), 1), round(100 * min(1.0, centre + half), 1)]


def share(k, n):
    return dict(k=int(k), n=int(n), pct=pct(k, n) if n else None, wilson95=wilson(k, n))


def available(v):
    return v in ('D', 'R')


def proxies(m, ok=available):
    rows = range(len(m))
    i_k = sum(all(ok(m[i, j]) for j in I_FIELDS) for i in rows)
    c_base = [i for i in rows if all(m[i, j] != 'NA' for j in C_FIELDS)]
    c_k = sum(all(ok(m[i, j]) for j in C_FIELDS) for i in c_base)
    m_base = [i for i in rows if m[i, M_FIELD] != 'NA']
    m_k = sum(ok(m[i, M_FIELD]) for i in m_base)
    return (i_k, len(m)), (c_k, len(c_base)), (m_k, len(m_base))


def main():
    cells, names = load(SRC)
    bench = sorted(names)
    assert len(bench) == 74 and len(cells) == 740
    mat = {r: np.array([[final_code(cells[(b, f)], r) for f in FIELDS] for b in bench]) for r in CRITERIA}
    m = mat['main']
    out = {'source': SRC.name, 'n_benchmarks': len(bench), 'n_units': len(cells)}

    out['code_distribution'] = dict(collections.Counter(m.flatten().tolist()))
    out['n_weak_boundary_NA'] = sum(c['app'] == 'Not applicable' and c['boundary'] == 'Weak boundary'
                                    for c in cells.values())
    out['n_R_requiring_convention'] = sum(c['status'] == 'R' and c['stability'] == 'Requires additional convention'
                                          for c in cells.values() if c['app'] == 'Applicable')

    # field-level counts and conditional availability under the four criteria
    fields = []
    for j, f in enumerate(FIELDS):
        cnt = collections.Counter(m[:, j].tolist())
        row = dict(field=f, D=cnt['D'], R=cnt['R'], U=cnt['U'], NA=cnt['NA'])
        for r in CRITERIA:
            col = mat[r][:, j]
            row[r] = share(sum(available(v) for v in col), sum(v != 'NA' for v in col))
        fields.append(row)
    out['fields'] = fields

    # units changed by each sensitivity rule
    for r in ('app', 'inf'):
        changed = collections.defaultdict(list)
        for i, b in enumerate(bench):
            for j, f in enumerate(FIELDS):
                if mat[r][i, j] != m[i, j]:
                    changed[f].append(names[b])
        out[f'changed_units_{r}'] = dict(changed)
    out['n_changed_units'] = {r: int((mat[r] != m).sum()) for r in ('app', 'inf', 'joint')}

    # proxies, Wilson intervals and benchmark-level bootstrap
    rng = np.random.default_rng(SEED)
    out['proxies'] = {}
    for r in CRITERIA:
        mm = mat[r]
        base = proxies(mm)
        boots, i_top, m_above_c = [], 0, 0
        for _ in range(N_BOOT):
            x = mm[rng.integers(0, len(mm), len(mm))]
            p = [k / n if n else np.nan for k, n in proxies(x)]
            boots.append(p)
            if p[0] > p[1] and p[0] > p[2]:
                i_top += 1
            if p[2] > p[1]:
                m_above_c += 1
        bt = np.array(boots)
        ci = [[round(100 * float(np.nanpercentile(bt[:, j], q)), 1) for q in (2.5, 97.5)] for j in range(3)]
        out['proxies'][r] = {
            'class_I': dict(share(*base[0]), bootstrap95=ci[0]),
            'class_C': dict(share(*base[1]), bootstrap95=ci[1]),
            'class_M': dict(share(*base[2]), bootstrap95=ci[2]),
            'resamples_I_highest_pct': round(100 * i_top / N_BOOT, 2),
            'resamples_M_above_C_pct': round(100 * m_above_c / N_BOOT, 2)}

    # Class-I proxy restricted to benchmarks where both fields are applicable
    both = [i for i in range(len(bench)) if all(m[i, j] != 'NA' for j in I_FIELDS)]
    out['class_I_both_fields_applicable'] = share(sum(all(available(m[i, j]) for j in I_FIELDS) for i in both),
                                                  len(both))

    # alternative proxy definitions under Protocol A
    lower = proxies(m, ok=lambda v: v == 'D')
    c_base = [i for i in range(len(bench)) if all(m[i, j] != 'NA' for j in C_FIELDS)]
    p_base = [i for i in range(len(bench)) if m[i, M_FIELD] != 'NA' or m[i, LINEAGE] != 'NA']
    p_ok = [i for i in p_base if available(m[i, M_FIELD]) or available(m[i, LINEAGE])]
    out['alternative_proxies'] = {
        'direct_only_lower_bound': dict(class_I=share(*lower[0]), class_C=share(*lower[1]), class_M=share(*lower[2])),
        'class_C_relaxed_upper_bound': share(sum(any(available(m[i, j]) for j in C_FIELDS) for i in c_base),
                                             len(c_base)),
        'persistent_update_indicator': share(len(p_ok), len(p_base))}

    # benchmark lists behind the main proxies
    out['class_I_not_met'] = [names[bench[i]] for i in range(len(bench)) if not all(available(m[i, j]) for j in I_FIELDS)]
    out['class_C_met'] = [names[bench[i]] for i in c_base if all(available(m[i, j]) for j in C_FIELDS)]
    out['validity_change_applicable'] = [
        dict(benchmark=names[b], status=cells[(b, FIELDS[M_FIELD])]['status'],
             stability=cells[(b, FIELDS[M_FIELD])]['stability'])
        for b in bench if cells[(b, FIELDS[M_FIELD])]['app'] == 'Applicable']

    # five deep fields by task family
    deep = [3, 4, 5, 8, 9]
    fam = []
    for name, lo, hi in FAMILIES:
        idx = [i for i, b in enumerate(bench) if lo <= b <= hi]
        row = dict(family=name, n_benchmarks=len(idx))
        for j in deep:
            col = [m[i, j] for i in idx]
            n = sum(v != 'NA' for v in col)
            row[FIELDS[j]] = share(sum(available(v) for v in col), n) if n else 'no applicable benchmark'
        fam.append(row)
    out['task_families'] = fam

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(json.dumps(out, indent=1), encoding='utf-8')
    p = out['proxies']['main']
    print(f"Protocol A proxies: I {p['class_I']['k']}/{p['class_I']['n']}, "
          f"C {p['class_C']['k']}/{p['class_C']['n']}, M {p['class_M']['k']}/{p['class_M']['n']}")
    print(f'Written to {DST}')


if __name__ == '__main__':
    main()
