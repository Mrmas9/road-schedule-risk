"""Run every scenario and write the tables and figures to results/.

Usage:
    python run_model.py
    python run_model.py --iterations 50000 --seed 7 --dist pert --out results/pert
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from schedule_risk import analysis, plots, scenarios
from schedule_risk.network import links_from_table, load_activities, project_duration
from schedule_risk.sampling import SAMPLERS

ROOT = Path(__file__).resolve().parent


def build_scenarios():
    S = scenarios.Scenario
    ft = scenarios.OVERLAPS
    return [
        S("Baseline"),
        S("Crashing (5 activities)", crash=scenarios.CRASH_ALL),
        S("Crashing (site works only)", crash=scenarios.CRASH_SITE),
        S("Fast-tracking, 20% rework", overlaps=ft, rework_probability=0.20),
        S("Fast-tracking, 35% rework", overlaps=ft, rework_probability=0.35),
        S("Fast-tracking, 50% rework", overlaps=ft, rework_probability=0.50),
        S("Crashing + fast-tracking (35% rework)", crash=scenarios.CRASH_ALL,
          overlaps=ft, rework_probability=0.35),
    ]


def main():
    parser = argparse.ArgumentParser(description="Schedule risk model for a UK road scheme")
    parser.add_argument("--iterations", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--dist", choices=sorted(SAMPLERS), default="triangular")
    parser.add_argument("--out", default="results")
    args = parser.parse_args()

    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)

    acts = load_activities(ROOT / "data" / "activities.csv")
    ids = list(acts["id"])
    names = list(acts["name"])
    links = links_from_table(acts)
    low, mode, high = (acts[c].to_numpy(dtype=float) for c in ("min", "mode", "max"))

    rng = np.random.default_rng(args.seed)
    durations = SAMPLERS[args.dist](rng, low, mode, high, args.iterations)
    rework_draws = rng.random((args.iterations, len(scenarios.OVERLAPS)))

    # the single-point plan: every activity at its most likely duration
    plan = float(project_duration(mode[None, :], ids, links)[0])

    rows, totals = [], {}
    for sc in build_scenarios():
        d, sc_links, cost = scenarios.apply(sc, acts, links, durations, rework_draws)
        totals[sc.name] = project_duration(d, ids, sc_links)
        base = rows[0] if rows else None
        rows.append(analysis.summary_row(
            sc.name, totals[sc.name], cost,
            baseline_p50=np.percentile(totals["Baseline"], 50) if base else None,
            baseline_cost=scenarios.base_cost(acts) if base else None,
        ))

    summary = pd.DataFrame(rows)
    summary.to_csv(out / "summary.csv", index=False)

    baseline = totals["Baseline"]
    sens = analysis.spearman(durations, baseline, names)
    sens.round(3).to_csv(out / "sensitivity.csv", index=False)

    for theme in ("light", "dark"):
        plots.histogram(baseline, out / f"histogram_{theme}.png", theme, plan=plan)
        plots.s_curves(
            [("Baseline", baseline),
             ("Crashing (5 activities)", totals["Crashing (5 activities)"]),
             ("Fast-tracking, 35% rework", totals["Fast-tracking, 35% rework"])],
            out / f"s_curves_{theme}.png", theme)
        plots.tornado(sens, out / f"tornado_{theme}.png", theme)

    pd.set_option("display.width", 160)
    print(f"{args.iterations:,} iterations, seed {args.seed}, {args.dist} durations\n")
    print(summary.to_string(index=False))
    print(f"\nPlan at most likely durations: {plan:,.0f} days")
    print(f"Chance of meeting that plan: {analysis.chance_of_finishing_by(baseline, plan):.1%}")
    print("\nTop drivers of the spread (Spearman rho):")
    print(sens.head(8).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
