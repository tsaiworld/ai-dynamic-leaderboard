#!/usr/bin/env python3

"""
Recompute rankings and regenerate data/ai_dashboard.json using the weighting:
Popularity 40%, Performance 25%, Cost 10%, Privacy 10%, Innovation 15%

- Reads existing JSON
- Recalculates total scores
- Sorts and truncates top 3 per category
- Updates meta.last_updated
"""
import json, sys, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "ai_dashboard.json"

def weighted_total(s, w):
    return (
        s["popularity"]*w["popularity"] +
        s["performance"]*w["performance"] +
        s["cost"]*w["cost"] +
        s["privacy"]*w["privacy"] +
        s["innovation"]*w["innovation"]
    )

def main():
    with open(DATA) as f:
        data = json.load(f)

    w = data["meta"]["weights"]
    for cat in data["categories"]:
        for e in cat["entries"]:
            e["total"] = round(weighted_total(e["scores"], w), 2)
        # Keep all entries but compute a "top3" view (UI slices to 3 already)
        cat["entries"].sort(key=lambda x: x["total"], reverse=True)

    data["meta"]["last_updated"] = datetime.date.today().isoformat()

    with open(DATA, "w") as f:
        json.dump(data, f, indent=2)

    print("Updated leaderboard totals and ordering.")

if __name__ == "__main__":
    sys.exit(main())
