# KPI plan: feasibility review (2026-09-22)

Checked against the files actually in `Data raw/`, `Data processed/` and the DEIS zips in `~/Downloads`.
Nothing below is implemented yet. Status legend:

- ✅ **DONE**: already in the project
- 🟢 **GO**: feasible as written, implement
- 🟡 **GO WITH FIX**: feasible, but the plan's version is wrong or misleading and needs the change noted
- 🔴 **DON'T**: not feasible or methodologically invalid, and the reason is given
- ⬜ **OPEN**: needs data that we don't have yet (the open task is named)

## 0. Blocking prerequisite

⬜ **OPEN: copy the DEIS files into the project.** `EGRESOS_2024.zip`, `EGRESOS_2020.zip` and
`DEFUNCIONES_FUENTE_DEIS_2024_2026_22092026.zip` are in `~/Downloads`, **not** in `Data raw/`.
The project's own `README.md`, `kpis.yaml` and dashboard still say "no DEIS data". Move them to `Data raw/_external/deis/`,
add script `09_procesar_deis.py`, and add the unzipped CSVs to `.gitignore` because they are 104–291 MB (GitHub's limit is 100 MB).

## 1. Regions/comunas with the most ageing

| KPI | Status | Notes |
|---|---|---|
| Índice de envejecimiento (IE) | ✅ DONE | `indicadores_comuna/region.csv`. Missing piece: show it **against the regional and national average** instead of as a ranking (🟢 dashboard-only change). |
| CV of IE across comunas, per region | 🟡 GO WITH FIX | Unweighted CV is driven by tiny comunas (Camarones has 861 people, IE 215). Use a **population-weighted** CV or drop comunas under about 2,000 people. Don't report CV for regions with very few comunas (Arica y Parinacota has 4), because the sample is meaningless. |
| Edad mediana | ✅ DONE | Approximate in 51 masked comunas (already flagged). |
| Índice de Friz | 🟢 GO | Computable from `censo_comuna_edad_sexo.csv` (bands <20 and 30–49 align with the 5-year age bands). Low priority because it duplicates IE. |
| Data source note | 🟡 | The plan says to use `D1_...xlsx` sheet 4. The project already uses the **microdata** (more precise, same totals). Keep the microdata and use D1 only as a cross-check. |

## 2. Pyramids and their evolution

| KPI | Status | Notes |
|---|---|---|
| Índice de longevidad (80+/60+) | 🟢 GO | Comuna/region 2024 from census, national 1992–2070 from the projection. |
| Masculinity index 65+ | 🟢 GO (snapshot) / 🟡 trend | 2024 by comuna: yes. **"Trend" is national only** (projection file). There's no comunal or regional trend without a second census. |
| Differential growth rate (65+ vs total) | 🟢 national / 🔴 regional & comunal | National: fine (projection). Regional: **circular**, because `kpi_proyeccion_regional.csv` is shift-share and applies the *national* growth rate of each age group to every region, so regional differences only reflect the 2024 age mix, not real dynamics. |
| Comunal evolution by "logistic replication" | 🔴 DON'T (as written) → ⬜ OPEN | No such model exists in the project, and building an ad-hoc comunal projection isn't defensible for a course project. **Better alternative (open task):** download the Censo 2017 comuna × age table (INE, public) and compute the **real 2017→2024 intercensal change** per comuna. That gives observed data rather than modelled data. |
| Regional aging index / old-age dependency ratio as a 3-point series (2024/2035/2050) | ✅ DONE | `07_kpis_pension_salud.py` now exports `indice_envejecimiento_proy`/`indice_dependencia_vejez_proy` in `kpi_proyeccion_regional.csv` (previously only `pob_0_14_proy`/`pob_15_64_proy` were computed in-loop, not exported). Same shift-share caveat as the row above — used in the dashboard (Pirámides, Pensiones y Salud) captioned as an approximation, not an official regional projection. |

## 3. Maps

| KPI | Status | Notes |
|---|---|---|
| Choropleth IE / median age / longevity | ✅ DONE (IE, % 65+) / 🟢 add longevity | 345/346 comunas (Antártica has no geometry). |
| Bivariate map: level × Δ IE 2024–2035 | 🔴 DON'T (with current projection) | Δ comes from the shift-share projection, so it's mostly a function of the current structure: the second layer largely repeats the first. Use the **2017→2024 observed Δ** instead (see ⬜ OPEN in §2). |
| Join DEIS to geometry | 🟡 GO WITH FIX | DEIS codes are zero-padded strings (`"04101"`), while the project uses integers (`4101`). Normalise with `int()`. Egresos cover 339 comunas and deaths 344, so a few comunas will have no data. |

## 4. Socioeconomic variables

🔴 **The plan is outdated here.** It says there's no CASEN, no income and no urban/rural flag. **All three already exist**:
`kpi_ingresos_comuna.csv` (CASEN 2022, 334/346 comunas), `pct_urbano` in `indicadores_comuna.csv` (census microdata, 346/346),
and correlations in `kpi_ingreso_envejecimiento.csv` / `kpi_urbanizacion_envejecimiento.csv`. ✅ DONE, so no action is needed beyond correcting the plan text.

## 5. Pressure on health and pensions

### Pensions: the biggest issue in the plan

🔴 **`c2`/`c3` are NOT the pension system.** They cover only the **old IPS / ex-caja system (pre-1981)**:
466,781 pensioners nationally, against 2.56 M people aged 65+ (already documented in `Data processed/README.md`).
They leave out AFP pensions, PGU and everything else. So:

| KPI | Status | Notes |
|---|---|---|
| Pensionados/cotizantes by region and age | 🔴 DON'T | Divides a shrinking old-system cohort (IPS) by active AFP contributors, which is apples vs oranges. The 65+ value would be 1,688 per 100, which is meaningless as a sustainability ratio. Keep it only as the "historical context" chart it already is. |
| Razón de soporte potencial (20–64 / 65+) | 🟢 GO | Pure census. The inverse (`indice_dependencia_vejez`, 15–64) already exists; add the 20–64 version for international comparability. |
| Cobertura previsional | ✅ DONE | Already built as cotizantes / 15–64. Switching to 20–64 is optional. Note the year mismatch (cotizantes 2025 vs census 2024). |
| Pensión promedio (monto/número) | 🟡 GO WITH FIX | Computable, but **label it "pensión promedio IPS ex-cajas"**. It does not represent the average pension of older adults. |
| Tasa de reemplazo | 🔴 DON'T | No wage field in the files (the plan already says so). |
| Region-label mapping table | ✅ DONE | `03_procesar_cotizantes_afiliados.py` already normalises both formats to `region_id`. |
| **Real AFP pensions by region** | ⬜ OPEN | For a valid pension KPI, download "Pensiones pagadas por AFP, por región" (Superintendencia de Pensiones, estadísticas) plus PGU beneficiaries by comuna (IPS/datos.gob.cl). |

### Health (DEIS), verified against the actual files

| KPI | Status | Notes |
|---|---|---|
| Hospital discharge rate per 1,000 people **65+** | 🔴 as written → 🟡 GO WITH FIX | Egresos use **10-year bands** (60–69, 70–79, 80–89, 90+), so **65+ cannot be computed**. Use **70+** and **80+** (80+ works: 80–89 + 90+). Denominator: census 70+/80+ by comuna of residence. |
| Suppressed rows | 🟡 | 7.5% of rows (124,508) have comuna **and age and sector** suppressed (`*`). They're probably sensitive diagnoses, **not random**, so they bias some causes. Document this; don't impute. |
| Egresos as a "need" measure | 🟡 caveat | Discharges also reflect **supply and access** (hospital density, FONASA vs ISAPRE). Comunas near large hospitals look "sicker". Say so explicitly and prefer region-level aggregation. |
| Días de estada promedio 70+/80+ | 🟢 GO | `DIAS_ESTADA`, same age-band caveat. |
| Trend in egresos | 🟡 | `EGRESOS_2020.zip` also exists, but 2020 was COVID-distorted (elective surgery was cancelled). Use it only as a labelled contrast, not a trend. |
| Mortality 65+/80+ by comuna | 🟡 GO WITH FIX | Single-year age is available (`EDAD_TIPO=1` = years), so 65+ works. **2026 only runs to 19 Sep** (partial year): don't compare its annual count. 2024–2025 are two points, not a trend. For comunas, **crude rates are unstable** (few deaths) and driven by age structure: use **age-standardised rates** and pool 2024–2025, or report by region. |

## 6. Composite "Índice de Presión Demográfica Territorial"

🟡 **GO WITH FIX, region level only.**
Problems with the plan's version:
1. IE and razón de soporte potencial both come from the same age structure (almost the same signal), so demography gets counted twice.
2. The pensionados/cotizantes leg is invalid (see §5), so drop it or replace it with cobertura previsional.
3. It mixes grains: pensions are regional only, and the rest are comunal.
4. Crude mortality is again age-structure driven, so use the age-standardised version.

Fix: build it at **region level**, check the correlation matrix first (drop one of any pair with r > 0.8),
report weight sensitivity, and extend or replace the existing `kpi_indice_demanda_salud_region.csv` rather than adding a parallel index.

"Every chart shows value vs regional/national average": 🟢 GO (dashboard change).

## 7. Mini Active Ageing Index

🟡 **GO WITH FIX, but don't call it AAI.** The UNECE AAI has 22 indicators across 4 domains. Three single-indicator proxies are not an AAI; call it
"índice inspirado en el AAI (UNECE)".

| Domain | Status | Notes |
|---|---|---|
| Employment (% 65+ cotizando) | 🟡 national only | `cotizantes_edad.xls` has a "más de 65" band, but **only nationally**. The regional × age file has *afiliados* (stock of accounts), not *cotizantes*. That makes it **not regionalizable**, which is a problem for a regional score. |
| Security | 🟡 | Cobertura previsional ✅. Razón de dependencia and pensión promedio are IPS-only (see §5), so don't use them as "security". |
| Independent/healthy living | 🟢 | Age-standardised mortality 65+ plus egresos 80+ (DEIS), by region. |
| Social participation | ⬜ OPEN / 🔴 | No source. CASEN full microdata has participation modules, but the project only has the income extract. Either download full CASEN 2022 or state the gap and leave the domain out. |

"Weakest domain drives the policy proposal": 🟢 good idea, fits the existing `6_📋_Politicas.py` segmentation.

`c1_202607.xlsx` staying Bronze-only: ✅ agreed.

## Suggested order

1. §0 move the DEIS files in, then `09_procesar_deis.py` (70+/80+ egresos, age-standardised mortality 2024–2025)
2. §1/§2 cheap census KPIs (longevidad, masculinidad 65+, Friz, weighted CV, 20–64 soporte)
3. §5 relabel IPS pensión promedio; drop pensionados/cotizantes as a sustainability ratio
4. §6 region-level composite with correlation check
5. §7 AAI-inspired index (3 domains, employment flagged as national-only)
6. ⬜ OPEN data pulls: Censo 2017 comunal (real Δ), AFP pensions by region, full CASEN (participation)
7. Update `README.md`, `kpis.yaml` and the dashboard captions that still say "no DEIS"
