#!/usr/bin/env python3
"""Print a dashboard query for a state.  q.py ST KIND [YEAR] [CHUNK] [ASOF]
KIND: S (statewide daily), C (county daily, CHUNK = SQL condition on county), T (totals, all years),
      P (precinct 2026, CHUNK on UPPER(CountyName)), H (heat, YEAR 2026|2022, ASOF), B (blocks, CHUNK),
      M (projection cells, YEAR 2022|2024|2026, ASOF)."""
import sys
st, kind = sys.argv[1], sys.argv[2]
YR = {'2026': ('abev_2026', 'voters', '2026-11-03'), '2024': ('abev_2024', 'voterfile_2024', '2024-11-05'),
      '2022': ('abev_2022', 'voterfile_2022', '2022-11-08')}
P = "CASE WHEN {x}.PartyRollUp IN ('Republican','Modeled Republican') THEN 'R' WHEN {x}.PartyRollUp IN ('Democrat','Modeled Democrat') THEN 'D' ELSE 'O' END"
T = 'coldspark-voterdata.national_file.'
def cte(y):
    ab, vf, ed = YR[y]
    return f"""WITH a AS (
  SELECT IFNULL(REGEXP_REPLACE(UPPER(a.Jurisname), ' COUNTY$', ''), 'UNKNOWN') AS county,
    a.RequestDate, a.ReturnDate, a.EarlyVoted, a.Rejected, {P.format(x='v')} AS party
  FROM `{T}{ab}` a LEFT JOIN `{T}{vf}` v ON v.DT_Regid = a.DT_Regid AND v.State = '{st}'
  WHERE a.State = '{st}'
),
u AS (
  SELECT county, 'req' AS m, DATE_DIFF(DATE '{ed}', RequestDate, DAY) AS d, party FROM a WHERE Rejected = 0 AND RequestDate BETWEEN DATE '{y}-01-01' AND DATE '{y}-12-31'
  UNION ALL SELECT county, 'ret', DATE_DIFF(DATE '{ed}', ReturnDate, DAY), party FROM a WHERE Rejected = 0 AND ReturnDate BETWEEN DATE '{y}-01-01' AND DATE '{y}-12-31'
  UNION ALL SELECT county, 'eip', DATE_DIFF(DATE '{ed}', EarlyVoted, DAY), party FROM a WHERE EarlyVoted BETWEEN DATE '{y}-01-01' AND DATE '{y}-12-31'
)"""
NINE = """COUNTIF(m='req' AND party='R') reqR, COUNTIF(m='req' AND party='D') reqD, COUNTIF(m='req' AND party='O') reqO,
  COUNTIF(m='ret' AND party='R') retR, COUNTIF(m='ret' AND party='D') retD, COUNTIF(m='ret' AND party='O') retO,
  COUNTIF(m='eip' AND party='R') eipR, COUNTIF(m='eip' AND party='D') eipD, COUNTIF(m='eip' AND party='O') eipO"""
if kind == 'S':
    y = sys.argv[3]
    print(f"{cte(y)}\nSELECT d,\n  {NINE},\n  REPEAT('x',10000) pad\nFROM u WHERE d BETWEEN -14 AND 60 GROUP BY d ORDER BY d")
elif kind == 'C':
    y, ch = sys.argv[3], sys.argv[4]
    print(f"{cte(y)}\nSELECT county, d,\n  {NINE},\n  REPEAT('x',300) pad\nFROM u WHERE d BETWEEN -14 AND 60 AND {ch} GROUP BY county, d ORDER BY county, d")
elif kind == 'T':
    parts = []
    for y, (ab, vf, ed) in YR.items():
        parts.append(f"SELECT '{y}' y, COUNT(*) rows_total, COUNTIF(a.Rejected=1) rejected_rows, COUNTIF(v.DT_Regid IS NULL) unmatched_rows "
                     f"FROM `{T}{ab}` a LEFT JOIN `{T}{vf}` v ON v.DT_Regid=a.DT_Regid AND v.State='{st}' WHERE a.State='{st}'")
    print('\nUNION ALL\n'.join(parts) + '\nORDER BY y DESC')
elif kind == 'P':
    ch = sys.argv[3]
    cols = []
    for m, cond in (('req', 'a.Rejected=0 AND a.RequestDate IS NOT NULL'), ('ret', 'a.Rejected=0 AND a.ReturnDate IS NOT NULL'), ('eip', 'a.EarlyVoted IS NOT NULL')):
        for p in 'RDO': cols.append(f"COUNTIF({cond} AND party='{p}') {m}{p}")
    print(f"""SELECT UPPER(v.CountyName) county, v.PrecinctCode precinct,
  COUNTIF(party='R') regR, COUNTIF(party='D') regD, COUNTIF(party='O') regO,
  {', '.join(cols)},
  REPEAT('x',300) pad
FROM (
  SELECT DT_Regid, CountyName, PrecinctCode, {P.format(x='voters')} AS party
  FROM `{T}voters` voters WHERE State='{st}' AND {ch}
) v
LEFT JOIN `{T}abev_2026` a ON a.DT_Regid = v.DT_Regid AND a.State='{st}'
GROUP BY 1,2 ORDER BY 1,2""".replace("voters voters WHERE", "voters voters WHERE").replace("{ch}", ch))
elif kind == 'H':
    y, asof = sys.argv[3], sys.argv[4]
    ab, vf, ed = YR[y]
    vh = ('VH18G', 'VH20G', 'VH22G', 'VH24G') if y == '2026' else ('VH14G', 'VH16G', 'VH18G', 'VH20G')
    hist = '+'.join(f'IF(v.{c} IS NOT NULL,1,0)' for c in vh)
    cut = f"DATE_SUB(DATE '{ed}', INTERVAL {asof} DAY)"
    extra = ''
    if y == '2022':
        extra = (f"COUNTIF((a.Rejected=0 AND a.ReturnDate BETWEEN DATE '2022-01-01' AND DATE '2022-12-31') OR a.EarlyVoted BETWEEN DATE '2022-01-01' AND DATE '2022-12-31') ev_final,\n"
                 "  COUNTIF(v.VH22G IS NOT NULL) voted22,\n  ")
    print(f"""SELECT UPPER(v.CountyName) county, {P.format(x='v')} party, ({hist}) hist,
  COUNT(*) reg,
  COUNTIF((a.Rejected=0 AND a.ReturnDate BETWEEN DATE '{y}-01-01' AND {cut}) OR a.EarlyVoted BETWEEN DATE '{y}-01-01' AND {cut}) ev_now,
  COUNTIF(a.Rejected=0 AND a.ReturnDate BETWEEN DATE '{y}-01-01' AND {cut}) mail_now,
  COUNTIF(a.EarlyVoted BETWEEN DATE '{y}-01-01' AND {cut}) eip_now,
  COUNTIF(a.Rejected=0 AND a.RequestDate BETWEEN DATE '{y}-01-01' AND {cut}) req_now,
  {extra}REPEAT('x',300) pad
FROM `{T}{vf}` v
LEFT JOIN `{T}{ab}` a ON a.DT_Regid = v.DT_Regid AND a.State='{st}'
WHERE v.State='{st}' GROUP BY 1,2,3 ORDER BY 1,2,3""")
elif kind == 'B':
    ch = sys.argv[3]
    print(f"""WITH b AS (
  SELECT UPPER(v.CountyName) county, v.PrecinctCode precinct, c.CensusBlock2020 blk, COUNT(*) n
  FROM `{T}voters` v
  JOIN `coldspark-voterdata.national_contact.voter_contact` c ON c.DT_Regid = v.DT_Regid
  WHERE v.State='{st}' AND {ch} AND c.CensusBlock2020 IS NOT NULL AND c.CensusBlock2020 != ''
  GROUP BY 1,2,3
), r AS (
  SELECT county, precinct, blk, n, ROW_NUMBER() OVER (PARTITION BY county, precinct ORDER BY n DESC) rk, SUM(n) OVER (PARTITION BY county, precinct) tot FROM b
)
SELECT county, precinct, ANY_VALUE(tot) voters_with_block, STRING_AGG(CONCAT(blk, ':', CAST(n AS STRING)), ',' ORDER BY n DESC) blocks, REPEAT('x',200) pad
FROM r WHERE rk <= 8 GROUP BY 1,2 ORDER BY 1,2""")
elif kind == 'M':
    y, asof = sys.argv[3], sys.argv[4]
    ab, vf, ed = YR[y]
    if y == '2022':
        vf, g, pr, fin, reg, having = 'voters', ('VH20G', 'VH18G', 'VH16G'), 'COALESCE(VH22P,VH20P)', 'VH22G IS NOT NULL OR a.dbe IS NOT NULL', " AND (f.RegistrationYear IS NULL OR f.RegistrationYear<=2022)", 'BETWEEN 0 AND 60'
    elif y == '2024':
        g, pr, fin, reg, having = ('VH22G', 'VH20G', 'VH18G'), 'COALESCE(VH24P,VH22P)', 'VH24G IS NOT NULL OR a.dbe IS NOT NULL', '', 'BETWEEN 0 AND 60'
    else:
        g, pr, fin, reg, having = ('VH24G', 'VH22G', 'VH20G'), 'COALESCE(VH26P,VH24P)', 'FALSE', '', f'BETWEEN {asof} AND 60'
    print(f"""WITH a AS (
  SELECT DT_Regid, MAX(DATE_DIFF(DATE '{ed}', LEAST(IFNULL(EarlyVoted, DATE '2099-01-01'), IFNULL(IF(Rejected=0, ReturnDate, NULL), DATE '2099-01-01')), DAY)) dbe
  FROM `{T}{ab}`
  WHERE State='{st}' AND (EarlyVoted IS NOT NULL OR (ReturnDate IS NOT NULL AND Rejected=0)) AND DT_Regid<>''
  GROUP BY 1 HAVING dbe {having}
), v AS (
  SELECT f.State st, f.ModeledParty party,
   CASE WHEN {g[0]} IN ('2','7') THEN 'E' WHEN {g[0]}='1' THEN 'D' WHEN {g[1]} IN ('2','7') THEN 'E' WHEN {g[1]}='1' THEN 'D' ELSE 'N' END habit,
   IF({g[0]} IS NOT NULL,1,0)+IF({g[1]} IS NOT NULL,1,0)+IF({g[2]} IS NOT NULL,1,0) freq,
   CASE WHEN {pr} IN ('3','4','8') THEN 'R' WHEN {pr} IN ('5','6','9') THEN 'D' ELSE 'N' END prim,
   {fin} fin, a.dbe
  FROM `{T}{vf}` f LEFT JOIN a USING (DT_Regid)
  WHERE f.State='{st}'{reg})
SELECT st,party,habit,freq,prim, COUNT(*) n, COUNTIF(fin) fin, COUNTIF(dbe>={asof}) e{asof}, REPEAT('x',300) pad
FROM v GROUP BY 1,2,3,4,5""")
# ---- compact variants: one row per county, the county's rows packed as JSON (fits any state in one query) ----
if kind == 'C2':
    y = sys.argv[3]
    print(f"""{cte(y)}
, g AS (SELECT county, d,
  {NINE}
FROM u WHERE d BETWEEN -14 AND 60 GROUP BY county, d)
SELECT county, TO_JSON_STRING(ARRAY_AGG(STRUCT(d, reqR, reqD, reqO, retR, retD, retO, eipR, eipD, eipO) ORDER BY d)) days, REPEAT('x',300) pad
FROM g GROUP BY county ORDER BY county""")
elif kind == 'P2':
    cols = []
    for m, cond in (('req', 'a.Rejected=0 AND a.RequestDate IS NOT NULL'), ('ret', 'a.Rejected=0 AND a.ReturnDate IS NOT NULL'), ('eip', 'a.EarlyVoted IS NOT NULL')):
        for p in 'RDO': cols.append(f"COUNTIF({cond} AND party='{p}') {m}{p}")
    print(f"""WITH g AS (
SELECT UPPER(v.CountyName) county, IFNULL(v.PrecinctCode, '') precinct,
  COUNTIF(party='R') regR, COUNTIF(party='D') regD, COUNTIF(party='O') regO,
  {', '.join(cols)}
FROM (
  SELECT DT_Regid, CountyName, PrecinctCode, {P.format(x='x')} AS party
  FROM `{T}voters` x WHERE State='{st}'
) v
LEFT JOIN `{T}abev_2026` a ON a.DT_Regid = v.DT_Regid AND a.State='{st}'
GROUP BY 1,2)
SELECT county, TO_JSON_STRING(ARRAY_AGG(STRUCT(precinct, regR, regD, regO, reqR, reqD, reqO, retR, retD, retO, eipR, eipD, eipO) ORDER BY precinct)) precincts, REPEAT('x',300) pad
FROM g GROUP BY county ORDER BY county""")
elif kind == 'B2':
    print(f"""WITH b AS (
  SELECT UPPER(v.CountyName) county, v.PrecinctCode precinct, c.CensusBlock2020 blk, COUNT(*) n
  FROM `{T}voters` v
  JOIN `coldspark-voterdata.national_contact.voter_contact` c ON c.DT_Regid = v.DT_Regid
  WHERE v.State='{st}' AND c.CensusBlock2020 IS NOT NULL AND c.CensusBlock2020 != '' AND v.PrecinctCode IS NOT NULL
  GROUP BY 1,2,3
), r AS (
  SELECT county, precinct, blk, n, ROW_NUMBER() OVER (PARTITION BY county, precinct ORDER BY n DESC) rk, SUM(n) OVER (PARTITION BY county, precinct) tot FROM b
), p AS (
  SELECT county, precinct, ANY_VALUE(tot) voters_with_block, STRING_AGG(CONCAT(blk, ':', CAST(n AS STRING)), ',' ORDER BY n DESC) blocks
  FROM r WHERE rk <= 8 GROUP BY 1,2
)
SELECT county, TO_JSON_STRING(ARRAY_AGG(STRUCT(precinct, voters_with_block, blocks) ORDER BY precinct)) precincts, REPEAT('x',200) pad
FROM p GROUP BY county ORDER BY county""")
