# Copyright (c) 2025. RIKEN All rights reserved.
# This is for academic and non-commercial research use only.
# The technology is currently under patent application.
# Commercial use is prohibited without a separate license agreement.
# E-mail: akihiro.ezoe@riken.jp

"""
Plotting functions for EZ-Pair Graph.
Replicates the exact rendering from slopegraph.py, clustered_line_plot.py,
parallel_arrow_plot.py, and trapezoid_plot.py.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle, Polygon
from matplotlib.colors import LinearSegmentedColormap

from .preparation import apply_log2_transform, compute_statistics

COPYRIGHT_TEXT = (
    "Copyright (c) 2025. RIKEN All rights reserved. "
    "This is for academic and non-commercial research use only.\n"
    "The technology is currently under patent application. "
    "Commercial use is prohibited without a separate license agreement. "
    "E-mail: akihiro.ezoe@riken.jp"
)

# Docker parallel_arrow_plot.py has a triple-quoted string where "akihiro"
# is split across lines, producing a 3-line copyright notice.  We replicate
# the exact same string so that bbox_inches='tight' yields identical output.
_COPYRIGHT_TEXT_ARROW = (
    "Copyright (c) 2025. RIKEN All rights reserved. "
    "This is for academic and non-commercial research use only.\n"
    "The technology is currently under patent application. "
    "Commercial use is prohibited without a separate license agreement. "
    "E-mail: akihi\nro.ezoe@riken.jp"
)


def _create_truncated_colormap(cmap_name, vmin=0.3, vmax=1.0):
    cmap = plt.get_cmap(cmap_name)
    colors = cmap(np.linspace(vmin, vmax, 256))
    return LinearSegmentedColormap.from_list(f'trunc_{cmap_name}', colors)


# ---------------------------------------------------------------------------
# Half-boxplot drawing (shared by clustered_line_plot and parallel_arrow_plot)
# ---------------------------------------------------------------------------

def _draw_half_boxplot_clustered(ax, data, position, width, side='left',
                                  facecolor='lightgray', edgecolor='gray',
                                  alpha=0.7, show_outliers=True):
    """Half-boxplot as used in clustered_line_plot.py."""
    data = np.array(data)
    q1 = np.percentile(data, 25)
    median = np.percentile(data, 50)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    lower_whisker = q1 - 1.5 * iqr
    upper_whisker = q3 + 1.5 * iqr
    whisker_min = data[data >= lower_whisker].min()
    whisker_max = data[data <= upper_whisker].max()
    outliers = data[(data < lower_whisker) | (data > upper_whisker)]
    half_width = width / 2

    if side == 'left':
        box_left = position - half_width
        box_right = position
    else:
        box_left = position
        box_right = position + half_width

    box = Rectangle(
        (box_left, q1), box_right - box_left, q3 - q1,
        facecolor=facecolor, edgecolor=edgecolor, alpha=alpha,
        linewidth=1, zorder=1
    )
    ax.add_patch(box)
    ax.plot([box_left, box_right], [median, median],
            color=edgecolor, linewidth=1.5, zorder=2)

    cap_width = half_width * 0.4
    if side == 'left':
        cap_left = position - cap_width
        cap_right = position
    else:
        cap_left = position
        cap_right = position + cap_width

    ax.plot([position, position], [whisker_min, q1],
            color=edgecolor, linewidth=1, zorder=1)
    ax.plot([cap_left, cap_right], [whisker_min, whisker_min],
            color=edgecolor, linewidth=1, zorder=1)
    ax.plot([position, position], [q3, whisker_max],
            color=edgecolor, linewidth=1, zorder=1)
    ax.plot([cap_left, cap_right], [whisker_max, whisker_max],
            color=edgecolor, linewidth=1, zorder=1)

    if show_outliers and len(outliers) > 0:
        ax.scatter([position] * len(outliers), outliers,
                   color=edgecolor, marker='o', s=20,
                   edgecolors=edgecolor, facecolors='none', zorder=1)

    return {
        'position': position, 'side': side,
        'q1': float(q1), 'median': float(median), 'q3': float(q3),
        'whisker_min': float(whisker_min), 'whisker_max': float(whisker_max),
        'box_left': float(box_left), 'box_right': float(box_right),
    }


def _draw_half_boxplot_arrow(ax, data, position, width, side='left',
                              facecolor='lightgray', edgecolor='gray',
                              alpha=0.7, show_outliers=True):
    """Half-boxplot as used in parallel_arrow_plot.py (slightly different return)."""
    data = np.array(data)
    q1 = np.percentile(data, 25)
    median = np.percentile(data, 50)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    lower_whisker = q1 - 1.5 * iqr
    upper_whisker = q3 + 1.5 * iqr
    whisker_min = data[data >= lower_whisker].min()
    whisker_max = data[data <= upper_whisker].max()
    half_width = width / 2

    if side == 'left':
        box_left = position - half_width
        box_right = position
    else:
        box_left = position
        box_right = position + half_width

    box = Rectangle(
        (box_left, q1), box_right - box_left, q3 - q1,
        facecolor=facecolor, edgecolor=edgecolor, alpha=alpha,
        linewidth=1, zorder=1
    )
    ax.add_patch(box)
    ax.plot([box_left, box_right], [median, median],
            color=edgecolor, linewidth=1.5, alpha=0.7, zorder=2)

    cap_width = half_width * 0.4
    if side == 'left':
        cap_left = position - cap_width
        cap_right = position
    else:
        cap_left = position
        cap_right = position + cap_width

    ax.plot([position, position], [whisker_min, q1],
            color=edgecolor, linewidth=1, alpha=0.5, zorder=1)
    ax.plot([cap_left, cap_right], [whisker_min, whisker_min],
            color=edgecolor, linewidth=1, alpha=0.5, zorder=1)
    ax.plot([position, position], [q3, whisker_max],
            color=edgecolor, linewidth=1, alpha=0.5, zorder=1)
    ax.plot([cap_left, cap_right], [whisker_max, whisker_max],
            color=edgecolor, linewidth=1, alpha=0.5, zorder=1)

    return whisker_min, whisker_max


# ---------------------------------------------------------------------------
# Helper: build calculated_points DataFrame-like structure from stats
# ---------------------------------------------------------------------------

def _build_calculated_points(stats):
    """Build a list of dicts matching the calculated_points.txt columns."""
    rows = []
    for cluster in sorted(stats.keys()):
        s = stats[cluster]
        c = s['calculated']
        rows.append({
            'Group': cluster,
            'X_Mean': c['mean_point'][0],
            'Y_Calculated_Mean': c['mean_point'][1],
            'X_Median': c['median_point'][0],
            'Y_Calculated_Median': c['median_point'][1],
            'g_num': c['n'],
        })
    return rows


# =========================================================================
# 1. Slope graph
# =========================================================================

def plot_slopegraph(x, y, ax=None, alpha=0.3, linewidth=0.5,
                    log2=False, no_outliers=False, show_numbers=False,
                    _log2_labels=False):
    """
    Render a slope graph.  Replicates slopegraph.py exactly.
    """
    x = np.asarray(x, dtype=float).copy()
    y = np.asarray(y, dtype=float).copy()

    if log2:
        x = apply_log2_transform(x)
        y = apply_log2_transform(y)

    show_log2 = log2 or _log2_labels

    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots(figsize=(8, 8))
    else:
        fig = ax.get_figure()

    x_pos = 1.0
    y_pos = 2.0

    total_pairs = len(x)
    diffs = y - x
    pos_count = int((diffs > 0).sum())
    neg_count = int((diffs < 0).sum())
    tie_count = int((diffs == 0).sum())
    pos_pct = 100 * pos_count / total_pairs
    neg_pct = 100 * neg_count / total_pairs

    # Optionally filter outliers for plotting
    if no_outliers:
        q1x, q3x = np.percentile(x, [25, 75])
        q1y, q3y = np.percentile(y, [25, 75])
        iqrx, iqry = q3x - q1x, q3y - q1y
        lx, ux = q1x - 1.5 * iqrx, q3x + 1.5 * iqrx
        ly, uy = q1y - 1.5 * iqry, q3y + 1.5 * iqry
        mask = (x >= lx) & (x <= ux) & (y >= ly) & (y <= uy)
        px, py = x[mask], y[mask]
    else:
        px, py = x, y

    for xi, yi in zip(px, py):
        d = yi - xi
        if d > 0:
            color = 'green'
        elif d < 0:
            color = 'red'
        else:
            color = 'gray'
        ax.plot([x_pos, y_pos], [xi, yi],
                color=color, alpha=alpha, linewidth=linewidth, zorder=2)

    ax.set_xticks([x_pos, y_pos])
    ax.set_xticklabels(['X', 'Y'], fontsize=12)
    ax.set_xlim(x_pos - 0.5, y_pos + 0.5)

    title = 'Slope Graph'
    if show_log2:
        title += ' (log2 scale)'
    ax.set_title(title, fontsize=14)
    ylabel = 'log2(Value)' if show_log2 else 'Value'
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.3)

    if show_numbers:
        ymin, ymax = ax.get_ylim()
        text_y = ymax - 0.03 * (ymax - ymin)
        lh = 0.05 * (ymax - ymin)
        ax.text(y_pos + 0.15, text_y,
                f'Ascending: {pos_count} ({pos_pct:.1f}%)',
                fontsize=10, color='green', verticalalignment='top')
        ax.text(y_pos + 0.15, text_y - lh,
                f'Descending: {neg_count} ({neg_pct:.1f}%)',
                fontsize=10, color='red', verticalalignment='top')
        if tie_count > 0:
            ax.text(y_pos + 0.15, text_y - 2 * lh,
                    f'Tie: {tie_count} ({100 * tie_count / total_pairs:.1f}%)',
                    fontsize=10, color='gray', verticalalignment='top')

    if own_fig:
        plt.figtext(0.5, 0.01, COPYRIGHT_TEXT, ha='center', fontsize=8, color='black')
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.12)

    return fig, ax


# =========================================================================
# 2. Clustered line plot
# =========================================================================

def plot_clustered_lines(x, y, clusters=None, stats=None, ax=None,
                         log2=False, no_outliers=False, show_numbers=False,
                         _log2_labels=False):
    """
    Render a clustered line plot.  Replicates clustered_line_plot.py exactly.
    """
    x = np.asarray(x, dtype=float).copy()
    y = np.asarray(y, dtype=float).copy()

    if log2:
        x = apply_log2_transform(x)
        y = apply_log2_transform(y)

    show_log2 = log2 or _log2_labels

    if clusters is None:
        from .preparation import cluster_data as _cd
        res = _cd(x, y)
        clusters = res['clusters']

    if stats is None:
        stats = compute_statistics(x, y, clusters)

    calc_points = _build_calculated_points(stats)

    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots(figsize=(8, 7))
    else:
        fig = ax.get_figure()

    x_pos = 1.0
    y_pos = 1.4
    box_width = 0.5
    show_out = not no_outliers

    bp_x = _draw_half_boxplot_clustered(ax, x, position=x_pos, width=box_width,
                                         side='left', show_outliers=show_out)
    bp_y = _draw_half_boxplot_clustered(ax, y, position=y_pos, width=box_width,
                                         side='right', show_outliers=show_out)

    x_wmin, x_wmax = bp_x['whisker_min'], bp_x['whisker_max']
    y_wmin, y_wmax = bp_y['whisker_min'], bp_y['whisker_max']

    # Filter clusters outside whisker range
    filtered = [r for r in calc_points
                if x_wmin <= r['X_Mean'] <= x_wmax
                and y_wmin <= r['Y_Calculated_Mean'] <= y_wmax]
    if not filtered:
        filtered = calc_points

    # Sort by g_num ascending (same as original)
    filtered.sort(key=lambda r: r['g_num'])

    g_nums = [r['g_num'] for r in filtered]
    g_min = min(g_nums)
    g_max = max(g_nums)

    for row in filtered:
        norm = (row['g_num'] - g_min) / (g_max - g_min) if g_max > g_min else 0.5
        color = plt.cm.Blues(0.3 + 0.7 * norm)
        lw = 1 + 4 * norm

        ax.plot([x_pos, y_pos],
                [row['X_Mean'], row['Y_Calculated_Mean']],
                color=color, linewidth=lw, solid_capstyle='round',
                zorder=int(10 + 90 * norm))

        if show_numbers:
            mx = (x_pos + y_pos) / 2
            my = (row['X_Mean'] + row['Y_Calculated_Mean']) / 2
            ax.text(mx, my + 0.02 * (y_wmax - y_wmin),
                    str(int(row['g_num'])), fontsize=7,
                    color=color, ha='center', va='bottom',
                    zorder=int(10 + 90 * norm) + 1)

    ax.set_xticks([x_pos, y_pos])
    ax.set_xticklabels(['X', 'Y'])
    ax.set_xlim(x_pos - 0.5, y_pos + 0.5)

    title = 'Boxplot with Calculated Points'
    if show_log2:
        title += ' (log2 scale)'
    ax.set_title(title, pad=30)
    ylabel = 'log2(Value)' if show_log2 else 'Value'
    ax.set_ylabel(ylabel)

    # Colorbar
    if own_fig:
        cmap_blue = _create_truncated_colormap('Blues', 0.3, 1.0)
        cax = fig.add_axes([0.25, 0.92, 0.5, 0.02])
        norm_obj = mcolors.Normalize(vmin=g_min, vmax=g_max)
        sm = plt.cm.ScalarMappable(cmap=cmap_blue, norm=norm_obj)
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cax, orientation='horizontal')
        cbar.set_ticks([g_min, g_max])
        cbar.set_ticklabels([str(int(g_min)), str(int(g_max))])
        cbar.ax.set_xlabel('g_num', fontsize=10)
        cbar.ax.tick_params(labelsize=9)
        plt.figtext(0.5, 0.01, COPYRIGHT_TEXT, ha='center', fontsize=8, color='black')
        plt.subplots_adjust(bottom=0.15, top=0.88)

    return fig, ax


# =========================================================================
# 3. Parallel arrow plot
# =========================================================================

def plot_parallel_arrows(x, y, clusters=None, stats=None, ax=None,
                         log2=False, no_outliers=False, show_numbers=False,
                         _log2_labels=False):
    """
    Render a parallel arrow plot.  Replicates parallel_arrow_plot.py exactly.
    """
    x = np.asarray(x, dtype=float).copy()
    y = np.asarray(y, dtype=float).copy()

    if log2:
        x = apply_log2_transform(x)
        y = apply_log2_transform(y)

    show_log2 = log2 or _log2_labels

    if clusters is None:
        from .preparation import cluster_data as _cd
        res = _cd(x, y)
        clusters = res['clusters']

    if stats is None:
        stats = compute_statistics(x, y, clusters)

    calc_points = _build_calculated_points(stats)

    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots(figsize=(8, 9.0))
    else:
        fig = ax.get_figure()

    x_box_pos = 0.35
    y_box_pos = 0.65
    box_width = 0.15
    labels = ['X Values', 'Y Values']
    show_out = not no_outliers

    w1min, w1max = _draw_half_boxplot_arrow(
        ax, x, x_box_pos, box_width, side='left',
        facecolor='lightgray', edgecolor='gray', alpha=0.7, show_outliers=show_out)
    w2min, w2max = _draw_half_boxplot_arrow(
        ax, y, y_box_pos, box_width, side='right',
        facecolor='lightgray', edgecolor='gray', alpha=0.7, show_outliers=show_out)

    # Filter outside whisker range
    filt = [r for r in calc_points
            if w1min <= r['X_Mean'] <= w1max
            and w2min <= r['Y_Calculated_Mean'] <= w2max]
    if not filt:
        filt = calc_points

    # Sort by g_num descending (same as original)
    filt.sort(key=lambda r: r['g_num'], reverse=True)

    g_nums = [r['g_num'] for r in filt]
    max_gn = max(g_nums)
    min_gn = min(g_nums)

    arrow_center = (x_box_pos + y_box_pos) / 2
    arrow_width = 0.15
    arrow_gap = 0.02

    asc_pts = [r for r in filt if r['Y_Calculated_Mean'] > r['X_Mean']]
    desc_pts = [r for r in filt if r['Y_Calculated_Mean'] <= r['X_Mean']]
    na = len(asc_pts)
    nd = len(desc_pts)

    if na > 1:
        asc_pos = np.linspace(arrow_center - arrow_width / 2,
                              arrow_center - arrow_gap / 2, na)
    elif na == 1:
        asc_pos = [arrow_center - arrow_width / 4]
    else:
        asc_pos = []

    if nd > 1:
        desc_pos = np.linspace(arrow_center + arrow_gap / 2,
                               arrow_center + arrow_width / 2, nd)
    elif nd == 1:
        desc_pos = [arrow_center + arrow_width / 4]
    else:
        desc_pos = []

    all_means = [r['X_Mean'] for r in filt] + [r['Y_Calculated_Mean'] for r in filt]
    arrow_min = min(all_means)
    arrow_max = max(all_means)
    bp_min = min(w1min, w2min)
    bp_max = max(w1max, w2max)
    overall_min = min(arrow_min, bp_min)
    overall_max = max(arrow_max, bp_max)
    data_range = overall_max - overall_min

    y_min = overall_min - data_range * 0.1
    y_max = overall_max + data_range * 0.1

    # Draw ascending arrows
    for i, row in enumerate(asc_pts):
        xm, ym, gn = row['X_Mean'], row['Y_Calculated_Mean'], row['g_num']
        lw = 1 + 7 * (gn - min_gn) / (max_gn - min_gn) if max_gn != min_gn else 4
        cv = (gn - min_gn) / (max_gn - min_gn) if max_gn != min_gn else 0.5
        color = mcolors.to_rgba(plt.cm.Blues(0.3 + 0.7 * cv))
        zv = 10 + int(gn)
        ax_x = asc_pos[i]
        th = data_range * 0.03
        tw = 0.007 * lw
        ax.plot([ax_x, ax_x], [xm, ym], color=color, linewidth=lw, zorder=zv)
        tri = Polygon([
            (ax_x - tw / 2, ym - th / 2),
            (ax_x + tw / 2, ym - th / 2),
            (ax_x, ym + th / 2)
        ], closed=True, facecolor=color, edgecolor=color, zorder=zv)
        ax.add_patch(tri)
        if show_numbers:
            mid_y = (xm + ym) / 2
            ax.text(ax_x - 0.02, mid_y, str(int(gn)), fontsize=7,
                    color=color, ha='right', va='center', zorder=zv + 1)

    # Draw descending arrows
    for i, row in enumerate(desc_pts):
        xm, ym, gn = row['X_Mean'], row['Y_Calculated_Mean'], row['g_num']
        lw = 1 + 7 * (gn - min_gn) / (max_gn - min_gn) if max_gn != min_gn else 4
        cv = (gn - min_gn) / (max_gn - min_gn) if max_gn != min_gn else 0.5
        color = mcolors.to_rgba(plt.cm.Blues(0.3 + 0.7 * cv))
        zv = 10 + int(gn)
        ax_x = desc_pos[i]
        th = data_range * 0.03
        tw = 0.007 * lw
        ax.plot([ax_x, ax_x], [xm, ym], color=color, linewidth=lw, zorder=zv)
        tri = Polygon([
            (ax_x - tw / 2, ym + th / 2),
            (ax_x + tw / 2, ym + th / 2),
            (ax_x, ym - th / 2)
        ], closed=True, facecolor=color, edgecolor=color, zorder=zv)
        ax.add_patch(tri)
        if show_numbers:
            mid_y = (xm + ym) / 2
            ax.text(ax_x + 0.02, mid_y, str(int(gn)), fontsize=7,
                    color=color, ha='left', va='center', zorder=zv + 1)

    ax.set_ylim(y_min, y_max)
    ax.set_xlim(0, 1)
    ylabel = 'log2(Value)' if show_log2 else 'Value'
    ax.set_ylabel(ylabel, fontsize=12)
    title = 'Changes from X to Y Values with Boxplots'
    if show_log2:
        title += ' (log2 scale)'
    ax.set_title(title, fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.set_xticks([x_box_pos, y_box_pos])
    ax.set_xticklabels(labels, fontsize=12)

    if own_fig:
        cmap_blue = _create_truncated_colormap('Blues', 0.3, 1.0)
        cax = fig.add_axes([0.92, 0.35, 0.02, 0.35])
        norm_obj = mcolors.Normalize(vmin=min_gn, vmax=max_gn)
        sm = plt.cm.ScalarMappable(cmap=cmap_blue, norm=norm_obj)
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cax)
        cbar.set_ticks([min_gn, max_gn])
        cbar.set_ticklabels([str(int(min_gn)), str(int(max_gn))])
        cbar.ax.set_title('g_num', fontsize=10, pad=5)
        cbar.ax.tick_params(labelsize=9)
        plt.subplots_adjust(left=0.1, right=0.88, top=0.9, bottom=0.15)
        plt.figtext(0.5, 0.02, _COPYRIGHT_TEXT_ARROW, ha='center', fontsize=8, color='black')

    return fig, ax


# =========================================================================
# 4. Trapezoid plot
# =========================================================================

def _calculate_quartiles(length):
    if length == 0:
        return None, None, None
    return int(length / 4), int(length / 2), int(length * 3 / 4)


def _check_outliers_extent(data):
    if not data or len(data) <= 4:
        return False
    if isinstance(data[0], list):
        flat = []
        for s in data:
            flat.extend(s)
        data = flat
    sd = sorted(data)
    n = len(sd)
    q1 = sd[int(n / 4)]
    q3 = sd[int(3 * n / 4)]
    iqr = q3 - q1
    lt, ut = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = [v for v in sd if v < lt or v > ut]
    if not outliers:
        return False
    non_out = [v for v in sd if lt <= v <= ut]
    no_min = min(non_out) if non_out else min(sd)
    no_max = max(non_out) if non_out else max(sd)
    extent = 0
    if min(outliers) < no_min:
        extent += no_min - min(outliers)
    if max(outliers) > no_max:
        extent += max(outliers) - no_max
    return extent > (max(sd) - min(sd)) / 3


def _get_whisker_range(data):
    sd = sorted(data)
    q1 = np.percentile(sd, 25)
    q3 = np.percentile(sd, 75)
    iqr = q3 - q1
    lw = q1 - 1.5 * iqr
    uw = q3 + 1.5 * iqr
    wmin = min([v for v in sd if v >= lw])
    wmax = max([v for v in sd if v <= uw])
    return wmin, wmax


def plot_trapezoid(x, y, ax=None,
                   log2=False, no_outliers=False, show_numbers=False,
                   _log2_labels=False):
    """
    Render a trapezoid plot.  Replicates trapezoid_plot.py exactly.
    """
    x = np.asarray(x, dtype=float).copy()
    y = np.asarray(y, dtype=float).copy()

    if log2:
        x = apply_log2_transform(x)
        y = apply_log2_transform(y)

    show_log2 = log2 or _log2_labels

    # Separate by direction
    sabun_up = []
    sabun_tie = []
    sabun_down = []
    for xi, yi in zip(x, y):
        d = yi - xi
        if d > 0:
            sabun_up.append([xi, yi, d])
        elif d == 0:
            sabun_tie.append([xi, yi, d])
        else:
            sabun_down.append([xi, yi, d])

    sorted_sabun_up = sorted(list(sabun_up), key=lambda v: v[0], reverse=True)
    sorted_sabun_down = sorted(list(sabun_down), key=lambda v: v[0], reverse=True)

    num_up_total = len(sabun_up)
    num_down_total = len(sabun_down)
    num_tie_total = len(sabun_tie)

    # ---- plotting ----
    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots(figsize=(8, 8))
    else:
        fig = ax.get_figure()

    x_pos = 1.0
    y_pos = 1.4

    all_data = [
        [it[0] for it in sorted_sabun_up + sorted_sabun_down + sabun_tie],
        [it[1] for it in sorted_sabun_up + sorted_sabun_down + sabun_tie],
    ]

    _check_outliers_extent([v for sub in all_data for v in sub])

    gray_color = 'gray'
    bp = ax.boxplot(all_data, positions=[x_pos, y_pos], widths=0.35,
                    tick_labels=['Group1', 'Group2'], showfliers=False,
                    medianprops=dict(color=gray_color),
                    whiskerprops=dict(color=gray_color),
                    capprops=dict(color=gray_color),
                    boxprops=dict(color=gray_color),
                    patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('lightgray')
        patch.set_edgecolor(gray_color)
        patch.set_alpha(0.8)

    w1min, w1max = _get_whisker_range(all_data[0])
    w2min, w2max = _get_whisker_range(all_data[1])

    yl, yh = ax.get_ylim()
    rect1 = Rectangle((x_pos, yl), 0.35, yh - yl,
                       facecolor='white', edgecolor='none', zorder=5)
    ax.add_patch(rect1)
    rect2 = Rectangle((y_pos - 0.35, yl), 0.35, yh - yl,
                       facecolor='white', edgecolor='none', zorder=5)
    ax.add_patch(rect2)

    ax.plot([x_pos, x_pos], [w1min, w1max], color=gray_color, linewidth=1, zorder=6)
    ax.plot([y_pos, y_pos], [w2min, w2max], color=gray_color, linewidth=1, zorder=6)

    if no_outliers:
        d0 = np.array(all_data[0])
        d1 = np.array(all_data[1])
        q1_0, q3_0 = np.percentile(d0, [25, 75])
        q1_1, q3_1 = np.percentile(d1, [25, 75])
        iqr0, iqr1 = q3_0 - q1_0, q3_1 - q1_1
        l0, u0 = q1_0 - 1.5 * iqr0, q3_0 + 1.5 * iqr0
        l1, u1 = q1_1 - 1.5 * iqr1, q3_1 + 1.5 * iqr1
        sorted_sabun_up = [it for it in sorted_sabun_up
                           if l0 <= it[0] <= u0 and l1 <= it[1] <= u1]
        sorted_sabun_down = [it for it in sorted_sabun_down
                             if l0 <= it[0] <= u0 and l1 <= it[1] <= u1]
        sabun_up = [it for it in sabun_up
                    if l0 <= it[0] <= u0 and l1 <= it[1] <= u1]
        sabun_down = [it for it in sabun_down
                      if l0 <= it[0] <= u0 and l1 <= it[1] <= u1]

    num_up_display = num_up_total
    num_down_display = num_down_total
    total = num_up_total + num_down_total + num_tie_total

    up_width = 1 + 5 * num_up_display / total if total > 0 else 1
    down_width = 1 + 5 * num_down_display / total if total > 0 else 1
    up_alpha = 0.3 + 0.7 * num_up_display / total if total > 0 else 0.3
    down_alpha = 0.3 + 0.7 * num_down_display / total if total > 0 else 0.3
    up_ci = 0.3 + 0.7 * num_up_display / total if total > 0 else 0.3
    down_ci = 0.3 + 0.7 * num_down_display / total if total > 0 else 0.3
    up_z = 10 + int(10 * num_up_display / total) if total > 0 else 10
    down_z = 10 + int(10 * num_down_display / total) if total > 0 else 10

    # Ascending trapezoid
    if sabun_up:
        nuf = len(sorted_sabun_up)
        q1i, q2i, q3i = _calculate_quartiles(nuf)
        sorted_slope_up = sorted(list(sabun_up), key=lambda v: v[2], reverse=True)

        q1s = sorted_sabun_up[q1i][0]
        q1d = sorted_slope_up[q1i][2]
        q1e = q1s + q1d
        q2s = sorted_sabun_up[q2i][0]
        q2d = sorted_slope_up[q2i][2]
        q2e = q2s + q2d
        q3s = sorted_sabun_up[q3i][0]
        q3d = sorted_slope_up[q3i][2]
        q3e = q3s + q3d

        ulc = (0, up_ci, 0)
        ax.plot([x_pos, y_pos], [q1s, q1e], color=ulc, linestyle=':', linewidth=2, alpha=up_alpha, zorder=up_z)
        ax.plot([x_pos, y_pos], [q2s, q2e], color=ulc, linestyle='-', linewidth=up_width, alpha=up_alpha, zorder=up_z)
        ax.plot([x_pos, y_pos], [q3s, q3e], color=ulc, linestyle=':', linewidth=2, alpha=up_alpha, zorder=up_z)
        ax.fill([x_pos, y_pos, y_pos, x_pos], [q1s, q1e, q3e, q3s],
                color='green', alpha=0.2, zorder=8)

        if show_numbers:
            mx = (x_pos + y_pos) / 2
            my = (q2s + q2e) / 2
            ty = my + 0.05 * (w1max - w1min)
            ax.text(mx, ty, f'n={num_up_display}', fontsize=9,
                    color=ulc, ha='center', va='bottom',
                    fontweight='bold', zorder=up_z + 1)

    # Descending trapezoid
    if sabun_down:
        ndf = len(sorted_sabun_down)
        q1i, q2i, q3i = _calculate_quartiles(ndf)
        sorted_slope_down = sorted(list(sabun_down), key=lambda v: v[2], reverse=True)

        q1s = sorted_sabun_down[q1i][0]
        q1d = sorted_slope_down[q1i][2]
        q1e = q1s + q1d
        q2s = sorted_sabun_down[q2i][0]
        q2d = sorted_slope_down[q2i][2]
        q2e = q2s + q2d
        q3s = sorted_sabun_down[q3i][0]
        q3d = sorted_slope_down[q3i][2]
        q3e = q3s + q3d

        dlc = (down_ci, 0, 0)
        ax.plot([x_pos, y_pos], [q1s, q1e], color=dlc, linestyle=':', linewidth=2, alpha=down_alpha, zorder=down_z)
        ax.plot([x_pos, y_pos], [q2s, q2e], color=dlc, linestyle='-', linewidth=down_width, alpha=down_alpha, zorder=down_z)
        ax.plot([x_pos, y_pos], [q3s, q3e], color=dlc, linestyle=':', linewidth=2, alpha=down_alpha, zorder=down_z)
        ax.fill([x_pos, y_pos, y_pos, x_pos], [q1s, q1e, q3e, q3s],
                color='red', alpha=0.2, zorder=8)

        if show_numbers:
            mx = (x_pos + y_pos) / 2
            my = (q2s + q2e) / 2
            ty = my - 0.05 * (w1max - w1min)
            ax.text(mx, ty, f'n={num_down_display}', fontsize=9,
                    color=dlc, ha='center', va='top',
                    fontweight='bold', zorder=down_z + 1)

    title = 'Trapezoid Plot'
    if show_log2:
        title += ' (log2 scale)'
    ax.set_title(title)
    ylabel = 'log2(Value)' if show_log2 else 'Value'
    ax.set_ylabel(ylabel)
    ax.set_xlim(x_pos - 0.4, y_pos + 0.4)

    if own_fig:
        plt.figtext(0.5, 0.01, COPYRIGHT_TEXT, ha='center', fontsize=8, wrap=True)
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)

    return fig, ax
