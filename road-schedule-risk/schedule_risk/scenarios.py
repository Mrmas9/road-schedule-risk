"""The schedule recovery strategies compared in the model.

Assumptions carried over from the MSc dissertation:
- every activity-day costs £15,000 (direct cost), so the baseline cost is
  £15,000 x the sum of most likely durations;
- an activity can be crashed by up to 25% of its most likely duration, and
  crashing it fully costs 50% more than its normal cost;
- fast-tracking starts the successor halfway through its predecessor, and
  with some probability the overlap causes rework that adds 40% to the
  successor's duration.
"""

import math
from dataclasses import dataclass, field

import numpy as np

from .network import Link

COST_PER_DAY = 15_000
CRASH_SHARE = 0.25
CRASH_PREMIUM = 0.50
OVERLAP = 0.50
REWORK_PENALTY = 0.40

# DCO review, bulk excavation, precast bridge beams, granular sub-base, asphalt base course
CRASH_ALL = [2, 22, 33, 39, 41]
# the same list without the consent stage
CRASH_SITE = [22, 33, 39, 41]
# (predecessor, successor): bulk excavation -> embankment, piling -> pile caps,
# kerbs and edging -> asphalt base course
OVERLAPS = [(22, 23), (30, 31), (40, 41)]


@dataclass
class Scenario:
    name: str
    crash: list = field(default_factory=list)
    overlaps: list = field(default_factory=list)
    rework_probability: float = 0.0


def round_half_up(x):
    return int(math.floor(x + 0.5))


def crash_days(activities, crashed):
    mode = dict(zip(activities["id"], activities["mode"]))
    return {act: round_half_up(CRASH_SHARE * mode[act]) for act in crashed}


def crash_premium(activities, crashed):
    mode = dict(zip(activities["id"], activities["mode"]))
    return sum(CRASH_PREMIUM * COST_PER_DAY * mode[act] for act in crashed)


def base_cost(activities):
    return COST_PER_DAY * float(activities["mode"].sum())


def apply(scenario, activities, links, durations, rework_draws):
    """Durations, links and direct cost for one scenario.

    durations and rework_draws are shared by every scenario (common random
    numbers), so two scenarios differ only by the strategy applied to them.
    """
    ids = list(activities["id"])
    col = {act: k for k, act in enumerate(ids)}
    d = durations.copy()

    for act, days in crash_days(activities, scenario.crash).items():
        d[:, col[act]] = np.maximum(d[:, col[act]] - days, 0.0)

    new_links = list(links)
    for k, (pred, succ) in enumerate(scenario.overlaps):
        new_links = [l for l in new_links if not (l.pred == pred and l.succ == succ)]
        new_links.append(Link(pred, succ, "SS", OVERLAP))
        rework = rework_draws[:, k] < scenario.rework_probability
        d[rework, col[succ]] *= 1 + REWORK_PENALTY

    cost = base_cost(activities) + crash_premium(activities, scenario.crash)
    return d, new_links, cost
