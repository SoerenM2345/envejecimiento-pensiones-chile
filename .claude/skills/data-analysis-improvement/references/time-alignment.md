# Time alignment: every input on the same period

**Goal.** Every number that enters a calculation should describe the same period. Ideally the same date (or the same calendar year with the same kind of measurement). When that is not possible, the mismatch must be a decision you made and explained, not an accident the viewer discovers. A ratio whose numerator is December 2025 and whose denominator is April 2024 answers a question nobody asked.

## 1. Build the alignment table (before computing anything)

One row per input, in the iteration log:

| Input | Role (numerator / denominator / price / income…) | Measure type | Reference period (exact) | Source & lag | Offset to target |
|---|---|---|---|---|---|
| e.g. contributors | numerator | **stock** at a date | 31 Dec 2024 | regulator, monthly | −4 months |
| e.g. population 65+ | denominator | stock at a date | Census, April 2024 | statistics office | target |
| e.g. spending | numerator | **flow** over a period | calendar 2024 | annual report | covers target |
| e.g. income survey | income | average over a quarter | Oct–Dec 2024 | survey | +6 months… |
| e.g. price index | deflator | average over a year / point in time | annual mean | central bank | — |

Rules for reading it:
- **Target** = the period of the *anchor* input that is hardest to move (usually a census, a survey wave or a legal date). Everything else is matched to it.
- **Stock vs flow vs average.** A stock (people on a date) matches best with another stock on the same date, or with a flow/average whose period *contains* that date. A flow (spending over a year) matches an annual average or the calendar year, not a December snapshot. Say which you assumed.
- **Reference period ≠ publication period.** Check what the publisher means by the date (a factsheet published in September may describe July contributors and June wages). Align on the reference period.
- Write the offset in months for every input. Offsets of 0 are the goal.

## 2. If an input does not match: decision order

1. **Look for the matching period** in the source (older/newer release, another table, monthly instead of annual). Prefer this; it costs one more download.
2. **Ask or request it** if only the user can get it (interactive portal, paid dataset), with the exact period needed.
3. **Use an adjacent period only with a written reason.** Evaluate, in this order:
   - *Distance*: how many months from the target? Prefer the nearest; if equidistant, prefer the earlier one for stocks that are published with revisions, the later one when the earlier is a forecast.
   - *Volatility*: does the quantity move fast? (Population 65+ grows ~4%/yr; wages in nominal pesos 6–10%/yr; a ratio of two things moving the same way is robust to a one-year shift, a ratio of things moving in opposite directions is not.)
   - *Direction of bias*: will the mismatch push the result up or down? State it.
   - *Size*: compute the result with **both** candidate periods (the "sensitivity pair") and report the difference. If it is below the precision you claim (say < 1–2%), the adjacent year is acceptable; if not, it is not.
   - *Kind of measure*: stock-for-stock at the nearest date is fine; substituting a flow for a stock, or a year-end value for a mid-year average, needs a correction (scale, interpolate between two dates) or a label.
4. **Adjust instead of substitute** when a clean rule exists: interpolate between two dates; deflate with the right price base; scale by a known growth factor; take the quarter that contains the target date. Show the adjustment in the processing script, not in the dashboard.
5. **Accept and label** when none of the above is possible: state the mismatch, its direction and approximate size in the caption and the KPI caveat, and note what data would remove it.

Never silently pick the most recent value because it is the newest. "Latest" is a period like any other.

## 3. Checks to run

- `python scripts/alignment_check.py inputs.csv --target 2024-12-31` prints each input's offset to the target and flags those outside its own period; fill `inputs.csv` from the table above.
- In tests: assert that the tables you join carry the same `anio` (or date) and that the engine's base year equals the target year.
- In the UI: the caption names the matched periods; if a regional view uses a different year from the country view (e.g. Census 2024 for regions vs the statistics office's 2025 estimate for the country), say so and why.

## 4. Examples from this project (calibration)

| Situation | Decision & reasoning |
|---|---|
| Country ratio of contributors (Dec 2025) over population 65+ | Used the statistics office's projection for **2025** (30 June) as the stock counterpart: a 6-month offset on a quantity growing ~4% a year, ≈ ±2%, acceptable and labelled. The original KPI divided Dec-2025 contributors by the **2024** census, a 12-month mismatch that overstated the ratio by ~4% and that also changes the population source (census 18.5 M vs adjusted estimate 19.8 M), so the two ratios (2.30 vs 2.06) differ for two reasons. |
| Regional view | Target = Census 2024 (April). Contributors and taxable income at **Dec 2024** (+8 months) instead of Dec 2025 (+20 months), survey income Oct–Dec 2024, benefit spending 2024. The regional view therefore starts in 2024, not 2025, even though newer contributor data exist. |
| Regional benefit spending | Only the share of each region (Q4 2024) was usable; applied to the national annual 2024 total, because the quarterly report mixes months, quarters and different peso bases. Reasoned as "shares are scale-free, so the quarter is a valid proxy for the year". |
| Pre-2018 region (Ñuble) | Income from the parent region, flagged in a column, because no separate series exists. |
| Deflator | Annual average price index for all money so that flows (annual) and snapshots (December) sit on one base; the December-snapshot incomes carry a ≤ 1–2% distortion in high-inflation years, stated. |
| Monthly contributors vs reference month | Factsheet publication month ≠ reference month; aligned on the reference month. |
