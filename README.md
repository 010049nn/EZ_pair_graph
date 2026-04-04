# EZ-Pair Graph

**A scalable unified-axis visualization for summarizing large-scale paired data**

## Overview

EZ-Pair Graph is a suite of visualization methods that summarizes large-scale paired data while preserving directional and magnitude information on a unified axis. It produces three plot types:

| Plot | Description |
|------|-------------|
| **Trapezoid plot** | Splits paired data into ascending and descending groups; quartile points (Q1–Q3) of starting positions and differences are connected to form a summary trapezoid. Line thickness is proportional to the number of observations. |
| **Clustered line plot** | Clusters paired connections within each directional group; each cluster is represented by its median summary line (Q2s, Q2d). Color intensity and line thickness indicate cluster size. |
| **Parallel arrow plot** | Renders each cluster's summary line as a vertical arrow between boxplots. Upward arrows indicate ascending groups; downward arrows indicate descending groups. Arrow thickness and color reflect group size. |

A conventional **slope graph** is also generated alongside these plots as a baseline reference, illustrating the visual saturation that the above methods resolve.

These methods are designed for datasets where conventional visualizations (slope graphs, Bland-Altman plots) suffer from visual saturation.

Output example of test_dataset.txt
<img width="2403" height="947" alt="Image" src="https://github.com/user-attachments/assets/86f2d935-a32f-4dc5-8782-2cc3b47fc12d" />

Output example of test_dataset_n1000.txt
<img width="2291" height="818" alt="Image" src="https://github.com/user-attachments/assets/d8c91209-a747-4cc3-8a74-0904f9bd7815" />

Two installation methods are available: [pip install](#usage-pip-install) and [Docker / Shell Script](#usage-docker--shell-script).

---

## Usage: pip install

### Installation

```bash
pip install git+https://github.com/010049nn/EZ_pair_graph.git -q
```

Or install from source:

```bash
git clone https://github.com/010049nn/EZ_pair_graph.git
cd EZ_pair_graph
pip install -e .
```

### Python API

```python
import ez_pair_graph as ezpg

# From a data file
ezpg.plot("data.txt")

# From numpy arrays
import numpy as np
x = np.random.normal(50, 10, 1000)
y = x + np.random.normal(2, 5, 1000)
ezpg.plot_array(x, y, format="png")

# From a pandas DataFrame
import pandas as pd
df = pd.read_csv("data.csv")
ezpg.plot_dataframe(df, x_col="before", y_col="after")

# Generate specific plots only
ezpg.plot("data.txt", plots=["trapezoid", "parallel_arrow"])

# With options
ezpg.plot("data.txt", format="svg", log2=True, no_outliers=True, show_numbers=True)
```

### Command line

```bash
# Basic usage
ez-pair-graph data.txt

# PNG output with specific plots
ez-pair-graph data.txt --format png --plots trapezoid clustered_line

# With clustering options
ez-pair-graph data.txt --method hdbscan --min-cluster-size 3

# All options
ez-pair-graph data.txt --format svg --log2 --no-outliers --show-numbers
```

### Analyzing your own data

```python
import ez_pair_graph as ezpg
ezpg.plot("your_data.txt", format="png", show_numbers=True)
```

```bash
ez-pair-graph your_data.txt --format png --show-numbers
```

For log-scale data:

```bash
ez-pair-graph your_data.txt --log2
```

### Command line options

| Option | Description |
|--------|-------------|
| `--format FORMAT` | Output format: `pdf` (default), `svg`, `png`, `html`, `json` |
| `--output-dir DIR` | Output directory (default: output_EZ) |
| `--output-prefix PREFIX` | Prefix for output filenames |
| `--plots TYPES` | Plot types: `slopegraph`, `trapezoid`, `clustered_line`, `parallel_arrow` |
| `--no-outliers` | Hide outliers in boxplots |
| `--log2` | Apply log2 transformation to values |
| `--show-numbers` | Display cluster numbers or sample counts on plots |
| `--method METHOD` | Clustering method: `hierarchical` (default) or `hdbscan` |
| `--max-k N` | Maximum number of clusters for hierarchical clustering (default: 7) |
| `--linkage METHOD` | Linkage method: `ward` (default), `complete`, `average`, `single` |
| `--min-cluster-size N` | Minimum cluster size for HDBSCAN (default: 5) |
| `--min-samples N` | Minimum samples for HDBSCAN core points |

### Demo Notebook

A Jupyter notebook is included: [`demo_ez_pair_graph.ipynb`](demo_ez_pair_graph.ipynb)

The notebook covers:
- Generating all three plot types (plus slope graph) from synthetic data
- Working with NumPy arrays, pandas DataFrames, and CSV files
- Comparing hierarchical and HDBSCAN clustering methods
- Log2 transformation for expression data
- Large-scale data visualization (n > 1,000)
- Accessing per-cluster statistics

---

## Usage: Docker / Shell Script

This workflow uses root-level Python scripts (`preparation_1.py`, `preparation_2.py`, `slopegraph.py`, `clustered_line_plot.py`, `parallel_arrow_plot.py`, `trapezoid_plot.py`) called by `pipeline_for_EZ_plot.sh`. These are separate from the `src/ez_pair_graph/` package used by the pip installation.

### Installation

```bash
git clone https://github.com/010049nn/EZ_pair_graph.git
cd EZ_pair_graph
docker build -t ez_pair_graph .
```

### Running the pipeline

```bash
# Using Docker
docker run --rm \
    -v $(pwd)/output_EZ:/app/output_EZ \
    ez_pair_graph \
    bash ./pipeline_for_EZ_plot.sh test_dataset.txt --no-outliers --show-numbers
```
```bash
# Or locally (without Docker)
bash pipeline_for_EZ_plot.sh test_dataset.txt --no-outliers --show-numbers
```

### Output

Four plot files are generated in `output_EZ/`:

```
output_EZ/
├── slopegraph.pdf              # Raw paired data as a slope graph
├── trapezoid.pdf               # Trapezoid plot summary
├── boxplot_with_lines.pdf      # Clustered line plot
└── arrow_boxplot_chart.pdf     # Parallel arrow plot
```

### Interpreting the plots

**Slope graph** (`slopegraph.pdf`): Shows all individual paired connections. Green lines indicate ascending pairs (Y > X), red lines indicate descending pairs (Y < X). This is the conventional view — note how lines overlap heavily even with moderate sample sizes.

**Trapezoid plot** (`trapezoid.pdf`): Summarizes the paired data into two groups:
- Green trapezoid = ascending group (Y > X)
- Red trapezoid = descending group (Y < X)
- Line thickness reflects the number of observations in each group
- The Q1, Q2 (median), and Q3 lines show the quartile structure of each group's starting positions and differences

**Clustered line plot** (`boxplot_with_lines.pdf`): Pairs are grouped into clusters using hierarchical clustering. Each cluster is represented by its median line (Q2). Color intensity and line thickness indicate the number of observations in each cluster, making it easy to identify dominant trends.

**Parallel arrow plot** (`arrow_boxplot_chart.pdf`): Each cluster from the clustered line plot is displayed as a vertical arrow between boxplots. Upward arrows (left side) represent ascending groups; downward arrows (right side) represent descending groups. Arrow thickness reflects cluster size.

### Analyzing your own data

```bash
# Shell script (local)
bash pipeline_for_EZ_plot.sh your_data.txt --output-prefix my_analysis --show-numbers

# Docker
docker run --rm \
    -v $(pwd)/data:/data \
    -v $(pwd)/output_EZ:/app/output_EZ \
    ez_pair_graph \
    bash ./pipeline_for_EZ_plot.sh /data/your_data.txt --output-prefix my_analysis --show-numbers
```

For log-scale data:

```bash
bash pipeline_for_EZ_plot.sh your_log_scale_data.txt --log2 --output-prefix log_data
```

### Command line options

> **Note:** The shell script uses **underscored** option names (e.g. `--min_cluster_size`). The pip CLI uses **hyphenated** names (e.g. `--min-cluster-size`). These are not interchangeable.

| Option | Description |
|--------|-------------|
| `--format FORMAT` | Output format: `pdf` (default), `svg`, `png`, `html`, `json` |
| `--output-prefix PREFIX` | Prefix for output filenames |
| `--no-outliers` | Hide outliers in boxplots |
| `--log2` | Apply log2 transformation to values |
| `--show-numbers` | Display cluster numbers or sample counts on plots |
| `--method METHOD` | Clustering method: `hierarchical` (default) or `hdbscan` |
| `--max_k N` | Maximum number of clusters for hierarchical clustering (default: 7) |
| `--linkage METHOD` | Linkage method: `ward`, `complete`, `average`, `single` |
| `--min_cluster_size N` | Minimum cluster size for HDBSCAN (default: 5) |
| `--min_samples N` | Minimum samples for HDBSCAN core points |

---

## Input Data Format

Create a text file with two columns (paired values). Headers are auto-detected:

```
Group_A    Group_B
45.2       42.1
38.7       41.3
52.0       48.9
...
```

Supported formats: space-separated, tab-separated, or comma-separated (CSV).

## Clustering Methods

EZ-Pair Graph provides two deterministic clustering algorithms, both of which produce identical results for the same input data and parameters:

### Hierarchical clustering (default)

- Uses agglomerative hierarchical clustering with Ward's minimum variance method
- The optimal number of clusters is determined automatically using the elbow method based on within-cluster sum of squares
- Controlled by `--max-k` / `--max_k` (maximum clusters, default: 7) and `--linkage` (default: ward)

### HDBSCAN

- Density-based clustering that does not require specifying the number of clusters
- Better for datasets with varying cluster densities
- Native implementation — no additional external dependencies required
- Controlled by `--min-cluster-size` / `--min_cluster_size` (default: 5) and `--min-samples` / `--min_samples`

Observations are first separated by direction of change (ascending: B−A ≥ 0; descending: B−A < 0), and clustering is performed independently within each group. Clusters whose median points fall outside the 1.5×IQR whisker range of the boxplots are treated as outliers and excluded from the visualization.

## Output Files

All output files are saved in the `output_EZ/` directory.

| File | Description |
|------|-------------|
| `clustered_data.txt` | Clustered data with assigned cluster labels |
| `calculated_points.txt` | Calculated summary statistics per cluster |
| `[PREFIX_]slopegraph.FORMAT` | Slope graph showing all paired data points |
| `[PREFIX_]boxplot_with_lines.FORMAT` | Clustered line plot with half-boxplots |
| `[PREFIX_]arrow_boxplot_chart.FORMAT` | Parallel arrow plot with boxplots |
| `[PREFIX_]trapezoid.FORMAT` | Trapezoid plot with quartile bands |

## Project Structure

This project provides two parallel entry points that share the same algorithms and produce identical results:

| Entry point | Implementation | When to use |
|-------------|---------------|-------------|
| **pip CLI / Python API** | `src/ez_pair_graph/` package (`cli.py`, `plotting.py`, `preparation.py`) | Install via `pip install` and use as a library or command-line tool. |
| **Shell script pipeline** | Root-level scripts (`preparation_1.py`, `preparation_2.py`, `slopegraph.py`, `clustered_line_plot.py`, `parallel_arrow_plot.py`, `trapezoid_plot.py`) called by `pipeline_for_EZ_plot.sh` | Used by the Docker workflow and for running the pipeline without pip installation. |

The root-level `.py` scripts are the standalone originals invoked directly by the shell script. The `src/ez_pair_graph/` package wraps the same logic into an installable Python library. Both are maintained and required — do not remove the root-level scripts if you use the Docker or shell script workflow.

## Dependencies

- Python >= 3.8
- NumPy >= 1.20
- pandas >= 1.3
- matplotlib >= 3.4
- SciPy >= 1.7

## Citation

If you use EZ-Pair Graph in your research, please cite:

> Ezoe, A., Seki, M. and Mochida, K. EZ-Pair Graph: A scalable unified-axis visualization for summarizing large-scale paired data. *Bioinformatics Advances* (2026).

## License

[![License: Academic/Non-commercial](https://img.shields.io/badge/License-Academic%2FNon--commercial-blue.svg)](LICENSE.md)

Only for academic and research use. See [LICENSE.md](LICENSE.md) for details.

## Contact

Akihiro Ezoe — akihiro.ezoe@riken.jp
RIKEN Center for Sustainable Resource Science
