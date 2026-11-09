# Presentation conventions for a KPI card (learned on KPI 1.2, then applied to 2.2 and 2.3)

A deeper analysis is only useful if it can be read in a few seconds. After the content passes the stakeholder test, run this checklist on the card. These came from a review of KPI 1.2 where the first deepening was correct but too wordy, in a different text style from its neighbours, and with the formulas far from the chart they explain.

## 1. One text style across the whole dashboard
- Put the style in **one helper** that every chart goes through (here `estilo_kpi(fig, alto)` in `components/charts.py`: black title, axes, legend and labels; legend below the chart; same margins). Call `st.plotly_chart(..., theme=None)` so the host theme does not overwrite the colours.
- Use the helper for **every** chart of the KPI, old and new, and for sibling KPIs when you touch them. A card where the old chart is grey-on-dark and the new one black-on-light looks unfinished.
- Before inventing a style, open the KPI the team already approved (here 1.3) and copy it.

## 2. Layout
- Two charts that answer related questions go **side by side** (`st.columns(2)`), each with its own control (switch, selector) *inside its column*. A full-width pair wastes the screen and hides the comparison.
- The chart that carries the main message (the critical point, the threshold) stays **full width, below**.
- The map/choropleth and its companion bars are already a natural pair; keep them side by side.

## 3. Formulas next to the chart they explain
- Side panel (`st.columns([3, 1])` or similar) with **one box per line of the chart**. Each box has: the formula in symbols, a **checkbox** that shows or hides that line, and the **actual numbers for the base year** ("$2,31 M × 2,70 M personas → $6,25 billones"), computed from the data on screen, never typed in.
- If the chart has two views (money / ratio), the panel switches with the view and shows that view's formulas.
- Markers that need both lines (the ★ of a crossing) appear **only while both lines are visible**; the builder takes a `mostrar=(bool, bool)` argument for this.

## 4. Less text
Viewers do not read paragraphs inside a KPI card. Per card:
- **No intro paragraph.** The card header (definition, formula, caveat) already introduces it.
- **"Lectura:" is one line**, generated from the data on screen, with the two or three numbers that matter.
- **Remarks are small notes marked with `*`** (`st.caption("\\* ...")`), one short sentence each. A remark that needs more than a sentence belongs in the expander.
- **Method, dates and sources go in a collapsed `st.expander("Método y fuentes")`**: matched periods, observed vs scenario, deviations and their reason, sensitivities, sources. Nothing needed to *read the chart* may live only there.
- Shorten the KPI's description, formula and caveat in the config file to one line each. Long caveats in the header push the charts off the first screen.
- Do not delete numbers other people quote; move them to the expander.

## 5. Config text is cached
Streamlit caches the YAML/CSV loaders. After changing `config/kpis.yaml` the running dashboard still shows the old text until **C → "Clear cache"** or a server restart. Say so in the report, or the user will think the edit failed.

## 6. Verify what you changed, all of it
Open the page in a headless browser (or use the project's app tests) and look at **every section you touched after your last edit**, not only the first screens. List in the report which sections you looked at and which you did not. In the KPI 1.2 session the final edits to the critical-point section were not re-checked, and the report had to say so.

## 7. Consistency sweep
When a convention is established on one KPI, grep the sibling KPI render functions (`st.plotly_chart(` without the style helper, long `st.markdown` blocks, captions longer than a sentence) and list which ones deviate. Fix them if the user asked for the convention project-wide ("apply to 2.3"); otherwise list them in the report.

## 8. Class design rules (docs/Clase_visualizacion_storytelling.pdf; decisions of 2026-11-09)
Applied to every chart in `components/charts.py`, new ones included. The checks live in `tests/test_dashboard_smoke.py`.
- **Title = message, no abbreviations.** Build it with `_titulo(mensaje, detalle)`: the sentence states the finding with numbers computed from the data ("El costo supera la capacidad desde 2038"), the small subtitle gives unit and scope. No sigla in a title: write "Pensión Garantizada Universal", "Administradoras de Fondos de Pensiones", "producto interno bruto" (test `test_titulos_de_graficos_sin_siglas`). Subplot titles go through `_subtitulo`. Plotly does not wrap, so the helpers wrap and `colores_legibles` grows the top margin.
- **Direct labels instead of a legend** for line charts where each line is a different variable: `rotular_final` + `ampliar_derecha`. Keep a legend for bars and for keys that explain a style (observed vs scenario markers).
- **At most 4 lines per chart.** KPI 1.3 keeps the sensitivity with the invalidity insurance behind a checkbox.
- **Axes start at 0, scatter plots included** (`_rango`), no exception. **Bars**: one colour per series, gap = half a bar (`BARRAS`), sorted by value.
- **Double axis** only with different chart styles and contrasting colours; prefer one axis when both series share the unit (the 1.2 cushion is an area on the main axis).
- **Scenario stays dashed** (project convention kept; the user will ask the professor in person; if the answer is "solid only", change every `dash=` in `charts.py`).
- **Colour blindness** (simulated, Machado 2009, CIE76 ΔE ≥ 25 between colours of one chart): VIOLET is now a dark plum (#5c1a5c) because the old violet clashed with BLUE; RED vs ORANGE is still weak (ΔE 10 in tritanopia), so never use them together as the only cue (the MCO trend lines are dark navy); RED vs green/AQUA needs a second cue (area style or direct label). Re-run the audit (all figures of the 3 final pages) when adding a colour.
- **Storytelling**: introduction → development → conflict → climax → call to action; a card that ends without a concrete action for a stakeholder is unfinished.
