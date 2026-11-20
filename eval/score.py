"""
Scores an AI's answers. Input: a JSON file of {"id": ..., "sql": ...} the AI wrote from the docs alone.
Each SQL is run on the built models; its first value is compared with the question's true answer.

  python eval/score.py eval/answers_v1.json [routine|hard]  ->  eval/results_v1.json and a printed score
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from questions import HARD, QUESTIONS  # noqa: E402

DB = Path(__file__).resolve().parent.parent / "target" / "kit_pipeline_review.duckdb"


def first_value(con, sql):
    row = con.sql(sql).fetchone()
    return None if row is None else row[0]


def same(kind, got, truth):
    if got is None or truth is None:
        return False
    if kind == "text":
        return str(got).strip().lower() == str(truth).strip().lower()
    got, truth = float(got if not isinstance(got, Decimal) else float(got)), float(truth)
    if kind == "rate":
        # A share may come back as 0.268 or 26.8.
        return abs(got - truth) <= 0.0015 or abs(got / 100 - truth) <= 0.0015
    if kind == "points":
        # A change in percentage points may come back as 0.043 or 4.3.
        return abs(got - truth) <= 0.0015 or abs(got / 100 - truth) <= 0.0015
    if kind == "count":
        return round(got) == round(truth)
    if kind == "days":
        return abs(got - truth) <= 0.5
    return abs(got - truth) <= 1.0  # amount, within a dollar


def main(path: str, which: str = "routine") -> None:
    questions = HARD if which == "hard" else QUESTIONS
    answers = {a["id"]: a for a in json.loads(Path(path).read_text(encoding="utf-8"))}
    con = duckdb.connect(str(DB), read_only=True)
    results = []
    for q in questions:
        truth = first_value(con, q["truth"])
        sql = answers.get(q["id"], {}).get("sql", "")
        try:
            got, error = first_value(con, sql), None
        except Exception as exc:  # the AI's SQL failed to run
            got, error = None, str(exc).splitlines()[0][:200]
        ok = same(q["kind"], got, truth)
        results.append({"id": q["id"], "ask": q["ask"], "correct": ok, "ai_answer": None if got is None else str(got), "truth": str(truth), "error": error, "sql": sql})
    out = Path(path).with_name(Path(path).name.replace("answers_", "results_"))
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    right = sum(r["correct"] for r in results)
    print(f"{right}/{len(results)} correct")
    for r in results:
        print(("OK   " if r["correct"] else "MISS ") + r["id"], r["ask"], "| ai:", r["ai_answer"], "| truth:", r["truth"], ("| error: " + r["error"]) if r["error"] else "")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "routine")
