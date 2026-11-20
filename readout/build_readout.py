"""
Builds the one-page readout (README.md) and its chart from the built models and the eval results.
Every number on the first screen comes from this run, not from memory.

  python readout/build_readout.py          writes README.md and readout/win_rate_three_ways.png
  python readout/build_readout.py --check  fails if README.md is out of date with the data
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "target" / "kit_pipeline_review.duckdb"
CHART = ROOT / "readout" / "win_rate_three_ways.png"
# Complete quarters only: the data starts in 2025-Q3 (no full history) and 2026-Q4 is in progress.
QUARTERS = ["2025-Q4", "2026-Q1", "2026-Q2", "2026-Q3"]
FOCUS = "2026-Q2"


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def pts(x: float) -> str:
    return f"{abs(x) * 100:.1f} points"


def score(name: str) -> tuple[int, int, list[dict]]:
    rows = json.loads((ROOT / "eval" / f"results_{name}.json").read_text(encoding="utf-8"))
    return sum(r["correct"] for r in rows), len(rows), rows


def main(check: bool) -> None:
    con = duckdb.connect(str(DB), read_only=True)
    q = lambda sql: con.sql(sql).fetchall()  # noqa: E731
    rows = {r[0]: r for r in q(f"""
        select a.quarter, a.win_rate, b.win_rate, r.win_rate_reported, r.deals_that_moved, a.deals_won + a.deals_lost
        from main.mart_win_rate_by_close_quarter a
        join main.mart_win_rate_by_created_cohort b on b.cohort_quarter = a.quarter
        join main.mart_win_rate_reported_vs_now r on r.quarter = a.quarter
        where a.quarter in ({", ".join(f"'{x}'" for x in QUARTERS)})
    """)}
    deals = q("select count(*) from main.fct_deals")[0][0]
    moved_back = q("select count(*) from main.fct_deals where was_moved_back")[0][0]
    gaps = [rows[x][1] - rows[x][3] for x in QUARTERS]
    _, close_now, cohort, reported, moved, closed = rows[FOCUS]
    routine_ok, routine_n, _ = score("v1")
    hard1_ok, hard_n, hard1 = score("hard_v1")
    hard2_ok, _, _ = score("hard_v2")
    miss = next(r for r in hard1 if not r["correct"] and r["id"] == "h2")

    if not check:
        plot(rows)
    readme = README.format(
        deals=deals, moved_back=moved_back, focus=FOCUS,
        reported=pct(reported), now=pct(close_now), drop=pts(close_now - reported), moved=moved, closed=closed,
        cohort=pct(cohort), def_gap=pts(close_now - cohort),
        all_lower="every" if all(g < 0 for g in gaps) else "most",
        n_quarters=len(QUARTERS), min_gap=pts(max(gaps)), max_gap=pts(min(gaps)),
        routine=f"{routine_ok}/{routine_n}", hard1=f"{hard1_ok}/{hard_n}", hard2=f"{hard2_ok}/{hard_n}",
        miss_ai=miss["ai_answer"], miss_truth=miss["truth"],
    )
    path = ROOT / "README.md"
    if check:
        if path.read_text(encoding="utf-8") != readme:
            sys.exit("README.md is out of date: run python readout/build_readout.py")
        print("README.md matches the data")
        return
    path.write_text(readme, encoding="utf-8")
    print(f"wrote README.md and {CHART.name}")


def plot(rows: dict) -> None:
    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=160)
    width = 0.26
    xs = range(len(QUARTERS))
    series = [
        ("Reported at the pipeline review", 3, "#9AA0A6"),
        ("Close-date win rate, CRM today (default)", 1, "#D97757"),
        ("Created-cohort win rate", 2, "#3A6EA5"),
    ]
    for i, (label, col, color) in enumerate(series):
        vals = [rows[x][col] * 100 for x in QUARTERS]
        bars = ax.bar([x + (i - 1) * width for x in xs], vals, width, label=label, color=color)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.1f}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(list(xs), QUARTERS)
    ax.set_ylabel("Win rate (%)")
    ax.set_title("One quarter, three win rates (sample data)", fontsize=11, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=7.5, frameon=False, loc="upper left")
    ax.set_ylim(0, max(rows[x][c] for x in QUARTERS for c in (1, 2, 3)) * 100 * 1.25)
    fig.tight_layout()
    fig.savefig(CHART)


README = """# Kit's pipeline numbers, for people and for AI

Kit's Senior Analytics Engineer posting asks for sales metrics that Sales and RevOps trust without manual
reconciliation, documented well enough that an AI agent can answer routine questions without a data
teammate. This is a small version of that work, built on **sample data in HubSpot's deal shape**
({deals} synthetic deals; no Kit data).

## What I found (two minute read)

**1. The number we reported is not the number the CRM shows now.** {focus}'s win rate was **{reported}**
at the pipeline review a week after the quarter. The CRM says **{now}** today, {drop} lower: {moved} of
{closed} closed deals moved after the review (losses logged late, close dates backdated). In {all_lower} one
of the {n_quarters} complete quarters the reported rate was higher, by {min_gap} to {max_gap}.
*So:* report from property history as of the review date, and show "changed since reported" next to it.

**2. One quarter has two honest win rates.** {focus} is **{now}** by close date and **{cohort}** by the
quarter deals were created, {def_gap} apart. Both are right; they answer different questions.
*So:* close date is the default ("how did the quarter go"); cohort is labelled as deal quality, never
mixed in the same chart without saying which is which.

**3. An AI answered from the docs alone, and its one miss was silent.**

| Question set | One-line docs (v1) | Rewritten docs (v2) |
|---|---|---|
| 10 routine questions (one mart answers each) | {routine} | not needed |
| 10 questions no single mart answers | {hard1} | {hard2} |

The v1 miss: "how many deals are in Contract sent" filtered on the label instead of HubSpot's stage id
and returned **{miss_ai}** instead of **{miss_truth}**, with no error. The v2 docs name the grain, which
date counts, ids versus labels, and how to add up rates. (One run per docs version with a fresh AI each
time: an example of the failure, not a benchmark.)
*So:* name a mart after each routine question, and keep a question set like this as a test that runs
whenever a definition changes.

![One quarter, three win rates](readout/win_rate_three_ways.png)

## What I would do in my first month at Kit

1. Map HubSpot deals, pipelines and stages, companies, contacts and owners into the dbt models, and list the gaps.
2. Rebuild last quarter's reported win rate from property history and measure the gap on real data.
3. Write down the competing win rate definitions with RevOps, pick a default, and document the outcome.
4. Turn the questions Sales and RevOps actually ask into an AI question set that runs as a test.

*Assumptions:* the data is synthetic, in HubSpot's default deal and pipeline shape; the "pipeline review"
is 7 days after quarter end; {moved_back} of {deals} sample deals were pushed back a stage at least once.

---

## How to run it

```bash
pip install dbt-duckdb matplotlib
python generate/make_sample_crm.py      # sample HubSpot-shaped export into seeds/
dbt build --profiles-dir .              # seeds, models and 40 tests on DuckDB
python eval/score.py eval/answers_hard_v2.json hard
python readout/build_readout.py --check # this page matches the data
```

The SQL avoids DuckDB-only syntax (`macros/portable.sql` switches the two functions that differ) so the
models run on Redshift.

## What is in the repo

| Path | What |
|---|---|
| `generate/` | The sample HubSpot export: deals, stage and close date history, owners, stages |
| `models/` | Staging, the history rebuild of what each review knew, `fct_deals`, one mart per metric |
| `tests/` | Rates are shares, won amount reconciles to the cent, each deal counted once, reviews never see later edits |
| `docs/metrics.md` | The v2 definitions, written for people and AI tools |
| `eval/` | The questions, the AI's SQL for each docs version, and the scorer |
| `readout/` | This page's generator and chart |
"""

if __name__ == "__main__":
    main("--check" in sys.argv)
