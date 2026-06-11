# ATTENDANCE ZONE CLASSIFIER AGENT 🕘
# Reads checkin times for all people across all days.
# SAFE ZONE   → checked in at or before 09:30
# DANGER ZONE → checked in after 09:30
# Produces a summary CSV report with per-person stats.

import os
import pandas as pd
from datetime import datetime, time

# ───────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────
CSV_PATH    = "attendance_2023_2024.csv"   # input file
REPORT_PATH = "attendance_status_report.csv"             # output file
CUTOFF      = time(9, 30)                                # 09:30 is still SAFE

# ───────────────────────────────────────────
# HELPER: classify a single cell
# Cell format: "HH:MM-HH:MM"  (checkin-checkout)
# ───────────────────────────────────────────
def classify_cell(cell):
    """
    Extract the checkin time from a cell and return its zone.

    Returns:
        checkin_str (str)  : e.g. "09:15"
        status      (str)  : "SAFE ZONE" | "DANGER ZONE" | "UNKNOWN"
    """
    try:
        checkin_str = str(cell).split("-")[0].strip()
        checkin     = datetime.strptime(checkin_str, "%H:%M").time()
        if checkin <= CUTOFF:
            return checkin_str, "SAFE ZONE"
        else:
            return checkin_str, "DANGER ZONE"
    except Exception:
        return "N/A", "UNKNOWN"

# ───────────────────────────────────────────
# AGENT LOGIC
# ───────────────────────────────────────────
def run_agent():
    print("=" * 55)
    print("  ATTENDANCE ZONE CLASSIFIER AGENT")
    print(f"  Cutoff: on or before {CUTOFF.strftime('%H:%M')} → ✅ SAFE ZONE")
    print(f"         after {CUTOFF.strftime('%H:%M')} → 🚨 DANGER ZONE")
    print("=" * 55)

    # ── Load CSV ──────────────────────────────────────────
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: File not found → {CSV_PATH}")
        return

    df          = pd.read_csv(CSV_PATH)
    person_cols = [c for c in df.columns if c.startswith("Person_")]
    total_days  = len(df)

    print(f"\n📂 Loaded: {CSV_PATH}")
    print(f"   People : {len(person_cols)}")
    print(f"   Days   : {total_days}")
    print(f"\n⏳ Analysing...\n")

    # ── Process each person ───────────────────────────────
    records = []
    for person in person_cols:
        safe   = 0
        danger = 0
        unknown = 0
        earliest = "23:59"
        latest   = "00:00"

        for _, row in df.iterrows():
            checkin_str, status = classify_cell(row[person])

            if status == "SAFE ZONE":
                safe += 1
            elif status == "DANGER ZONE":
                danger += 1
            else:
                unknown += 1

            # Track earliest / latest checkin for this person
            if checkin_str not in ("N/A",):
                if checkin_str < earliest:
                    earliest = checkin_str
                if checkin_str > latest:
                    latest = checkin_str

        total    = safe + danger + unknown
        late_pct = round(danger / (safe + danger) * 100, 1) if (safe + danger) > 0 else 0

        # Overall status = majority wins
        if safe >= danger:
            overall_status = "SAFE ZONE"
        else:
            overall_status = "DANGER ZONE"

        records.append({
            "Person"          : person,
            "Total Days"      : total,
            "Safe Days"       : safe,
            "Danger Days"     : danger,
            "Unknown Days"    : unknown,
            "Late %"          : f"{late_pct}%",
            "Earliest Checkin": earliest,
            "Latest Checkin"  : latest,
            "Overall Status"  : overall_status,
        })

    # ── Build summary DataFrame ───────────────────────────
    summary_df = pd.DataFrame(records)

    # ── Console report ────────────────────────────────────
    safe_count   = (summary_df["Overall Status"] == "SAFE ZONE").sum()
    danger_count = (summary_df["Overall Status"] == "DANGER ZONE").sum()

    print("─" * 55)
    print("  OVERALL SUMMARY")
    print("─" * 55)
    print(f"  ✅ SAFE ZONE   : {safe_count} people")
    print(f"  🚨 DANGER ZONE : {danger_count} people")
    print("─" * 55)

    # Top 10 most punctual (fewest late days)
    print("\n🏆 Top 10 most punctual (fewest late days):")
    top10 = summary_df.nsmallest(10, "Danger Days")[["Person", "Danger Days", "Late %"]]
    print(top10.to_string(index=False))

    # Top 10 most late
    print("\n⚠️  Top 10 most late arrivals:")
    late10 = summary_df.nlargest(10, "Danger Days")[["Person", "Danger Days", "Late %", "Latest Checkin"]]
    print(late10.to_string(index=False))

    # ── Save report ───────────────────────────────────────
    summary_df.to_csv(REPORT_PATH, index=False)
    print(f"\n✅ Report saved → {REPORT_PATH}")
    print(f"   {len(summary_df)} rows × {len(summary_df.columns)} columns")

# ───────────────────────────────────────────
# ENTRY POINT
# ───────────────────────────────────────────
if __name__ == "__main__":
    run_agent()