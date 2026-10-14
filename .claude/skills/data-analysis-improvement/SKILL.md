---
name: data-analysis-improvement
description: Review a KPI or dashboard view against the project's requirements and deepen it, step by step, until it answers who / where / when / how big the problem is and supports concrete recommendations for at least two stakeholders. Use it whenever the user asks to improve, deepen, review, upgrade or "find the critical point" of a KPI, chart, dashboard page or analysis, asks "what does this KPI really tell us", wants old-vs-new comparisons of a KPI, needs missing data found or downloaded for a KPI, or says a view "is too shallow / just a snapshot / doesn't lead anywhere" — even when the KPI, the sources or the country are different from the Chilean pensions project this was learned on.
---

# Data analysis improvement

A KPI view is finished when someone can act on it, not when the number is correct. A correct number on a bar chart usually answers "what is the value?". People who have to decide ask four deeper things: **who** is affected, **where** it is concentrated, **when** it becomes a problem (or already was), and **how big** it is compared with something that matters. This skill takes a KPI view from the first kind of answer to the second, and keeps going until recommendations for **at least two different stakeholders** can be derived from what the view shows.

The method was learned by improving KPI 1.2 ("cotizantes por persona de 65+") and KPI 1.3 of the Chilean pension-aging dashboard; `references/worked-examples.md` has the before/after of both, and `references/project-requirements.md` has the standing requirements of that project, and `references/ui-conventions.md` the presentation checklist for a KPI card (shared chart style, layout, formula panel, less text, cache, verification). Read all three before starting. Treat them as the positive examples to compare against, not as templates to copy: the KPI, sources, country and stakeholders will differ.

## The loop in one picture

```
 0 Preflight & baseline ─▶ 1 Diagnose gaps ─▶ 2 Brainstorm deepenings ─▶ 3 Data: have / need / get
        ▲                                                                          │
        │                                                                          ▼
 7 Report (before/after) ◀─ 6 STAKEHOLDER TEST ◀─ 5 Verify & document ◀─ 4 Build (script → engine → chart → UI)
                                   │ fails: name the weakest of who/where/when/how big
                                   └──────────▶ back to 2 (next deeper question)
```

Two checks run through every pass, not just once: the **stakeholder test** (step 6) decides whether the view is deep enough, and the **time-alignment check** (see below) decides whether the numbers behind it are comparable. A deeper view built on mismatched periods is deeper nonsense.

Do not skip step 6 or stop after one pass. The loop ends only when the stakeholder test passes or when the data genuinely runs out (then say precisely what is missing and how to get it). Keep an iteration log (template in `references/stakeholder-test.md`) so each pass is compared with the last.

## 0. Preflight and baseline

Why: other people and other Claude sessions work in the same repo, and you cannot show "improved" without a recorded "before".

1. Run `python <skill-dir>/scripts/preflight.py <project-root> [--kpi 1.2]`. It prints git state (ahead/behind, uncommitted files you did not write), the next free script number, the tests folder, running Streamlit servers and the KPI's config entry. Never commit or overwrite files you did not touch; if a merge needs a clean tree, stash only those paths and restore them afterwards. Pass `--files <paths>` (the files you expect to edit, e.g. the page module, `charts.py`, `config/kpis.yaml`) and it reports which of them already carry uncommitted changes. Those files are **shared with another session**: see "Editing a file someone else is changing" below.
2. Read the project's own rules first: README, `config/` (KPI definitions), `docs/` (guides, data gaps), the source inventory, test conventions, and any CLAUDE.md. `references/project-requirements.md` lists what these were in the pension project; look for the equivalents elsewhere.
3. Record the baseline of the target view: which file(s) and function render it, the formula, the data files and years used, the control numbers it shows, its status/caveats, and what a viewer concludes from it in one sentence. Run the existing tests so you know what "green" meant before you started.

## 1. Diagnose: what does the view fail to say?

Read the view as a decision-maker, not as its author. For each lens, ask "can I answer this from the view?" and note the gap:

| Lens | Typical shallow state | Deeper state to aim for |
|---|---|---|
| **Who** | One national figure; no groups | Split by the groups that carry the problem (sex, age, income, worker type, payer, institution) |
| **Where** | National or one level of geography | Region → lower level (comuna/district) with a clearly labelled approximation when the data stops |
| **When** | One snapshot | History + forecast; the year a threshold is crossed; years with real data highlighted |
| **How big** | A ratio with no yardstick | Money, % of wage / GDP / budget, per person, versus a tolerable limit or a legal rate |
| **Why / mechanism** | Only the outcome | The decomposition (who pays what, where the flow goes, which component moves) |
| **Comparability** | Numerator and denominator from different dates | Every input on the same period (see "Time alignment" below), deflated money, definitions stated |

Also check the honesty of what exists: mismatched years, mixed bases, silent drops (a region or month missing without warning), unlabeled approximations. Fix or flag these first; deeper analysis on a shaky base only deepens the error. (In the pension project a parser silently dropped one of 16 regions because of an accent; it only surfaced when a deeper view needed the regional totals.)

## Time alignment: the standing goal for every calculation

**Goal: every input of a calculation describes the same period, ideally the same date.** Check this at diagnosis (is the existing KPI aligned?), when choosing data (which release/period to fetch), when building (the engine's base year = the target year) and when verifying. Details, decision rules and project examples are in `references/time-alignment.md`; the short version:

1. **Make an alignment table** before computing: for each input its role, whether it is a stock (value on a date), a flow (total over a period) or an average, its exact reference period (not its publication date), and its offset in months from the **target** (the period of the hardest-to-move anchor input, e.g. a census or survey wave). `scripts/alignment_check.py` computes the offsets and flags them MATCH / NEAR / OFF.
2. **If an input does not match, go down this ladder and write down the result:** (a) find the matching period in the source; (b) ask the user to fetch it if only they can (exact period, exact table); (c) only then consider the adjacent period, e.g. the following year, and decide by evidence: distance in months, how fast the quantity moves, which direction the bias goes, whether stock is being swapped for flow, and a **sensitivity pair** (compute with both periods and report the difference; if it is below the precision you claim, the neighbour is acceptable, otherwise not); (d) prefer an adjustment you can show (interpolate between two dates, deflate to one price base, take the quarter that contains the target) over a substitution; (e) if nothing works, keep the mismatch but label its direction and size in the caption and caveat and name the data that would remove it.
3. **Never pick a period because it is the newest.** "Latest" is only a period like any other; the regional view in this project deliberately starts in 2024 although 2025 contributors exist, because the population anchor is the 2024 census.
4. **Say it where the viewer reads it:** the caption names the matched periods and every deliberate deviation with its reason.

## 2. Brainstorm deeper questions, then pick

Write 5–10 candidate deepenings in plain words, each as a question a stakeholder would ask ("From which year does X exceed what Y can pay?", "Which region carries the most Z per worker?", "What share of the flow reaches the party that pays for it?"). Useful moves that worked before:

- **Turn a trend into a threshold.** A falling ratio says "worse"; a break-even says "critical from year N". Define the two quantities that meet (cost vs capacity, supply vs demand, inflow vs outflow) and mark the crossing.
- **Put the number in money and in a yardstick.** Convert ratios to currency in constant prices and to a share of something stakeholders already track.
- **Decompose.** Break a total into who pays / who receives / which component, over time.
- **Offer two bases, one chart.** When there are two legitimate bases (e.g. contributors vs everyone employed; mean vs median) use a toggle instead of two charts so the viewer sees the difference by flipping.
- **Match years; show real vs scenario.** Observed solid, scenario dashed; highlight the years that have real data.
- **Go one geographic level lower** when data allows, and say plainly which parts inherit from the higher level.
- **Scenario sliders with a defensible default** (explain why the default is what it is, e.g. a legal rate), never a hidden constant.

Score each candidate on (a) how much it changes what a stakeholder would do, (b) data availability, (c) effort. Do the top one or two now; keep the rest for the next loop pass. Prefer the one that fixes the weakest lens from step 1.

## 3. Data: what exists, what is missing, how to get it

1. **Inventory what is already in the repo** (processed tables, raw sources, the source inventory) before searching outside. Reuse existing loaders and tables.
2. **List what is missing**, each item as: variable, unit, **exact period needed (taken from the alignment table)**, level (national/region/…), why it matters, and where it likely lives (official statistics office, regulator, central bank, budget office, survey). When you ask the user to download, name the period that matches the target, and a wider window only if it also serves other uses.
3. **Acquire in this order** (this ladder came from a session where only part of the files could be fetched automatically):
   - **Scripted download.** Look at the source page's form and JavaScript to find the real request. Government portals often need a session cookie, a browser User-Agent and a Referer, and return a redirect-to-404 without them. Download only what is missing (detect existing files by the date inside them, not by the filename), validate each response against the requested period, pause politely between requests, and make the script re-runnable. Standard library is enough.
   - **Guided manual download** when the portal is interactive or blocked. Give the user: the exact menu path as they will see it, which numbered tables/files, which period (and why that window — it should overlap the other sources), where to save and how to name them, and what is optional. Ask for the menu list if their screen differs from what you expected and map it for them. Never ask for more than the analysis needs.
   - **Seed values.** If neither works yet, use clearly published headline figures flagged "provisional" in the UI and swap them for the full series later.
4. **Inspect every received file before trusting it.** Real examples: a ".xls" that is an HTML table; an ".xlsx" whose workbook points at the wrong sheet; rounded values; older duplicate exports next to newer ones; a layout that changes between years; units in thousands. Check two or three control values against the publisher's own page.
5. **Handle partial delivery.** Parse what arrived, compute what is still missing (by period), backfill with the script, and say so in the log. Record every new source in the source inventory with period, units and caveats.

Use web search for sources and official numbers, and cite links when you hand the user a list. Say which links you actually opened and which you only saw in search results.

## 4. Build

Keep the same separation the project uses; it makes each layer testable:

1. **Processing script** (next free number from preflight; parallel sessions have collided on numbers before). Writes tidy tables with documented columns, units and method notes in the docstring. Deflate money to one base year. Never edit raw data.
2. **Pure calculation engine** (no UI imports, no file reads): takes DataFrames and a small scenario dataclass, returns a DataFrame and a result like the crossing year. Mark observed vs projected rows.
3. **Chart builder** as a pure function returning a figure, in the project's existing style (palette, layout, Spanish labels if the UI is Spanish). Observed solid, scenario dashed, anchor years as diamonds, critical point as a star with its year.
4. **UI block** added *under* the existing view inside the same KPI card, leaving the original numbers and charts untouched unless the user asks otherwise. Territory selectors, toggles for alternative bases, sliders with help text, 3–4 metrics, a **dynamic "Lectura" sentence** generated from the data on screen (so it never goes stale), and a caption stating matched years, approximations and what is observed vs scenario.
5. **Presentation pass** with `references/ui-conventions.md`: one shared text-style helper for every chart, related charts side by side, formulas in a side panel with a checkbox per line and the live numbers, a one-line "Lectura", remarks as `*` notes, method and sources in a collapsed expander, short header text in the config.
6. **Docs** where the project keeps them: KPI definition file, user guide with a manual recipe and control values, source inventory, READMEs.

## 5. Verify and document

- **Alignment:** fill `inputs.csv` for the calculation, run `scripts/alignment_check.py --target <date>` and keep the output in the log; every OFF must be fixed, adjusted or explicitly labelled, and every NEAR needs its written reason. Assert in a test that the joined tables share the same year and that the engine's base year equals the target.
- Tests, mirroring the project's: input-table control values taken from the publisher's page; a hand-checked calculation; invariants (e.g. the crossing moves later when wages grow faster); every selector path runs without exception (headless app test); the old KPI's regression values still pass.
- Run the **whole** suite, not just the new tests, and report failures honestly, including ones caused by someone else's uncommitted work.
- **Look at the result.** Render the page headless (or via the project's app tests) and check every section you changed *after your last edit*. Write down which sections you looked at; whatever you did not re-check goes into the report as "not re-checked".
- **Diff against HEAD** before committing: `git diff HEAD -- <file>` must show only your hunks. Removed lines you did not mean to remove mean you overwrote someone else's work (see below).
- Sanity-check magnitudes against an official projection or published figure.
- If a deeper view needs a table that an earlier script quietly gets wrong, fix that script, rerun it, and record the fix.

## 6. The stakeholder test (this is the loop's exit condition)

Follow `references/stakeholder-test.md`. In short:

1. **Map stakeholders** — those in the data (payers, receivers, operators) and those indirectly involved (regulators, treasury/budget office, employers, municipalities, health or education systems, civil society). List at least four; choose the two or more the view informs best.
2. For each chosen stakeholder write **finding → implication → recommended action**, and check each recommendation against five criteria: traceable to a number or chart in the view; **how big** (quantified with unit and yardstick); **where / who** (specific territory or group); **when** (a year, a window or a trigger); **actionable and different** from the other stakeholders' (not the same advice restated).
3. **Compare** against (a) the time-alignment goal (is every input on the same period, and is every deviation justified in writing?), (b) the positive examples (does your view reach at least the depth of the before/after in `references/worked-examples.md`?), (c) the user's explicit demands in this project (matched years, toggles, highlighted years, lower level, etc.), and (d) what a competent analyst at an official body would show.
4. **Pass** = ≥2 stakeholders, all five criteria met for each. **Fail** = name the single weakest dimension (who / where / when / how big / mechanism), write the next deeper question that would fix it, and return to step 2. Also stop the loop if two consecutive passes add nothing new; then report the limit and the data that would move it.

Do not pad: a recommendation that cannot point at a number on the screen does not count, and a vague "monitor the situation" never does.

## 7. Report to the user

Give, briefly and in the user's language: the **period alignment** (which period each input uses, and any deviation with the reason it was accepted), the **before/after** of the view (what it said, what it says now, with the headline numbers), what each pass added and why, the **recommendations per stakeholder** with the number behind each, caveats and approximations, what data is still missing and exactly how to get it, tests run (and any red ones that are not yours), and what is uncommitted. Say which sections of the page you looked at after the last edit and which you did not. If you changed `config/` text, remind the user that the running Streamlit app caches it (C → "Clear cache" or restart). If you apply a convention to another KPI, list which siblings were changed and which still deviate. Commits: group into few, meaningful commits with descriptive titles in the project's language; never push without being asked, and say plainly if the push is the only remaining step for collaborators to see the update.

## Editing a file someone else is changing

Several sessions (and teammates) edit the same page modules, `charts.py` and `config/kpis.yaml`. In the KPI 1.2 session a full rewrite of a block silently erased another session's committed work (a communes table, the 2024 base year, a Censo-adjustment note); two failing tests revealed it. Rules:

1. Before editing, run `git diff HEAD -- <file>` and `git log -3 --format=%h\ %s -- <file>`. If the file has uncommitted changes, they are not yours.
2. Edit with **targeted replacements** of the function or block you own. Do not regenerate or rewrite a whole file or a block that other KPIs share.
3. After editing, `git diff HEAD -- <file>`: every removed line must be one you meant to remove. Run the full suite right away; a test failing in code you did not touch is the signal.
4. If the file already has someone else's uncommitted hunks, do **not** commit it whole. Commit only your hunks (`git diff -- <file>` → keep your hunks in a patch → `git apply --cached`), or leave the file uncommitted and say exactly which hunks are yours.
5. If you did overwrite something, restore it from HEAD, rerun the tests, and tell the user in the report. Do not hide it.

## Things that go wrong (learned the hard way)

- Starting to code before the baseline exists, so "improved" cannot be shown.
- Mixing dates (this year's contributors over last census's population) without saying so, or "fixing" it by silently using the neighbouring year without testing how much it changes the result.
- Two charts where a toggle would let the viewer compare directly.
- A threshold with no stated tolerance; the user cannot judge a "critical year" whose assumption is hidden.
- Treating a regional or lower-level figure as measured when it is inherited from above and not labelled.
- Renaming or overwriting numbers the rest of the team already quotes. Add below; change only on request.
- Taking over other people's uncommitted work in the same folder, or rewriting a shared block and erasing a teammate's committed changes.
- A new chart in a different text style from the rest of the card (or from the neighbouring KPIs).
- Paragraphs where one line and a `*` note would do; method details that should sit in the expander.
- Reporting "done" after checking only the first screens of the page, or forgetting that the app caches the config text.
