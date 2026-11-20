"""
Sample CRM export in HubSpot's own deal shape. Synthetic: no real Kit data, no real people.

What it imitates (HubSpot CRM concepts, public docs):
  - deals with dealstage, pipeline, amount, createdate, closedate, hubspot_owner_id
  - property history for dealstage and closedate (each change with its timestamp)
  - HubSpot's default sales pipeline stage ids

What makes it realistic for this problem:
  - some deals move backwards (contract sent -> back to presentation)
  - some close dates are edited after the quarter has ended (backdated edits),
    which is why a quarter's win rate can change after it was reported

Seeded, so every number in the readout comes from the same data.
"""
from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 20261121
OUT = Path(__file__).resolve().parent.parent / "seeds"

STAGES = [
    ("appointmentscheduled", "Appointment scheduled", 1, 0.20),
    ("qualifiedtobuy", "Qualified to buy", 2, 0.40),
    ("presentationscheduled", "Presentation scheduled", 3, 0.60),
    ("decisionmakerboughtin", "Decision maker bought in", 4, 0.80),
    ("contractsent", "Contract sent", 5, 0.90),
    ("closedwon", "Closed won", 6, 1.00),
    ("closedlost", "Closed lost", 7, 0.00),
]
OPEN = [s[0] for s in STAGES[:5]]
# Chance an open deal at each stage moves forward rather than being lost.
ADVANCE = {"appointmentscheduled": 0.76, "qualifiedtobuy": 0.74, "presentationscheduled": 0.70, "decisionmakerboughtin": 0.76, "contractsent": 0.80}

START = datetime(2025, 7, 1, tzinfo=timezone.utc)
END = datetime(2026, 11, 10, 23, 59, tzinfo=timezone.utc)
EXPORTED_AT = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)
N_DEALS = 900
N_OWNERS = 6


def iso(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def quarter_end(ts: datetime) -> datetime:
    q_end_month = ((ts.month - 1) // 3 + 1) * 3
    first_next = datetime(ts.year + (q_end_month == 12), (q_end_month % 12) + 1, 1, tzinfo=timezone.utc)
    return first_next - timedelta(seconds=1)


def main() -> None:
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)

    owners = [{"owner_id": str(100 + i), "owner_name": f"Sales rep {chr(65 + i)}", "team": "Sales"} for i in range(N_OWNERS)]
    owner_skill = {o["owner_id"]: rng.uniform(-0.06, 0.06) for o in owners}

    deals, stage_history, closedate_history = [], [], []
    span = (END - START).total_seconds()
    for n in range(N_DEALS):
        deal_id = str(9_000_000 + n)
        owner = rng.choice(owners)["owner_id"]
        created = START + timedelta(seconds=rng.uniform(0, span))
        amount = round(rng.lognormvariate(8.3, 0.7), 2)
        skill = owner_skill[owner]

        t = created
        stage_idx = 0
        stage = OPEN[0]
        stage_history.append({"deal_id": deal_id, "property": "dealstage", "value": stage, "timestamp": iso(t), "source": "CRM_UI"})
        outcome = None
        moved_back = False
        while outcome is None:
            t = t + timedelta(days=rng.uniform(3, 24))
            if t > EXPORTED_AT:
                break
            # Occasionally a deal is pushed back one stage, once.
            if stage_idx >= 3 and not moved_back and rng.random() < 0.10:
                moved_back = True
                stage_idx -= 2
                stage = OPEN[stage_idx]
                stage_history.append({"deal_id": deal_id, "property": "dealstage", "value": stage, "timestamp": iso(t), "source": "CRM_UI"})
                continue
            if rng.random() < ADVANCE[stage] + skill:
                stage_idx += 1
                if stage_idx == len(OPEN):
                    outcome = "closedwon"
                else:
                    stage = OPEN[stage_idx]
                    stage_history.append({"deal_id": deal_id, "property": "dealstage", "value": stage, "timestamp": iso(t), "source": "CRM_UI"})
            else:
                outcome = "closedlost"

        closedate = None
        final_stage = stage
        if outcome is not None:
            closedate = t
            final_stage = outcome
            # Reps often mark a deal closed some days after it really closed: the stage change is
            # logged late, and the close date is backdated to when it closed.
            logged = t + timedelta(days=rng.choice([0, 0, 0, 1, 2, 5]))
            stage_history.append({"deal_id": deal_id, "property": "dealstage", "value": outcome, "timestamp": iso(logged), "source": "CRM_UI"})
            closedate_history.append({"deal_id": deal_id, "property": "closedate", "value": iso(closedate), "timestamp": iso(logged), "source": "CRM_UI"})
            q_end = quarter_end(closedate)
            # Backdated edits: after the quarter was reported, some close dates are corrected.
            if logged <= q_end and rng.random() < 0.09:
                fix_at = q_end + timedelta(days=rng.uniform(3, 30))
                if fix_at < EXPORTED_AT:
                    if outcome == "closedwon" and rng.random() < 0.55:
                        # A win recorded this quarter really signed next quarter.
                        new_close = q_end + timedelta(days=rng.uniform(2, 20))
                    else:
                        # A deal that died earlier is backdated into this quarter.
                        new_close = closedate - timedelta(days=rng.uniform(0, 10))
                    closedate = new_close
                    closedate_history.append({"deal_id": deal_id, "property": "closedate", "value": iso(closedate), "timestamp": iso(fix_at), "source": "CRM_UI"})

        deals.append({
            "hs_object_id": deal_id,
            "dealname": f"Sample deal {n + 1}",
            "pipeline": "default",
            "dealstage": final_stage,
            "amount": f"{amount:.2f}",
            "createdate": iso(created),
            "closedate": iso(closedate) if closedate else "",
            "hubspot_owner_id": owner,
        })

    # Late-logged losses, the other common edit: a quarter's open deals that were really lost in that
    # quarter are only marked lost weeks later, with the close date set back into the quarter.
    by_id = {d["hs_object_id"]: d for d in deals}
    for d in deals:
        if d["dealstage"] != "closedlost":
            continue
        close = datetime.strptime(d["closedate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        q_end = quarter_end(close)
        if rng.random() < 0.10 and q_end + timedelta(days=40) < EXPORTED_AT:
            late = q_end + timedelta(days=rng.uniform(5, 35))
            for row in stage_history:
                if row["deal_id"] == d["hs_object_id"] and row["value"] == "closedlost":
                    row["timestamp"] = iso(late)
            for row in closedate_history:
                if row["deal_id"] == d["hs_object_id"]:
                    row["timestamp"] = iso(late)
    assert len(by_id) == len(deals)

    write(OUT / "hubspot_deals.csv", deals)
    write(OUT / "hubspot_deal_property_history.csv", sorted(stage_history + closedate_history, key=lambda r: (r["deal_id"], r["timestamp"], r["property"])))
    write(OUT / "hubspot_owners.csv", owners)
    write(OUT / "hubspot_pipeline_stages.csv", [{"stage_id": s[0], "label": s[1], "display_order": s[2], "probability": s[3]} for s in STAGES])
    (OUT / "export_meta.csv").write_text(f"exported_at\n{iso(EXPORTED_AT)}\n", encoding="utf-8")
    print(f"deals={len(deals)} history_rows={len(stage_history) + len(closedate_history)} owners={len(owners)}")


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
