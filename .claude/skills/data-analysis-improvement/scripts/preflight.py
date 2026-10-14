#!/usr/bin/env python3
"""Preflight for the data-analysis-improvement skill (read-only; standard library only).

Prints what you need to know before changing a KPI view in a shared repo:
  - git: branch, ahead/behind versus the remote (after an optional fetch), uncommitted and untracked files
  - the next free number for a new Scripts/NN_*.py (parallel sessions have collided on numbers)
  - the tests folder and the pytest command if a venv exists
  - Streamlit servers listening locally
  - the KPI entry in config/kpis.yaml (text match, no YAML dependency) when --kpi is given

Usage:
  python preflight.py <project-root> [--kpi 1.2] [--fetch]
"""
import argparse
import re
import subprocess
from pathlib import Path


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--kpi", help="KPI id as written in config/kpis.yaml, e.g. 1.2")
    ap.add_argument("--fetch", action="store_true", help="git fetch first (network)")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    print("== git ==")
    if a.fetch:
        run(["git", "fetch", "-q"], root)
    print(run(["git", "status", "-sb"], root) or "(clean)")
    print("remote-only commits:", run(["git", "log", "--oneline", "HEAD..@{u}"], root) or "none")
    print("local-only commits :", run(["git", "log", "--oneline", "@{u}..HEAD"], root) or "none")
    print("Files you did not write may be someone else's work in progress: do not commit or overwrite them.")

    print("\n== scripts ==")
    nums = sorted(int(m.group(1)) for p in (root / "Scripts").glob("*.py") if (m := re.match(r"(\d+)_", p.name)))
    print("numbers in use:", nums, "| next free:", (max(nums) + 1) if nums else 0)

    print("\n== tests ==")
    venv = root / "Data raw" / ".venv" / "bin" / "python"
    print("tests dir:", "found" if (root / "tests").is_dir() else "none")
    if venv.exists():
        print(f'run: "{venv.relative_to(root)}" -I -m pytest tests -q')

    print("\n== streamlit servers ==")
    listening = run(["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"], root).splitlines()
    print("\n".join(l for l in listening if re.search(r":85\d\d", l)) or "none on 85xx")

    cfg = root / "config" / "kpis.yaml"
    if a.kpi and cfg.exists():
        print(f"\n== config/kpis.yaml, KPI {a.kpi} ==")
        txt = cfg.read_text(encoding="utf-8")
        m = re.search(r'-\s+id:\s*"%s"\n(.*?)(?=\n\s+-\s+id:|\Z)' % re.escape(a.kpi), txt, re.S)
        print(m.group(0)[:2500] if m else "not found")


if __name__ == "__main__":
    main()
