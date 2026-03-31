# Copyright (c) 2025. RIKEN All rights reserved.
# This is for academic and non-commercial research use only.
# The technology is currently under patent application.
# Commercial use is prohibited without a separate license agreement.
# E-mail: akihiro.ezoe@riken.jp

"""Plotting functions for EZ-Pair Graph visualizations (faithful port of original scripts)."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, Polygon
from matplotlib.colors import LinearSegmentedColormap, Normalize
import matplotlib.colors as mcolors
from matplotlib.cm import Blues


COPYRIGHT_TEXT = "Copyright (c) 2025. RIKEN All rights reserved. This is for academic and non-commercial research use only.\nThe technology is currently under patent application. Commercial use is prohibited without a separate license agreement. E-mail: akihiro.ezoe@riken.jp"


def _apply_log2_transform(data, min_value=1e-10):
    """Apply log2 transformation to data."""
    data = np.array(data, dtype=float)
    data = np.where(data <= 0, min_value, data)
    return np.log2(data)


def _get_whisker_range(data):
    """Calculate whisker range (Q1-1.5*IQR to Q3+1.5*IQR)."""
    sorted_data = sorted(data)
    q1 = np.percentile(sorted_data, 25)
    q3 = np.percentile(sorted_data, 75)
    iqr = q3 - q1
    lower_whisker = q1 - 1.5 * iqr
    upper_whisker = q3 + 1.5 * iqr
    whisker_min = min([x for x in sorted_data if x >= lower_whisker])
    whisker_max = max([x for x in sorted_data if x <= upper_whisker])
    return whisker_min, whisker_max


def _calculate_quartiles(length):
    """Calculate quartile indices."""
    if length == 0:
        return None, None, None
    q1_idx = int(length / 4)
    q2_idx = int(length / 2)
    q3_idx = int(length * 3 / 4)
    return q1_idx, q2_idx, q3_idx


def _check_outliers_extent(data):
    """Check if outliers extend significantly beyond non-outliers."""
    if not data or len(data) <= 4:
        return False
    if isinstance(data[0], list):
        flat_data = []
        for sublist in data:
            flat_data.extend(sublist)
        data = flat_data
    sorted_data = sorted(data)
    n = len(sorted_data)
    q1_idx = int(n / 4)
    q3_idx = int(3 * n / 4)
    q1 = sorted_data[q1_idx]
    q3 = sorted_data[q3_idx]
    iqr = q3 - q1
    lower_threshold = q1 - 1.5 * iqr
    upper_threshold = q3 + 1.5 * iqr
    outliers = [x for x in sorted_data if x < lower_threshold or x > upper_threshold]
    if not outliers:
        return False
    data_range = max(sorted_data) - min(sorted_data)
    outlier_min = min(outliers)
    outlier_max = max(outliers)
    non_outliers = [x for x in sorted_data if lower_threshold <= x <= upper_threshold]
    non_outlier_min = min(non_outliers) if non_outliers else min(sorted_data)
    non_outlier_max = max(non_outliers) if non_outliers else max(sorted_data)
    outlier_extent = 0
    if outlier_min < non_outlier_min:
        outlier_extent += non_outlier_min - outlier_min
    if outlier_max > non_outlier_max:
        outlier_extent += outlier_max - non_outlier_max
    return outlier_extent > data_range / 3


def plot_slopegraph(x, y, ax=None, no_outliers=False, log2=False, show_numbers=False,
                    alpha=0.3, linewidth=0.5):
    """
    Create a slope graph visualization (faithful port of slopegraph.py).

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
        x = _apply_log2_transform(x)
        y = _apply_log2_transform(y)

    plot_data_x = x.copy()
    plot_data_y = y.copy()

    if no_outliers:
        q1_x, q3_x = np.percentile(x, [25, 75])
        q1_y, q3_y = np.percentile(y, [25, 75])
        iqr_x, iqr_y = q3_x - q1_x, q3_y - q1_y
        lower_x, upper_x = q1_x - 1.5 * iqr_x, q3_x + 1.5 * iqr_x
        lower_y, upper_y = q1_y - 1.5 * iqr_y, q3_y + 1.5 * iqr_y
        mask = (x >= lower_x) & (x <= upper_x) & (y >= lower_y) & (y <= upper_y)
        plot_data_x = x[mask]
        plot_data_y = y[mask]
        if len(x) - len(plot_data_x) > 0:
            print(f"Filtered out {len(x) - len(plot_data_x)} data points outside whisker range for plotting")

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))
    else:
        fig = ax.get_figure()

    x_pos = 1.0
    y_pos = 2.0

    # Plot lines by direction
    for x_val, y_val in zip(plot_data_x, plot_data_y):
        diff = y_val - x_val
        if diff > 0:
            color = 'green'
        elif diff < 0:
            color = 'red'
        else:
            color = 'gray'
        ax.plot([x_pos, y_pos], [x_val, y_val],
                color=color, alpha=alpha, linewidth=linewidth, zorder=2)

    ax.set_xticks([x_pos, y_pos])
    ax.set_xticklabels(['X', 'Y'], fontsize=12)
    ax.set_xlim(x_pos - 0.5, y_pos + 0.5)

    title = 'Slope Graph'
    if log2:
        title += ' (log2 scale)'
    ax.set_title(title, fontsize=14)

    ylabel = 'log2(Value)' if log2 else 'Value'
    ax.set_ylabel(ylabel, fontsize=12)

    ax.grid(True, linestyle='--', alpha=0.3)

    # Add statistics
    total_pairs = len(x)
    differences = y - x
    positive_count = int((differences > 0).sum())
    negative_count = int((differences < 0).sum())
    tie_count = int((differences == 0).sum())

    if show_numbers:
        y_min, y_max = ax.get_ylim()
        text_y = y_max - 0.03 * (y_max - y_min)
        line_height = 0.05 * (y_max - y_min)
        positive_pct = 100 * positive_count / total_pairs if total_pairs > 0 else 0
        negative_pct = 100 * negative_count / total_pairs if total_pairs > 0 else 0
        tie_pct = 100 * tie_count / total_pairs if total_pairs > 0 else 0
        ax.text(y_pos + 0.15, text_y, f'Ascending: {positive_count} ({positive_pct:.1f}%)',
                fontsize=10, color='green', verticalalignment='top')
        ax.text(y_pos + 0.15, text_y - line_height, f'Descending: {negative_count} ({negative_pct:.1f}%)',
                fontsize=10, color='red', verticalalignment='top')
        if tie_count > 0:
            ax.text(y_pos + 0.15, text_y - 2 * line_height, f'Tie: {tie_count} ({tie_pct:.1f}%)',
                    fontsize=10, color='gray', verticalalignment='top')

    plt.figtext(0.5, 0.01, COPYRIGHT_TEXT, ha='center', fontsize=8, color='black')
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)

    return fig, ax


def plot_trapezoid(x, y, ax=None, no_outliers=False, log2=False, show_numbers=False):
    """
    Create a trapezoid plot visualization (faithful port of trapezoid_plot.py).

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
        x = _apply_log2_transform(x)
        y = _apply_log2_transform(y)

    # Split by direction
    diffs = y - x
    up_indices = np.where(diffs > 0)[0]
    down_indices = np.where(diffs < 0)[0]
    tie_indices = np.where(diffs == 0)[0]

    sabun_up = [[x[i], y[i], diffs[i]] for i in up_indices]
    sabun_down = [[x[i], y[i], diffs[i]] for i in down_indices]
    sabun_tie = [[x[i], y[i], diffs[i]] for i in tie_indices]

    sorted_sabun_up = sorted(sabun_up.copy(), key=lambda item: item[0], reverse=True)
    sorted_sabun_down = sorted(sabun_down.copy(), key=lambda item: item[0], reverse=True)

    num_up_total = len(sabun_up)
    num_down_total = len(sabun_down)
    num_tie_total = len(sabun_tie)

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))
    else:
        fig = ax.get_figure()

    x_pos = 1.0
    y_pos = 1.4

    # Create all_data for boxplot
    all_data = [
        [item[0] for item in sorted_sabun_up + sorted_sabun_down + sabun_tie],
        [item[1] for item in sorted_sabun_up + sorted_sabun_down + sabun_tie]
    ]

    hide_outliers = _check_outliers_extent([item for sublist in all_data for item in sublist])

    gray_color = 'gray'

    # Draw boxplots
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

    whisker1_min, whisker1_max = _get_whisker_range(all_data[0])
    whisker2_min, whisker2_max = _get_whisker_range(all_data[1])

    y_min, y_max = ax.get_ylim()

    # Cover whiskers with white rectangles
    rect1 = Rectangle((x_pos, y_min), 0.35, y_max - y_min,
                       facecolor='white', edgecolor='none', zorder=5)
    ax.add_patch(rect1)

    rect2 = Rectangle((y_pos - 0.35, y_min), 0.35, y_max - y_min,
                       facecolor='white', edgecolor='none', zorder=5)
    ax.add_patch(rect2)

    # Draw whisker lines
    ax.plot([x_pos, x_pos], [whisker1_min, whisker1_max], color=gray_color, linewidth=1, zorder=6)
    ax.plot([y_pos, y_pos], [whisker2_min, whisker2_max], color=gray_color, linewidth=1, zorder=6)

    # Filter outliers if requested
    if no_outliers:
        data0 = np.array(all_data[0])
        data1 = np.array(all_data[1])
        q1_0, q3_0 = np.percentile(data0, [25, 75])
        q1_1, q3_1 = np.percentile(data1, [25, 75])
        iqr_0, iqr_1 = q3_0 - q1_0, q3_1 - q1_1
        lower_0, upper_0 = q1_0 - 1.5 * iqr_0, q3_0 + 1.5 * iqr_0
        lower_1, upper_1 = q1_1 - 1.5 * iqr_1, q3_1 + 1.5 * iqr_1

        sorted_sabun_up = [item for item in sorted_sabun_up
                          if lower_0 <= item[0] <= upper_0 and lower_1 <= item[1] <= upper_1]
        sorted_sabun_down = [item for item in sorted_sabun_down
                            if lower_0 <= item[0] <= upper_0 and lower_1 <= item[1] <= upper_1]
        sabun_up = [item for item in sabun_up
                   if lower_0 <= item[0] <= upper_0 and lower_1 <= item[1] <= upper_1]
        sabun_down = [item for item in sabun_down
                     if lower_0 <= item[0] <= upper_0 and lower_1 <= item[1] <= upper_1]

        filtered_up = num_up_total - len(sabun_up)
        filtered_down = num_down_total - len(sabun_down)
        if filtered_up > 0 or filtered_down > 0:
            print(f"Filtered out {filtered_up} ascending and {filtered_down} descending points outside whisker range")

    num_up_display = len(sabun_up)
    num_down_display = len(sabun_down)
    total = num_up_display + num_down_display + num_tie_total

    up_width = 1 + 5 * num_up_display / total if total > 0 else 1
    down_width = 1 + 5 * num_down_display / total if total > 0 else 1

    up_alpha = 0.3 + 0.7 * num_up_display / total if total > 0 else 0.3
    down_alpha = 0.3 + 0.7 * num_down_display / total if total > 0 else 0.3

    up_color_intensity = 0.3 + 0.7 * num_up_display / total if total > 0 else 0.3
    down_color_intensity = 0.3 + 0.7 * num_down_display / total if total > 0 else 0.3

    up_zorder = 10 + int(10 * num_up_display / total) if total > 0 else 10
    down_zorder = 10 + int(10 * num_down_display / total) if total > 0 else 10

    # Draw trapezoid bands for ascending group
    if sabun_up:
        num_up_filtered = len(sorted_sabun_up)
        q1_idx, q2_idx, q3_idx = _calculate_quartiles(num_up_filtered)

        sorted_by_slope_up = sorted(sabun_up.copy(), key=lambda x: x[2], reverse=True)

        q1_start = sorted_sabun_up[q1_idx][0]
        q1_diff = sorted_by_slope_up[q1_idx][2]
        q1_end = q1_start + q1_diff

        q2_start = sorted_sabun_up[q2_idx][0]
        q2_diff = sorted_by_slope_up[q2_idx][2]
        q2_end = q2_start + q2_diff

        q3_start = sorted_sabun_up[q3_idx][0]
        q3_diff = sorted_by_slope_up[q3_idx][2]
        q3_end = q3_start + q3_diff

        up_line_color = (0, up_color_intensity, 0)
        ax.plot([x_pos, y_pos], [q1_start, q1_end], color=up_line_color, linestyle=':', linewidth=2, alpha=up_alpha, zorder=up_zorder)
        ax.plot([x_pos, y_pos], [q2_start, q2_end], color=up_line_color, linestyle='-', linewidth=up_width, alpha=up_alpha, zorder=up_zorder)
        ax.plot([x_pos, y_pos], [q3_start, q3_end], color=up_line_color, linestyle=':', linewidth=2, alpha=up_alpha, zorder=up_zorder)

        x_coords = [x_pos, y_pos, y_pos, x_pos]
        y_coords = [q1_start, q1_end, q3_end, q3_start]
        ax.fill(x_coords, y_coords, color='green', alpha=0.2, zorder=8)

        if show_numbers:
            mid_x = (x_pos + y_pos) / 2
            mid_y = (q2_start + q2_end) / 2
            text_y = mid_y + 0.05 * (whisker1_max - whisker1_min)
            ax.text(mid_x, text_y, f'n={num_up_display}', fontsize=9,
                    color=up_line_color, ha='center', va='bottom',
                    fontweight='bold', zorder=up_zorder + 1)

    # Draw trapezoid bands for descending group
    if sabun_down:
        num_down_filtered = len(sorted_sabun_down)
        q1_idx, q2_idx, q3_idx = _calculate_quartiles(num_down_filtered)

        sorted_by_slope_down = sorted(sabun_down.copy(), key=lambda x: x[2], reverse=True)

        q1_start = sorted_sabun_down[q1_idx][0]
        q1_diff = sorted_by_slope_down[q1_idx][2]
        q1_end = q1_start + q1_diff

        q2_start = sorted_sabun_down[q2_idx][0]
        q2_diff = sorted_by_slope_down[q2_idx][2]
        q2_end = q2_start + q2_diff

        q3_start = sorted_sabun_down[q3_idx][0]
        q3_diff = sorted_by_slope_down[q3_idx][2]
        q3_end = q3_start + q3_diff

        down_line_color = (down_color_intensity, 0, 0)
        ax.plot([x_pos, y_pos], [q1_start, q1_end], color=down_line_color, linestyle=':', linewidth=2, alpha=down_alpha, zorder=down_zorder)
        ax.plot([x_pos, y_pos], [q2_start, q2_end], color=down_line_color, linestyle='-', linewidth=down_width, alpha=down_alpha, zorder=down_zorder)
        ax.plot([x_pos, y_pos], [q3_start, q3_end], color=down_line_color, linestyle=':', linewidth=2, alpha=down_alpha, zorder=down_zorder)

        x_coords = [x_pos, y_pos, y_pos, x_pos]
        y_coords = [q1_start, q1_end, q3_end, q3_start]
        ax.fill(x_coords, y_coords, color='red', alpha=0.2, zorder=8)

        if show_numbers:
            mid_x = (x_pos + y_pos) / 2
            mid_y = (q2_start + q2_end) / 2
            text_y = mid_y - 0.05 * (whisker1_max - whisker1_min)
            ax.text(mid_x, text_y, f'n={num_down_display}', fontsize=9,
                    color=down_line_color, ha='center', va='top',
                    fontweight='bold', zorder=down_zorder + 1)

    title = 'Trapezoid Plot'
    if log2:
        title += ' (log2 scale)'
    plt.title(title)

    ylabel = 'log2(Value)' if log2 else 'Value'
    plt.ylabel(ylabel)
    ax.set_xlim(x_pos - 0.4, y_pos + 0.4)

    plt.figtext(0.5, 0.01, COPYRIGHT_TEXT, ha='center', fontsize=8, wrap=True)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)

    return fig, ax


def _draw_half_boxplot(ax, data, position, width, side='left',
                       facecolor='lightgray', edgecolor='gray', alpha=0.7,
                       show_outliers=True):
    """Draw a half-boxplot (faithful port from clustered_line_plot.py)."""
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
        (box_left, q1),
        box_right - box_left,
        q3 - q1,
        facecolor=facecolor,
        edgecolor=edgecolor,
        alpha=alpha,
        linewidth=1,
        zorder=1
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
        'position': position,
        'side': side,
        'q1': float(q1),
        'median': float(median),
        'q3': float(q3),
        'whisker_min': float(whisker_min),
        'whisker_max': float(whisker_max),
        'outliers': [float(o) for o in outliers],
    }


def _create_truncated_colormap(cmap_name, vmin=0.3, vmax=1.0):
    """Create a truncated colormap."""
    cmap = plt.get_cmap(cmap_name)
    colors = cmap(np.linspace(vmin, vmax, 256))
    return LinearSegmentedColormap.from_list(f'trunc_{cmap_name}', colors)


def plot_clustered_lines(x, y, clusters, stats, ax=None, no_outliers=False,
                         log2=False, show_numbers=False):
    """
    Create a clustered line plot visualization (faithful port of clustered_line_plot.py).

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
        x = _apply_log2_transform(x)
        y = _apply_log2_transform(y)

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 7))
    else:
        fig = ax.get_figure()

    x_pos = 1.0
    y_pos = 1.4
    box_width = 0.5

    show_outliers = not no_outliers

    bp_x = _draw_half_boxplot(ax, x, position=x_pos, width=box_width,
                              side='left', facecolor='lightgray', edgecolor='gray',
                              show_outliers=show_outliers)
    bp_x['label'] = 'X'

    bp_y = _draw_half_boxplot(ax, y, position=y_pos, width=box_width,
                              side='right', facecolor='lightgray', edgecolor='gray',
                              show_outliers=show_outliers)
    bp_y['label'] = 'Y'

    x_whisker_min, x_whisker_max = bp_x['whisker_min'], bp_x['whisker_max']
    y_whisker_min, y_whisker_max = bp_y['whisker_min'], bp_y['whisker_max']

    # Build calculated_points data from stats
    calculated_points = []
    for g_num, stat_data in sorted(stats.items()):
        calc_data = stat_data.get('calculated', {})
        calculated_points.append({
            'g_num': g_num,
            'X_Mean': calc_data.get('q2_start', 0),
            'Y_Calculated_Mean': calc_data.get('q2_end', 0),
            'Group': g_num,
        })

    # Filter calculated points
    calculated_points_filtered = [
        cp for cp in calculated_points
        if (x_whisker_min <= cp['X_Mean'] <= x_whisker_max and
            y_whisker_min <= cp['Y_Calculated_Mean'] <= y_whisker_max)
    ]

    filtered_count = len(calculated_points) - len(calculated_points_filtered)
    if filtered_count > 0:
        print(f"Filtered out {filtered_count} cluster(s) outside whisker range")

    if len(calculated_points_filtered) == 0:
        print("Warning: All clusters filtered out. Using original data.")
        calculated_points_filtered = calculated_points.copy()

    if len(calculated_points_filtered) > 0:
        g_num_min = min(cp['g_num'] for cp in calculated_points_filtered)
        g_num_max = max(cp['g_num'] for cp in calculated_points_filtered)
    else:
        g_num_min = 0
        g_num_max = 1

    # Plot lines for each cluster
    for cp in sorted(calculated_points_filtered, key=lambda x: x['g_num']):
        norm_g_num = (cp['g_num'] - g_num_min) / (g_num_max - g_num_min) if g_num_max > g_num_min else 0.5

        color = Blues(0.3 + 0.7 * norm_g_num)
        line_width = 1 + 4 * norm_g_num

        ax.plot([x_pos, y_pos], [cp['X_Mean'], cp['Y_Calculated_Mean']],
                color=color, linewidth=line_width, solid_capstyle='round',
                zorder=int(10 + 90 * norm_g_num))

        if show_numbers:
            mid_x = (x_pos + y_pos) / 2
            mid_y = (cp['X_Mean'] + cp['Y_Calculated_Mean']) / 2
            ax.text(mid_x, mid_y + 0.02 * (y_whisker_max - y_whisker_min),
                    str(int(cp['g_num'])), fontsize=7,
                    color=color, ha='center', va='bottom',
                    zorder=int(10 + 90 * norm_g_num) + 1)

    ax.set_xticks([x_pos, y_pos])
    ax.set_xticklabels(['X', 'Y'])
    ax.set_xlim(x_pos - 0.5, y_pos + 0.5)

    title = 'Boxplot with Calculated Points'
    if log2:
        title += ' (log2 scale)'
    ax.set_title(title, pad=30)

    ylabel = 'log2(Value)' if log2 else 'Value'
    ax.set_ylabel(ylabel)

    cmap_blue = _create_truncated_colormap('Blues', 0.3, 1.0)
    cax_blue = fig.add_axes([0.25, 0.92, 0.5, 0.02])
    norm = mcolors.Normalize(vmin=g_num_min, vmax=g_num_max)
    sm_blue = plt.cm.ScalarMappable(cmap=cmap_blue, norm=norm)
    sm_blue.set_array([])
    cbar_blue = fig.colorbar(sm_blue, cax=cax_blue, orientation='horizontal')
    cbar_blue.set_ticks([g_num_min, g_num_max])
    cbar_blue.set_ticklabels([str(int(g_num_min)), str(int(g_num_max))])
    cbar_blue.ax.set_xlabel('g_num', fontsize=10)
    cbar_blue.ax.tick_params(labelsize=9)

    plt.figtext(0.5, 0.01, COPYRIGHT_TEXT, ha='center', fontsize=8, color='black')

    plt.subplots_adjust(bottom=0.15, top=0.88)

    return fig, ax


def _draw_half_boxplot_for_arrows(ax, data, position, width, side='left',
                                  facecolor='lightgray', edgecolor='gray', alpha=0.7,
                                  show_outliers=True):
    """Draw a half-boxplot for arrow plot (faithful port from parallel_arrow_plot.py)."""
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
        (box_left, q1),
        box_right - box_left,
        q3 - q1,
        facecolor=facecolor,
        edgecolor=edgecolor,
        alpha=alpha,
        linewidth=1,
        zorder=1
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

    return whisker_min, whisker_max, {
        'position': float(position),
        'side': side,
        'q1': float(q1),
        'median': float(median),
        'q3': float(q3),
        'whisker_min': float(whisker_min),
        'whisker_max': float(whisker_max),
    }


def plot_parallel_arrows(x, y, clusters, stats, ax=None, no_outliers=False,
                         log2=False, show_numbers=False):
    """
    Create a parallel arrow plot visualization (faithful port of parallel_arrow_plot.py).

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
        x = _apply_log2_transform(x)
        y = _apply_log2_transform(y)

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 9.0))
    else:
        fig = ax.get_figure()

    x_box_pos = 0.35
    y_box_pos = 0.65
    box_width = 0.15
    labels = ['X Values', 'Y Values']

    show_outliers = not no_outliers

    whisker1_min, whisker1_max, bp_x = _draw_half_boxplot_for_arrows(
        ax, x, x_box_pos, box_width,
        side='left', facecolor='lightgray', edgecolor='gray', alpha=0.7,
        show_outliers=show_outliers
    )
    bp_x['label'] = 'X'

    whisker2_min, whisker2_max, bp_y = _draw_half_boxplot_for_arrows(
        ax, y, y_box_pos, box_width,
        side='right', facecolor='lightgray', edgecolor='gray', alpha=0.7,
        show_outliers=show_outliers
    )
    bp_y['label'] = 'Y'

    # Build calculated_points data from stats
    calculated_points = []
    for g_num, stat_data in sorted(stats.items()):
        calc_data = stat_data.get('calculated', {})
        calculated_points.append({
            'g_num': g_num,
            'X_Mean': calc_data.get('q2_start', 0),
            'Y_Calculated_Mean': calc_data.get('q2_end', 0),
            'Group': g_num,
        })

    # Filter by whisker range
    calculated_points_filtered = [
        cp for cp in calculated_points
        if (whisker1_min <= cp['X_Mean'] <= whisker1_max and
            whisker2_min <= cp['Y_Calculated_Mean'] <= whisker2_max)
    ]

    filtered_count = len(calculated_points) - len(calculated_points_filtered)
    if filtered_count > 0:
        print(f"Filtered out {filtered_count} cluster(s) outside whisker range")

    if len(calculated_points_filtered) == 0:
        print("Warning: All clusters filtered out. Using original data.")
        calculated_points_filtered = calculated_points.copy()

    calculated_points_sorted = sorted(calculated_points_filtered, key=lambda x: x['g_num'], reverse=True)
    max_g_num = max(cp['g_num'] for cp in calculated_points_sorted) if calculated_points_sorted else 1
    min_g_num = min(cp['g_num'] for cp in calculated_points_sorted) if calculated_points_sorted else 0

    arrow_center_pos = (x_box_pos + y_box_pos) / 2
    arrow_width = 0.15
    arrow_gap = 0.02

    ascending_points = [cp for cp in calculated_points_sorted if cp['Y_Calculated_Mean'] > cp['X_Mean']]
    descending_points = [cp for cp in calculated_points_sorted if cp['Y_Calculated_Mean'] <= cp['X_Mean']]

    num_ascending = len(ascending_points)
    num_descending = len(descending_points)

    # Calculate arrow positions
    if num_ascending > 1:
        ascending_positions = np.linspace(
            arrow_center_pos - arrow_width/2,
            arrow_center_pos - arrow_gap/2,
            num_ascending
        )
    elif num_ascending == 1:
        ascending_positions = [arrow_center_pos - arrow_width/4]
    else:
        ascending_positions = []

    if num_descending > 1:
        descending_positions = np.linspace(
            arrow_center_pos + arrow_gap/2,
            arrow_center_pos + arrow_width/2,
            num_descending
        )
    elif num_descending == 1:
        descending_positions = [arrow_center_pos + arrow_width/4]
    else:
        descending_positions = []

    arrow_min = min([cp['X_Mean'] for cp in calculated_points_filtered] + [cp['Y_Calculated_Mean'] for cp in calculated_points_filtered]) if calculated_points_filtered else 0
    arrow_max = max([cp['X_Mean'] for cp in calculated_points_filtered] + [cp['Y_Calculated_Mean'] for cp in calculated_points_filtered]) if calculated_points_filtered else 1

    boxplot_min = min(whisker1_min, whisker2_min)
    boxplot_max = max(whisker1_max, whisker2_max)

    overall_min = min(arrow_min, boxplot_min)
    overall_max = max(arrow_max, boxplot_max)

    data_range = overall_max - overall_min

    bottom_padding = data_range * 0.1
    top_padding = data_range * 0.1

    y_min = overall_min - bottom_padding
    y_max = overall_max + top_padding

    # Draw ascending arrows
    for i, row in enumerate(ascending_points):
        x_mean = row['X_Mean']
        y_mean = row['Y_Calculated_Mean']
        g_num = row['g_num']

        line_width = 1 + 7 * (g_num - min_g_num) / (max_g_num - min_g_num) if max_g_num != min_g_num else 4
        color_val = (g_num - min_g_num) / (max_g_num - min_g_num) if max_g_num != min_g_num else 0.5
        color = mcolors.to_rgba(Blues(0.3 + 0.7 * color_val))

        z_val = 10 + int(g_num)
        arrow_x = ascending_positions[i]
        triangle_height = data_range * 0.03
        triangle_width = 0.007 * line_width

        ax.plot([arrow_x, arrow_x], [x_mean, y_mean],
                color=color, linewidth=line_width, zorder=z_val)

        triangle = Polygon([
            (arrow_x - triangle_width/2, y_mean - triangle_height/2),
            (arrow_x + triangle_width/2, y_mean - triangle_height/2),
            (arrow_x, y_mean + triangle_height/2)
        ], closed=True, facecolor=color, edgecolor=color, zorder=z_val)
        ax.add_patch(triangle)

        if show_numbers:
            mid_y = (x_mean + y_mean) / 2
            text_x = arrow_x - 0.02
            ax.text(text_x, mid_y, str(int(g_num)), fontsize=7,
                    color=color, ha='right', va='center', zorder=z_val + 1)

    # Draw descending arrows
    for i, row in enumerate(descending_points):
        x_mean = row['X_Mean']
        y_mean = row['Y_Calculated_Mean']
        g_num = row['g_num']

        line_width = 1 + 7 * (g_num - min_g_num) / (max_g_num - min_g_num) if max_g_num != min_g_num else 4
        color_val = (g_num - min_g_num) / (max_g_num - min_g_num) if max_g_num != min_g_num else 0.5
        color = mcolors.to_rgba(Blues(0.3 + 0.7 * color_val))

        z_val = 10 + int(g_num)
        arrow_x = descending_positions[i]
        triangle_height = data_range * 0.03
        triangle_width = 0.007 * line_width

        ax.plot([arrow_x, arrow_x], [x_mean, y_mean],
                color=color, linewidth=line_width, zorder=z_val)

        triangle = Polygon([
            (arrow_x - triangle_width/2, y_mean + triangle_height/2),
            (arrow_x + triangle_width/2, y_mean + triangle_height/2),
            (arrow_x, y_mean - triangle_height/2)
        ], closed=True, facecolor=color, edgecolor=color, zorder=z_val)
        ax.add_patch(triangle)

        if show_numbers:
            mid_y = (x_mean + y_mean) / 2
            text_x = arrow_x + 0.02
            ax.text(text_x, mid_y, str(int(g_num)), fontsize=7,
                    color=color, ha='left', va='center', zorder=z_val + 1)

    ax.set_ylim(y_min, y_max)
    ax.set_xlim(0, 1)
    ax.set_xlabel('', fontsize=12)

    ylabel = 'log2(Value)' if log2 else 'Value'
    ax.set_ylabel(ylabel, fontsize=12)

    title = 'Changes from X to Y Values with Boxplots'
    if log2:
        title += ' (log2 scale)'
    ax.set_title(title, fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.4)

    ax.set_xticks([x_box_pos, y_box_pos])
    ax.set_xticklabels(labels, fontsize=12)

    cmap_blue = _create_truncated_colormap('Blues', 0.3, 1.0)
    cax_blue = fig.add_axes([0.92, 0.35, 0.02, 0.35])
    norm = mcolors.Normalize(vmin=min_g_num, vmax=max_g_num)
    sm_blue = plt.cm.ScalarMappable(cmap=cmap_blue, norm=norm)
    sm_blue.set_array([])
    cbar_blue = fig.colorbar(sm_blue, cax=cax_blue)
    cbar_blue.set_ticks([min_g_num, max_g_num])
    cbar_blue.set_ticklabels([str(int(min_g_num)), str(int(max_g_num))])
    cbar_blue.ax.set_title('g_num', fontsize=10, pad=5)
    cbar_blue.ax.tick_params(labelsize=9)

    plt.subplots_adjust(left=0.1, right=0.88, top=0.9, bottom=0.15)
    plt.figtext(0.5, 0.02, COPYRIGHT_TEXT, ha='center', fontsize=8, color='black')

    return fig, ax
