"""Summary statistics and sensitivity."""

import numpy as np
import pandas as pd


def summary_row(name, totals, cost, baseline_p50=None, baseline_cost=None):
    p10, p50, p90 = np.percentile(totals, [10, 50, 90])
    row = {
        "scenario": name,
        "P10": round(p10),
        "P50": round(p50),
        "P90": round(p90),
        "mean": round(float(totals.mean()), 1),
        "sd": round(float(totals.std()), 1),
        "direct_cost_gbp_m": round(cost / 1e6, 3),
    }
    if baseline_p50 is None:
        row["days_saved_at_P50"] = 0
        row["premium_per_day_saved_gbp"] = 0
    else:
        saved = baseline_p50 - p50
        extra = cost - baseline_cost
        row["days_saved_at_P50"] = int(round(saved))
        row["premium_per_day_saved_gbp"] = int(round(extra / saved)) if extra > 0 and saved > 0 else 0
    return row


def spearman(durations, totals, names):
    """Rank correlation between each activity's duration and the project duration."""
    ranks = pd.DataFrame(durations).rank()
    total_ranks = pd.Series(totals).rank()
    rho = ranks.corrwith(total_ranks)
    out = pd.DataFrame({"activity": names, "rho": rho.to_numpy()})
    return out.sort_values("rho", ascending=False, ignore_index=True)


def chance_of_finishing_by(totals, day):
    return float((totals <= day).mean())
