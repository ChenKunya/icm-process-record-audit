"""Render MAST-AG2 trajectories as a case set with message numbers.

Usage:
    python scripts/build_case_set.py <MAST>/traces/AG2/experiments <output.html> [--review]

Without --review the case set contains all 86 trajectories of data/targeted_sample_86.csv,
with --review only the 24 cases of data/review_sample_24.csv. Python 3.9+, standard library only.

The conversion changes only the display. Every message of the trajectory is shown in order
and unchanged. [i] is the zero-based index of the message in the trajectory list of the MAST
file and is the message number used in the coding table and the review forms. Messages
containing SOLUTION_FOUND are highlighted in yellow and execution returns (messages starting
with exitcode) in blue. The case sets used in the study were produced by the same conversion
with Chinese labels.
"""
import csv
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STYLE = """<style>
:root{--bg:#fff;--fg:#1d1d1f;--muted:#666;--line:#ddd;--card:#f7f7f8;--hl:#fff4cc;--ex:#e8f1ff}
@media (prefers-color-scheme:dark){:root{--bg:#161618;--fg:#e8e8ea;--muted:#9a9aa0;--line:#333;--card:#202024;--hl:#4a3f12;--ex:#14284a}}
body{background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,sans-serif;max-width:960px;margin:0 auto;padding:16px}
h1{font-size:22px} h2{font-size:18px;border-top:2px solid var(--line);padding-top:16px;margin-top:40px}
.meta{color:var(--muted);font-size:14px} .ans{background:var(--card);padding:8px 12px;border-radius:6px;margin:8px 0}
.msg{border-left:3px solid var(--line);margin:10px 0;padding:4px 10px;background:var(--card);border-radius:4px}
.msg.ex{background:var(--ex)} .msg.found{background:var(--hl)}
.who{font-weight:600;font-size:14px} pre{white-space:pre-wrap;word-break:break-word;margin:4px 0;font:13px/1.5 ui-monospace,Menlo,Consolas,monospace}
.toc a{display:inline-block;margin:2px 6px 2px 0} a{color:inherit}
</style>"""


def block(case_id, rec):
    od = rec['other_data']
    out = [f"<h2 id='{case_id}'>{case_id}</h2>",
           f"<div class='ans'>Reference answer: <b>{html.escape(str(od['answer']))}</b> | "
           f"System final answer: <b>{html.escape(str(od['given'])) or '(empty)'}</b></div>"]
    for i, m in enumerate(rec['trajectory']):
        text = '\n'.join(m['content']) if isinstance(m['content'], list) else str(m['content'])
        cls = ' found' if i > 0 and 'SOLUTION_FOUND' in text else (' ex' if text.lstrip().startswith('exitcode') else '')
        who = 'Problem (system input)' if i == 0 else m.get('name', '')
        out.append(f"<div class='msg{cls}'><div class='who'>[{i}] {html.escape(who)}</div><pre>{html.escape(text)}</pre></div>")
    return '\n'.join(out)


def main():
    exp, dst = Path(sys.argv[1]), Path(sys.argv[2])
    sample = list(csv.DictReader(open(ROOT / 'data' / 'targeted_sample_86.csv', encoding='utf-8')))
    if '--review' in sys.argv[3:]:
        keep = {r['case_id'] for r in csv.DictReader(open(ROOT / 'data' / 'review_sample_24.csv', encoding='utf-8'))}
        sample = [r for r in sample if r['case_id'] in keep]
    body = [block(r['case_id'], json.loads((exp / r['trajectory_file']).read_text(encoding='utf-8'))) for r in sample]
    head = ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'><title>Targeted test case set</title>"
            + STYLE + f"</head><body><h1>Targeted test case set ({len(sample)} cases)</h1>"
            "<p class='meta'>Format conversion only. No message is removed or edited. [i] is the message number. "
            "Blue messages are execution returns and yellow messages contain SOLUTION_FOUND. Sender names are "
            "occasionally misplaced, so judge by content and order.</p><p class='toc'>"
            + ''.join(f"<a href='#{r['case_id']}'>{r['case_id']}</a>" for r in sample) + '</p>')
    dst.write_text(head + '\n'.join(body) + '</body></html>', encoding='utf-8')
    print(f'{len(sample)} cases written to {dst}')


if __name__ == '__main__':
    main()
