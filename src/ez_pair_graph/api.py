# Copyright (c) 2025. RIKEN All rights reserved.
# This is for academic and non-commercial research use only.
# The technology is currently under patent application.
# Commercial use is prohibited without a separate license agreement.
# E-mail: akihiro.ezoe@riken.jp

"""High-level API for generating EZ-Pair Graph visualizations."""

import os
import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from ez_pair_graph.preparation import load_data, cluster_data, compute_statistics
from ez_pair_graph.plotting import (
    plot_slopegraph,
    plot_trapezoid,
    plot_clustered_lines,
    plot_parallel_arrows,
)


def _ensure_output_dir(output_dir):
    """Create output directory if it doesn't exist."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)


def _save_figure(fig, output_dir, filename, format="pdf"):
    """Save figure in specified format."""
    _ensure_output_dir(output_dir)
    filepath = os.path.join(output_dir, filename)

    if format.lower() == "pdf":
        fig.savefig(filepath, format="pdf", dpi=300, bbox_inches="tight")
    elif format.lower() == "png":
        fig.savefig(filepath, format="png", dpi=300, bbox_inches="tight")
    elif format.lower() == "svg":
        fig.savefig(filepath, format="svg", bbox_inches="tight")
    else:
        fig.savefig(filepath, format=format, bbox_inches="tight")

    return filepath


def _save_json_data(data_dict, output_dir, filename):
    """Save data as JSON."""
    _ensure_output_dir(output_dir)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        json.dump(data_dict, f, indent=2)

    return filepath


def _save_html_with_svg(fig, output_dir, filename):
    """Save figure as SVG embedded in HTML."""
    _ensure_output_dir(output_dir)
    filepath = os.path.join(output_dir, filename)

    svg_filename = filename.replace(".html", ".svg")
    svg_path = os.path.join(output_dir, svg_filename)
    fig.savefig(svg_path, format="svg", bbox_inches="tight")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EZ-Pair Graph</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            img {{ max-width: 100%; height: auto; }}
        </style>
    </head>
    <body>
        <h1>EZ-Pair Graph Visualization</h1>
        <img src="{svg_filename}" alt="Graph">
    </body>
    </html>
    """

    with open(filepath, "w") as f:
        f.write(html_content)

    return filepath


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
        Path to input data file (CSV or tab-separated).
    output_dir : str, default="output_EZ"
        Directory to save output files.
    format : str, default="pdf"
        Output format: "pdf", "png", "svg", or "html".
    plots : list of str, optional
        Plot types to generate. Options: "slopegraph", "trapezoid",
        "clustered_line", "parallel_arrow". Default is all four.
    method : str, default="hierarchical"
        Clustering method: "hierarchical" or "hdbscan".
    max_k : int, default=7
        Maximum number of clusters for hierarchical method.
    linkage_method : str, default="ward"
        Linkage method for hierarchical clustering.
    min_cluster_size : int, default=5
        Minimum cluster size for HDBSCAN.
    min_samples : int, optional
        Minimum samples for HDBSCAN core points.
    no_outliers : bool, default=False
        If True, filters outliers using whisker range.
    log2 : bool, default=False
        If True, applies log2 transformation.
    show_numbers : bool, default=False
        If True, displays numeric values on plots.
    output_prefix : str, optional
        Prefix for output filenames. Defaults to input filename stem.

    Returns
    -------
    dict
        Dictionary mapping plot names to (fig, ax) tuples.
    """
    if plots is None:
        plots = ["slopegraph", "trapezoid", "clustered_line", "parallel_arrow"]

    # Load data
    data = load_data(input_file)
    if len(data) == 0:
        raise ValueError(f"No valid data found in {input_file}")

    x, y = data[:, 0], data[:, 1]

    # Cluster data
    cluster_result = cluster_data(
        x, y,
        method=method,
        max_k=max_k,
        linkage_method=linkage_method,
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        log2=log2,
    )
    clusters = cluster_result["clusters"]

    # Compute statistics
    stats = compute_statistics(x, y, clusters)

    # Set output prefix
    if output_prefix is None:
        output_prefix = Path(input_file).stem

    _ensure_output_dir(output_dir)

    # Generate plots
    figures = {}

    if "slopegraph" in plots:
        fig, ax = plot_slopegraph(
            x, y, ax=None, no_outliers=no_outliers, log2=log2,
            show_numbers=show_numbers
        )
        figures["slopegraph"] = (fig, ax)
        _save_figure(fig, output_dir, f"{output_prefix}_slopegraph.{format}", format)
        if format == "html":
            _save_html_with_svg(fig, output_dir, f"{output_prefix}_slopegraph.html")
        plt.close(fig)

    if "trapezoid" in plots:
        fig, ax = plot_trapezoid(
            x, y, ax=None, no_outliers=no_outliers, log2=log2,
            show_numbers=show_numbers
        )
        figures["trapezoid"] = (fig, ax)
        _save_figure(fig, output_dir, f"{output_prefix}_trapezoid.{format}", format)
        if format == "html":
            _save_html_with_svg(fig, output_dir, f"{output_prefix}_trapezoid.html")
        plt.close(fig)

    if "clustered_line" in plots:
        fig, ax = plot_clustered_lines(
            x, y, clusters, stats, ax=None, no_outliers=no_outliers, log2=log2,
            show_numbers=show_numbers
        )
        figures["clustered_line"] = (fig, ax)
        _save_figure(fig, output_dir, f"{output_prefix}_clustered_line.{format}", format)
        if format == "html":
            _save_html_with_svg(fig, output_dir, f"{output_prefix}_clustered_line.html")
        plt.close(fig)

    if "parallel_arrow" in plots:
        fig, ax = plot_parallel_arrows(
            x, y, clusters, stats, ax=None, no_outliers=no_outliers, log2=log2,
            show_numbers=show_numbers
        )
        figures["parallel_arrow"] = (fig, ax)
        _save_figure(fig, output_dir, f"{output_prefix}_parallel_arrow.{format}", format)
        if format == "html":
            _save_html_with_svg(fig, output_dir, f"{output_prefix}_parallel_arrow.html")
        plt.close(fig)

    # Save statistics as JSON
    _save_json_data(
        {"stats": {str(k): v for k, v in stats.items()}},
        output_dir,
        f"{output_prefix}_stats.json"
    )

    # Save clustering results
    cluster_data_dict = {
        "x": x.tolist(),
        "y": y.tolist(),
        "clusters": clusters.tolist(),
        "n_clusters": int(len(set(clusters))),
    }
    _save_json_data(cluster_data_dict, output_dir, f"{output_prefix}_clustering.json")

    return figures


def plot_array(x, y, output_dir="output_EZ", format="pdf", plots=None, **kwargs):
    """
    Generate EZ-Pair Graph visualizations from numpy arrays.

    Parameters
    ----------
    x : array-like
        Values for the first measurement.
    y : array-like
        Values for the second measurement.
    output_dir : str, default="output_EZ"
        Directory to save output files.
    format : str, default="pdf"
        Output format: "pdf", "png", "svg", or "html".
    plots : list of str, optional
        Plot types to generate. Options: "slopegraph", "trapezoid",
        "clustered_line", "parallel_arrow". Default is all four.
    **kwargs : dict
        Additional keyword arguments passed to plot functions.

    Returns
    -------
    dict
        Dictionary mapping plot names to (fig, ax) tuples.
    """
    if plots is None:
        plots = ["slopegraph", "trapezoid", "clustered_line", "parallel_arrow"]

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if len(x) != len(y):
        raise ValueError("x and y must have the same length")

    # Extract parameters
    method = kwargs.get("method", "hierarchical")
    max_k = kwargs.get("max_k", 7)
    linkage_method = kwargs.get("linkage_method", "ward")
    min_cluster_size = kwargs.get("min_cluster_size", 5)
    min_samples = kwargs.get("min_samples", None)
    no_outliers = kwargs.get("no_outliers", False)
    log2 = kwargs.get("log2", False)
    show_numbers = kwargs.get("show_numbers", False)

    # Cluster data
    cluster_result = cluster_data(
        x, y,
        method=method,
        max_k=max_k,
        linkage_method=linkage_method,
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        log2=log2,
    )
    clusters = cluster_result["clusters"]

    # Compute statistics
    stats = compute_statistics(x, y, clusters)

    _ensure_output_dir(output_dir)

    # Generate plots
    figures = {}

    if "slopegraph" in plots:
        fig, ax = plot_slopegraph(
            x, y, ax=None, no_outliers=no_outliers, log2=log2,
            show_numbers=show_numbers
        )
        figures["slopegraph"] = (fig, ax)
        _save_figure(fig, output_dir, f"slopegraph.{format}", format)
        if format == "html":
            _save_html_with_svg(fig, output_dir, "slopegraph.html")
        plt.close(fig)

    if "trapezoid" in plots:
        fig, ax = plot_trapezoid(
            x, y, ax=None, no_outliers=no_outliers, log2=log2,
            show_numbers=show_numbers
        )
        figures["trapezoid"] = (fig, ax)
        _save_figure(fig, output_dir, f"trapezoid.{format}", format)
        if format == "html":
            _save_html_with_svg(fig, output_dir, "trapezoid.html")
        plt.close(fig)

    if "clustered_line" in plots:
        fig, ax = plot_clustered_lines(
            x, y, clusters, stats, ax=None, no_outliers=no_outliers, log2=log2,
            show_numbers=show_numbers
        )
        figures["clustered_line"] = (fig, ax)
        _save_figure(fig, output_dir, f"clustered_line.{format}", format)
        if format == "html":
            _save_html_with_svg(fig, output_dir, "clustered_line.html")
        plt.close(fig)

    if "parallel_arrow" in plots:
        fig, ax = plot_parallel_arrows(
            x, y, clusters, stats, ax=None, no_outliers=no_outliers, log2=log2,
            show_numbers=show_numbers
        )
        figures["parallel_arrow"] = (fig, ax)
        _save_figure(fig, output_dir, f"parallel_arrow.{format}", format)
        if format == "html":
            _save_html_with_svg(fig, output_dir, "parallel_arrow.html")
        plt.close(fig)

    # Save statistics as JSON
    _save_json_data(
        {"stats": {str(k): v for k, v in stats.items()}},
        output_dir,
        "stats.json"
    )

    # Save clustering results
    cluster_data_dict = {
        "x": x.tolist(),
        "y": y.tolist(),
        "clusters": clusters.tolist(),
        "n_clusters": int(len(set(clusters))),
    }
    _save_json_data(cluster_data_dict, output_dir, "clustering.json")

    return figures


def plot_dataframe(df, x_col=None, y_col=None, output_dir="output_EZ", format="pdf",
                   plots=None, **kwargs):
    """
    Generate EZ-Pair Graph visualizations from a pandas DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing the data.
    x_col : str
        Column name for X values. If None, uses first numeric column.
    y_col : str
        Column name for Y values. If None, uses second numeric column.
    output_dir : str, default="output_EZ"
        Directory to save output files.
    format : str, default="pdf"
        Output format: "pdf", "png", "svg", or "html".
    plots : list of str, optional
        Plot types to generate. Options: "slopegraph", "trapezoid",
        "clustered_line", "parallel_arrow". Default is all four.
    **kwargs : dict
        Additional keyword arguments passed to plot functions.

    Returns
    -------
    dict
        Dictionary mapping plot names to (fig, ax) tuples.
    """
    if plots is None:
        plots = ["slopegraph", "trapezoid", "clustered_line", "parallel_arrow"]

    # Get numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if x_col is None:
        x_col = numeric_cols[0] if len(numeric_cols) > 0 else None
    if y_col is None:
        y_col = numeric_cols[1] if len(numeric_cols) > 1 else None

    if x_col is None or y_col is None:
        raise ValueError("Could not identify X and Y columns. Please specify x_col and y_col.")

    x = df[x_col].values
    y = df[y_col].values

    return plot_array(x, y, output_dir=output_dir, format=format, plots=plots, **kwargs)
