# Standing requirements of the pension-aging dashboard project

These are the project's conventions and the demands the team and user made while KPI 1.2 and 1.3 were deepened. When the skill is used on this repo, satisfy them; on another project, look for the equivalents and ask where unclear.

## Repo map (where things live)
- `Dashboards/Inicio.py` — entry point with two modes: **final** (5 pages) and **dev** (`?mode=dev`, extra pages incl. the data explorer).
- `Dashboards/final_pages/objetivo1.py`, `objetivo2.py` — KPI cards (`kpi_card("1.2", render_1_2)`); a card shows definition, formula, status and caveat from `config/kpis.yaml` around the render function.
- `Dashboards/components/` — `charts.py` (pure figure builders), `critical_point.py` (pure engine), `kpi_card.py`.
- `Dashboards/utils.py` — `load_csv` (cached, reads `Data processed/`), palette (`BLUE ORANGE RED VIOLET INK_*`), `PLOTLY_LAYOUT`, `kpi_card_row`.
- `Scripts/NN_*.py` — numbered pipeline; docstring lists sources, outputs and method notes. Check the next free number (others add scripts in parallel).
- `Data raw/` (sources; never edited; inventory in `INVENTARIO_FUENTES.md`), `Data processed/` (generated tables, README), `config/kpis.yaml`, `docs/GUIA_KPIs_DASHBOARD.md` (manual recipes + control values), `docs/DATOS_ABIERTOS.md` (data gaps), `tests/`.
- Run: `cd Dashboards && "../Data raw/.venv/bin/python" -I -m streamlit run Inicio.py`. Tests from the root: `"Data raw/.venv/bin/python" -I -m pytest tests -q`. Use the venv python with `-I`; stdlib-only for new download scripts.

## Conventions
- UI text, docstrings, docs and commit titles in **Spanish**; chat with the user in the language they use.
- Plotly only; figure builders take DataFrames and return figures; titles/axes in Spanish; observed solid, scenario dashed; reference lines dotted in the muted ink colour.
- Money in **constant pesos of one base year** (here 2025), say so in captions.
- Each KPI has a dynamic "Lectura:" sentence; each view has a caption stating matched years, approximations and observed vs scenario.
- New analysis goes **below** the existing KPI content, inside the same card; existing numbers stay (regression-tested).
- Every recipe in the guide is also a test (`tests/test_manual_mode.py` runs the data explorer widget by widget); control values appear in the guide's table and in tests.

## Demands made by the user during the KPI 1.2 work (carry over as defaults)
1. **Same-year matching** of data wherever possible.
2. **One chart with a toggle** when two options exist (income base A/B, average/median, money/ratio view), not two charts.
3. **Overlay** the cost side and the income side in one chart; the **crossing is the critical point** and is highlighted (marker, line, year).
4. **Highlight the years that have regional data** (2024 Census, 2035, 2050) and let the user pick a region and, below it, a commune when data allows (label inheritance).
5. Two income options: mean/median of **those who pay in** vs of **everyone employed**.
6. Forecast both sides; sliders for the assumptions; default for the tolerable burden explained.
7. Data: use what exists, research what is missing, give links; where only part could be downloaded automatically, write a script for the rest and use what was already delivered.
8. Commits: few, with correct titles; pushing only when asked; sync with the teammate's remote work (merge, resolve conflicts keeping both sides, renumber colliding scripts, update control values that the teammate's change altered).
9. Do not touch or commit other sessions' uncommitted work.
10. **The Census 2024 wins** when it conflicts with another source (population level, age structure, territory). The other source contributes only its dynamics, rescaled to the Census level, and every conflict goes into `docs/DISCUSION_FUENTES.md` with the sources, the decision and the effect on the results (compute both options). Reference year = 2024.
11. Show commune figures where data allows (table of all communes of the selected region), labelled as inherited from the region when they are.

## Stakeholders already present in this project's data
Pension-fund administrators (AFP — earn commission only on individual-account contributions), workers/contributors (by region, income, sex), employers (new contribution under Ley 21.735), the State/Treasury (PGU, PBS, APS), the Superintendencia de Pensiones (regulator and data source), pensioners (65+, poverty), regions/communes, and indirectly the health system (demand index in the dev pages) and the budget office/fiscal council.
