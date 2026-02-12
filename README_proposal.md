# EZ-Pair Graph

**A scalable unified-axis visualization for summarizing large-scale paired data**

[![License: Academic/Non-commercial](https://img.shields.io/badge/License-Academic%2FNon--commercial-blue.svg)](LICENSE.md)

Free for academic and research use. See [LICENSE.md](LICENSE.md) for details.

## Overview

EZ-Pair Graph is a suite of visualization methods that summarizes large-scale paired data while preserving directional and magnitude information on a unified axis. It produces three complementary plot types:

| Plot | Best for | Description |
|------|----------|-------------|
| **Trapezoid plot** | Quick summary of overall trends | Summarizes ascending/descending groups using quartile-based trapezoids |
| **Clustered line plot** | Detecting subgroup patterns | Groups paired connections by clustering, with color intensity indicating cluster size |
| **Parallel arrow plot** | Comparing direction and magnitude | Displays clustered differences as parallel arrows between boxplots |

These methods are particularly effective for datasets where conventional visualizations (slope graphs, Bland-Altman plots) suffer from visual saturation.

<img width="2403" height="883" alt="EZ-Pair Graph output examples" src="https://github.com/user-attachments/assets/a0fb21c0-dde7-4ff6-9e51-be7fa00f9cbf" />

## Installation

### Option 1: Docker (recommended)

```bash
git clone https://github.com/010049nn/EZ_pair_graph.git
cd EZ_pair_graph
docker build -t ez_pair_graph .
```

### Option 2: Local installation

Requires Python 3.x with the following packages:

```bash
pip install numpy pandas matplotlib scipy
```

No additional external libraries are required. HDBSCAN clustering is implemented natively without external dependencies.

## Tutorial: Getting Started with the Test Dataset

This section walks through a complete analysis using the included test dataset.

### Step 1: Run the pipeline

```bash
# Using Docker
docker run --rm \
    -v $(pwd)/output_EZ:/app/output_EZ \
    ez_pair_graph \
    bash ./pipeline_for_EZ_plot.sh test_dataset.txt

# Or locally
bash pipeline_for_EZ_plot.sh test_dataset.txt
```

### Step 2: Check the output

Four plot files are generated in `output_EZ/`:

```
output_EZ/
├── slopegraph.pdf              # Raw paired data as a slope graph
├── trapezoid.pdf               # Trapezoid plot summary
├── boxplot_with_lines.pdf      # Clustered line plot
└── arrow_boxplot_chart.pdf     # Parallel arrow plot
```

### Step 3: Interpret the plots

**Slope graph** (`slopegraph.pdf`): Shows all individual paired connections. Green lines indicate ascending pairs (Y > X), red lines indicate descending pairs (Y < X). This is the conventional view — note how lines overlap heavily even with moderate sample sizes.

**Trapezoid plot** (`trapezoid.pdf`): Summarizes the paired data into two groups:
- Green trapezoid = ascending group (Y > X)
- Red trapezoid = descending group (Y < X)
- Line thickness reflects the number of observations in each group
- The Q1, Q2 (median), and Q3 lines show the quartile structure of each group's starting positions and differences

**Clustered line plot** (`boxplot_with_lines.pdf`): Pairs are grouped into clusters using hierarchical clustering. Each cluster is represented by its median line (Q2). Color intensity and line thickness indicate the number of observations in each cluster, making it easy to identify dominant trends.

**Parallel arrow plot** (`arrow_boxplot_chart.pdf`): Each cluster from the clustered line plot is displayed as a vertical arrow between boxplots. Upward arrows (left side) represent ascending groups; downward arrows (right side) represent descending groups. Arrow thickness reflects cluster size.

### Step 4: Try different options

```bash
# Output as SVG for editing in Illustrator/Inkscape
bash pipeline_for_EZ_plot.sh test_dataset.txt --format svg

# Show cluster sizes on the plot
bash pipeline_for_EZ_plot.sh test_dataset.txt --show-numbers

# Use HDBSCAN clustering instead of hierarchical
bash pipeline_for_EZ_plot.sh test_dataset.txt --method hdbscan --min_cluster_size 3

# Combine multiple options
bash pipeline_for_EZ_plot.sh test_dataset.txt --format png --show-numbers --no-outliers
```

## Tutorial: Analyzing Your Own Data

### Preparing input data

Create a text file with two columns (paired values). Headers are auto-detected:

```
Group_A    Group_B
45.2       42.1
38.7       41.3
52.0       48.9
...
```

Supported formats: space-separated, tab-separated, or comma-separated (CSV).

### Running the analysis

```bash
# Local
bash pipeline_for_EZ_plot.sh your_data.txt --output-prefix my_analysis --show-numbers

# Docker
docker run --rm \
    -v $(pwd)/data:/data \
    -v $(pwd)/output_EZ:/app/output_EZ \
    ez_pair_graph \
    bash ./pipeline_for_EZ_plot.sh /data/your_data.txt --output-prefix my_analysis --show-numbers
```

### For gene expression data (log-scale)

```bash
bash pipeline_for_EZ_plot.sh expression_data.txt --log2 --output-prefix gene_exp
```

Non-positive values are automatically handled (replaced with 1e-10 before log2 transformation).

## Clustering Methods

EZ-Pair Graph provides two deterministic clustering algorithms, both of which produce identical results for the same input data and parameters:

### Hierarchical clustering (default)

- Uses agglomerative hierarchical clustering with Ward's minimum variance method
- The optimal number of clusters is determined automatically using the elbow method based on within-cluster sum of squares
- Controlled by `--max_k` (maximum clusters, default: 7) and `--linkage` (default: ward)

### HDBSCAN

- Density-based clustering that does not require specifying the number of clusters
- Better for datasets with varying cluster densities
- Controlled by `--min_cluster_size` (default: 5) and `--min_samples`

Observations are first separated by direction of change (ascending: B−A ≥ 0; descending: B−A < 0), and clustering is performed independently within each group. Clusters whose median points fall outside the 1.5×IQR whisker range of the boxplots are treated as outliers and excluded from the visualization.

## Command Line Options

### Output Options

| Option | Description |
|--------|-------------|
| `--format FORMAT` | Output format: `pdf` (default), `svg`, `png`, `html`, `json` |
| `--output-prefix PREFIX` | Prefix for output filenames (e.g., 'exp1' creates exp1_slopegraph.pdf) |
| `--no-outliers` | Hide outliers in boxplots |
| `--log2` | Apply log2 transformation to values |
| `--show-numbers` | Display cluster numbers or sample counts on plots |

### Clustering Options

| Option | Description |
|--------|-------------|
| `--method METHOD` | Clustering method: `hierarchical` (default) or `hdbscan` |
| `--max_k N` | Maximum number of clusters for hierarchical clustering (default: 7) |
| `--linkage METHOD` | Linkage method: `ward` (default), `complete`, `average`, `single` |
| `--min_cluster_size N` | Minimum cluster size for HDBSCAN (default: 5) |
| `--min_samples N` | Minimum samples for HDBSCAN core points (default: None) |

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

## Dependencies

- Python 3.x
- NumPy
- Pandas
- Matplotlib
- SciPy

All clustering algorithms (hierarchical and HDBSCAN) are implemented natively using NumPy/SciPy. No additional packages are required.

## Citation

If you use EZ-Pair Graph in your research, please cite:

> Ezoe, A., Seki, M. and Mochida, K. EZ-Pair Graph: A scalable unified-axis visualization for summarizing large-scale paired data. *Bioinformatics Advances* (2025).

## License

This software is free for academic and non-commercial research use. See [LICENSE.md](LICENSE.md) for full terms.

## Contact

Akihiro Ezoe — akihiro.ezoe@riken.jp  
RIKEN Center for Sustainable Resource Science
