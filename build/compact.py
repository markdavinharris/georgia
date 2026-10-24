#!/usr/bin/env python3
"""Convert the compact (one-row-per-county JSON) query results to the kit's files.
  compact.py county OUT.json RESULT   (Query C2) -> {"COUNTY":[[d,reqR,...,eipO],...]}           (aliases applied)
  compact.py precinct OUT.json RESULT (Query P2) -> {"COUNTY":[["code",regR,...,eipO],...]}       (aliases applied)
  compact.py blocks OUT.json RESULT   (Query B2) -> precinct_blocks.json {"COUNTY":{"code":{"tot":N,"blocks":[[geoid,n],...]}}}
ALIAS comes from merge_county.py in the same folder (the state's Census spellings)."""
import json, sys, os, re
kind, out, src = sys.argv[1:4]
here = os.path.dirname(os.path.abspath(out)) if kind == 'blocks' else os.getcwd()
ALIAS = eval(re.search(r"^ALIAS = (\{.*?\})", open(os.path.join(os.getcwd(), 'merge_county.py')).read(), re.M).group(1))
d = json.load(open(src)); assert d['jobComplete'], src
cols = [f['name'] for f in d['schema']['fields']]
res = {}
C9 = ['reqR', 'reqD', 'reqO', 'retR', 'retD', 'retO', 'eipR', 'eipD', 'eipO']
for r in d['rows']:
    v = [f['v'] for f in r['f']]
    cty = ALIAS.get(v[0], v[0]); items = json.loads(v[1])
    if kind == 'county':
        rows = [[int(it['d'])] + [int(it[k]) for k in C9] for it in items]
        acc = res.setdefault(cty, {})
        for row in rows:  # alias spellings merged day by day
            a = acc.setdefault(row[0], [row[0]] + [0] * 9)
            for i in range(1, 10): a[i] += row[i]
    elif kind == 'precinct':
        for it in items:
            res.setdefault(cty, []).append([it['precinct']] + [int(it[k]) for k in ['regR', 'regD', 'regO'] + C9])
    elif kind == 'blocks':
        for it in items:
            res.setdefault(cty, {})[it['precinct']] = {'tot': int(it['voters_with_block']), 'blocks': [[b.split(':')[0], int(b.split(':')[1])] for b in it['blocks'].split(',')]}
if kind == 'county':
    res = {c: sorted(v.values()) for c, v in res.items()}
    s = [sum(r[i + 1] for rows in res.values() for r in rows) for i in range(9)]
    print(out, 'counties', len(res), 'rows', sum(len(v) for v in res.values()), 'sums', s)
elif kind == 'precinct':
    dups = []
    for c in res:
        res[c].sort(key=lambda r: r[0]); seen = set()
        for r in res[c]:
            if r[0] in seen: dups.append((c, r[0]))
            seen.add(r[0])
    s = [sum(r[i + 1] for rows in res.values() for r in rows) for i in range(12)]
    print(out, 'counties', len(res), 'precincts', sum(len(v) for v in res.values()), 'sums', s, 'dups', dups[:5], len(dups))
else:
    print(out, 'counties', len(res), 'precincts', sum(len(v) for v in res.values()))
json.dump(res, open(out, 'w'), separators=(',', ':'))
