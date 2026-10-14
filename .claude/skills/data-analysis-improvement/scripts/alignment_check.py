#!/usr/bin/env python3
"""Time-alignment check for the data-analysis-improvement skill (standard library only).

Reads a small CSV that describes every input of a calculation and reports how far each one is from the target date.

inputs.csv columns:
  name      free text, e.g. "contributors"
  role      numerator | denominator | income | price | cost ...
  type      stock (a value at a date) | flow (a total over a period) | average (a mean over a period)
  start     YYYY-MM-DD first day the value covers (for a stock: the date itself)
  end       YYYY-MM-DD last day the value covers (for a stock: the same date)

Usage:
  python alignment_check.py inputs.csv --target 2024-12-31 [--tolerance-months 6]

Verdicts:
  MATCH   the target date lies inside the input's period (or a stock is dated on the target)
  NEAR    outside, but within the tolerance: acceptable only with a written reason (see references/time-alignment.md)
  OFF     further than the tolerance: look for the matching period, adjust, or label it
The exit code is 1 if any input is OFF, so it can run inside a test.
"""
import argparse
import csv
import sys
from datetime import date


def d(s):
    return date.fromisoformat(s.strip())


def months_between(a, b):
    return (b.year - a.year) * 12 + (b.month - a.month) + (b.day - a.day) / 30.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--target", required=True, help="YYYY-MM-DD, the date of the anchor input")
    ap.add_argument("--tolerance-months", type=float, default=6.0)
    a = ap.parse_args()
    target = d(a.target)

    rows, bad = [], 0
    with open(a.csv, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            s, e = d(r["start"]), d(r["end"])
            if s <= target <= e:
                off, verdict = 0.0, "MATCH"
            else:
                off = months_between(target, s) if s > target else months_between(e, target) * -1
                verdict = "NEAR" if abs(off) <= a.tolerance_months else "OFF"
            kind = r["type"].strip().lower()
            note = ""
            if kind == "flow" and verdict == "MATCH" and (e - s).days < 300:
                note = "flow shorter than a year: check it is comparable with annual inputs"
            if kind == "stock" and verdict != "MATCH":
                note = "stock on another date: interpolate or find the same date"
            bad += verdict == "OFF"
            rows.append((r["name"], r["role"], kind, f'{r["start"]}..{r["end"]}', f"{off:+.1f}", verdict, note))

    head = ("input", "role", "type", "period", "offset (months)", "verdict", "note")
    w = [max(len(str(x[i])) for x in rows + [head]) for i in range(len(head))]
    for line in [head] + rows:
        print("  ".join(str(x).ljust(w[i]) for i, x in enumerate(line)))
    print(f"\ntarget {target}; {sum(1 for r in rows if r[5] == 'MATCH')} MATCH, "
          f"{sum(1 for r in rows if r[5] == 'NEAR')} NEAR, {bad} OFF")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
