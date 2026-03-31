# Copyright (c) 2025. RIKEN All rights reserved.
# This is for academic and non-commercial research use only.
# The technology is currently under patent application.
# Commercial use is prohibited without a separate license agreement.
# E-mail: akihiro.ezoe@riken.jp

"""
EZ-Pair Graph: Scalable unified-axis visualization for summarizing large-scale paired data.

Quick Start:
    >>> import ez_pair_graph as ezpg
    >>> ezpg.plot("data.txt")                        # Generate all plots
    >>> ezpg.plot("data.txt", format="png")           # PNG output
    >>> ezpg.plot("data.txt", plots=["trapezoid"])    # Specific plot only
    >>> figs = ezpg.plot_array(x, y)                  # From numpy arrays
"""

__version__ = "0.1.0"
__author__ = "Akihiro Ezoe, Motoaki Seki, Keiichi Mochida"
__license__ = "Academic/Non-commercial use only (RIKEN)"

from ez_pair_graph.api import plot, plot_array, plot_dataframe
from ez_pair_graph.preparation import cluster_data, compute_statistics

__all__ = [
    "plot",
    "plot_array",
    "plot_dataframe",
    "cluster_data",
    "compute_statistics",
]
