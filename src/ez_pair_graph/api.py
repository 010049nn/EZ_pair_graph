# Copyright (c) 2025. RIKEN All rights reserved.
# This is for academic and non-commercial research use only.
# The technology is currently under patent application.
# Commercial use is prohibited without a separate license agreement.
# E-mail: akihiro.ezoe@riken.jp

"""High-level API for generating EZ-Pair Graph visualizations using original scripts."""

import os
import tempfile
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Import the original scripts as modules
from ez_pair_graph import _preparation_1, _preparation_2
from ez_pair_graph import _slopegraph, _trapezoid_plot, _clustered_line_plot, _parallel_arrow_plot


def _ensure_output_dir(output_dir):
    """Create output directory if it doesn't exist."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)


def _write_input_file(x_data, y_data, output_path):
    """Write x, y data to a temporary file in the expected format."""
    with open(output_path, 'w') as f:
        f.write("X Y\n")
        for x, y in zip(x_data, y_data):
            f.write(f"{x} {y}\n")


def plot(input_file, output_dir="output_EZ", format="pdf", plots=None,
         method="hierarchical", max_k=7, linkage_method="ward",
         min_cluster_size=5, min_samples=None,
         no_outliers=False, log2=False, show_numbers=False,
         output_prefix=None):
    """
    Generate EZ-Pair Graph visualizations from a data file.

    Parameters
    ----------
    input_file : str
        Path to input data file (comma/tab/space-separated X Y values)
    output_dir : str
        Directory for output files (default: output_EZ)
    format : str
        Output format: 'pdf', 'png', 'svg', 'html', 'json' (default: pdf)
    plots : list of str or None
        Which plots to generate. Options: 'slopegraph', 'trapezoid', 'clustered_line', 'parallel_arrow'
        If None, generates all plots
    method : str
        Clustering method: 'hierarchical' or 'hdbscan' (default: hierarchical)
    max_k : int
        Maximum number of clusters for hierarchical (default: 7)
    linkage_method : str
        Linkage method for hierarchical: 'ward', 'complete', 'average', 'single' (default: ward)
    min_cluster_size : int
        Minimum cluster size for HDBSCAN (default: 5)
    min_samples : int or None
        Minimum samples for HDBSCAN core points (default: None)
    no_outliers : bool
        Hide outliers in plots (default: False)
    log2 : bool
        Apply log2 transformation to values (default: False)
    show_numbers : bool
        Display cluster numbers on plots (default: False)
    output_prefix : str or None
        Prefix for output filenames (default: None)

    Returns
    -------
    dict
        Dictionary with keys for each generated plot
    """
    _ensure_output_dir(output_dir)

    if plots is None:
        plots = ["slopegraph", "trapezoid", "clustered_line", "parallel_arrow"]

    results = {}

    # Step 1: Run preparation_1.py (clustering)
    print(f"\nStep 1: Clustering data from {input_file}...")
    _run_preparation_1(
        input_file=input_file,
        output_dir=output_dir,
        method=method,
        max_k=max_k,
        linkage_method=linkage_method,
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        log2=log2
    )

    # Step 2: Run preparation_2.py (statistics)
    print("Step 2: Computing statistics...")
    _run_preparation_2(output_dir=output_dir)

    # Step 3: Run each visualization script
    print("Step 3: Generating visualizations...")

    if "slopegraph" in plots:
        print("  - Slopegraph...")
        _run_slopegraph(
            output_dir=output_dir,
            output_format=format,
            no_outliers=no_outliers,
            log2=log2,
            show_numbers=show_numbers,
            output_prefix=output_prefix
        )
        results["slopegraph"] = f"{output_dir}/slopegraph.{format}"

    if "trapezoid" in plots:
        print("  - Trapezoid plot...")
        _run_trapezoid_plot(
            output_dir=output_dir,
            output_format=format,
            no_outliers=no_outliers,
            log2=log2,
            show_numbers=show_numbers,
            output_prefix=output_prefix
        )
        results["trapezoid"] = f"{output_dir}/trapezoid.{format}"

    if "clustered_line" in plots:
        print("  - Clustered line plot...")
        _run_clustered_line_plot(
            output_dir=output_dir,
            output_format=format,
            no_outliers=no_outliers,
            log2=log2,
            show_numbers=show_numbers,
            output_prefix=output_prefix
        )
        results["clustered_line"] = f"{output_dir}/boxplot_with_lines.{format}"

    if "parallel_arrow" in plots:
        print("  - Parallel arrow plot...")
        _run_parallel_arrow_plot(
            output_dir=output_dir,
            output_format=format,
            no_outliers=no_outliers,
            log2=log2,
            show_numbers=show_numbers,
            output_prefix=output_prefix
        )
        results["parallel_arrow"] = f"{output_dir}/arrow_boxplot_chart.{format}"

    print("\nPipeline completed successfully!")
    return results


def plot_array(x, y, output_dir="output_EZ", format="pdf", plots=None,
               method="hierarchical", max_k=7, linkage_method="ward",
               min_cluster_size=5, min_samples=None,
               no_outliers=False, log2=False, show_numbers=False,
               output_prefix=None):
    """
    Generate EZ-Pair Graph visualizations from numpy arrays.

    Parameters
    ----------
    x : array-like
        X values
    y : array-like
        Y values
    output_dir : str
        Directory for output files (default: output_EZ)
    format : str
        Output format: 'pdf', 'png', 'svg', 'html', 'json' (default: pdf)
    plots : list of str or None
        Which plots to generate (default: all)
    method : str
        Clustering method: 'hierarchical' or 'hdbscan' (default: hierarchical)
    max_k : int
        Maximum number of clusters for hierarchical (default: 7)
    linkage_method : str
        Linkage method for hierarchical (default: ward)
    min_cluster_size : int
        Minimum cluster size for HDBSCAN (default: 5)
    min_samples : int or None
        Minimum samples for HDBSCAN core points (default: None)
    no_outliers : bool
        Hide outliers in plots (default: False)
    log2 : bool
        Apply log2 transformation to values (default: False)
    show_numbers : bool
        Display cluster numbers on plots (default: False)
    output_prefix : str or None
        Prefix for output filenames (default: None)

    Returns
    -------
    dict
        Dictionary with keys for each generated plot
    """
    # Create temporary input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        temp_input = f.name
        _write_input_file(x, y, temp_input)

    try:
        return plot(
            input_file=temp_input,
            output_dir=output_dir,
            format=format,
            plots=plots,
            method=method,
            max_k=max_k,
            linkage_method=linkage_method,
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            no_outliers=no_outliers,
            log2=log2,
            show_numbers=show_numbers,
            output_prefix=output_prefix
        )
    finally:
        if os.path.exists(temp_input):
            os.remove(temp_input)


def plot_dataframe(df, x_col, y_col, output_dir="output_EZ", format="pdf", plots=None,
                   method="hierarchical", max_k=7, linkage_method="ward",
                   min_cluster_size=5, min_samples=None,
                   no_outliers=False, log2=False, show_numbers=False,
                   output_prefix=None):
    """
    Generate EZ-Pair Graph visualizations from a pandas DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data
    x_col : str
        Column name for X values
    y_col : str
        Column name for Y values
    output_dir : str
        Directory for output files (default: output_EZ)
    format : str
        Output format: 'pdf', 'png', 'svg', 'html', 'json' (default: pdf)
    plots : list of str or None
        Which plots to generate (default: all)
    method : str
        Clustering method: 'hierarchical' or 'hdbscan' (default: hierarchical)
    max_k : int
        Maximum number of clusters for hierarchical (default: 7)
    linkage_method : str
        Linkage method for hierarchical (default: ward)
    min_cluster_size : int
        Minimum cluster size for HDBSCAN (default: 5)
    min_samples : int or None
        Minimum samples for HDBSCAN core points (default: None)
    no_outliers : bool
        Hide outliers in plots (default: False)
    log2 : bool
        Apply log2 transformation to values (default: False)
    show_numbers : bool
        Display cluster numbers on plots (default: False)
    output_prefix : str or None
        Prefix for output filenames (default: None)

    Returns
    -------
    dict
        Dictionary with keys for each generated plot
    """
    x = df[x_col].values
    y = df[y_col].values

    return plot_array(
        x=x,
        y=y,
        output_dir=output_dir,
        format=format,
        plots=plots,
        method=method,
        max_k=max_k,
        linkage_method=linkage_method,
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        no_outliers=no_outliers,
        log2=log2,
        show_numbers=show_numbers,
        output_prefix=output_prefix
    )


# ============================================================================
# Internal functions that call the original script logic
# ============================================================================

def _run_preparation_1(input_file, output_dir, method, max_k, linkage_method,
                       min_cluster_size, min_samples, log2):
    """Run preparation_1.py clustering logic directly."""
    os.makedirs(output_dir, exist_ok=True)

    # Load data using the original function
    data = _preparation_1.load_data(input_file)
    if len(data) == 0:
        raise ValueError(f"No valid data found in {input_file}")

    print(f"Loaded {len(data)} data points from {input_file}")

    # Handle log2 transformation
    use_log2 = log2
    marker_file = os.path.join(output_dir, '.log2_transformed')
    if use_log2:
        data, filtered_count = _preparation_1.filter_non_positive_for_log2(data)
        if filtered_count > 0:
            print(f"Excluded {filtered_count} data points with non-positive values for log2 transformation")
        print(f"Applying log2 transformation to {len(data)} data points...")
        data[:, 0] = np.log2(data[:, 0])
        data[:, 1] = np.log2(data[:, 1])
        with open(marker_file, 'w') as f:
            f.write('log2_transformed=true\n')
    else:
        if os.path.exists(marker_file):
            os.remove(marker_file)

    print(f"Clustering method: {method}")

    # Split by direction
    pos_indices, neg_indices = _preparation_1.split_by_direction(data)
    pos_data = data[pos_indices] if pos_indices else np.array([])
    neg_data = data[neg_indices] if neg_indices else np.array([])

    print(f"Positive changes (Y >= X): {len(pos_indices)} points")
    print(f"Negative changes (Y < X): {len(neg_indices)} points")

    # Cluster
    all_clusters = np.zeros(len(data), dtype=int)
    cluster_offset = 0

    if len(pos_data) > 0:
        if method == 'hierarchical':
            pos_clusters, pos_k = _preparation_1.hierarchical_clustering(
                pos_data,
                max_k=max_k,
                method=linkage_method
            )
        else:
            pos_clusters, pos_k = _preparation_1.hdbscan_clustering(
                pos_data,
                min_cluster_size=min_cluster_size,
                min_samples=min_samples
            )

        for i, idx in enumerate(pos_indices):
            all_clusters[idx] = pos_clusters[i]

        cluster_offset = pos_clusters.max() + 1 if len(pos_clusters) > 0 else 0
        print(f"Positive group: {pos_k} clusters")

    if len(neg_data) > 0:
        if method == 'hierarchical':
            neg_clusters, neg_k = _preparation_1.hierarchical_clustering(
                neg_data,
                max_k=max_k,
                method=linkage_method
            )
        else:
            neg_clusters, neg_k = _preparation_1.hdbscan_clustering(
                neg_data,
                min_cluster_size=min_cluster_size,
                min_samples=min_samples
            )

        for i, idx in enumerate(neg_indices):
            all_clusters[idx] = neg_clusters[i] + cluster_offset

        print(f"Negative group: {neg_k} clusters")

    # Write clustered data
    output_file = os.path.join(output_dir, 'clustered_data.txt')
    with open(output_file, 'w') as f:
        f.write("X Y Cluster\n")
        for i, (x, y) in enumerate(data):
            f.write(f"{x} {y} {all_clusters[i]}\n")

    print(f"Results saved to {output_file}")

    total_clusters = len(set(all_clusters))
    print(f"\nSummary:")
    print(f"  Total clusters: {total_clusters}")
    print(f"  Method: {method}")
    print(f"  Log2 transformation: {use_log2}")
    if method == 'hierarchical':
        print(f"  Linkage: {linkage_method}")
        print(f"  Max k: {max_k}")
    else:
        print(f"  Min cluster size: {min_cluster_size}")


def _run_preparation_2(output_dir):
    """Run preparation_2.py statistics computation logic directly."""
    input_file = os.path.join(output_dir, 'clustered_data.txt')
    stats_file = os.path.join(output_dir, 'group_statistics.txt')
    calc_file = os.path.join(output_dir, 'calculated_points.txt')

    # Read clustered data
    data = []
    with open(input_file, 'r') as f:
        header = f.readline()
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                data.append([float(parts[0]), float(parts[1]), int(parts[2])])

    # Group by cluster
    groups = {}
    for row in data:
        cluster = row[2]
        if cluster not in groups:
            groups[cluster] = []
        x_val = row[0]
        y_val = row[1]
        diff = y_val - x_val
        groups[cluster].append([x_val, y_val, diff])

    # Compute statistics
    stats_results = {}

    for cluster in sorted(groups.keys()):
        group_data = groups[cluster]
        x_values = [p[0] for p in group_data]
        y_values = [p[1] for p in group_data]
        diff_values = [p[2] for p in group_data]

        m = len(group_data)

        x_mean, x_q1, x_q2, x_q3, _ = _preparation_2.calculate_stats(x_values)
        y_mean, y_q1, y_q2, y_q3, _ = _preparation_2.calculate_stats(y_values)

        sorted_by_x = sorted(group_data, key=lambda item: item[0], reverse=True)
        sorted_by_diff = sorted(group_data, key=lambda item: item[2], reverse=True)

        q1_idx, q2_idx, q3_idx = _preparation_2.calculate_quartile_indices(m)

        if q2_idx is not None:
            q2_start = sorted_by_x[q2_idx][0]
            q2_diff = sorted_by_diff[q2_idx][2]
            calc_y_q2 = q2_start + q2_diff

            q1_start = sorted_by_x[q1_idx][0]
            q1_diff = sorted_by_diff[q1_idx][2]

            q3_start = sorted_by_x[q3_idx][0]
            q3_diff = sorted_by_diff[q3_idx][2]
        else:
            q2_start = x_q2
            q2_diff = y_q2 - x_q2
            calc_y_q2 = q2_start + q2_diff
            q1_start = x_q1
            q1_diff = y_q1 - x_q1
            q3_start = x_q3
            q3_diff = y_q3 - x_q3

        diff_mean, diff_q1, diff_q2, diff_q3, _ = _preparation_2.calculate_stats(diff_values)

        stats_results[cluster] = {
            'x': {'mean': x_mean, 'q1': x_q1, 'q2': x_q2, 'q3': x_q3},
            'y': {'mean': y_mean, 'q1': y_q1, 'q2': y_q2, 'q3': y_q3},
            'diff': {
                'mean': diff_mean,
                'q1': diff_q1,
                'q2': diff_q2,
                'q3': diff_q3,
                'q1_trapezoid': q1_diff,
                'q2_trapezoid': q2_diff,
                'q3_trapezoid': q3_diff
            },
            'calculated': {
                'mean_point': [q2_start, calc_y_q2],
                'median_point': [q2_start, calc_y_q2],
                'n': m,
                'q2_start': q2_start,
                'q2_diff': q2_diff
            }
        }

    # Write statistics file
    with open(stats_file, 'w') as f:
        for cluster in sorted(stats_results.keys()):
            s = stats_results[cluster]
            f.write(f"Statistics for Group {cluster}:\n")
            f.write(f"X: Mean={s['x']['mean']:.4f}, Q1={s['x']['q1']:.4f}, Q2={s['x']['q2']:.4f}, Q3={s['x']['q3']:.4f}\n")
            f.write(f"Y: Mean={s['y']['mean']:.4f}, Q1={s['y']['q1']:.4f}, Q2={s['y']['q2']:.4f}, Q3={s['y']['q3']:.4f}\n")
            f.write(f"Diff: Mean={s['diff']['mean']:.4f}, Q1={s['diff']['q1']:.4f}, Q2={s['diff']['q2']:.4f}, Q3={s['diff']['q3']:.4f}\n")
            f.write(f"Diff(trapezoid): Q1={s['diff']['q1_trapezoid']:.4f}, Q2={s['diff']['q2_trapezoid']:.4f}, Q3={s['diff']['q3_trapezoid']:.4f}\n")
            f.write(f"Calculated: Q2s={s['calculated']['q2_start']:.4f}, Q2d={s['calculated']['q2_diff']:.4f}\n")
            f.write("\n")

    # Write calculated points file
    with open(calc_file, 'w') as f:
        f.write("Group\tX_Mean\tY_Calculated_Mean\tX_Median\tY_Calculated_Median\tg_num\n")
        for cluster in sorted(stats_results.keys()):
            s = stats_results[cluster]
            c = s['calculated']
            f.write(f"{cluster}\t{c['mean_point'][0]:.4f}\t{c['mean_point'][1]:.4f}\t{c['median_point'][0]:.4f}\t{c['median_point'][1]:.4f}\t{c['n']}\n")

    print(f"Statistics computed and saved to {stats_file} and {calc_file}")


def _run_slopegraph(output_dir, output_format, no_outliers, log2, show_numbers, output_prefix):
    """Run slopegraph.py visualization logic by calling the original main()."""
    import sys
    import argparse

    # Monkey-patch the read_csv to use correct path
    original_read_csv = pd.read_csv
    def patched_read_csv(filepath, **kwargs):
        if 'clustered_data.txt' in str(filepath):
            filepath = os.path.join(output_dir, 'clustered_data.txt')
        return original_read_csv(filepath, **kwargs)

    old_argv = sys.argv
    old_read_csv = pd.read_csv
    try:
        pd.read_csv = patched_read_csv
        args_list = ['slopegraph.py', '--format', output_format]
        if no_outliers:
            args_list.append('--no-outliers')
        if log2:
            args_list.append('--log2')
        if show_numbers:
            args_list.append('--show-numbers')
        if output_prefix:
            args_list.extend(['--output-prefix', output_prefix])
        sys.argv = args_list
        _slopegraph.main()
    finally:
        sys.argv = old_argv
        pd.read_csv = old_read_csv


def _run_trapezoid_plot(output_dir, output_format, no_outliers, log2, show_numbers, output_prefix):
    """Run trapezoid_plot.py visualization logic by calling the original main()."""
    import sys

    original_read_csv = pd.read_csv
    def patched_read_csv(filepath, **kwargs):
        if 'clustered_data.txt' in str(filepath) or 'calculated_points.txt' in str(filepath):
            filepath = os.path.join(output_dir, os.path.basename(str(filepath)))
        return original_read_csv(filepath, **kwargs)

    original_exists = os.path.exists
    def patched_exists(filepath):
        if '.log2_transformed' in str(filepath):
            filepath = os.path.join(output_dir, '.log2_transformed')
        return original_exists(filepath)

    old_argv = sys.argv
    old_read_csv = pd.read_csv
    old_exists = os.path.exists
    try:
        pd.read_csv = patched_read_csv
        os.path.exists = patched_exists
        args_list = ['trapezoid_plot.py', '--format', output_format]
        if no_outliers:
            args_list.append('--no-outliers')
        if log2:
            args_list.append('--log2')
        if show_numbers:
            args_list.append('--show-numbers')
        if output_prefix:
            args_list.extend(['--output-prefix', output_prefix])
        sys.argv = args_list
        _trapezoid_plot.main()
    finally:
        sys.argv = old_argv
        pd.read_csv = old_read_csv
        os.path.exists = old_exists


def _run_clustered_line_plot(output_dir, output_format, no_outliers, log2, show_numbers, output_prefix):
    """Run clustered_line_plot.py visualization logic by calling the original main()."""
    import sys

    original_read_csv = pd.read_csv
    def patched_read_csv(filepath, **kwargs):
        if 'clustered_data.txt' in str(filepath) or 'calculated_points.txt' in str(filepath):
            filepath = os.path.join(output_dir, os.path.basename(str(filepath)))
        return original_read_csv(filepath, **kwargs)

    original_exists = os.path.exists
    def patched_exists(filepath):
        if '.log2_transformed' in str(filepath):
            filepath = os.path.join(output_dir, '.log2_transformed')
        return original_exists(filepath)

    old_argv = sys.argv
    old_read_csv = pd.read_csv
    old_exists = os.path.exists
    try:
        pd.read_csv = patched_read_csv
        os.path.exists = patched_exists
        args_list = ['clustered_line_plot.py', '--format', output_format]
        if no_outliers:
            args_list.append('--no-outliers')
        if log2:
            args_list.append('--log2')
        if show_numbers:
            args_list.append('--show-numbers')
        if output_prefix:
            args_list.extend(['--output-prefix', output_prefix])
        sys.argv = args_list
        _clustered_line_plot.main()
    finally:
        sys.argv = old_argv
        pd.read_csv = old_read_csv
        os.path.exists = old_exists


def _run_parallel_arrow_plot(output_dir, output_format, no_outliers, log2, show_numbers, output_prefix):
    """Run parallel_arrow_plot.py visualization logic by calling the original main()."""
    import sys

    original_read_csv = pd.read_csv
    def patched_read_csv(filepath, **kwargs):
        if 'clustered_data.txt' in str(filepath) or 'calculated_points.txt' in str(filepath):
            filepath = os.path.join(output_dir, os.path.basename(str(filepath)))
        return original_read_csv(filepath, **kwargs)

    original_exists = os.path.exists
    def patched_exists(filepath):
        if '.log2_transformed' in str(filepath):
            filepath = os.path.join(output_dir, '.log2_transformed')
        return original_exists(filepath)

    old_argv = sys.argv
    old_read_csv = pd.read_csv
    old_exists = os.path.exists
    try:
        pd.read_csv = patched_read_csv
        os.path.exists = patched_exists
        args_list = ['parallel_arrow_plot.py', '--format', output_format]
        if no_outliers:
            args_list.append('--no-outliers')
        if log2:
            args_list.append('--log2')
        if show_numbers:
            args_list.append('--show-numbers')
        if output_prefix:
            args_list.extend(['--output-prefix', output_prefix])
        sys.argv = args_list
        _parallel_arrow_plot.main()
    finally:
        sys.argv = old_argv
        pd.read_csv = old_read_csv
        os.path.exists = old_exists
