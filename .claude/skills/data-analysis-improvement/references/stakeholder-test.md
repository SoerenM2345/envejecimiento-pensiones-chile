# Stakeholder test and iteration log

The loop in `SKILL.md` exits through this test. Fill it in for every pass; the log makes it visible whether a pass added depth or only polish.

## A. Stakeholder map

List at least four. Mark each as **in the data** (appears as a column, payer, receiver, operator) or **indirect** (affected or able to act, but not in the dataset).

| Stakeholder | In data / indirect | What they control or decide | What they need to know (who / where / when / how big) |
|---|---|---|---|
| | | | |

Typical candidates (adapt to the domain): the operators who earn from the flow (companies, administrators), the payer side (workers, employers, taxpayers), the receiver side (pensioners, patients, students, beneficiaries), the regulator or supervisor, the budget office or treasury, the central or local government, municipalities, adjacent systems (health, social care, labour market), civil society or researchers.

## B. Recommendation sheet (one block per chosen stakeholder, at least two)

```
Stakeholder:
Finding (the number on screen, with chart/metric where it is):
Implication (what it means for this stakeholder):
Recommended action (verb + object):
  How big : <quantity, unit, yardstick>            [criterion 2]
  Where/who: <territory or group>                  [criterion 3]
  When     : <year / window / trigger condition>   [criterion 4]
Differs from the other stakeholders' action because:   [criterion 5]
```

### Criteria (all five for each recommendation)

1. **Traceable** — points at a number, line or highlighted point visible in the view.
2. **How big** — quantified with a unit and compared with a yardstick (share of wage, of budget, per person, versus a threshold or legal rate).
3. **Where / who** — a specific territory, segment or group, not "the country" unless the finding really is national.
4. **When** — a year, a window or an explicit trigger ("when the ratio falls below X").
5. **Actionable and distinct** — a decision someone could take; not the same advice as another stakeholder's with the name swapped.

## C. Comparison checks

- **Against the time-alignment goal** (`time-alignment.md`): alignment table filled, no OFF inputs left unexplained, every deviation reasoned and shown in the caption.
- **Against positive examples** (`worked-examples.md`): does the view reach at least the same depth on the lenses who / where / when / how big / mechanism?
- **Against the user's explicit demands** in this project (see `project-requirements.md` and the current conversation): matched years, toggles instead of duplicate charts, real vs scenario, highlighted anchor years, critical point marked, lower geographic level, original numbers untouched.
- **Against a competent analyst's version**: would an official body's report show something this view cannot (a decomposition, a distribution, a break-even)?

## D. Verdict

- **PASS**: ≥2 stakeholders, all five criteria each, comparison checks without blocking gaps.
- **FAIL**: write the single weakest dimension and the next deeper question:

| Weakest dimension | Typical next deepening |
|---|---|
| Who | Split by group (sex, income band, worker type, payer) or decompose by payer/receiver |
| Where | Regional split; one level lower with a labelled approximation |
| When | History + forecast; threshold crossing year; anchor years with real data |
| How big | Convert to money in constant prices and to a share of a yardstick |
| Mechanism | Decompose the flow; show which component moves and why |

Stop the loop and report the limit if two consecutive passes add no new stakeholder-relevant insight.

## E. Iteration log template

| Pass | Weakest dimension found | Deepening applied | Data added / script | Alignment (inputs matched / deviations + reason) | New stakeholder-relevant insight | Verdict |
|---|---|---|---|---|---|---|
| 0 | (baseline) | — | — | Offsets of the original inputs | One-sentence reading of the original view | — |
| 1 | | | | | | |
| 2 | | | | | | |
