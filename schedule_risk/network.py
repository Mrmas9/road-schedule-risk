"""Activity network and a vectorised critical path forward pass.

Each column of the duration matrix is one activity and each row is one
Monte Carlo iteration, so one pass over the activities schedules every
iteration at the same time.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Link:
    """A precedence link between two activities.

    kind="FS": the successor starts when the predecessor finishes.
    kind="SS": the successor starts once (1 - overlap) of the predecessor is
    done, and it cannot finish before the predecessor finishes.
    """

    pred: int
    succ: int
    kind: str = "FS"
    overlap: float = 0.0


def load_activities(path):
    df = pd.read_csv(path, dtype={"predecessors": str})
    df["predecessors"] = df["predecessors"].fillna("")
    return df


def links_from_table(df):
    """Finish-to-start links from the 'predecessors' column (ids separated by ';')."""
    links = []
    for row in df.itertuples():
        for pred in filter(None, str(row.predecessors).split(";")):
            links.append(Link(int(pred), int(row.id)))
    return links


def topological_order(ids, links):
    """Order activities so that every predecessor comes before its successors."""
    waiting = {act: 0 for act in ids}
    after = {act: [] for act in ids}
    for link in links:
        waiting[link.succ] += 1
        after[link.pred].append(link.succ)

    ready = [act for act in ids if waiting[act] == 0]
    order = []
    while ready:
        act = ready.pop(0)
        order.append(act)
        for nxt in after[act]:
            waiting[nxt] -= 1
            if waiting[nxt] == 0:
                ready.append(nxt)

    if len(order) != len(ids):
        raise ValueError("The network contains a loop.")
    return order


def forward_pass(durations, ids, links):
    """Early start and early finish of every activity in every iteration.

    durations has shape (iterations, activities), with columns in the order of ids.
    Returns (start, finish), both with the same shape.
    """
    col = {act: k for k, act in enumerate(ids)}
    into = {act: [] for act in ids}
    for link in links:
        into[link.succ].append(link)

    n = durations.shape[0]
    start = np.zeros(durations.shape)
    finish = np.zeros(durations.shape)

    for act in topological_order(ids, links):
        j = col[act]
        earliest = np.zeros(n)
        must_finish_after = np.zeros(n)
        for link in into[act]:
            i = col[link.pred]
            if link.kind == "FS":
                earliest = np.maximum(earliest, finish[:, i])
            elif link.kind == "SS":
                lag = (1.0 - link.overlap) * durations[:, i]
                earliest = np.maximum(earliest, start[:, i] + lag)
                must_finish_after = np.maximum(must_finish_after, finish[:, i])
            else:
                raise ValueError(f"Unknown link type: {link.kind!r}")
        start[:, j] = earliest
        finish[:, j] = np.maximum(earliest + durations[:, j], must_finish_after)

    return start, finish


def project_duration(durations, ids, links):
    """Finish day of the whole project for each iteration."""
    _, finish = forward_pass(durations, ids, links)
    return finish.max(axis=1)
