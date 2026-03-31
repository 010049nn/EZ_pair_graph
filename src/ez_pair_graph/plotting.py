# Copyright (c) 2025. RIKEN All rights reserved.
# This is for academic and non-commercial research use only.
# The technology is currently under patent application.
# Commercial use is prohibited without a separate license agreement.
# E-mail: akihiro.ezoe@riken.jp

"""Plotting functions for EZ-Pair Graph visualizations."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable, Blues
from scipy import stats as scipy_stats

from ez_pair_graph.preparation import split_by_direction


COPYRIGHT_TEXT = "Copyright (c) 2025. RIKEN All rights reserved."


def _add_copyright(ax):
    """Add copyright text to the bottom of the plot."""
    ax.text(
        0.5,
        -0.08,
        COPYRIGHT_TEXT,
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=7,
        style="italic",
        color="gray",
    )


def _filter_outliers(x, y):
    """Filter outliers using whisker range (Q1 - 1.5*IQR to Q3 + 1.5*IQR)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    q1_x, q3_x = np.percentile(x, [25, 75])
    iqr_x = q3_x - q1_x
    lower_x, upper_x = q1_x - 1.5 * iqr_x, q3_x + 1.5 * iqr_x

    q1_y, q3_y = np.percentile(y, [25, 75])
    iqr_y = q3_y - q1_y
    lower_y, upper_y = q1_y - 1.5 * iqr_y, q3_y + 1.5 * iqr_y

    mask = (x >= lower_x) & (x <= upper_x) & (y >= lower_y) & (y <= upper_y)
    return x[mask], y[mask]


def _apply_log2_transform(x, y):
    """Apply log2 transformation to positive values."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = (x > 0) & (y > 0)
    return np.log2(x[mask]), np.log2(y[mask])


def plot_slopegraph(x, y, ax=None, no_outliers=False, log2=False, show_numbers=False,
                    alpha=0.3, linewidth=0.5):
    """
    Create a slope graph visualization.

    Displays paired data as lines from X to Y positions. Green lines indicate
    ascending values (Y > X), red lines indicate descending values (Y < X).

    Parameters
    ----------
    x : array-like
        Values for the first measurement (X-axis position).
    y : array-like
        Values for the second measurement (Y-axis position).
    ax : matplotlib.axes.Axes, optional
        Axes object to plot on. If None, creates a new figure.
    no_outliers : bool, default=False
        If True, filters outliers using whisker range.
    log2 : bool, default=False
        If True, applies log2 transformation to positive values.
    show_numbers : bool, default=False
        If True, displays numeric values at data points.
    alpha : float, default=0.3
        Transparency of lines.
    linewidth : float, default=0.5
        Width of lines.

    Returns
    -------
    tuple
        (fig, ax) - matplotlib figure and axes objects.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if log2:
        x, y = _apply_log2_transform(x, y)
    if no_outliers:
        x, y = _filter_outliers(x, y)

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))
    else:
        fig = ax.get_figure()

    # Split by direction
    diffs = y - x
    asc_mask = diffs >= 0
    desc_mask = diffs < 0

    x_asc, y_asc = x[asc_mask], y[asc_mask]
    x_desc, y_desc = x[desc_mask], y[desc_mask]

    # Plot ascending lines (green)
    for xi, yi in zip(x_asc, y_asc):
        ax.plot([0, 1], [xi, yi], color="green", alpha=alpha, linewidth=linewidth)
        if show_numbers:
            ax.text(0, xi, f"{xi:.1f}", fontsize=7, ha="right")
            ax.text(1, yi, f"{yi:.1f}", fontsize=7, ha="left")

    # Plot descending lines (red)
    for xi, yi in zip(x_desc, y_desc):
        ax.plot([0, 1], [xi, yi], color="red", alpha=alpha, linewidth=linewidth)
        if show_numbers:
            ax.text(0, xi, f"{xi:.1f}", fontsize=7, ha="right")
            ax.text(1, yi, f"{yi:.1f}", fontsize=7, ha="left")

    ax.set_xlim(-0.1, 1.1)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["X", "Y"])
    ax.set_ylabel("Value")
    ax.set_title("Slope Graph")
    ax.grid(True, alpha=0.3)

    _add_copyright(ax)
    fig.tight_layout()

    return fig, ax


def plot_trapezoid(x, y, ax=None, no_outliers=False, log2=False, show_numbers=False):
    """
    Create a trapezoid plot visualization.

    Splits data into ascending and descending groups, calculates quartiles of
    starting positions and differences, and draws trapezoid bands with Q2 lines.

    Parameters
    ----------
    x : array-like
        Values for the first measurement.
    y : array-like
        Values for the second measurement.
    ax : matplotlib.axes.Axes, optional
        Axes object to plot on. If None, creates a new figure.
    no_outliers : bool, default=False
        If True, filters outliers using whisker range.
    log2 : bool, default=False
        If True, applies log2 transformation to positive values.
    show_numbers : bool, default=False
        If True, displays numeric values.

    Returns
    -------
    tuple
        (fig, ax) - matplotlib figure and axes objects.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if log2:
        x, y = _apply_log2_transform(x, y)
    if no_outliers:
        x, y = _filter_outliers(x, y)

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))
    else:
        fig = ax.get_figure()

    data = np.column_stack([x, y])

    # Split by direction
    pos_indices, neg_indices = split_by_direction(data)
    pos_data = data[pos_indices] if pos_indices else np.array([])
    neg_data = data[neg_indices] if neg_indices else np.array([])

    def _draw_trapezoid_group(group_data, color, x_pos_start, x_pos_end):
        """Draw trapezoid bands for a group (ascending or descending)."""
        if len(group_data) == 0:
            return

        sorted_by_x = sorted(group_data, key=lambda item: item[0], reverse=True)
        sorted_by_diff = sorted(group_data, key=lambda item: item[1] - item[0], reverse=True)

        m = len(group_data)
        q1_idx = int(m / 4)
        q2_idx = int(m / 2)
        q3_idx = int(m * 3 / 4)

        q1_start = sorted_by_x[q1_idx][0]
        q1_diff = sorted_by_diff[q1_idx][1] - sorted_by_diff[q1_idx][0]

        q2_start = sorted_by_x[q2_idx][0]
        q2_diff = sorted_by_diff[q2_idx][1] - sorted_by_diff[q2_idx][0]

        q3_start = sorted_by_x[q3_idx][0]
        q3_diff = sorted_by_diff[q3_idx][1] - sorted_by_diff[q3_idx][0]

        # Draw Q1-Q3 trapezoid band
        x_coords = [x_pos_start, x_pos_end, x_pos_end, x_pos_start, x_pos_start]
        y_coords = [q1_start, q1_start + q1_diff, q3_start + q3_diff, q3_start, q1_start]
        ax.fill(x_coords, y_coords, alpha=0.2, color=color)
        ax.plot(x_coords, y_coords, color=color, linewidth=0.5, alpha=0.5)

        # Draw Q2 line with width proportional to group size
        line_width = max(0.5, min(3, m / 10))
        ax.plot([x_pos_start, x_pos_end], [q2_start, q2_start + q2_diff],
                color=color, linewidth=line_width, alpha=0.8)

    # Draw ascending group (green)
    if len(pos_data) > 0:
        _draw_trapezoid_group(pos_data.tolist(), "green", 0, 1)

    # Draw descending group (red)
    if len(neg_data) > 0:
        _draw_trapezoid_group(neg_data.tolist(), "red", 0, 1)

    ax.set_xlim(-0.1, 1.1)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["X", "Y"])
    ax.set_ylabel("Value")
    ax.set_title("Trapezoid Plot")
    ax.grid(True, alpha=0.3)

    _add_copyright(ax)
    fig.tight_layout()

    return fig, ax


def plot_clustered_lines(x, y, clusters, stats, ax=None, no_outliers=False,
                         log2=False, show_numbers=False):
    """
    Create a clustered line plot with half-boxplots and summary lines.

    Displays cluster patterns with half-boxplots on left (X) and right (Y) sides,
    with summary lines connecting cluster medians. Coloring based on cluster size.

    Parameters
    ----------
    x : array-like
        Values for the first measurement.
    y : array-like
        Values for the second measurement.
    clusters : array-like
        Cluster assignments for each data point.
    stats : dict
        Pre-computed statistics from compute_statistics().
    ax : matplotlib.axes.Axes, optional
        Axes object to plot on. If None, creates a new figure.
    no_outliers : bool, default=False
        If True, filters outliers using whisker range.
    log2 : bool, default=False
        If True, applies log2 transformation to positive values.
    show_numbers : bool, default=False
        If True, displays numeric values.

    Returns
    -------
    tuple
        (fig, ax) - matplotlib figure and axes objects.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    clusters = np.asarray(clusters, dtype=int)

    if log2:
        x, y = _apply_log2_transform(x, y)
    if no_outliers:
        x, y = _filter_outliers(x, y)

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))
    else:
        fig = ax.get_figure()

    # Normalize cluster sizes for coloring
    cluster_sizes = [stats[c]["calculated"]["n"] for c in sorted(stats.keys())]
    size_norm = Normalize(vmin=min(cluster_sizes), vmax=max(cluster_sizes))
    cmap = Blues

    x_pos = 0
    y_pos = 1

    # Draw half-boxplots and summary lines
    for cluster_id in sorted(stats.keys()):
        cluster_mask = clusters == cluster_id
        x_vals = x[cluster_mask]
        y_vals = y[cluster_mask]

        stat = stats[cluster_id]
        n = stat["calculated"]["n"]
        color = cmap(size_norm(n))

        if len(x_vals) > 0:
            # Half-boxplot on left (X side)
            q1_x, med_x, q3_x = stat["x"]["q1"], stat["x"]["q2"], stat["x"]["q3"]
            ax.plot([x_pos - 0.1, x_pos], [med_x, med_x], color=color, linewidth=2)
            ax.plot([x_pos - 0.05, x_pos - 0.05], [q1_x, q3_x], color=color, linewidth=1)
            ax.plot([x_pos - 0.1, x_pos], [q1_x, q1_x], color=color, linewidth=0.5)
            ax.plot([x_pos - 0.1, x_pos], [q3_x, q3_x], color=color, linewidth=0.5)

            # Half-boxplot on right (Y side)
            q1_y, med_y, q3_y = stat["y"]["q1"], stat["y"]["q2"], stat["y"]["q3"]
            ax.plot([y_pos, y_pos + 0.1], [med_y, med_y], color=color, linewidth=2)
            ax.plot([y_pos + 0.05, y_pos + 0.05], [q1_y, q3_y], color=color, linewidth=1)
            ax.plot([y_pos, y_pos + 0.1], [q1_y, q1_y], color=color, linewidth=0.5)
            ax.plot([y_pos, y_pos + 0.1], [q3_y, q3_y], color=color, linewidth=0.5)

            # Summary line from X to Y
            q2_start = stat["calculated"]["q2_start"]
            q2_diff = stat["calculated"]["q2_diff"]
            ax.plot([x_pos, y_pos], [q2_start, q2_start + q2_diff],
                    color=color, linewidth=2, alpha=0.7)

    ax.set_xlim(-0.2, 1.2)
    ax.set_xticks([x_pos, y_pos])
    ax.set_xticklabels(["X", "Y"])
    ax.set_ylabel("Value")
    ax.set_title("Clustered Lines")
    ax.grid(True, alpha=0.3, axis="y")

    _add_copyright(ax)
    fig.tight_layout()

    return fig, ax


def plot_parallel_arrows(x, y, clusters, stats, ax=None, no_outliers=False,
                         log2=False, show_numbers=False):
    """
    Create a parallel arrow plot showing cluster changes.

    Displays half-boxplots with arrows indicating the median change for each cluster.
    Ascending clusters shown on left, descending on right.

    Parameters
    ----------
    x : array-like
        Values for the first measurement.
    y : array-like
        Values for the second measurement.
    clusters : array-like
        Cluster assignments for each data point.
    stats : dict
        Pre-computed statistics from compute_statistics().
    ax : matplotlib.axes.Axes, optional
        Axes object to plot on. If None, creates a new figure.
    no_outliers : bool, default=False
        If True, filters outliers using whisker range.
    log2 : bool, default=False
        If True, applies log2 transformation to positive values.
    show_numbers : bool, default=False
        If True, displays numeric values.

    Returns
    -------
    tuple
        (fig, ax) - matplotlib figure and axes objects.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    clusters = np.asarray(clusters, dtype=int)

    if log2:
        x, y = _apply_log2_transform(x, y)
    if no_outliers:
        x, y = _filter_outliers(x, y)

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))
    else:
        fig = ax.get_figure()

    # Normalize cluster sizes for coloring
    cluster_sizes = [stats[c]["calculated"]["n"] for c in sorted(stats.keys())]
    size_norm = Normalize(vmin=min(cluster_sizes), vmax=max(cluster_sizes))
    cmap = Blues

    x_pos = 0
    y_pos = 1

    # Determine ascending/descending clusters
    asc_clusters = []
    desc_clusters = []
    for cluster_id in sorted(stats.keys()):
        q2_diff = stats[cluster_id]["calculated"]["q2_diff"]
        if q2_diff >= 0:
            asc_clusters.append(cluster_id)
        else:
            desc_clusters.append(cluster_id)

    # Draw half-boxplots
    all_clusters = sorted(stats.keys())
    for cluster_id in all_clusters:
        stat = stats[cluster_id]
        n = stat["calculated"]["n"]
        color = cmap(size_norm(n))

        # Half-boxplot on left (X side)
        q1_x, med_x, q3_x = stat["x"]["q1"], stat["x"]["q2"], stat["x"]["q3"]
        ax.plot([x_pos - 0.1, x_pos], [med_x, med_x], color=color, linewidth=2)
        ax.plot([x_pos - 0.05, x_pos - 0.05], [q1_x, q3_x], color=color, linewidth=1)

        # Half-boxplot on right (Y side)
        q1_y, med_y, q3_y = stat["y"]["q1"], stat["y"]["q2"], stat["y"]["q3"]
        ax.plot([y_pos, y_pos + 0.1], [med_y, med_y], color=color, linewidth=2)
        ax.plot([y_pos + 0.05, y_pos + 0.05], [q1_y, q3_y], color=color, linewidth=1)

    # Draw arrows
    arrow_offset = 0.05
    for idx, cluster_id in enumerate(asc_clusters):
        stat = stats[cluster_id]
        n = stat["calculated"]["n"]
        color = cmap(size_norm(n))
        q2_start = stat["calculated"]["q2_start"]
        q2_diff = stat["calculated"]["q2_diff"]
        arrow_width = max(0.01, min(0.1, n / 50))
        mid_pos = 0.3 - idx * arrow_offset

        ax.arrow(mid_pos, q2_start, 0, q2_diff, head_width=0.05, head_length=abs(q2_diff) * 0.1,
                fc=color, ec=color, linewidth=arrow_width, alpha=0.7)

    for idx, cluster_id in enumerate(desc_clusters):
        stat = stats[cluster_id]
        n = stat["calculated"]["n"]
        color = cmap(size_norm(n))
        q2_start = stat["calculated"]["q2_start"]
        q2_diff = stat["calculated"]["q2_diff"]
        arrow_width = max(0.01, min(0.1, n / 50))
        mid_pos = 0.7 + idx * arrow_offset

        ax.arrow(mid_pos, q2_start, 0, q2_diff, head_width=0.05, head_length=abs(q2_diff) * 0.1,
                fc=color, ec=color, linewidth=arrow_width, alpha=0.7)

    ax.set_xlim(-0.2, 1.2)
    ax.set_xticks([x_pos, y_pos])
    ax.set_xticklabels(["X", "Y"])
    ax.set_ylabel("Value")
    ax.set_title("Parallel Arrows")
    ax.grid(True, alpha=0.3, axis="y")

    _add_copyright(ax)
    fig.tight_layout()

    return fig, ax
