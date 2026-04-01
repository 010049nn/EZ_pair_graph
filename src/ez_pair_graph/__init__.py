# Copyright (c) 2025. RIKEN All rights reserved.
# This is for academic and non-commercial research use only.
# The technology is currently under patent application.
# Commercial use is prohibited without a separate license agreement.
# E-mail: akihiro.ezoe@riken.jp

"""
EZ-Pair Graph
=============
A scalable unified-axis visualization for summarizing large-scale paired data.
"""

__version__ = "0.1.0"

import os
import numpy as np

from .preparation import cluster_data, compute_statistics, load_data
from .plotting import (
    plot_slopegraph,
    plot_clustered_lines,
    plot_parallel_arrows,
    plot_trapezoid,
)

ALL_PLOTS = ['slopegraph', 'trapezoid', 'clustered_line', 'parallel_arrow']

_PLOT_FUNCS = {
    'slopegraph': plot_slopegraph,
    'trapezoid': plot_trapezoid,
    'clustered_line': plot_clustered_lines,
    'parallel_arrow': plot_parallel_arrows,
}

_PLOT_FILENAMES = {
    'slopegraph': 'slopegraph',
    'trapezoid': 'trapezoid',
    'clustered_line': 'boxplot_with_lines',
    'parallel_arrow': 'arrow_boxplot_chart',
}


def _run_pipeline(x, y, output_dir='output_EZ', format='pdf',
                  output_prefix=None, plots=None,
                  method='hierarchical', max_k=7, linkage_method='ward',
                  min_cluster_size=5, min_samples=None,
                  log2=False, no_outliers=False, show_numbers=False):
    """
    Internal: run the full pipeline on (x, y) arrays.
    Returns dict of {plot_name: filepath}.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    os.makedirs(output_dir, exist_ok=True)

    if plots is None:
        plots = ALL_PLOTS

    # Step 1: cluster
    result = cluster_data(
        x, y,
        method=method, max_k=max_k, linkage_method=linkage_method,
        min_cluster_size=min_cluster_size, min_samples=min_samples,
        log2=log2,
    )
    cx = result['x']
    cy = result['y']
    clusters = result['clusters']
    use_log2 = result['log2_applied']

    # Step 2: compute statistics
    stats = compute_statistics(cx, cy, clusters)

    # Step 3: generate each plot
    outputs = {}
    for pname in plots:
        if pname not in _PLOT_FUNCS:
            raise ValueError(f"Unknown plot type: {pname}. "
                             f"Choose from {ALL_PLOTS}")

        base = _PLOT_FILENAMES[pname]
        if output_prefix:
            base = f'{output_prefix}_{base}'
        if use_log2:
            base += '_log2'
        fname = os.path.join(output_dir, f'{base}.{format}')

        func = _PLOT_FUNCS[pname]

        # For slopegraph and trapezoid, clustering/stats not passed;
        # for clustered_line and parallel_arrow, pass them.
        # Pass _log2_labels so titles/ylabels reflect log2 scale
        # without double-transforming the already-transformed data.
        if pname in ('slopegraph', 'trapezoid'):
            fig, ax = func(
                cx, cy,
                log2=False,  # already transformed if needed
                no_outliers=no_outliers,
                show_numbers=show_numbers,
                _log2_labels=use_log2,
            )
        else:
            fig, ax = func(
                cx, cy,
                clusters=clusters, stats=stats,
                log2=False,
                no_outliers=no_outliers,
                show_numbers=show_numbers,
                _log2_labels=use_log2,
            )

        # Save — per-plot options matching the Docker shell-script versions.
        #   slopegraph.py      : PdfPages(dpi=300, bbox='tight'), png(dpi=300, bbox='tight')
        #   clustered_line_plot : plt.savefig (no bbox), png(dpi=300, no bbox)
        #   parallel_arrow_plot : PdfPages(dpi=300, bbox='tight'), png(dpi=300, bbox='tight')
        #   trapezoid_plot      : PdfPages(no dpi, no bbox), png(dpi=300, no bbox)
        use_tight = pname in ('slopegraph', 'parallel_arrow')
        bbox = 'tight' if use_tight else None

        if format == 'pdf':
            if pname in ('slopegraph', 'parallel_arrow'):
                with PdfPages(fname) as pdf:
                    pdf.savefig(fig, dpi=300, bbox_inches='tight')
            elif pname == 'trapezoid':
                with PdfPages(fname) as pdf:
                    pdf.savefig(fig)
            else:
                # clustered_line — direct savefig, no bbox
                fig.savefig(fname, format='pdf')
        elif format == 'png':
            fig.savefig(fname, format='png', dpi=300,
                        **(dict(bbox_inches='tight') if use_tight else {}))
        else:
            kw = dict(bbox_inches='tight') if use_tight else {}
            fig.savefig(fname, format=format, **kw)

        plt.close(fig)
        outputs[pname] = fname

    return outputs


def plot(input_file, **kwargs):
    """
    Run the full EZ-Pair Graph pipeline from a data file.

    Parameters
    ----------
    input_file : str
        Path to data file (space/tab/comma-separated, two columns).
    output_dir : str
        Output directory (default: 'output_EZ').
    format : str
        'pdf', 'svg', 'png' (default: 'pdf').
    output_prefix : str or None
        Prefix for output filenames.
    plots : list of str or None
        Which plots to generate. None = all four.
    method : str
        'hierarchical' or 'hdbscan'.
    max_k : int
        Max clusters for hierarchical.
    log2 : bool
        Apply log2 transformation.
    no_outliers : bool
        Hide outliers.
    show_numbers : bool
        Show numbers on plots.

    Returns
    -------
    dict : {plot_name: filepath}
    """
    x, y = load_data(input_file)
    if len(x) == 0:
        raise ValueError(f"No valid data found in {input_file}")
    return _run_pipeline(x, y, **kwargs)


def plot_array(x, y, **kwargs):
    """
    Run the full EZ-Pair Graph pipeline from NumPy arrays.

    Parameters
    ----------
    x, y : array-like
        Paired data.
    **kwargs
        Same as plot().

    Returns
    -------
    dict : {plot_name: filepath}
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) != len(y):
        raise ValueError(f"x and y must have the same length (got {len(x)} and {len(y)})")
    return _run_pipeline(x, y, **kwargs)


def plot_dataframe(df, x_col=None, y_col=None, **kwargs):
    """
    Run the full EZ-Pair Graph pipeline from a pandas DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with at least two numeric columns.
    x_col : str or None
        Column name for X values. None = first column.
    y_col : str or None
        Column name for Y values. None = second column.
    **kwargs
        Same as plot().

    Returns
    -------
    dict : {plot_name: filepath}
    """
    if x_col is None:
        x_col = df.columns[0]
    if y_col is None:
        y_col = df.columns[1]
    x = df[x_col].values.astype(float)
    y = df[y_col].values.astype(float)
    return _run_pipeline(x, y, **kwargs)
