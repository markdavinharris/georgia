# Georgia Early Vote 2026 dashboard — daily refresh runbook

Published artifact (update in place, never create a new one): **https://claude.ai/artifact/AcxFCioq3EtQ3U8tobWTFo** — title "Georgia Early Vote 2026".
First published 2026-10-24 with data through 2026-10-22, with the gated "Projected final electorate" panel (PROJECTION.md).
Public site: https://georgia.coldspark.com, repo `markdavinharris/georgia`, refreshed by its own GitHub Action at
:25 past each hour 7 AM–11 PM ET (`build/AUTOMATION.md`, `claude/early-vote-sites-publish.md`). Claude refresh
tasks must NOT push to the repo. The public page carries no projection panel (the Action refreshes only the data block,
so a committed projection would go stale).

All kit files are in this Project under `claude/georgia-ev-dashboard/` and in the repo under `build/`.

## Steps (about 15 minutes)
1. Make a working folder `georgia/` in the scratchpad with `data/` and `bq/`. Fetch every file in
   `claude/georgia-ev-dashboard/` with `project_read` and write it under its own name (`counties.json` goes in `data/`).
2. Run the queries in SPEC.md with q.py (ASOF = the day number of the last complete day, 12 on 2026-10-24 for data through
   2026-10-22; if unsure, run S 2026 first and take the smallest d whose returns + in-person exceed 500). Save, copy to `bq/`,
   convert with the helpers. Never retype numbers.
3. `python3 build.py` → `dashboard.html` and `index.html`; it prints the as-of date and the projection line. If proj.json is for
   a different day the projection is hidden (by design).
4. Spot-check: `SELECT COUNTIF(Rejected=0 AND ReturnDate BETWEEN '2026-01-01' AND '<asof>') + COUNTIF(EarlyVoted BETWEEN '2026-01-01' AND '<asof>') FROM abev_2026 WHERE State='GA'`
   must equal the "Early votes cast" tile. For a county, compare on `REGEXP_REPLACE(UPPER(Jurisname),' COUNTY$','')`, not on an exact Jurisname.
5. `python3 shot.py index.html out.png` and look at it. Publish with the Artifact tool: `url: https://claude.ai/artifact/AcxFCioq3EtQ3U8tobWTFo`,
   `file_path: <dashboard.html>`, `label: "Data through <date>"`, `files: {"site/index.html": {"from": "<abs index.html>", "contentType": "text/html"}}`.
   Read the artifact first if asked. No `icon`. The 159 `precincts/*.json` already on the artifact are kept.
6. If template.html or app.js changed, write them back to the Project. For a design change on the public site, build a copy
   WITHOUT proj.json (`mkdir pub/data`, copy `data/*.json` except proj.json, `python3 build.py pub/data pub/dashboard.html`) and
   commit `pub/index.html` as the repo's `index.html` (add_repo push), then dispatch the workflow with force.
7. Report: as-of date, statewide early votes and vs 2024 / 2022 at the same point, net R−D, projection line, anything odd.

## Data notes
- Party: modeled party (Georgia has no party registration; `PartyRollUp` is `Modeled Republican` / `Modeled Democrat` / `Modeled Independent/Unaffiliated` for every voter).
- Advance in-person voting Oct 13 – Oct 30, 2026 (d=21 to d=4); Oct 15 – Nov 1, 2024; Oct 17 – Nov 4, 2022.
- Jurisname comes in mixed case for the same county (e.g. Fulton: 178,553 rows as "Fulton County" and 168 as "FULTON County"
  on 2026-10-22), so always upper-case before comparing. A spot-check with an exact Jurisname misses those rows.
- 2026-10-22 (d=12, first build 2026-10-24): 1,467,783 early votes, 82,906 outstanding mail ballots; 1,552,593 ABEV rows,
  1,896 rejected, 6,476 not matched to a voter (counted in "Modeled independent").
- The ABEV party flags are zero for every GA row; party always comes from the voter file.
- Requests made more than 60 days out are dated 2026-09-04 (the cap); the requested line steps there.
- County spellings: `DE KALB`→`DEKALB` (voter file, and part of the feed), `BENHILL`→`BEN HILL`, `JEFFDAVIS`→`JEFF DAVIS` (2024 feed). build.py asserts exactly 159 counties.
- Precinct maps: NYT 2024 precinct map (`GA-precincts-with-results.geojson.gz`) matched to `voters.PrecinctCode` by each code's top-8 census blocks (Query B2). 2026-10-24: 2,575 of 2,576 codes placed, 50 weak, 15 shapes shared by more than one code. 159 files, 3.1 MB.
- Projection on the first build: early −11.6 → projected +0.8 (range −6.5 to +2.6), GOP−Dem points of the modeled-party electorate, as of 2026-10-22 (d=12). Backtest at d=12: train 2022→predict 2024 model error 1.3 vs raw-early 1.8; 2024→2022 −5.6 vs −9.2.
