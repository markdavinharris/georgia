import json, sys
# usage: make_daily.py out.json S_2026 S_2024 S_2022  (totals are pasted below from the totals query output)
TOT = {'2026': {'rows_total': 1552593, 'rejected_rows': 1896, 'unmatched_rows': 6476}, '2024': {'rows_total': 4093450, 'rejected_rows': 14776, 'unmatched_rows': 1818}, '2022': {'rows_total': 2566880, 'rejected_rows': 6747, 'unmatched_rows': 4047}}  # totals query, 2026-10-24
out = {}
for y, p in zip(['2026','2024','2022'], sys.argv[2:5]):
    d = json.load(open(p)); assert d['jobComplete']
    cols = [f['name'] for f in d['schema']['fields']]
    assert cols[:10] == ['d','reqR','reqD','reqO','retR','retD','retO','eipR','eipD','eipO'], cols
    rows = [[int(f['v']) for f in r['f'][:10]] for r in d['rows']]
    out[y] = {'rows': rows, **TOT[y]}
    s = [sum(r[i] for r in rows) for i in range(1,10)]
    print(y, 'days', len(rows), 'sums req/ret/eip', [sum(s[0:3]), sum(s[3:6]), sum(s[6:9])], 'by party R/D/O ev', [s[3]+s[6], s[4]+s[7], s[5]+s[8]])
json.dump(out, open(sys.argv[1],'w'), separators=(',',':'))
