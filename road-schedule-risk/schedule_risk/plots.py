"""Figures for the README, drawn in a light and a dark version."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import FuncFormatter, PercentFormatter  # noqa: E402

THEMES = {
    "light": {
        "surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781",
        "grid": "#e1e0d9", "axis": "#c3c2b7",
        "series": ["#2a78d6", "#eb6834", "#1baf7a"],
    },
    "dark": {
        "surface": "#1a1a19", "ink": "#f0efec", "ink2": "#c3c2b7", "muted": "#898781",
        "grid": "#2c2c2a", "axis": "#383835",
        "series": ["#3987e5", "#d95926", "#199e70"],
    },
}

THOUSANDS = FuncFormatter(lambda x, _: f"{x:,.0f}")


def _figure(theme):
    t = THEMES[theme]
    fig, ax = plt.subplots(figsize=(8, 4.4), dpi=160)
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(t["axis"])
    ax.tick_params(colors=t["muted"], length=0, labelsize=9)
    ax.set_axisbelow(True)
    return fig, ax, t


def _finish(fig, ax, t, title, xlabel, ylabel, path):
    ax.set_title(title, loc="left", fontsize=12, color=t["ink"], pad=12)
    ax.set_xlabel(xlabel, color=t["ink2"], fontsize=10)
    ax.set_ylabel(ylabel, color=t["ink2"], fontsize=10)
    fig.tight_layout()
    fig.savefig(path, facecolor=t["surface"])
    plt.close(fig)


def histogram(totals, path, theme="light", plan=None):
    """Spread of the baseline finish, with P10/P50/P90 and, if given, the single-point plan."""
    fig, ax, t = _figure(theme)
    ax.grid(axis="y", color=t["grid"], linewidth=0.8)
    ax.hist(totals, bins=45, color=t["series"][0], rwidth=0.82)
    top = ax.get_ylim()[1]
    marks = [(np.percentile(totals, q), label) for q, label in ((10, "P10"), (50, "P50"), (90, "P90"))]
    if plan is not None:
        marks.insert(0, (plan, "Plan"))
        ax.set_xlim(left=min(plan, totals.min()) - 25)
    for value, label in marks:
        ax.axvline(value, color=t["ink2"], linewidth=1)
        ax.text(value, top * 0.985, f" {label} {value:,.0f}", color=t["ink2"], va="top", fontsize=9)
    ax.xaxis.set_major_formatter(THOUSANDS)
    ax.yaxis.set_major_formatter(THOUSANDS)
    _finish(fig, ax, t, "Baseline: how long the project could take",
            "Project duration (days)", "Iterations", path)


def s_curves(curves, path, theme="light"):
    """curves: list of (label, totals), at most three, always in the same order."""
    fig, ax, t = _figure(theme)
    ax.grid(axis="both", color=t["grid"], linewidth=0.8)
    for (label, totals), colour in zip(curves, t["series"]):
        x = np.sort(totals)
        y = np.arange(1, len(x) + 1) / len(x)
        p50 = np.percentile(totals, 50)
        ax.plot(x, y, color=colour, linewidth=2, solid_capstyle="round",
                label=f"{label}  (P50 {p50:,.0f} days)")
        ax.plot([p50], [0.5], marker="o", markersize=8, color=colour,
                markeredgecolor=t["surface"], markeredgewidth=2)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.xaxis.set_major_formatter(THOUSANDS)
    legend = ax.legend(frameon=False, loc="lower right", fontsize=9)
    for text in legend.get_texts():
        text.set_color(t["ink2"])
    _finish(fig, ax, t, "Chance of finishing by a given day",
            "Project duration (days)", "Probability", path)


def tornado(sensitivity, path, theme="light", top=8):
    fig, ax, t = _figure(theme)
    ax.grid(axis="x", color=t["grid"], linewidth=0.8)
    data = sensitivity.head(top).iloc[::-1]
    bars = ax.barh(data["activity"], data["rho"], height=0.32, color=t["series"][0])
    for bar, value in zip(bars, data["rho"]):
        ax.text(bar.get_width() + 0.012, bar.get_y() + bar.get_height() / 2,
                f"{value:.2f}", va="center", color=t["ink2"], fontsize=9)
    ax.set_xlim(0, float(data["rho"].max()) * 1.15)
    ax.tick_params(axis="y", colors=t["ink2"], labelsize=9)
    _finish(fig, ax, t, "What drives the spread in project duration",
            "Spearman rank correlation with project duration", "", path)
