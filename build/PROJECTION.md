# Georgia — projected final electorate (gated panel)

Same model as Texas and North Carolina (see `claude/texas-ev-dashboard/PROJECTION.md` for the full write-up).
Cells = ModeledParty × habit (E/D/N from the last two generals' vote method) × general-election frequency (0–3) × primary
(R/D/N). For each cell the share of the final vote still to come after day d is learned from a past year, shrunk toward
parent cells (500-voter prior), and scaled by k = (2026 cell early rate / training-year rate)^alpha. Central: train 2022 on
current-file labels (voters, RegistrationYear ≤ 2022), alpha 0.5. Range: train {2022, 2024} × alpha {0.25, 0.5, 0.75}.
Shown as GOP−Dem points among the projected electorate (HardGOP+SoftGOP minus HardDem+SoftDem; Swing in the denominator).

Queries: `python3 q.py GA M 2022 ASOF`, `M 2024 ASOF`, `M 2026 ASOF` (same ASOF as the page). Then
`python3 make_proj.py data/proj.json GA ASOF bq/M_2022.json bq/M_2024.json bq/M_2026.json`.
make_proj.py reads the BigQuery result JSON files (not CSV).

First build: early −11.6 → projected +0.8 (range −6.5 to +2.6), GOP−Dem points of the modeled-party electorate, as of 2026-10-22 (d=12). Backtest at d=12: train 2022→predict 2024 model error 1.3 vs raw-early 1.8; 2024→2022 −5.6 vs −9.2.

The panel is hidden behind a click-through ("I acknowledge modeling off of EV is insane but I want to look anyways") and
appears only on the Claude artifact, never on the public GitHub site.
