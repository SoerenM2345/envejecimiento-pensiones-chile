# Worked examples (positive examples to compare against)

Both come from the Chilean pension-aging dashboard (Streamlit, Plotly, Spanish UI, processed tables in `Data processed/`). Use them to calibrate depth, not to copy content.

## Example 1 — KPI 1.2, "cotizantes por persona de 65+" (support ratio)

### Before
- Regional bar chart: contributors (Dec 2025) ÷ population 65+ (Census 2024); country 2.30, Ñuble most pressured (1.54).
- Three-point scenario line (2024 → 2035 → 2050) with coverage held constant.
- Reading: "the ratio falls". Nothing says *when it becomes a problem*, *how big* the money is, or *for whom*.
- Weak lenses: **when** (no threshold), **how big** (no money, no yardstick), **comparability** (contributors of December 2025 over a 2024 census).

### Deepening passes
1. **Threshold, in money.** Defined two lines that cross: *cost* = cost of the tax-financed old-age pillar per person aged 65+ × population 65+; *capacity* = tolerable share of wage × income per worker × workers. The crossing is the **critical point**. Default tolerable share = 10% (the mandatory pension contribution), explained in the help text and moveable by slider. Also shown as ratio view: observed support ratio vs break-even ratio R*.
2. **Two income bases in one chart (toggle).** Base A: taxable income of contributors × contributors ("who pays in"). Base B: income of all employed × employed ("if everyone paid in"). Each with average or median. This answers the user's worry that lower-income workers do not contribute.
3. **Same-year matching** (rules and reasoning in `time-alignment.md`). Country 2025 (contributors Dec, income Dec, employed Oct–Dec, spending of the year, INE population); regions 2024 (Census 2024 with Dec-2024 data). Mismatches are stated in the caption.
4. **Real vs scenario; anchor years.** Observed solid, scenario dashed; diamonds at 2024 / 2035 / 2050, the years with regional population; star at the crossing year.
5. **Geography.** Country → region → optional commune (commune inherits coverage, income and cost from its region; only its age structure is its own; labelled approximation).
6. **Scenario sliders:** real wage growth, tolerable share, contributor coverage in 2050, and the legal PGU step-up (Ley 21.735) as a checkbox.
7. **Data acquisition** that made it possible: monthly contributor/income tables from the supervisor (HTML disguised as .xls; session cookie + Referer needed; missing months backfilled by script), brackets of taxable income (median by interpolation), employment-survey income and employed counts, CPI to deflate to one year's prices. Part of this the user downloaded by hand from interactive menus; the rest the script filled.
8. **A silent-drop bug found on the way:** the regional benefits table lost one region because of an accent in its name; fixed and rerun.

### After (default scenario, country)
- 2025: 2.06 contributors per person 65+ (INE population), financing the old-age floor takes 6.7% of contributors' wage; 2050: 12.4%.
- With a 10% tolerable share, **critical point 2039** (earlier with median income, later if everyone employed contributed).
- Stakeholder reading that this supports: *the treasury/budget office* (the floor's cost reaches the tolerable share in about 14 years — plan financing or indexing before then), *the operators of the individual-account system* (the contributor base per elderly person halves by 2050 — retain/expand contributors in the regions that cross first), *labour/employment policy* (formalising workers shifts the critical year by ~9 years: base B vs A).

## Example 2 — KPI 1.3, "participación de partes interesadas"

### Before
Pending: no money amounts of worker contributions in any source.

### What was done
- Redefined from the point of view of one stakeholder (a pension-fund administrator): **share of the system's flow that passes through individual accounts**, the only part on which commission is earned.
  `KPI 1.3 = contributions to individual accounts ÷ total flow to the system`; total = individual accounts + social-insurance fund + State (basic/universal pension and top-ups).
- **Decomposition by payer/destination**, stacked bars (trillions of pesos) for observed years, plus a line of the share with observed (solid) and scenarios (dashed: base, and real income +1.5% a year).
- Worker contribution *estimated* from monthly factsheets: contributors × average income × 10%; employer contribution from the fund's financial statement and the law's phase-in table (no interpolation: the table publishes every year).
- Careful reference-month handling (a factsheet's publication month is not its reference month).
- Result: share about 57% (2024) → 55–56% (2025) → dips as the new social-insurance share enters → partial recovery by the time the employer rate is complete; the scenario never returns to 2025's level.

### Why it is a good example
It moves from "no data" to **who** (payer/destination), **when** (phase-in years), **how big** (trillions and %), and gives two stakeholders something to act on (the administrators: base shrinks relative to flow; the State/regulator: how the social-insurance share changes the commission base).

## What the two examples share (the pattern)
1. Re-read the KPI from a stakeholder's seat, not the author's.
2. Name the missing lens and fix comparability first.
3. Turn the outcome into a mechanism (threshold or decomposition) with money and a yardstick.
4. One chart per question; toggles for alternative bases; observed vs scenario; real-data years highlighted.
5. Acquire data with a ladder (script → guided manual → seed), inspect every file.
6. Tests with publisher control values, docs updated, honest caveats.
7. End with per-stakeholder recommendations, each traceable to a number on screen.
